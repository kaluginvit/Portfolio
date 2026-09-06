"""
Пометить все посты по 28.08.2026 (включительно) как прочитанные.

Источники:
  1. Все чаты из chats.json (по сессиям)
  2. Все каналы из папки «Финансы» в Telegram (session2)

Run:
    uv run python chat_summaries/mark_read_to_date.py
    uv run python chat_summaries/mark_read_to_date.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parents[1]
CHATS_CFG = Path(__file__).parent / "chats.json"
FINANCE_DB = Path(__file__).parent / "finance" / "finance_messages.db"
FOLDER_NAME = "Финансы"

# Помечаем всё до 28.08.2026 включительно
# offset_date в Telethon — эксклюзивная верхняя граница, т.е. берём < 2026-08-29 00:00
UNTIL = datetime(2026, 8, 29, 0, 0, 0, tzinfo=timezone.utc)


def load_env() -> tuple[int, str]:
    load_dotenv(ROOT / ".env")
    return int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"]


def folder_title(folder) -> str:
    title = getattr(folder, "title", "") or ""
    return title.text if hasattr(title, "text") else str(title)


async def get_max_id_before(client: TelegramClient, entity, until: datetime) -> int | None:
    async for msg in client.iter_messages(entity, offset_date=until):
        return msg.id
    return None


async def mark_entity(
    client: TelegramClient, entity, label: str, until: datetime, dry_run: bool
) -> None:
    max_id = await get_max_id_before(client, entity, until)
    if max_id is None:
        print(f"  {label}: нет сообщений до {until.date()} — пропуск")
        return
    if dry_run:
        print(f"  {label}: max_id={max_id} [dry-run]")
        return
    try:
        await client.send_read_acknowledge(entity, max_id=max_id)
        print(f"  {label}: OK, до message_id={max_id}")
    except Exception as exc:
        print(f"  {label}: ошибка — {exc}")


async def mark_chats_json(api_id: int, api_hash: str, until: datetime, dry_run: bool) -> None:
    cfg = json.loads(CHATS_CFG.read_text(encoding="utf-8"))["chats"]

    by_session: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for name, chat_cfg in cfg.items():
        by_session[chat_cfg["session"]].append((name, chat_cfg))

    print(f"\n=== chats.json: {len(cfg)} источников, {len(by_session)} сессий ===")

    for session_name, chats in sorted(by_session.items()):
        print(f"\n[сессия: {session_name}] {len(chats)} каналов")
        client = TelegramClient(str(ROOT / session_name), api_id, api_hash)
        await client.connect()

        if not await client.is_user_authorized():
            print(f"  Сессия {session_name} не авторизована — пропуск")
            await client.disconnect()
            continue

        for name, chat_cfg in chats:
            try:
                if chat_cfg.get("chat_titles"):
                    titles = [t.lower() for t in chat_cfg["chat_titles"]]
                    found = False
                    async for dialog in client.iter_dialogs():
                        if any(t in (dialog.name or "").lower() for t in titles):
                            await mark_entity(client, dialog.entity, name, until, dry_run)
                            found = True
                            break
                    if not found:
                        print(f"  {name}: диалог не найден")
                else:
                    entity = await client.get_entity(chat_cfg["chat"])
                    await mark_entity(client, entity, name, until, dry_run)
            except Exception as exc:
                print(f"  {name}: ошибка — {exc}")

        await client.disconnect()


async def mark_finance(api_id: int, api_hash: str, until: datetime, dry_run: bool) -> None:
    print(f"\n=== Финансы: папка «{FOLDER_NAME}» (session2) ===")

    if FINANCE_DB.exists():
        con = sqlite3.connect(FINANCE_DB)
        sources = con.execute(
            "SELECT source_peer_id, title, username FROM sources ORDER BY title"
        ).fetchall()
        con.close()
        print(f"  Источников в finance_messages.db: {len(sources)}")
        for peer_id, title, username in sources:
            label = f"@{username}" if username else str(peer_id)
            print(f"    {title} ({label})")
    else:
        print("  finance_messages.db не найден, продолжаем через папку TG")

    client = TelegramClient(str(ROOT / "session2"), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print("  session2 не авторизована — пропуск")
        await client.disconnect()
        return

    filters = await client(GetDialogFiltersRequest())
    folder = next(
        (f for f in filters.filters if hasattr(f, "title") and FOLDER_NAME.lower() in folder_title(f).lower()),
        None,
    )
    if not folder:
        print(f"  Папка «{FOLDER_NAME}» не найдена в Telegram")
        await client.disconnect()
        return

    peers = getattr(folder, "include_peers", [])
    print(f"\n  Помечаем {len(peers)} источников из папки TG...")

    for peer in peers:
        try:
            entity = await client.get_entity(peer)
            name = getattr(entity, "title", None) or getattr(entity, "username", None) or str(peer)
            await mark_entity(client, entity, name, until, dry_run)
        except Exception as exc:
            print(f"  peer {peer}: ошибка — {exc}")

    await client.disconnect()


async def main(dry_run: bool) -> None:
    api_id, api_hash = load_env()

    if dry_run:
        print("[DRY-RUN] Только показываем max_id, ничего не помечаем.")

    await mark_chats_json(api_id, api_hash, UNTIL, dry_run)
    await mark_finance(api_id, api_hash, UNTIL, dry_run)

    print("\nГотово.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Только показать max_id, без пометки")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))
