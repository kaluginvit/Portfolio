"""
Tracks Telegram message reactions and appends them to reactions.csv.

This is the first product-analytics step for CLm03: it turns the channel from
"publish only" into a measurable funnel where reactions can be correlated with
topics, report format, and future subscription offers.

Requirements:
  - the bot must be allowed to receive message_reaction updates;
  - for channel posts, the bot should be an admin of the channel;
  - TELEGRAM_BOT_TOKEN must be set in .env.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()

CSV_FIELDS = [
    "timestamp",
    "chat_id",
    "message_id",
    "user_id",
    "old_reactions",
    "new_reactions",
    "raw_update_id",
]


def _reaction_label(item: dict[str, Any]) -> str:
    reaction_type = item.get("type", "")
    if reaction_type == "emoji":
        return str(item.get("emoji", ""))
    if reaction_type == "custom_emoji":
        return f"custom:{item.get('custom_emoji_id', '')}"
    return str(reaction_type or item)


def _reaction_list(items: list[dict[str, Any]] | None) -> str:
    if not items:
        return ""
    return " ".join(_reaction_label(item) for item in items)


def _ensure_csv(path: Path) -> None:
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()


async def _get_updates(client: httpx.AsyncClient, token: str, offset: int | None, timeout: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "timeout": timeout,
        "allowed_updates": ["message_reaction"],
    }
    if offset is not None:
        payload["offset"] = offset
    response = await client.post(f"https://api.telegram.org/bot{token}/getUpdates", json=payload, timeout=timeout + 10)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data)
    return data


def _append_reaction(path: Path, update: dict[str, Any]) -> bool:
    reaction = update.get("message_reaction")
    if not reaction:
        return False

    chat = reaction.get("chat", {})
    user = reaction.get("user", {})
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chat_id": chat.get("id", ""),
        "message_id": reaction.get("message_id", ""),
        "user_id": user.get("id", ""),
        "old_reactions": _reaction_list(reaction.get("old_reaction")),
        "new_reactions": _reaction_list(reaction.get("new_reaction")),
        "raw_update_id": update.get("update_id", ""),
    }

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(row)
    return True


async def track_reactions(csv_path: Path, *, once: bool, timeout: int) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")

    _ensure_csv(csv_path)
    offset: int | None = None
    print(f"Tracking Telegram reactions into {csv_path}")

    async with httpx.AsyncClient() as client:
        while True:
            data = await _get_updates(client, token, offset, timeout)
            updates = data.get("result", [])
            for update in updates:
                offset = int(update["update_id"]) + 1
                if _append_reaction(csv_path, update):
                    print(f"saved reaction update {update['update_id']}")

            if once:
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="Track Telegram message reactions into CSV")
    parser.add_argument("--csv", default="reactions.csv", help="CSV output path")
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    parser.add_argument("--timeout", type=int, default=30, help="Long polling timeout in seconds")
    args = parser.parse_args()

    asyncio.run(track_reactions(Path(args.csv), once=args.once, timeout=args.timeout))


if __name__ == "__main__":
    main()
