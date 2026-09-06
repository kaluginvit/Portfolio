"""
Бот-модератор для чата с комментами.

Реклама (t.me/ ссылки, внешние URL + ключевые слова, цена+контакт) → бан сразу.
Оскорбления (грубые слова, угрозы, мат) → прогрессивно:
  1-й раз  → мьют 1 час
  2-й раз  → мьют 1 день
  3-й раз+ → бан

Запуск:
    python -X utf8 bot.py
"""
import asyncio
import os
import time

import httpx
from dotenv import load_dotenv

from filters import is_ad, is_insult
from violations import get_count, increment

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GROUP_ID = os.environ["TELEGRAM_GROUP_ID"]
ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")
WHITELIST = {int(x) for x in os.environ.get("WHITELIST_USER_IDS", "").split(",") if x.strip()}
API = f"https://api.telegram.org/bot{TOKEN}"

MUTE_1H  = 3_600
MUTE_1D  = 86_400


async def api_post(http: httpx.AsyncClient, method: str, **kwargs) -> dict:
    r = await http.post(f"{API}/{method}", json=kwargs, timeout=20)
    return r.json()


async def delete_message(http, chat_id, message_id):
    await api_post(http, "deleteMessage", chat_id=chat_id, message_id=message_id)


async def mute_user(http, chat_id, user_id, seconds):
    await api_post(http, "restrictChatMember",
        chat_id=chat_id,
        user_id=user_id,
        until_date=int(time.time()) + seconds,
        permissions={
            "can_send_messages": False,
            "can_send_audios": False,
            "can_send_documents": False,
            "can_send_photos": False,
            "can_send_videos": False,
            "can_send_video_notes": False,
            "can_send_voice_notes": False,
            "can_send_polls": False,
            "can_send_other_messages": False,
            "can_add_web_page_previews": False,
        },
    )


async def ban_user(http, chat_id, user_id):
    await api_post(http, "banChatMember",
        chat_id=chat_id,
        user_id=user_id,
        revoke_messages=True,
    )


async def notify_admin(http, text: str):
    if ADMIN_CHAT_ID:
        await api_post(http, "sendMessage",
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode="HTML",
        )


async def notify_chat(http, chat_id, text: str):
    await api_post(http, "sendMessage",
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
    )


async def handle_message(http: httpx.AsyncClient, msg: dict):
    chat_id = msg["chat"]["id"]
    if str(chat_id) != str(GROUP_ID):
        return

    user = msg.get("from", {})
    if not user or user.get("is_bot"):
        return

    user_id = user["id"]
    if user_id in WHITELIST:
        return

    username = user.get("username", "")
    first_name = user.get("first_name", "")
    name = f"@{username}" if username else first_name
    msg_id = msg["message_id"]
    text = msg.get("text") or msg.get("caption") or ""

    # GIF (animation) — удаляем без предупреждения
    if msg.get("animation"):
        await delete_message(http, chat_id, msg_id)
        print(f"[GIF удалён]  {name} ({user_id})")
        return

    # Скрытые ссылки в entities (text_link прячет URL за текстом)
    entities = msg.get("entities") or msg.get("caption_entities") or []
    has_link_entity = any(e.get("type") in ("url", "text_link") for e in entities)

    if not text and not has_link_entity:
        return

    if is_ad(text) or has_link_entity:
        await asyncio.gather(
            delete_message(http, chat_id, msg_id),
            ban_user(http, chat_id, user_id),
            notify_admin(http,
                f"🚫 <b>Бан (реклама)</b>\n"
                f"Пользователь: {name} (<code>{user_id}</code>)\n"
                f"Текст: <code>{text[:300]}</code>"),
        )
        print(f"[БАН/реклама]  {name} ({user_id}): {text[:80]!r}")
        return

    if is_insult(text):
        count = increment(user_id)

        if count == 1:
            duration = MUTE_1H
            chat_msg = f"🔇 {name} замолчит на <b>1 час</b> за оскорбления. (предупреждение 1/3)"
            admin_msg = f"🔇 <b>Мьют 1 час (нарушение #1)</b>\nПользователь: {name} (<code>{user_id}</code>)\nТекст: <code>{text[:300]}</code>"
            log_label = "МЬЮТ 1Ч"
        elif count == 2:
            duration = MUTE_1D
            chat_msg = f"🔇 {name} замолчит на <b>1 день</b> за повторные оскорбления. (предупреждение 2/3)"
            admin_msg = f"🔇 <b>Мьют 1 день (нарушение #2)</b>\nПользователь: {name} (<code>{user_id}</code>)\nТекст: <code>{text[:300]}</code>"
            log_label = "МЬЮТ 1Д"
        else:
            await asyncio.gather(
                delete_message(http, chat_id, msg_id),
                ban_user(http, chat_id, user_id),
                notify_chat(http, chat_id,
                    f"🚫 {name} заблокирован за систематические оскорбления (нарушение #{count})."),
                notify_admin(http,
                    f"🚫 <b>Бан (оскорбления, нарушение #{count})</b>\n"
                    f"Пользователь: {name} (<code>{user_id}</code>)\n"
                    f"Текст: <code>{text[:300]}</code>"),
            )
            print(f"[БАН/оскорбл #{count}]  {name} ({user_id}): {text[:80]!r}")
            return

        await asyncio.gather(
            delete_message(http, chat_id, msg_id),
            mute_user(http, chat_id, user_id, duration),
            notify_chat(http, chat_id, chat_msg),
            notify_admin(http, admin_msg),
        )
        print(f"[{log_label} #{count}]  {name} ({user_id}): {text[:80]!r}")


async def check_no_webhook(http: httpx.AsyncClient) -> None:
    r = await http.get(f"{API}/getWebhookInfo")
    info = r.json().get("result", {})
    url = info.get("url", "")
    if url:
        raise SystemExit(
            f"\n❌ СТОП: активен webhook → {url}\n"
            "   Polling нельзя запускать параллельно с Modal — это сбросит webhook.\n"
            "   Используй Modal: https://modal.com/apps\n"
        )


async def main():
    print(f"Модератор запущен. Группа: {GROUP_ID}")
    if ADMIN_CHAT_ID:
        print(f"Алерты -> {ADMIN_CHAT_ID}")

    offset = 0
    async with httpx.AsyncClient(verify=False, timeout=35) as http:
        await check_no_webhook(http)
        while True:
            try:
                r = await http.get(f"{API}/getUpdates", params={
                    "offset": offset,
                    "timeout": 30,
                    "allowed_updates": ["message"],
                })
                data = r.json()
                if not data.get("ok"):
                    print(f"Ошибка getUpdates: {data}")
                    await asyncio.sleep(5)
                    continue

                for update in data["result"]:
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if msg:
                        await handle_message(http, msg)

            except Exception as e:
                print(f"Ошибка: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
