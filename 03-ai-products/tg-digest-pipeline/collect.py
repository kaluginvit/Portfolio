"""
Telethon-коллектор: дочитывает новые посты канала с момента последнего в БД.

Использование:
    python collect.py [--since YYYY-MM-DD]

Требуется .env с переменными:
    TG_API_ID=...
    TG_API_HASH=...
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent

from dotenv import load_dotenv
import os

load_dotenv(HERE / ".env")

from db import connect_rw, one
from schema import init_db


# ---------------------------------------------------------------------------
# Вспомогательные функции (совместимы с import_json.py)
# ---------------------------------------------------------------------------

def _extract_text(message) -> str:
    """Извлечь текст из telethon Message."""
    return message.message or ""


def _extract_links_from_entities(message) -> list[str]:
    """Извлечь URL из MessageEntityTextUrl."""
    links: list[str] = []
    if not message.entities:
        return links
    text = message.message or ""
    for ent in message.entities:
        from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl
        if isinstance(ent, MessageEntityTextUrl):
            links.append(ent.url)
        elif isinstance(ent, MessageEntityUrl):
            fragment = text[ent.offset: ent.offset + ent.length]
            links.append(fragment)
    return links


def _extract_hashtags(text: str) -> list[str]:
    import re
    return re.findall(r"#\w+", text)


def _dt_to_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------------------
# Основная логика
# ---------------------------------------------------------------------------

async def collect(since_override: str | None = None) -> None:
    api_id_raw = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")

    if not api_id_raw or not api_hash:
        print("Ошибка: TG_API_ID и TG_API_HASH должны быть заданы в .env")
        sys.exit(1)

    api_id = int(api_id_raw)

    # Читаем конфиг
    config_path = HERE / "config.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    channel: str = config["channel"]
    session_name: str = str(HERE / config["session"])

    db_path = HERE / config.get("data_dir", "data") / "messages.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = init_db(db_path)

    # Определяем since
    if since_override:
        since_str = since_override
    else:
        row = one(con, "SELECT MAX(date) AS max_date FROM messages")
        since_str = row.get("max_date") or "2019-01-01T00:00:00"
        # Берём только дату, если пришла дата+время
        if "T" in since_str:
            since_str = since_str  # оставляем как есть

    since_dt = datetime.fromisoformat(since_str).replace(tzinfo=timezone.utc)
    print(f"Канал: {channel}")
    print(f"Получаем посты начиная с: {since_str}")

    from telethon import TelegramClient
    from telethon.errors import FloodWaitError

    client = TelegramClient(session_name, api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print(
            "\nСессия не авторизована. Выполните вход вручную:\n"
            "  1. Запустите интерактивный Python в этой директории\n"
            "  2. from telethon import TelegramClient\n"
            f"  3. client = TelegramClient('{session_name}', {api_id}, '<api_hash>')\n"
            "  4. await client.start()\n"
            "  5. (введите номер телефона и код подтверждения)\n"
            "После этого повторно запустите collect.py."
        )
        await client.disconnect()
        sys.exit(1)

    imported = 0

    try:
        async for message in client.iter_messages(channel, reverse=True, offset_date=since_dt):
            # Пропускаем сервисные сообщения
            if message.message is None and not hasattr(message, "media"):
                continue

            message_id: int = message.id
            date_str: str = _dt_to_iso(message.date.astimezone(timezone.utc))
            edited_str: str | None = (
                _dt_to_iso(message.edit_date.astimezone(timezone.utc))
                if message.edit_date
                else None
            )

            text = _extract_text(message)
            links = _extract_links_from_entities(message)
            raw_tags = _extract_hashtags(text)

            # Пересылка
            fwd_from: str | None = None
            fwd_from_id: str | None = None
            if message.fwd_from:
                fwd = message.fwd_from
                if hasattr(fwd, "from_name") and fwd.from_name:
                    fwd_from = fwd.from_name
                if hasattr(fwd, "from_id") and fwd.from_id:
                    fwd_from_id = str(fwd.from_id)

            # Фото
            photo: str | None = None
            has_photo = 0
            try:
                from telethon.tl.types import MessageMediaPhoto
                if isinstance(message.media, MessageMediaPhoto):
                    photo = f"photo_{message_id}.jpg"
                    has_photo = 1
            except Exception:
                pass

            try:
                con.execute(
                    """
                    INSERT OR IGNORE INTO messages
                        (message_id, date, text, forwarded_from, forwarded_from_id,
                         photo, has_photo, edited, links, raw_tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        date_str,
                        text,
                        fwd_from,
                        fwd_from_id,
                        photo,
                        has_photo,
                        edited_str,
                        json.dumps(links, ensure_ascii=False),
                        json.dumps(raw_tags, ensure_ascii=False),
                    ),
                )
                if con.execute("SELECT changes()").fetchone()[0] > 0:
                    con.execute(
                        "INSERT INTO messages_fts(message_id, text) VALUES (?, ?)",
                        (message_id, text),
                    )
                    imported += 1
            except Exception as exc:
                print(f"  [WARN] message_id={message_id}: {exc}")

    except FloodWaitError as e:
        print(f"FloodWait: ждём {e.seconds} секунд...")
        await asyncio.sleep(e.seconds)

    con.commit()
    con.close()
    await client.disconnect()

    print(f"\nНовых постов: {imported}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Телеграм-коллектор для @infopovod")
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Собирать посты начиная с даты YYYY-MM-DD (по умолчанию: MAX(date) из БД)",
    )
    args = parser.parse_args()
    asyncio.run(collect(since_override=args.since))


if __name__ == "__main__":
    main()
