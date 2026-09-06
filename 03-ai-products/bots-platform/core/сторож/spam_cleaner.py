"""
Читает admin log канала через MTProto (Telethon) и банит вступивших через Bot API.

Требует в .env:
    TG_API_ID      — с https://my.telegram.org → App configuration
    TG_API_HASH    — там же
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHANNEL_ID

При первом запуске Telethon запросит номер телефона и код — создаст файл сессии
tg_session.session рядом со скриптом (в .gitignore).

Запуск:
    python spam_cleaner.py              # последний час
    python spam_cleaner.py --hours 6    # последние 6 часов
    python spam_cleaner.py --dry-run    # только показать, не банить
"""

import argparse
import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import GetAdminLogRequest
from telethon.tl.types import (
    ChannelAdminLogEventActionParticipantJoin,
    ChannelAdminLogEventActionParticipantJoinByInvite,
    ChannelAdminLogEventActionParticipantJoinByRequest,
    ChannelAdminLogEventsFilter,
)

load_dotenv()

SESSION_FILE = Path(__file__).parent / "tg_session"


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise SystemExit(f"❌ Не задана переменная окружения {key}")
    return val


async def fetch_joined_user_ids(
    client: TelegramClient,
    channel,
    since: datetime,
) -> list[tuple[int, str, datetime]]:
    """Возвращает [(user_id, username, joined_at), ...] для всех вступивших после since."""
    join_filter = ChannelAdminLogEventsFilter(join=True, invite=True)
    results: list[tuple[int, str, datetime]] = []
    max_id = 0

    while True:
        chunk = await client(
            GetAdminLogRequest(
                channel=channel, q="",
                events_filter=join_filter,
                admins=None, max_id=max_id, min_id=0, limit=100,
            )
        )
        if not chunk.events:
            break

        for event in chunk.events:
            event_dt = event.date.replace(tzinfo=timezone.utc)
            if event_dt < since:
                return results

            action = event.action
            if isinstance(action, (
                ChannelAdminLogEventActionParticipantJoin,
                ChannelAdminLogEventActionParticipantJoinByInvite,
                ChannelAdminLogEventActionParticipantJoinByRequest,
            )):
                uid = event.user_id
                if uid:
                    results.append((uid, f"id={uid}", event_dt))

        max_id = chunk.events[-1].id

    return results


async def ban_via_bot_api(
    token: str,
    chat_id: str,
    user_ids: list[int],
    dry_run: bool,
) -> tuple[int, int]:
    import httpx

    ok = fail = 0
    async with httpx.AsyncClient(verify=False) as http:
        for uid in user_ids:
            if dry_run:
                ok += 1
                continue
            r = await http.post(
                f"https://api.telegram.org/bot{token}/banChatMember",
                json={"chat_id": chat_id, "user_id": uid, "revoke_messages": False},
                timeout=10,
            )
            data = r.json()
            if data.get("ok"):
                ok += 1
            else:
                fail += 1
                print(f"  FAIL uid={uid}: {data.get('description')}")
    return ok, fail


async def main(hours: float, dry_run: bool) -> None:
    api_id = int(_require("TG_API_ID"))
    api_hash = _require("TG_API_HASH")
    bot_token = _require("TELEGRAM_BOT_TOKEN")
    channel_id_raw = _require("TELEGRAM_CHANNEL_ID")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    print(f"🔍 Ищем вступивших с {since.strftime('%Y-%m-%d %H:%M UTC')} (последние {hours}ч)")
    if dry_run:
        print("⚠️  DRY-RUN: баним только в уме, реальных банов не будет")

    async with TelegramClient(str(SESSION_FILE), api_id, api_hash) as client:
        channel_username = os.getenv("TELEGRAM_CHANNEL_USERNAME")
        if channel_username:
            channel = await client.get_entity(channel_username.lstrip("@"))
        else:
            from telethon.tl.types import PeerChannel
            raw = int(channel_id_raw)
            mtproto_id = int(str(abs(raw))[3:]) if str(abs(raw)).startswith("100") else abs(raw)
            channel = await client.get_entity(PeerChannel(mtproto_id))

        joined = await fetch_joined_user_ids(client, channel, since)

    if not joined:
        print("✅ За указанный период новых подписчиков не обнаружено.")
        return

    print(f"\n📋 Найдено вступивших: {len(joined)}")
    for uid, uname, dt in joined:
        print(f"  [{dt.strftime('%H:%M')}] id={uid} {uname}")

    user_ids = [uid for uid, _, _ in joined]
    print(f"\n🔨 {'(dry-run) ' if dry_run else ''}Баним {len(user_ids)} аккаунтов...")
    ok, fail = await ban_via_bot_api(bot_token, channel_id_raw, user_ids, dry_run)
    print(f"✅ Заблокировано: {ok}  ❌ Ошибок: {fail}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Бан спам-подписчиков через MTProto + Bot API")
    parser.add_argument("--hours", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.hours, args.dry_run))
