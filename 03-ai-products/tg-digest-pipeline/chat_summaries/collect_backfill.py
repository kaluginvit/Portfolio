import asyncio, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path
from telethon import TelegramClient

sys.stdout.reconfigure(encoding='utf-8')

API_ID   = 20184352
API_HASH = '032a063336e3d8278243047c9defc6e2'
SESSION  = str(Path(__file__).parent.parent / 'session2')

SINCE = datetime(2026, 1, 1,  tzinfo=timezone.utc)
UNTIL = datetime(2026, 5, 13, tzinfo=timezone.utc)  # до 13 мая не включая = по 12 мая вкл

CHATS = {
    '@thefinansist_chat': Path(__file__).parent / 'nebaffet' / 'messages.db',
    '@c0ldtalk':          Path(__file__).parent / 'c0ldtalk' / 'messages.db',
}


def init_db(con):
    con.execute('''CREATE TABLE IF NOT EXISTS messages (
        message_id   INTEGER PRIMARY KEY,
        date         TEXT,
        sender_id    INTEGER,
        sender_name  TEXT,
        text         TEXT,
        reply_to     INTEGER
    )''')
    con.commit()


async def collect(client, chat, db_path):
    con = sqlite3.connect(db_path)
    init_db(con)
    existing = {r[0] for r in con.execute('SELECT message_id FROM messages')}
    print(f'\n[{chat}] Уже в БД: {len(existing)}. Добираю с {SINCE.date()} по {UNTIL.date()}...')

    count = 0
    async for msg in client.iter_messages(chat, offset_date=UNTIL, reverse=False):
        if msg.date < SINCE:
            break
        if msg.id in existing:
            continue
        if not msg.text:
            continue

        sender_name = ''
        if msg.sender:
            fn = getattr(msg.sender, 'first_name', '') or ''
            ln = getattr(msg.sender, 'last_name', '') or ''
            un = getattr(msg.sender, 'username', '') or ''
            sender_name = f'{fn} {ln}'.strip() or un

        con.execute(
            'INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?)',
            (msg.id, msg.date.isoformat(), msg.sender_id, sender_name,
             msg.text, msg.reply_to_msg_id)
        )
        count += 1
        if count % 500 == 0:
            con.commit()
            print(f'  [{chat}] собрано: {count}...')

    con.commit()
    total = con.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
    print(f'  [{chat}] Готово. Новых: {count}. Всего в БД: {total}')
    con.close()


async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    for chat, db_path in CHATS.items():
        await collect(client, chat, db_path)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
