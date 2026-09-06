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
    # Вступившие из лога
    joined_ids = set()
    for line in Path("spam_history_10h.txt").read_text(encoding="utf-8").splitlines():
        m = re.search(r'id=(\d+)', line)
        if m:
            joined_ids.add(int(m.group(1)))

    client = TelegramClient(str(SESSION_FILE), int(os.getenv("TG_API_ID")), os.getenv("TG_API_HASH"))
    await client.connect()
    channel = await client.get_entity(os.getenv("TELEGRAM_CHANNEL_USERNAME"))
    since = datetime.now(timezone.utc) - timedelta(hours=10)

    # Собираем отписавшихся с временем
    leave_events = []
    max_id = 0
    while True:
        chunk = await client(GetAdminLogRequest(
            channel=channel, q="",
            events_filter=ChannelAdminLogEventsFilter(leave=True),
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
                if event.user_id not in joined_ids:
                    leave_events.append((event.user_id, dt))
        if stop:
            break
        max_id = chunk.events[-1].id

    print(f"Живых подписчиков, отписавшихся: {len(leave_events)}\n")

    # Получаем профили
    for uid, dt in sorted(leave_events, key=lambda x: x[1]):
        local_dt = dt + timedelta(hours=5)
        try:
            user = await client.get_entity(uid)
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            username = f"@{user.username}" if user.username else "(нет username)"
            phone = getattr(user, 'phone', None) or "(скрыт)"
            bot = "БОТ" if user.bot else "человек"
        except Exception as e:
            name, username, phone, bot = "недоступен", "-", "-", "-"
        print(f"[{local_dt.strftime('%Y-%m-%d %H:%M')} мест.] id={uid}")
        print(f"  Имя:      {name}")
        print(f"  Username: {username}")
        print(f"  Телефон:  {phone}")
        print(f"  Тип:      {bot}")
        print()

    await client.disconnect()

asyncio.run(main())
