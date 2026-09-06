"""
Бот-модератор — Modal webhook (24/7).

Деплой:
    cd Бот_модератор
    uv run modal deploy modal_app.py

После деплоя один раз зарегистрировать webhook:
    uv run modal run modal_app.py::register_webhook

Секреты Modal (dashboard → Secrets → "telegram-moderator"):
    TELEGRAM_BOT_TOKEN
    TELEGRAM_GROUP_ID    (-1003999887282)
    TELEGRAM_ADMIN_CHAT_ID
"""

import modal

app = modal.App("bot-moderator")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("httpx>=0.27.0", "fastapi[standard]>=0.100.0")
    .add_local_file("filters.py", "/app/filters.py")
    .add_local_file("violations.py", "/app/violations.py")
)

violations_dict = modal.Dict.from_name("moderator-violations", create_if_missing=True)

MUTE_1H = 3_600
MUTE_1D = 86_400


def _get_count(user_id: int) -> int:
    return violations_dict.get(str(user_id), 0)


def _increment(user_id: int) -> int:
    key = str(user_id)
    count = violations_dict.get(key, 0) + 1
    violations_dict[key] = count
    return count


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("telegram-moderator")],
    timeout=25,
)
@modal.fastapi_endpoint(method="POST")
async def webhook(body: dict):
    import os, time, asyncio, sys
    sys.path.insert(0, "/app")
    import httpx
    from filters import is_ad, is_insult

    TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    GROUP_ID = os.environ["TELEGRAM_GROUP_ID"]
    ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")
    WHITELIST = {int(x) for x in os.environ.get("WHITELIST_USER_IDS", "").split(",") if x.strip()}
    API = f"https://api.telegram.org/bot{TOKEN}"

    msg = body.get("message")
    if not msg:
        return {"ok": True}

    chat_id = msg["chat"]["id"]
    if str(chat_id) != str(GROUP_ID):
        return {"ok": True}

    user = msg.get("from", {})
    if not user or user.get("is_bot"):
        return {"ok": True}

    user_id = user["id"]
    if user_id in WHITELIST:
        return {"ok": True}

    username = user.get("username", "")
    first_name = user.get("first_name", "")
    name = f"@{username}" if username else first_name
    msg_id = msg["message_id"]
    text = msg.get("text") or msg.get("caption") or ""

    async def delete():
        async with httpx.AsyncClient(timeout=20) as h:
            r = await h.post(f"{API}/deleteMessage", json={"chat_id": chat_id, "message_id": msg_id})
            result = r.json()
            if not result.get("ok"):
                print(f"deleteMessage failed: {result}")
                if ADMIN_CHAT_ID:
                    await h.post(f"{API}/sendMessage", json={
                        "chat_id": ADMIN_CHAT_ID,
                        "text": f"⚠️ Не удалось удалить сообщение {msg_id}: {result.get('description')}",
                    })

    async def mute(seconds):
        async with httpx.AsyncClient(timeout=20) as h:
            await h.post(f"{API}/restrictChatMember", json={
                "chat_id": chat_id, "user_id": user_id,
                "until_date": int(time.time()) + seconds,
                "permissions": {k: False for k in [
                    "can_send_messages","can_send_audios","can_send_documents",
                    "can_send_photos","can_send_videos","can_send_video_notes",
                    "can_send_voice_notes","can_send_polls","can_send_other_messages",
                    "can_add_web_page_previews",
                ]},
            })

    async def ban():
        async with httpx.AsyncClient(timeout=20) as h:
            await h.post(f"{API}/banChatMember", json={"chat_id": chat_id, "user_id": user_id, "revoke_messages": True})

    async def send(chat, text_msg):
        async with httpx.AsyncClient(timeout=20) as h:
            await h.post(f"{API}/sendMessage", json={"chat_id": chat, "text": text_msg, "parse_mode": "HTML"})

    # GIF
    if msg.get("animation"):
        await delete()
        print(f"[GIF] {name}")
        return {"ok": True}

    # Скрытые ссылки в entities (text_link прячет URL за текстом)
    entities = msg.get("entities") or msg.get("caption_entities") or []
    has_link_entity = any(e.get("type") in ("url", "text_link") for e in entities)

    if not text and not has_link_entity:
        return {"ok": True}

    # Реклама
    if is_ad(text) or has_link_entity:
        await asyncio.gather(delete(), ban(),
            send(ADMIN_CHAT_ID, f"🚫 <b>Бан (реклама)</b>\n{name} (<code>{user_id}</code>)\n<code>{text[:300]}</code>") if ADMIN_CHAT_ID else asyncio.sleep(0))
        print(f"[БАН/реклама] {name}")
        return {"ok": True}

    # Оскорбления
    if is_insult(text):
        count = _increment(user_id)
        if count == 1:
            await asyncio.gather(
                delete(), mute(MUTE_1H),
                send(chat_id, f"🔇 {name} замолчит на <b>1 час</b> за оскорбления. (предупреждение 1/3)"),
                send(ADMIN_CHAT_ID, f"🔇 Мьют 1ч #{count}: {name} (<code>{user_id}</code>)\n<code>{text[:300]}</code>") if ADMIN_CHAT_ID else asyncio.sleep(0),
            )
        elif count == 2:
            await asyncio.gather(
                delete(), mute(MUTE_1D),
                send(chat_id, f"🔇 {name} замолчит на <b>1 день</b> за повторные оскорбления. (предупреждение 2/3)"),
                send(ADMIN_CHAT_ID, f"🔇 Мьют 1д #{count}: {name} (<code>{user_id}</code>)\n<code>{text[:300]}</code>") if ADMIN_CHAT_ID else asyncio.sleep(0),
            )
        else:
            await asyncio.gather(
                delete(), ban(),
                send(chat_id, f"🚫 {name} заблокирован за систематические оскорбления (нарушение #{count})."),
                send(ADMIN_CHAT_ID, f"🚫 Бан/оскорбл #{count}: {name} (<code>{user_id}</code>)\n<code>{text[:300]}</code>") if ADMIN_CHAT_ID else asyncio.sleep(0),
            )
        print(f"[ОСКОРБЛ #{count}] {name}")

    return {"ok": True}


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("telegram-moderator")],
)
async def register_webhook():
    """Регистрирует webhook URL у Telegram. Запустить один раз после деплоя."""
    import os, httpx
    TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    # Получаем URL задеплоенного webhook
    webhook_url = f"https://kaluginvit--bot-moderator-webhook.modal.run"
    async with httpx.AsyncClient(timeout=20) as h:
        r = await h.post(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            json={"url": webhook_url, "allowed_updates": ["message"]},
        )
        print(r.json())
