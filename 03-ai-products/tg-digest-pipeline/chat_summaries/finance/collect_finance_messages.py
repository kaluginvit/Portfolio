"""
Collect raw Telegram messages from the folder "Финансы" into SQLite.

Default period: 2026-01-01 through 2026-07-25.

Run:
    uv run python finance/collect_finance_messages.py
    uv run python finance/collect_finance_messages.py --mark-read
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DocumentAttributeVideo, MessageEntityTextUrl, MessageMediaDocument, MessageMediaWebPage


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent
REPO_ROOT = PROJECT_ROOT.parent
DB_PATH = PROJECT_ROOT / "finance_messages.db"
FOLDER_NAME = "Финансы"
SESSION_NAME = "session2"
START_DEFAULT = date(2026, 1, 1)
END_DEFAULT = date(2026, 7, 25)

URL_RE = re.compile(
    r"(?P<url>(?:https?://|www\.)[^\s<>\"]+|t\.me/[^\s<>\"]+)",
    re.IGNORECASE,
)
TRAILING_PUNCTUATION = """.,;:!?)\]}'" """


def utc_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def utc_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def folder_title(folder) -> str:
    title = getattr(folder, "title", "") or ""
    return title.text if hasattr(title, "text") else str(title)


def normalize_link(url: str) -> str:
    url = url.strip().strip(TRAILING_PUNCTUATION)
    if url.startswith("www."):
        url = f"https://{url}"
    if url.startswith("t.me/"):
        url = f"https://{url}"
    return url


def extract_links(msg) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    def add(url: str | None) -> None:
        if not url:
            return
        link = normalize_link(str(url))
        if link and link not in seen:
            seen.add(link)
            links.append(link)

    for match in URL_RE.finditer(msg.raw_text or msg.text or ""):
        add(match.group("url"))
    for entity in getattr(msg, "entities", None) or []:
        if isinstance(entity, MessageEntityTextUrl):
            add(entity.url)
    if isinstance(getattr(msg, "media", None), MessageMediaWebPage):
        add(getattr(msg.media.webpage, "url", None))
    return links


def media_info(msg) -> tuple[int, str, float | None]:
    if not msg.media:
        return 0, "", None
    if isinstance(msg.media, MessageMediaDocument):
        doc = msg.media.document
        media_type = doc.mime_type or "document"
        duration_sec = None
        for attr in doc.attributes:
            if isinstance(attr, DocumentAttributeVideo):
                media_type = "video"
                duration_sec = float(attr.duration or 0)
        return 1, media_type, duration_sec
    return 1, type(msg.media).__name__, None


