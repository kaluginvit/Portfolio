"""
Банит всех из bots_to_ban.txt через Bot API.
Запуск: python ban_saved.py
"""
import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
API = f"https://api.telegram.org/bot{TOKEN}"
import sys
_default_file = "bots_to_ban.txt"
_arg_file = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == "--file"), None)
INPUT_FILE = Path(__file__).parent / (_arg_file or _default_file)

DELAY = 0.05  # секунд между запросами (20 в сек — в запасе от лимита)


async def ban_all() -> None:
    if not INPUT_FILE.exists():
        print(f"Файл не найден: {INPUT_FILE}")
        print("Сначала запусти: python save_bot_ids.py --hours 6")
        return

    ids = [line.strip() for line in INPUT_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not ids:
        print("Список пустой — некого банить.")
        return

    print(f"Банить: {len(ids)} пользователей из {INPUT_FILE.name}")
    print("Начинаю...\n")

    banned = 0
    already_gone = 0
    errors = 0

    async with httpx.AsyncClient(verify=False, timeout=20) as http:
        for i, user_id in enumerate(ids, 1):
            try:
                r = await http.post(f"{API}/banChatMember", json={
                    "chat_id": CHANNEL_ID,
                    "user_id": int(user_id),
                    "revoke_messages": False,
                })
                data = r.json()
                if data.get("ok"):
                    banned += 1
                    if i % 100 == 0 or i == len(ids):
                        print(f"  [{i}/{len(ids)}] забанено: {banned}, ушло само: {already_gone}, ошибок: {errors}")
                else:
                    desc = data.get("description", "")
                    if "USER_NOT_PARTICIPANT" in desc or "not a member" in desc.lower():
                        already_gone += 1
                    else:
                        errors += 1
                        if errors <= 10:
                            print(f"  [!] {user_id}: {desc}")
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"  [!] {user_id}: {e}")

            await asyncio.sleep(DELAY)

    print(f"\nГотово: забанено {banned}, ушло само {already_gone}, ошибок {errors}")


if __name__ == "__main__":
    asyncio.run(ban_all())
