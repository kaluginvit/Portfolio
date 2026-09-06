import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot
from telegram.request import HTTPXRequest


def _ssl_verify() -> bool:
    return os.getenv("TELEGRAM_VERIFY_SSL", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


async def main() -> None:
    load_dotenv()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    bot = Bot(token, request=HTTPXRequest(httpx_kwargs={"verify": _ssl_verify()}))
    updates = await bot.get_updates(
        timeout=1,
        allowed_updates=["channel_post", "message", "edited_channel_post", "edited_message"],
    )
    for update in updates[-30:]:
        msg = (
            update.channel_post
            or update.edited_channel_post
            or update.message
            or update.edited_message
        )
        if not msg:
            continue
        text = (msg.text or msg.caption or "").replace("\n", " ")[:180]
        print(
            f"update_id={update.update_id} chat_id={msg.chat_id} "
            f"message_id={msg.message_id} date={msg.date.isoformat()} text={text}"
        )


if __name__ == "__main__":
    asyncio.run(main())
