"""
Collect document file metadata (filename, extension, size) from Telegram messages.

Does NOT download files — only reads message attributes via Telethon.
Stores results in finance_doc_files table in finance_messages.db.

Run:
    uv run python finance/fetch_doc_metadata.py --dry-run
    uv run python finance/fetch_doc_metadata.py
    uv run python finance/fetch_doc_metadata.py --start 2026-01-01 --end 2026-08-13
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    MessageMediaDocument,
    MessageMediaPhoto,
)


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
PROJECT_ROOT = ROOT.parent
DB_PATH = ROOT / "finance_messages.db"
FOLDER_NAME = "Финансы"
SESSION_NAME = "session2"
START_DEFAULT = date(2026, 1, 1)
END_DEFAULT = date(2026, 8, 13)

# MIME types that are NOT documents we care about
SKIP_MIME = {
    "video",
    "MessageMediaPhoto",
    "MessageMediaWebPage",
    "MessageMediaPoll",
    "MessageMediaGeo",
    "MessageMediaUnsupported",
    "MessageMediaGeoLive",
}


def utc_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def utc_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def folder_title(folder) -> str:
    title = getattr(folder, "title", "") or ""
    return title.text if hasattr(title, "text") else str(title)


MIME_TO_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/msword": ".doc",
    "text/markdown": ".md",
    "text/plain": ".txt",
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


def is_video_doc(doc) -> bool:
    return any(isinstance(a, DocumentAttributeVideo) for a in (doc.attributes or []))


def extract_doc_info(msg) -> dict | None:
    media = getattr(msg, "media", None)

    if isinstance(media, MessageMediaPhoto):
        photo = media.photo
        if not photo:
            return None
        # берём наибольший размер
        best = None
        for sz in getattr(photo, "sizes", []):
            w = getattr(sz, "w", 0)
            h = getattr(sz, "h", 0)
            s = getattr(sz, "size", 0)
            if s and (best is None or s > best["file_size"]):
                best = {"width": w, "height": h, "file_size": s}
        if best is None:
            return None
        return {
            "filename": None,
            "extension": ".jpg",
            "file_size": best["file_size"],
            "mime_type": "image/jpeg",
            "width": best["width"],
            "height": best["height"],
        }

    if isinstance(media, MessageMediaDocument):
        doc = media.document
        if is_video_doc(doc):
            return None  # видео обрабатывается отдельно
        mime = doc.mime_type or "application/octet-stream"
        filename = None
        for attr in (doc.attributes or []):
            if isinstance(attr, DocumentAttributeFilename):
                filename = attr.file_name
                break
        ext = Path(filename).suffix.lower() if filename else MIME_TO_EXT.get(mime, "")
        return {
            "filename": filename,
            "extension": ext,
            "file_size": doc.size or 0,
            "mime_type": mime,
            "width": None,
            "height": None,
        }

    return None


def init_db(con: sqlite3.Connection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS finance_doc_files (
            source_peer_id INTEGER NOT NULL,
            message_id     INTEGER NOT NULL,
            filename       TEXT,
            extension      TEXT,
            file_size      INTEGER,
            mime_type      TEXT,
            width          INTEGER,
            height         INTEGER,
            post_url       TEXT,
            indexed_at     TEXT NOT NULL,
            PRIMARY KEY (source_peer_id, message_id)
        )
    """)
    # добавляем колонки если таблица уже существует
    cols = {r[1] for r in con.execute("PRAGMA table_info(finance_doc_files)")}
    for col, defn in [("width", "INTEGER"), ("height", "INTEGER")]:
        if col not in cols:
            con.execute(f"ALTER TABLE finance_doc_files ADD COLUMN {col} {defn}")
    con.commit()


