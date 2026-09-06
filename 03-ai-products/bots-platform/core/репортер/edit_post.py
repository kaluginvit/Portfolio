"""
Редактирует последний опубликованный пост в Telegram используя сохранённый message_id.
Вызывается из lc_money_alert_bot.py как: python edit_post.py

Если last_post_state.json отсутствует или message_id не найден — публикует новый пост.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from run import _find_data_json, _load_data_json, _load_post_state, _publish_result  # noqa: E402


async def main() -> None:
    path = _find_data_json()
    if not path:
        raise SystemExit("❌ edit_post.py: не найден data.json")

    print(f"📂 edit_post.py: читаю {path}")
    result = _load_data_json(path)
    if result is None:
        raise SystemExit("❌ edit_post.py: не удалось прочитать data.json")

    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    run_id = result["stats"].get("run_id", "?")
    score = result["result"].get("total_score", "?")
    print(f"   Прогон #{run_id} | очки: {score}")

    await _publish_result(result, raw_data=raw_data)


if __name__ == "__main__":
    asyncio.run(main())
