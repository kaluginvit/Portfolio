"""Находит самое раннее время вступления среди ID в bots_to_ban.txt"""
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
IDS_FILE = Path(__file__).parent / "bots_to_ban.txt"


async def main():
    ids = set(int(x) for x in IDS_FILE.read_text(encoding="utf-8").splitlines() if x.strip())
    print(f"ID в файле: {len(ids)}")

    since = datetime.now(timezone.utc) - timedelta(hours=7)  # чуть шире
    earliest = None
    latest = None

    async with TelegramClient(str(SESSION_FILE), int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"]) as client:
        channel = await client.get_entity(os.environ["TELEGRAM_CHANNEL_USERNAME"])
        join_filter = ChannelAdminLogEventsFilter(join=True, invite=True)
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
                if event.user_id in ids:
                    if earliest is None or dt < earliest:
                        earliest = dt
                    if latest is None or dt > latest:
                        latest = dt
            if stop:
                break
            max_id = chunk.events[-1].id

    tz5 = timezone(timedelta(hours=5))
    if earliest:
        print(f"Самое раннее: {earliest.astimezone(tz5).strftime('%Y-%m-%d %H:%M:%S')} (+5)")
        print(f"Самое позднее: {latest.astimezone(tz5).strftime('%Y-%m-%d %H:%M:%S')} (+5)")
    else:
        print("Не найдено совпадений")


asyncio.run(main())
