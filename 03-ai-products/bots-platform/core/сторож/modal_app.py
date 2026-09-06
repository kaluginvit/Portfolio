"""
Modal приложение — spam watcher (cloud cron, каждую минуту).

Отслеживает новых участников через getUpdates.
Если скорость прихода > THRESHOLD за минуту — шлёт алерт.

Деплой:
    modal deploy modal_app.py

Секреты Modal (dashboard → Secrets → "telegram"):
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHANNEL_ID   (-1001324653248)
    TELEGRAM_ADMIN_CHAT_ID (316087324)
"""

import modal

app = modal.App("spam-watcher")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("httpx>=0.27.0")
)

THRESHOLD = 4  # алерт если > 4 вступлений за минуту
WINDOW_SEC = 60

state = modal.Dict.from_name("spam-watcher-state", create_if_missing=True)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("telegram")],
    schedule=modal.Cron("* * * * *"),
    timeout=25,
)
async def spam_watcher_cron():
    import os
    import time
    import httpx
    from datetime import datetime, timedelta, timezone

    TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
    ADMIN_CHAT_ID = os.environ["TELEGRAM_ADMIN_CHAT_ID"]
    API = f"https://api.telegram.org/bot{TOKEN}"

    last_update_id: int = await state.get.aio("last_update_id", 0)
    join_timestamps: list = await state.get.aio("join_timestamps", [])
    alert_active: bool = await state.get.aio("alert_active", False)

    now_ts = time.time()

    async with httpx.AsyncClient(timeout=20) as http:
        params = {
            "offset": last_update_id + 1 if last_update_id else 0,
            "limit": 100,
            "allowed_updates": ["message", "chat_member"],
            "timeout": 0,
        }
        r = await http.get(f"{API}/getUpdates", params=params)
        data = r.json()

        if not data.get("ok"):
            print(f"spam_watcher: ошибка getUpdates: {data}")
            return

        for update in data["result"]:
            uid = update["update_id"]
            if uid > last_update_id:
                last_update_id = uid

            msg = update.get("message", {})
            for member in msg.get("new_chat_members", []):
                if not member.get("is_bot", False):
                    join_timestamps.append(now_ts)

        # Скользящее окно — только последние WINDOW_SEC секунд
        join_timestamps = [t for t in join_timestamps if now_ts - t <= WINDOW_SEC]
        rate = len(join_timestamps)

        now = datetime.now(timezone.utc)
        ts_local = (now + timedelta(hours=5)).strftime("%H:%M:%S")

        print(f"spam_watcher: rate={rate}/мин, alert_active={alert_active}")

        if rate > THRESHOLD and not alert_active:
            await http.post(f"{API}/sendMessage", json={
                "chat_id": ADMIN_CHAT_ID,
                "text": (
                    f"⚠️ <b>Атака на канал!</b>\n"
                    f"Вступлений за минуту: <b>{rate}</b> (порог {THRESHOLD}/мин)\n"
                    f"Время: {ts_local}"
                ),
                "parse_mode": "HTML",
            })
            alert_active = True

        elif alert_active and rate == 0:
            await http.post(f"{API}/sendMessage", json={
                "chat_id": ADMIN_CHAT_ID,
                "text": (
                    f"✅ <b>Атака прекратилась</b>\n"
                    f"Вступлений за минуту: {rate}\n"
                    f"Время: {ts_local}"
                ),
                "parse_mode": "HTML",
            })
            alert_active = False

    await state.put.aio("last_update_id", last_update_id)
    await state.put.aio("join_timestamps", join_timestamps)
    await state.put.aio("alert_active", alert_active)