def post_url(username: str | None, entity_id: int, message_id: int) -> str:
    if username:
        return f"https://t.me/{username}/{message_id}"
    return f"https://t.me/c/{abs(entity_id)}/{message_id}"


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS sources (
            source_peer_id       INTEGER PRIMARY KEY,
            title                TEXT NOT NULL,
            username             TEXT,
            entity_id            INTEGER,
            access_hash          INTEGER,
            type                 TEXT,
            first_seen_at        TEXT NOT NULL,
            last_seen_at         TEXT NOT NULL,
            last_collected_until TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            source_peer_id INTEGER NOT NULL REFERENCES sources(source_peer_id),
            message_id     INTEGER NOT NULL,
            date           TEXT NOT NULL,
            edited_at      TEXT,
            sender_id      INTEGER,
            sender_name    TEXT,
            text           TEXT,
            text_len       INTEGER NOT NULL DEFAULT 0,
            reply_to       INTEGER,
            views          INTEGER,
            forwards       INTEGER,
            replies        INTEGER,
            reactions      INTEGER,
            has_media      INTEGER NOT NULL DEFAULT 0,
            media_type     TEXT,
            video_duration_sec REAL,
            post_url       TEXT,
            links_json     TEXT,
            fetched_at     TEXT NOT NULL,
            PRIMARY KEY(source_peer_id, message_id)
        );

        CREATE INDEX IF NOT EXISTS idx_finance_messages_date ON messages(date);
        CREATE INDEX IF NOT EXISTS idx_finance_messages_source_date ON messages(source_peer_id, date);
        """
    )
    con.commit()


def reaction_count(msg) -> int | None:
    reactions = getattr(msg, "reactions", None)
    if not reactions or not getattr(reactions, "results", None):
        return None
    return sum(int(getattr(item, "count", 0) or 0) for item in reactions.results)


def reply_count(msg) -> int | None:
    replies = getattr(msg, "replies", None)
    return getattr(replies, "replies", None) if replies else None


def upsert_source(con: sqlite3.Connection, entity, collected_until: date) -> tuple[int, str, str | None, int]:
    now = datetime.now(timezone.utc).isoformat()
    entity_id = int(getattr(entity, "id", 0) or 0)
    source_peer_id = abs(entity_id)
    title = getattr(entity, "title", None) or getattr(entity, "first_name", None) or str(entity_id)
    username = getattr(entity, "username", None)
    access_hash = getattr(entity, "access_hash", None)
    entity_type = type(entity).__name__
    con.execute(
        """
        INSERT INTO sources (
            source_peer_id, title, username, entity_id, access_hash, type,
            first_seen_at, last_seen_at, last_collected_until
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_peer_id) DO UPDATE SET
            title=excluded.title,
            username=excluded.username,
            entity_id=excluded.entity_id,
            access_hash=excluded.access_hash,
            type=excluded.type,
            last_seen_at=excluded.last_seen_at,
            last_collected_until=excluded.last_collected_until
        """,
        (
            source_peer_id,
            title,
            username,
            entity_id,
            access_hash,
            entity_type,
            now,
            now,
            collected_until.isoformat(),
        ),
    )
    return source_peer_id, title, username, entity_id


def save_message(
    con: sqlite3.Connection,
    source_peer_id: int,
    username: str | None,
    entity_id: int,
    msg,
) -> None:
    text = msg.raw_text or msg.text or ""
    has_media, media_type, duration_sec = media_info(msg)
    links = extract_links(msg)
    sender_name = ""
    if msg.sender:
        first_name = getattr(msg.sender, "first_name", "") or ""
        last_name = getattr(msg.sender, "last_name", "") or ""
        username_sender = getattr(msg.sender, "username", "") or ""
        sender_name = f"{first_name} {last_name}".strip() or username_sender
    con.execute(
        """
        INSERT INTO messages (
            source_peer_id, message_id, date, edited_at, sender_id, sender_name,
            text, text_len, reply_to, views, forwards, replies, reactions,
            has_media, media_type, video_duration_sec, post_url, links_json, fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_peer_id, message_id) DO UPDATE SET
            date=excluded.date,
            edited_at=excluded.edited_at,
            sender_id=excluded.sender_id,
            sender_name=excluded.sender_name,
            text=excluded.text,
            text_len=excluded.text_len,
            reply_to=excluded.reply_to,
            views=excluded.views,
            forwards=excluded.forwards,
            replies=excluded.replies,
            reactions=excluded.reactions,
            has_media=excluded.has_media,
            media_type=excluded.media_type,
            video_duration_sec=excluded.video_duration_sec,
            post_url=excluded.post_url,
            links_json=excluded.links_json,
            fetched_at=excluded.fetched_at
        """,
        (
            source_peer_id,
            msg.id,
            msg.date.isoformat(),
            msg.edit_date.isoformat() if getattr(msg, "edit_date", None) else None,
            msg.sender_id,
            sender_name,
            text,
            len(text),
            msg.reply_to_msg_id,
            getattr(msg, "views", None),
            getattr(msg, "forwards", None),
            reply_count(msg),
            reaction_count(msg),
            has_media,
            media_type,
            duration_sec,
            post_url(username, entity_id, msg.id),
            json.dumps(links, ensure_ascii=False) if links else None,
            datetime.now(timezone.utc).isoformat(),
        ),
    )


async def collect_source(
    con: sqlite3.Connection,
    client: TelegramClient,
    entity,
    start: date,
    end: date,
    mark_read: bool,
) -> dict:
    source_peer_id, title, username, entity_id = upsert_source(con, entity, end)
    con.commit()
    seen = saved = skipped_empty = 0
    max_message_id = 0
    print(f"  {title} ...", end=" ", flush=True)
    try:
        async for msg in client.iter_messages(entity, offset_date=utc_end(end)):
            if not msg.date:
                continue
            msg_dt = msg.date.astimezone(timezone.utc)
            if msg_dt < utc_start(start):
                break
            seen += 1
            max_message_id = max(max_message_id, int(msg.id))
            if not (msg.raw_text or msg.text or msg.media):
                skipped_empty += 1
                continue
            save_message(con, source_peer_id, username, entity_id, msg)
            saved += 1
            if saved % 500 == 0:
                con.commit()
                print(f"{saved}...", end="", flush=True)
        con.commit()
        if mark_read and max_message_id:
            await client.send_read_acknowledge(entity, max_id=max_message_id)
    except FloodWaitError as exc:
        con.commit()
        print(f"FloodWait {exc.seconds}s")
        return {"title": title, "seen": seen, "saved": saved, "read_to": None, "error": f"FloodWait {exc.seconds}s"}
    except Exception as exc:
        con.commit()
        print(f"ERROR: {exc}")
        return {"title": title, "seen": seen, "saved": saved, "read_to": None, "error": repr(exc)}

    print(f"seen={seen}, saved={saved}, empty={skipped_empty}, read_to={max_message_id if mark_read else '-'}")
    return {"title": title, "seen": seen, "saved": saved, "read_to": max_message_id if mark_read else None, "error": None}


async def main(start: date, end: date, mark_read: bool, session_name: str) -> None:
    load_dotenv(REPO_ROOT / ".env")
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

    con = sqlite3.connect(DB_PATH)
    init_db(con)

    client = TelegramClient(str(REPO_ROOT / session_name), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print(f"Сессия {session_name} не авторизована")
        await client.disconnect()
        return

    filters = await client(GetDialogFiltersRequest())
    folder = next(
        (
            item
            for item in filters.filters
            if hasattr(item, "title") and FOLDER_NAME.lower() in folder_title(item).lower()
        ),
        None,
    )
    if not folder:
        print(f"Папка «{FOLDER_NAME}» не найдена")
        await client.disconnect()
        return

    peers = getattr(folder, "include_peers", [])
    print(f"Источников: {len(peers)} | период: {start} — {end} | mark_read={mark_read}")
    results = []
    for peer in peers:
        try:
            entity = await client.get_entity(peer)
        except Exception as exc:
            print(f"  peer error: {exc}")
            continue
        results.append(await collect_source(con, client, entity, start, end, mark_read))

    await client.disconnect()
    total_messages = con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    total_sources = con.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    with_links = con.execute("SELECT COUNT(*) FROM messages WHERE links_json IS NOT NULL").fetchone()[0]
    with_video = con.execute("SELECT COUNT(*) FROM messages WHERE media_type = 'video'").fetchone()[0]
    min_date, max_date = con.execute("SELECT MIN(date), MAX(date) FROM messages").fetchone()
    con.close()

    print()
    print(f"БД: {DB_PATH}")
    print(f"Источников в БД: {total_sources}")
    print(f"Сообщений в БД: {total_messages}")
    print(f"Диапазон дат: {min_date} — {max_date}")
    print(f"Сообщений со ссылками: {with_links}")
    print(f"Сообщений с видео: {with_video}")
    print(f"Ошибок источников: {sum(1 for item in results if item.get('error'))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=date.fromisoformat, default=START_DEFAULT)
    parser.add_argument("--end", type=date.fromisoformat, default=END_DEFAULT)
    parser.add_argument("--mark-read", action="store_true", help="Mark each source as read up to the last collected message.")
    parser.add_argument("--session-name", default=SESSION_NAME)
    args = parser.parse_args()
    asyncio.run(main(args.start, args.end, args.mark_read, args.session_name))
