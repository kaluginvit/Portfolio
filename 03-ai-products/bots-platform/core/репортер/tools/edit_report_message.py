import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot
from telegram.request import HTTPXRequest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run import _load_data_json  # noqa: E402
from telegram_publisher import format_telegram_report  # noqa: E402


def _ssl_verify() -> bool:
    return os.getenv("TELEGRAM_VERIFY_SSL", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Edit an existing Telegram report message")
    parser.add_argument("message_id", type=int)
    parser.add_argument("data_json")
    parser.add_argument("--chat-id", default=None)
    args = parser.parse_args()

    load_dotenv()
    loaded = _load_data_json(args.data_json)
    if loaded is None:
        raise SystemExit(1)

    report = format_telegram_report(loaded, loaded["stats"])
    if len(report) > 4096:
        raise SystemExit(f"Report is too long for one edited message: {len(report)} chars")

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = args.chat_id or os.environ["TELEGRAM_CHANNEL_ID"]
    bot = Bot(token, request=HTTPXRequest(httpx_kwargs={"verify": _ssl_verify()}))

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=args.message_id,
            text=report,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception as exc:
        if "parse entities" not in str(exc).lower():
            raise
        plain = re.sub(r"<[^>]+>", "", report)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=args.message_id,
            text=plain,
            disable_web_page_preview=True,
        )
    print(f"Edited message_id={args.message_id} from {args.data_json}")


if __name__ == "__main__":
    asyncio.run(main())
