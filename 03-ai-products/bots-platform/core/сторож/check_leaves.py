import asyncio, os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import GetAdminLogRequest
from telethon.tl.types import ChannelAdminLogEventsFilter, ChannelAdminLogEventActionParticipantLeave

load_dotenv()
SESSION_FILE = Path("tg_session")

async def main():
    client = TelegramClient(str(SESSION_FILE), int(os.getenv("TG_API_ID")), os.getenv("TG_API_HASH"))
    await client.connect()
    channel = await client.get_entity(os.getenv("TELEGRAM_CHANNEL_USERNAME"))
    since = datetime.now(timezone.utc) - timedelta(hours=10)
    leave_filter = ChannelAdminLogEventsFilter(leave=True)
    count = 0
    max_id = 0
    while True:
        chunk = await client(GetAdminLogRequest(
            channel=channel, q="", events_filter=leave_filter,
            admins=None, max_id=max_id, min_id=0, limit=100))
        if not chunk.events:
            break
        for event in chunk.events:
            dt = event.date.replace(tzinfo=timezone.utc)
            if dt < since:
                print(f"Отписались за 10ч: {count}")
                await client.disconnect()
                return
            if isinstance(event.action, ChannelAdminLogEventActionParticipantLeave):
                count += 1
        max_id = chunk.events[-1].id
    print(f"Отписались за 10ч: {count}")
    await client.disconnect()

asyncio.run(main())
