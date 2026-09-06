"""
Отмечает чат прочитанным до последнего сообщения в БД.

Использование:
    uv run python chat_summaries/mark_read.py c0ldtalk
    uv run python chat_summaries/mark_read.py nebaffet
"""

import argparse
import asyncio
import json
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parents[1]
CHATS_CFG = Path(__file__).parent / 'chats.json'


async def main(chat_name: str):
    load_dotenv(ROOT / '.env')
    import os
    cfg = json.loads(CHATS_CFG.read_text(encoding='utf-8'))['chats'][chat_name]
    session = ROOT / f"{cfg.get('session', 'session')}.session"

    folder = cfg.get('folder', chat_name)
    db_path = Path(__file__).parent / folder / 'messages.db'
    con = sqlite3.connect(db_path)
    row = con.execute('SELECT MAX(message_id) FROM messages').fetchone()
    max_id = row[0] if row and row[0] else 0
    con.close()
    print(f'Max message_id в БД: {max_id}')

    client = TelegramClient(str(session), int(os.environ['TG_API_ID']), os.environ['TG_API_HASH'])
    await client.start()

    chat_id = cfg.get('chat') or cfg.get('chat_titles', [None])[0]
    entity = await client.get_entity(chat_id)
    await client.send_read_acknowledge(entity, max_id=max_id)
    print(f'Чат {chat_name} отмечен прочитанным до message_id={max_id}')

    await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('chat', help='Имя чата из chats.json')
    args = parser.parse_args()
    asyncio.run(main(args.chat))