def save_doc(
    con: sqlite3.Connection,
    source_peer_id: int,
    message_id: int,
    post_url: str,
    info: dict,
) -> None:
    con.execute(
        """
        INSERT INTO finance_doc_files
            (source_peer_id, message_id, filename, extension, file_size, mime_type, width, height, post_url, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_peer_id, message_id) DO UPDATE SET
            filename=excluded.filename,
            extension=excluded.extension,
            file_size=excluded.file_size,
            mime_type=excluded.mime_type,
            width=excluded.width,
            height=excluded.height,
            post_url=excluded.post_url,
            indexed_at=excluded.indexed_at
        """,
        (
            source_peer_id,
            message_id,
            info["filename"],
            info["extension"],
            info["file_size"],
            info["mime_type"],
            info.get("width"),
            info.get("height"),
            post_url,
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def build_post_url(username: str | None, entity_id: int, message_id: int) -> str:
    if username:
        return f"https://t.me/{username}/{message_id}"
    return f"https://t.me/c/{abs(entity_id)}/{message_id}"


async def scan_source(
    con: sqlite3.Connection,
    client: TelegramClient,
    entity,
    start: date,
    end: date,
    dry_run: bool,
) -> dict:
    entity_id = int(getattr(entity, "id", 0) or 0)
    source_peer_id = abs(entity_id)
    title = getattr(entity, "title", None) or getattr(entity, "first_name", None) or str(entity_id)
    username = getattr(entity, "username", None)

    seen = saved = skipped = 0
    print(f"  {title} ...", end=" ", flush=True)
    try:
        async for msg in client.iter_messages(entity, offset_date=utc_end(end)):
            if not msg.date:
                continue
            if msg.date.astimezone(timezone.utc) < utc_start(start):
                break
            seen += 1
            info = extract_doc_info(msg)
            if info is None:
                skipped += 1
                continue
            url = build_post_url(username, entity_id, msg.id)
            if dry_run:
                dims = f" | {info['width']}x{info['height']}" if info.get("width") else ""
                print(f"\n    [dry] {url} | {info['mime_type']} | {info['filename']}{dims} | {info['file_size']} bytes")
            else:
                save_doc(con, source_peer_id, msg.id, url, info)
            saved += 1
            if not dry_run and saved % 20 == 0:
                con.commit()
        if not dry_run:
            con.commit()
    except FloodWaitError as exc:
        con.commit()
        print(f"FloodWait {exc.seconds}s — ждём...")
        await asyncio.sleep(exc.seconds + 3)
    except Exception as exc:
        con.commit()
        print(f"ERROR: {exc}")
        return {"title": title, "seen": seen, "saved": saved, "error": repr(exc)}

    print(f"seen={seen}, docs={saved}, non-doc={skipped}")
    return {"title": title, "seen": seen, "saved": saved, "error": None}


async def run(args: argparse.Namespace) -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

    con = sqlite3.connect(DB_PATH)
    init_db(con)

    client = TelegramClient(str(PROJECT_ROOT / args.session_name), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print(f"Сессия {args.session_name} не авторизована.")
        await client.disconnect()
        return

    filters = await client(GetDialogFiltersRequest())
    folder = next(
        (f for f in filters.filters if hasattr(f, "title") and FOLDER_NAME.lower() in folder_title(f).lower()),
        None,
    )
    if not folder:
        print(f"Папка «{FOLDER_NAME}» не найдена.")
        await client.disconnect()
        return

    peers = getattr(folder, "include_peers", [])
    print(f"Источников: {len(peers)} | период: {args.start} — {args.end} | dry_run={args.dry_run}")
    print()

    total_docs = 0
    for peer in peers:
        try:
            entity = await client.get_entity(peer)
        except Exception as exc:
            print(f"  peer error: {exc}")
            continue
        result = await scan_source(con, client, entity, args.start, args.end, args.dry_run)
        total_docs += result["saved"]

    await client.disconnect()

    if not args.dry_run:
        count = con.execute("SELECT COUNT(*) FROM finance_doc_files").fetchone()[0]
        by_ext = con.execute(
            "SELECT extension, COUNT(*), SUM(file_size) FROM finance_doc_files GROUP BY extension ORDER BY COUNT(*) DESC"
        ).fetchall()
        photos = con.execute("SELECT COUNT(*) FROM finance_doc_files WHERE mime_type='image/jpeg' AND filename IS NULL").fetchone()[0]
        print()
        print(f"Всего записей в finance_doc_files: {count}  (фото: {photos}, файлы: {count - photos})")
        print("По расширениям:")
        for r in by_ext:
            size_mb = round((r[2] or 0) / 1024 / 1024, 1)
            print(f"  {r[0] or '?'}: {r[1]} шт, {size_mb} MB")

    con.close()
    print(f"\nДокументов найдено в этом проходе: {total_docs}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=date.fromisoformat, default=START_DEFAULT)
    parser.add_argument("--end", type=date.fromisoformat, default=END_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--session-name", default=SESSION_NAME)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
