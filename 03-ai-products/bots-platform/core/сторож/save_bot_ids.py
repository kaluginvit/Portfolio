"""
Сохраняет ID вступивших за последние N часов в bots_to_ban.txt.
Запуск: python save_bot_ids.py --hours 6
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
OUTPUT_FILE = Path(__file__).parent / "bots_to_ban.txt"


async def main(hours: float) -> None:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    print(f"Собираю ID вступивших с {since.strftime('%Y-%m-%d %H:%M UTC')}...")

    async with TelegramClient(str(SESSION_FILE), int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"]) as client:
        channel = await client.get_entity(os.environ["TELEGRAM_CHANNEL_USERNAME"])
        join_filter = ChannelAdminLogEventsFilter(join=True, invite=True)
        ids: list[int] = []
        max_id = 0

        while True:
            chunk = await client(GetAdminLogRequest(
                channel=channel, q="", events_filter=join_filter,
                admins=None, max_id=max_id, min_id=0, limit=100,
            ))
            if not chunk.events:
                break
            stop = False
            for event in chunk.events:
                dt = event.date.replace(tzinfo=timezone.utc)
                if dt < since:
                    stop = True
                    break
                if isinstance(event.action, (
                    ChannelAdminLogEventActionParticipantJoin,
                    ChannelAdminLogEventActionParticipantJoinByInvite,
                    ChannelAdminLogEventActionParticipantJoinByRequest,
                )):
                    if event.user_id:
                        ids.append(event.user_id)
            if stop:
                break
            max_id = chunk.events[-1].id

    OUTPUT_FILE.write_text("\n".join(str(i) for i in ids), encoding="utf-8")
    print(f"Сохранено: {len(ids)} ID → {OUTPUT_FILE}")
    print(f"Когда будешь готов банить: python ban_saved.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=6.0)
    args = parser.parse_args()
    asyncio.run(main(args.hours))
