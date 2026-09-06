"""
Импорт сообщений из «Избранного» (Saved Messages) обоих аккаунтов.

Offset для message_id (избегаем коллизий с ID канала):
  Виталий @KaluginVit    → +1_000_000_000
  Андрей @grey_rhinocero → +2_000_000_000

Дата-отсечка: <= 2026-08-31

Использование:
    python import_saved.py
    python import_saved.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import (
    MessageEntityTextUrl,
    MessageEntityUrl,
    MessageMediaPhoto,
    PeerChannel,
    PeerUser,
    PeerChat,
)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"

load_dotenv(HERE / ".env")

API_ID   = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]

CUTOFF_DATE = datetime(2026, 8, 31, 23, 59, 59, tzinfo=timezone.utc)

ACCOUNTS = [
    {
        "session": str(HERE.parent / "session2"),
        "source":  "saved_vitaliy",
        "offset":  1_000_000_000,
        "label":   "Виталий @KaluginVit",
    },
    {
        "session": str(HERE.parent / "session"),
        "source":  "saved_andrey",
        "offset":  2_000_000_000,
        "label":   "Андрей @grey_rhinocero",
    },
]


# ---------------------------------------------------------------------------
# Миграция: добавляем колонку source
# ---------------------------------------------------------------------------

def migrate_source_column(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(messages)").fetchall()]
        if "source" not in cols:
            print("Миграция: добавляем колонку source …")
            con.execute("ALTER TABLE messages ADD COLUMN source TEXT DEFAULT 'channel'")
            con.execute("UPDATE messages SET source = 'channel' WHERE source IS NULL")
            con.execute("CREATE INDEX IF NOT EXISTS idx_messages_source ON messages(source)")
            con.commit()
            print("  OK — source добавлена, все старые записи = 'channel'")
        else:
            print("Колонка source уже есть.")
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _extract_links(msg) -> list[str]:
    links = []
    if not msg.entities:
        return links
    text = msg.message or ""
    for ent in msg.entities:
        if isinstance(ent, MessageEntityTextUrl):
            links.append(ent.url)
        elif isinstance(ent, MessageEntityUrl):
            links.append(text[ent.offset: ent.offset + ent.length])
    return links


def _fwd_name(fwd) -> str | None:
    if fwd is None:
        return None
    return fwd.from_name or None


def _fwd_id(fwd) -> str | None:
    if fwd is None or fwd.from_id is None:
        return None
    if isinstance(fwd.from_id, PeerChannel):
        return f"channel{fwd.from_id.channel_id}"
    if isinstance(fwd.from_id, PeerUser):
        return f"user{fwd.from_id.user_id}"
    if isinstance(fwd.from_id, PeerChat):
        return f"chat{fwd.from_id.chat_id}"
    return str(fwd.from_id)


# ---------------------------------------------------------------------------
# Импорт одного аккаунта
# ---------------------------------------------------------------------------

async def _import_account(acc: dict, db_path: Path, dry_run: bool) -> dict:
    client = TelegramClient(acc["session"], API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print(f"  [{acc['label']}] Не авторизован, пропускаем.")
        await client.disconnect()
        return {"imported": 0, "skipped_date": 0, "skipped_dup": 0, "errors": 0}

    con = sqlite3.connect(db_path)
    imported = skipped_date = skipped_dup = errors = 0
    total_seen = 0

    async for msg in client.iter_messages("me", limit=None):
        total_seen += 1

        if msg.date > CUTOFF_DATE:
            skipped_date += 1
            continue

        synthetic_id = msg.id + acc["offset"]
        text      = msg.message or ""
        links     = _extract_links(msg)
        has_photo = 1 if isinstance(msg.media, MessageMediaPhoto) else 0
        fwd_name  = _fwd_name(msg.fwd_from)
        fwd_id    = _fwd_id(msg.fwd_from)
        date_str  = msg.date.strftime("%Y-%m-%dT%H:%M:%S")

        if dry_run:
            imported += 1
            continue

        try:
            con.execute(
                """
                INSERT OR IGNORE INTO messages
                    (message_id, date, text, forwarded_from, forwarded_from_id,
                     has_photo, links, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    synthetic_id,
                    date_str,
                    text,
                    fwd_name,
                    fwd_id,
                    has_photo,
                    json.dumps(links, ensure_ascii=False),
                    acc["source"],
                ),
            )
            if con.execute("SELECT changes()").fetchone()[0] > 0:
                con.execute(
                    "INSERT INTO messages_fts(message_id, text) VALUES (?, ?)",
                    (synthetic_id, text),
                )
                imported += 1
            else:
                skipped_dup += 1

        except sqlite3.Error as exc:
            print(f"  [WARN] id={synthetic_id}: {exc}")
            errors += 1

        if (imported + skipped_dup) % 500 == 0 and (imported + skipped_dup) > 0:
            con.commit()
            print(f"  … {imported} импортировано, {total_seen} просмотрено")

    if not dry_run:
        con.commit()
    con.close()
    await client.disconnect()

    return {
        "imported": imported,
        "skipped_date": skipped_date,
        "skipped_dup": skipped_dup,
        "errors": errors,
        "total_seen": total_seen,
    }


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------

async def import_saved_messages(db_path: Path = DB_PATH, dry_run: bool = False) -> None:
    migrate_source_column(db_path)

    for acc in ACCOUNTS:
        print(f"\n=== {acc['label']} (source={acc['source']}, offset=+{acc['offset']:,}) ===")
        stats = await _import_account(acc, db_path, dry_run)
        print(f"  Просмотрено:              {stats['total_seen']}")
        print(f"  Импортировано:            {stats['imported']}")
        print(f"  Пропущено (дата > 31.08): {stats['skipped_date']}")
        print(f"  Пропущено (дубли):        {stats['skipped_dup']}")
        if stats["errors"]:
            print(f"  Ошибок:                   {stats['errors']}")

    if dry_run:
        print("\n[dry-run] Ничего не записано.")
    else:
        print("\nГотово. Запусти: python pipeline.py --gate  — чтобы добавить в очередь обогащения.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Импорт Избранного из двух аккаунтов")
    parser.add_argument("--dry-run", action="store_true", help="Показать что будет импортировано, ничего не писать")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    asyncio.run(import_saved_messages(db_path=args.db, dry_run=args.dry_run))
