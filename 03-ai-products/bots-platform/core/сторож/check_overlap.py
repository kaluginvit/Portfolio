import asyncio, os, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import GetAdminLogRequest
from telethon.tl.types import ChannelAdminLogEventsFilter, ChannelAdminLogEventActionParticipantLeave

load_dotenv()
SESSION_FILE = Path("tg_session")

async def main():
    # 1. Загружаем вступивших из уже готового лога
    joined_ids = set()
    log_path = Path("spam_history_10h.txt")
    for line in log_path.read_text(encoding="utf-8").splitlines():
        m = re.search(r'id=(\d+)', line)
        if m:
            joined_ids.add(int(m.group(1)))
    print(f"Вступивших в логе: {len(joined_ids)}")

    # 2. Получаем отписавшихся через Telethon
    client = TelegramClient(str(SESSION_FILE), int(os.getenv("TG_API_ID")), os.getenv("TG_API_HASH"))
    await client.connect()
    channel = await client.get_entity(os.getenv("TELEGRAM_CHANNEL_USERNAME"))
    since = datetime.now(timezone.utc) - timedelta(hours=10)

    leave_filter = ChannelAdminLogEventsFilter(leave=True)
    left_ids = set()
    max_id = 0
    while True:
        chunk = await client(GetAdminLogRequest(
            channel=channel, q="", events_filter=leave_filter,
            admins=None, max_id=max_id, min_id=0, limit=100))
        if not chunk.events:
            break
        stop = False
        for event in chunk.events:
            dt = event.date.replace(tzinfo=timezone.utc)
            if dt < since:
                stop = True
                break
            if isinstance(event.action, ChannelAdminLogEventActionParticipantLeave):
                left_ids.add(event.user_id)
        if stop:
            break
        max_id = chunk.events[-1].id

    await client.disconnect()

    # 3. Анализ пересечений
    both = joined_ids & left_ids          # пришли и ушли (боты-однодневки)
    only_left = left_ids - joined_ids     # ушли, но НЕ приходили сегодня (живые подписчики)
    only_joined = joined_ids - left_ids   # пришли и остались

    print(f"Отписавшихся всего:       {len(left_ids)}")
    print(f"Пришли И ушли (боты):     {len(both)}")
    print(f"Ушли НЕ из пришедших:     {len(only_left)}  <-- ЖИВЫЕ подписчики, которые отписались")
    print(f"Пришли и остались:        {len(only_joined)}")
    print()
    pct_bots = len(both) / len(left_ids) * 100 if left_ids else 0
    pct_real = len(only_left) / len(left_ids) * 100 if left_ids else 0
    print(f"Из отписавшихся — боты:   {pct_bots:.1f}%")
    print(f"Из отписавшихся — живые:  {pct_real:.1f}%")

asyncio.run(main())
