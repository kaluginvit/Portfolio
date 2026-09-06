"""
Сторож через Bot API — сравнивает getChatMemberCount каждую минуту.
Если прирост > threshold — шлёт алерт.

Запуск:
    python spam_watcher.py
    python spam_watcher.py --threshold 4
"""

import argparse
import asyncio
import os
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
ADMIN_CHAT_ID = os.environ["TELEGRAM_ADMIN_CHAT_ID"]
API = f"https://api.telegram.org/bot{TOKEN}"


async def tg_get(http: httpx.AsyncClient, method: str, **params) -> dict:
    r = await http.get(f"{API}/{method}", params=params, timeout=20)
    return r.json()


async def send(http: httpx.AsyncClient, text: str) -> None:
    await http.post(f"{API}/sendMessage", json={
        "chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "HTML"
    }, timeout=20)


async def main(threshold: int) -> None:
    print(f"Сторож запущен. Порог: +{threshold}/мин")
    print(f"Алерты → chat_id {ADMIN_CHAT_ID}\n")

    prev_count = None
    alert_active = False

    async with httpx.AsyncClient(verify=False, timeout=20) as http:
        while True:
            try:
                data = await tg_get(http, "getChatMemberCount", chat_id=CHANNEL_ID)
                current_count = data["result"]
            except Exception as e:
                print(f"Ошибка: {e}")
                await asyncio.sleep(60)
                continue

            now = datetime.now(timezone.utc)
            ts = (now + timedelta(hours=5)).strftime("%H:%M:%S")

            if prev_count is None:
                print(f"[{ts}] Подписчиков: {current_count}")
                prev_count = current_count
                await asyncio.sleep(60)
                continue

            delta = current_count - prev_count
            prev_count = current_count

            if delta > threshold:
                print(f"[{ts}] {current_count} (+{delta}) ⚠️ АТАКА")
                if not alert_active:
                    await send(http,
                        f"⚠️ <b>Атака на канал!</b>\n"
                        f"Прирост: <b>+{delta}</b> за минуту (порог +{threshold}/мин)\n"
                        f"Всего подписчиков: {current_count}\n"
                        f"Время: {ts}")
                    alert_active = True
            else:
                print(f"[{ts}] {current_count} ({delta:+d})")
                if alert_active and delta <= 0:
                    await send(http,
                        f"✅ <b>Атака прекратилась</b>\n"
                        f"Поток в норме: {delta:+d}/мин\n"
                        f"Подписчиков: {current_count}")
                    alert_active = False

            await asyncio.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(main(args.threshold))
