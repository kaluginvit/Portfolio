"""
Единый коллектор сообщений для всех чатов из chats.json.

Конфиг чата поддерживает два режима:
  "chat": "@username"          — прямой доступ по username/slug
  "chat_titles": ["Название"]  — поиск по заголовку в iter_dialogs (все совпадения)

Использование:
    uv run python chat_summaries/collect.py nebaffet
    uv run python chat_summaries/collect.py pesochnitsa --since 2026-06-01
    uv run python chat_summaries/collect.py --all
"""

import argparse
import asyncio
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageEntityTextUrl, MessageMediaWebPage

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parents[1]
CHATS_CFG = Path(__file__).parent / "chats.json"
URL_RE = re.compile(
    r"(?P<url>(?:https?://|www\.)[^\s<>\"]+|t\.me/[^\s<>\"]+)",
    re.IGNORECASE,
)
TRAILING_PUNCTUATION = """.,;:!?)\]}'" """


def load_config() -> dict:
    return json.loads(CHATS_CFG.read_text(encoding="utf-8"))["chats"]


def init_db(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            source_peer_id  INTEGER NOT NULL DEFAULT 0,
            message_id      INTEGER NOT NULL,
            date            TEXT,
            sender_id       INTEGER,
            sender_name     TEXT,
            text            TEXT,
            reply_to        INTEGER,
            links           TEXT,
            analyzed_at     TEXT,
            PRIMARY KEY (source_peer_id, message_id)
        );
        CREATE INDEX IF NOT EXISTS idx_date ON messages(date);
    """)
    # Миграция старых БД
    cols = {r[1] for r in con.execute("PRAGMA table_info(messages)")}
    if "source_peer_id" not in cols:
        con.executescript("""
            ALTER TABLE messages ADD COLUMN source_peer_id INTEGER NOT NULL DEFAULT 0;
            CREATE UNIQUE INDEX IF NOT EXISTS idx_source_msg
                ON messages(source_peer_id, message_id);
        """)
    if "analyzed_at" not in cols:
        con.execute("ALTER TABLE messages ADD COLUMN analyzed_at TEXT")
    if "reply_to" not in cols:
        con.execute("ALTER TABLE messages ADD COLUMN reply_to INTEGER")
    if "links" not in cols:
        con.execute("ALTER TABLE messages ADD COLUMN links TEXT")
    con.commit()


def extract_links(msg) -> list[str]:
    links = []
    seen = set()

    def add(url: str | None) -> None:
        if not url:
            return
        url = url.strip().strip(TRAILING_PUNCTUATION)
        if url.startswith("www."):
            url = f"https://{url}"
        if url.startswith("t.me/"):
            url = f"https://{url}"
        if url and url not in seen:
            seen.add(url)
            links.append(url)

    for match in URL_RE.finditer(msg.raw_text or msg.text or ""):
        add(match.group("url"))

    if msg.entities:
        for ent in msg.entities:
            if isinstance(ent, MessageEntityTextUrl):
                add(ent.url)
    if isinstance(msg.media, MessageMediaWebPage):
        url = getattr(msg.media.webpage, "url", None)
        add(url)
    return links


async def find_entities(client: TelegramClient, cfg: dict) -> list[tuple]:
    """Возвращает список (peer_id, entity) для сбора."""
    if "chat" in cfg:
        entity = await client.get_entity(cfg["chat"])
        peer_id = getattr(entity, "id", 0)
        # Для групп (negative ID) нормализуем к положительному
        if peer_id < 0:
            peer_id = abs(peer_id)
        return [(peer_id, entity)]

    titles = [t.lower() for t in cfg["chat_titles"]]
    results = []
    print(f"  Ищем в диалогах: {cfg['chat_titles']}...")
    async for dialog in client.iter_dialogs():
        name = (dialog.name or "").lower()
        if any(t in name for t in titles):
            peer_id = getattr(dialog.entity, "id", 0)
            print(f"  Найдено: «{dialog.name}» (peer_id={peer_id})")
            results.append((peer_id, dialog.entity))
    return results


async def collect_entity(
    con: sqlite3.Connection,
    client: TelegramClient,
    peer_id: int,
    entity,
    since: datetime,
    label: str,
    until: datetime | None = None,
) -> int:
    existing = {
        r[0] for r in con.execute(
            "SELECT message_id FROM messages WHERE source_peer_id = ?", (peer_id,)
        )
    }
    print(f"  [{label}] peer_id={peer_id} | в БД: {len(existing)}")

    count = 0
    try:
        async for msg in client.iter_messages(entity):
            if not msg.date:
                continue
            msg_dt = msg.date.replace(tzinfo=timezone.utc)
            if until and msg_dt > until:
                continue
            if msg_dt < since:
                break
            if msg.id in existing:
                continue

            text = msg.text or ""
            links = extract_links(msg)
            if not text and not links:
                continue

            sender_name = ""
            if msg.sender:
                fn = getattr(msg.sender, "first_name", "") or ""
                ln = getattr(msg.sender, "last_name", "") or ""
                un = getattr(msg.sender, "username", "") or ""
                sender_name = f"{fn} {ln}".strip() or un

            con.execute(
                "INSERT OR IGNORE INTO messages"
                " (source_peer_id, message_id, date, sender_id, sender_name, text, reply_to, links)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (
                    peer_id,
                    msg.id,
                    msg.date.isoformat(),
                    msg.sender_id,
                    sender_name,
                    text,
                    msg.reply_to_msg_id,
                    json.dumps(links, ensure_ascii=False) if links else None,
                ),
            )
            count += 1
            if count % 500 == 0:
                con.commit()
                print(f"  [{label}] ...{count}")

        con.commit()
    except FloodWaitError as exc:
        con.commit()
        print(f"  [{label}] FloodWait {exc.seconds}s — прервано.")

    total = con.execute(
        "SELECT COUNT(*) FROM messages WHERE source_peer_id = ?", (peer_id,)
    ).fetchone()[0]
    print(f"  [{label}] Новых: {count} | Всего: {total}")
    return count


async def collect_chat(chat_name: str, cfg: dict, since_override: str | None, until_override: str | None = None) -> None:
    load_dotenv(ROOT / ".env")
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session = cfg["session"]

    since_str = since_override or cfg["since"]
    since = datetime.fromisoformat(since_str).replace(tzinfo=timezone.utc)
    until = datetime.fromisoformat(until_override).replace(tzinfo=timezone.utc) if until_override else None

    db_dir = Path(__file__).parent / cfg.get("folder", chat_name)
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "messages.db"

    con = sqlite3.connect(db_path)
    init_db(con)

    print(f"\n[{chat_name}] С: {since_str} | Сессия: {session}")

    client = TelegramClient(str(ROOT / session), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print(f"[{chat_name}] Сессия {session} не авторизована — пропуск.")
        await client.disconnect()
        con.close()
        return

    entities = await find_entities(client, cfg)
    if not entities:
        print(f"[{chat_name}] Источники не найдены.")
        await client.disconnect()
        con.close()
        return

    for peer_id, entity in entities:
        label = getattr(entity, "title", None) or getattr(entity, "username", None) or str(peer_id)
        await collect_entity(con, client, peer_id, entity, since, label, until=until)
        max_id = con.execute(
            "SELECT MAX(message_id) FROM messages WHERE source_peer_id = ?", (peer_id,)
        ).fetchone()[0]
        if max_id:
            try:
                await client.send_read_acknowledge(entity, max_id=max_id)
                print(f"  [{label}] Отмечено прочитанным до message_id={max_id}")
            except Exception as exc:
                print(f"  [{label}] mark_read не удался: {exc}")

    await client.disconnect()
    con.close()


async def _mark_read_from_db(api_id: int, api_hash: str, targets: list[str], cfg: dict) -> None:
    """Пометить все source_peer_id из БД как прочитанные после коллекта."""
    valid = [n for n in targets if n in cfg]
    if not valid:
        return

    by_session: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for name in valid:
        by_session[cfg[name]["session"]].append((name, cfg[name]))

    print("\n[mark_read] Помечаем источники из БД как прочитанные...")

    for session_name, chats in sorted(by_session.items()):
        client = TelegramClient(str(ROOT / session_name), api_id, api_hash)
        await client.connect()
        if not await client.is_user_authorized():
            print(f"  {session_name}: не авторизована — пропуск")
            await client.disconnect()
            continue

        for name, chat_cfg in chats:
            folder = chat_cfg.get("folder", name)
            db_path = Path(__file__).parent / folder / "messages.db"
            if not db_path.exists():
                continue
            con = sqlite3.connect(db_path)
            rows = con.execute(
                "SELECT source_peer_id, MAX(message_id) FROM messages GROUP BY source_peer_id"
            ).fetchall()
            con.close()
            if not rows:
                continue

            try:
                if chat_cfg.get("chat_titles"):
                    titles = [t.lower() for t in chat_cfg["chat_titles"]]
                    async for dialog in client.iter_dialogs():
                        if any(t in (dialog.name or "").lower() for t in titles):
                            peer_id = abs(getattr(dialog.entity, "id", 0))
                            max_id = next((r[1] for r in rows if r[0] == peer_id), rows[0][1])
                            await client.send_read_acknowledge(dialog.entity, max_id=max_id)
                            print(f"  {name}: до {max_id}")
                            break
                else:
                    entity = await client.get_entity(chat_cfg["chat"])
                    peer_id = abs(getattr(entity, "id", 0))
                    max_id = next((r[1] for r in rows if r[0] == peer_id), max(r[1] for r in rows))
                    await client.send_read_acknowledge(entity, max_id=max_id)
                    print(f"  {name}: до {max_id}")
            except Exception as exc:
                print(f"  {name}: mark_read — {exc}")

        await client.disconnect()

    print("[mark_read] Готово.")


async def run(args: argparse.Namespace) -> None:
    cfg = load_config()
    if args.all:
        targets = list(cfg.keys())
    elif args.folder:
        targets = [
            name
            for name, chat_cfg in cfg.items()
            if chat_cfg.get("folder", name) == args.folder
        ]
        if not targets:
            print(f"No chats with folder={args.folder!r} in chats.json.")
            return
    else:
        targets = [args.chat]

    for name in targets:
        if name not in cfg:
            print(f"Чат «{name}» не найден в chats.json. Доступные: {', '.join(cfg)}")
            continue
        await collect_chat(name, cfg[name], args.since, args.until)

    load_dotenv(ROOT / ".env")
    await _mark_read_from_db(
        int(os.environ["TG_API_ID"]),
        os.environ["TG_API_HASH"],
        targets,
        cfg,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Collect TG chat messages into SQLite")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("chat", nargs="?", help="Имя чата из chats.json")
    group.add_argument("--all", action="store_true", help="Собрать все чаты")
    p.add_argument("--since", metavar="YYYY-MM-DD", help="Переопределить дату начала")
    p.add_argument("--until", metavar="YYYY-MM-DD", help="Верхняя граница (включительно)")
    group.add_argument("--folder", help="Collect all chats whose folder value matches this name")
    asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    main()
