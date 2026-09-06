"""
Анализ источников из «Избранного»: резолвим forwarded_from_id,
проверяем критерии (≥500 подписчиков, активен, не в подписках),
дополняем tmp_final_channels.json.

Использование:
    python enrich_saved_sources.py [--dry-run]
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
from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError
from telethon.tl.functions.channels import GetFullChannelRequest

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"

load_dotenv(HERE / ".env")

API_ID   = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]

MIN_SUBSCRIBERS  = 500
MAX_INACTIVE_DAYS = 365 * 3   # 3 года без постов = неактивен
NOW = datetime.now(timezone.utc)

SUBSCRIPTIONS_FILES = [
    HERE / "tmp_dialogs.json",       # @KaluginVit
    HERE / "tmp_dialogs_s1.json",    # @grey_rhinocero
]
FINAL_CHANNELS_FILE = HERE / "tmp_final_channels.json"


# ---------------------------------------------------------------------------
# Загрузка существующих данных
# ---------------------------------------------------------------------------

def _load_known_channel_ids() -> set[int]:
    """ID каналов из текущих подписок и уже добавленных в final."""
    known: set[int] = set()

    for path in SUBSCRIPTIONS_FILES:
        if not path.exists():
            print(f"  [WARN] {path.name} не найден, пропускаем")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for ch in data.get("channels", []):
            known.add(ch["id"])

    if FINAL_CHANNELS_FILE.exists():
        for ch in json.loads(FINAL_CHANNELS_FILE.read_text(encoding="utf-8")):
            known.add(ch["id"])

    return known


def _load_final_channels() -> list[dict]:
    if FINAL_CHANNELS_FILE.exists():
        return json.loads(FINAL_CHANNELS_FILE.read_text(encoding="utf-8"))
    return []


# ---------------------------------------------------------------------------
# Источники из Избранного
# ---------------------------------------------------------------------------

def _get_saved_channel_ids(db_path: Path) -> set[int]:
    """Числовые ID каналов из forwarded_from_id записей Избранного."""
    con = sqlite3.connect(db_path)
    rows = con.execute(
        """
        SELECT DISTINCT forwarded_from_id
        FROM messages
        WHERE source IN ('saved_vitaliy', 'saved_andrey')
          AND forwarded_from_id LIKE 'channel%'
        """
    ).fetchall()
    con.close()

    ids: set[int] = set()
    for (fwd_id,) in rows:
        try:
            ids.add(int(fwd_id.replace("channel", "")))
        except ValueError:
            pass
    return ids


# ---------------------------------------------------------------------------
# Резолв метаданных канала
# ---------------------------------------------------------------------------

async def _resolve_channel(client: TelegramClient, channel_id: int) -> dict | None:
    try:
        entity = await client.get_entity(channel_id)
    except (ChannelPrivateError, ValueError, Exception) as exc:
        print(f"  [skip] {channel_id}: {exc}")
        return None

    if not getattr(entity, "broadcast", False):
        return None  # не канал (группа/чат)

    try:
        full = await client(GetFullChannelRequest(entity))
        subscribers = full.full_chat.participants_count or 0
    except Exception:
        subscribers = getattr(entity, "participants_count", 0) or 0

    username = getattr(entity, "username", None)

    # Последний пост — просто проверяем дату через entity.date (дата создания),
    # реальную дату последнего поста получаем через get_messages
    last_post_date = None
    try:
        async for msg in client.iter_messages(entity, limit=1):
            last_post_date = msg.date
    except Exception:
        pass

    inactive_days = None
    if last_post_date:
        inactive_days = (NOW - last_post_date).days

    return {
        "id":            entity.id,
        "title":         entity.title,
        "username":      username,
        "subscribers":   subscribers,
        "last_post_date": last_post_date.strftime("%Y-%m-%d") if last_post_date else None,
        "inactive_days": inactive_days,
    }


# ---------------------------------------------------------------------------
# Основная логика
# ---------------------------------------------------------------------------

async def enrich_saved_sources(db_path: Path = DB_PATH, dry_run: bool = False) -> None:
    print("Загружаем данные …")
    known_ids    = _load_known_channel_ids()
    final_list   = _load_final_channels()
    saved_ids    = _get_saved_channel_ids(db_path)

    new_candidates = saved_ids - known_ids
    print(f"  Источников в Избранном:  {len(saved_ids)}")
    print(f"  Уже известных:           {len(saved_ids & known_ids)}")
    print(f"  Новых кандидатов:        {len(new_candidates)}")

    if not new_candidates:
        print("Нет новых каналов для добавления.")
        return

    # Резолвим через session2 (read-only Виталий)
    client = TelegramClient(str(HERE.parent / "session2"), API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("session2 не авторизован!")
        await client.disconnect()
        return

    passed: list[dict] = []
    failed_private = failed_small = failed_inactive = 0

    for i, ch_id in enumerate(sorted(new_candidates), 1):
        print(f"  [{i}/{len(new_candidates)}] {ch_id} …", end=" ", flush=True)
        meta = await _resolve_channel(client, ch_id)

        if meta is None:
            print("skip (приватный/ошибка)")
            failed_private += 1
            continue

        if meta["subscribers"] < MIN_SUBSCRIBERS:
            print(f"skip ({meta['subscribers']} подписчиков < {MIN_SUBSCRIBERS})")
            failed_small += 1
            continue

        if meta["inactive_days"] is not None and meta["inactive_days"] > MAX_INACTIVE_DAYS:
            print(f"skip (неактивен {meta['inactive_days']} дней)")
            failed_inactive += 1
            continue

        print(f"OK  {meta['title']}  @{meta['username']}  {meta['subscribers']:,} подп.")
        passed.append(meta)

    await client.disconnect()

    print(f"\nРезультат:")
    print(f"  Прошло фильтр:     {len(passed)}")
    print(f"  Приватные/ошибки:  {failed_private}")
    print(f"  < {MIN_SUBSCRIBERS} подписчиков:  {failed_small}")
    print(f"  Неактивных:        {failed_inactive}")

    if not passed:
        print("Нечего добавлять.")
        return

    if dry_run:
        print("\n[dry-run] Новые каналы (не сохраняется):")
        for ch in passed:
            print(f"  {ch['title']}  @{ch['username']}  {ch['subscribers']:,}")
        return

    final_list.extend(passed)
    FINAL_CHANNELS_FILE.write_text(
        json.dumps(final_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nСохранено в {FINAL_CHANNELS_FILE.name}: итого {len(final_list)} каналов (+{len(passed)} новых)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Добавить источники из Избранного в список каналов")
    parser.add_argument("--dry-run", action="store_true", help="Не сохранять, только показать")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    asyncio.run(enrich_saved_sources(db_path=args.db, dry_run=args.dry_run))
