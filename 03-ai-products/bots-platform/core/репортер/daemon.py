"""
Демон автопубликации: следит за data.json и публикует при появлении нового прогона.

Логика:
  - Каждую минуту проверяет run_id в data.json
  - Если run_id изменился с прошлой публикации — публикует
  - Состояние (последний опубликованный run_id) хранится в .last_published_run_id

Настройка в .env:
    EXPORT_WEB_JSON=...          # путь к data.json
    WATCH_INTERVAL=60            # интервал проверки в секундах (по умолчанию 60)

Запуск:
    python daemon.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

_src = os.getenv("MONEY_ALERT_SRC")
if _src:
    sys.path.insert(0, _src)

sys.path.insert(0, str(Path(__file__).parent))

from telegram_publisher import format_telegram_report, send_telegram_report, notify_admin  # noqa: E402

STATE_FILE  = Path(__file__).parent / "last_post_state.json"


def _find_data_json() -> str | None:
    export_path = os.getenv("EXPORT_WEB_JSON")
    if export_path and Path(export_path).exists():
        return export_path
    if _src:
        fallback = Path(_src).parent / "docs" / "data.json"
        if fallback.exists():
            return str(fallback)
    return None


def _load_data_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения {path}: {e}")
        return None

    # triggered_criteria может быть списком строк (ID) или словарей
    raw_criteria = data.get("triggered_criteria", [])
    criteria_status = {c["id"]: c for c in data.get("criteria_status", []) if isinstance(c, dict)}
    triggered: list[dict] = []
    for item in raw_criteria:
        if isinstance(item, dict):
            triggered.append(item)
        else:
            detail = criteria_status.get(str(item), {})
            triggered.append({
                "name":     detail.get("name", str(item)),
                "weight":   detail.get("weight", ""),
                "evidence": detail.get("rationale", ""),
            })

    # sources может быть списком URL-строк или словарей
    raw_sources = data.get("sources", [])
    sources: list[dict] = []
    for i, src in enumerate(raw_sources, start=1):
        if isinstance(src, dict):
            sources.append(src)
        else:
            sources.append({"id": i, "url": str(src), "date": ""})

    return {
        "result": {
            "risk_level":          data.get("risk_level", "unknown"),
            "total_score":         data.get("total_score", 0),
            "confidence":          data.get("confidence"),
            "deposit_access_risk": data.get("deposit_access_risk", "green"),
            "triggered_criteria":  triggered,
            "summary":             data.get("summary", "") or data.get("pulse_summary", ""),
            "recommendation":      data.get("recommendation", ""),
            "positive_trends":     data.get("positive_trends", []),
            "negative_trends":     data.get("negative_trends", []),
            "key_risks_6m":        data.get("key_risks_6m", []),
            "asset_guidance":      data.get("asset_guidance", []),
            "watchlist":           data.get("watchlist", []),
            "sources":             sources,
        },
        "stats": {
            **data.get("stats", {}),
            "run_id":        data.get("run_id"),
            "history_trend": "",
        },
    }


def _get_last_published() -> int | None:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data.get("run_id")
        except Exception:
            return None
    return None


def _set_last_published(run_id: int) -> None:
    existing = {}
    if STATE_FILE.exists():
        try:
            existing = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing["run_id"] = run_id
    existing["published_at"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")


async def _publish_once(result: dict) -> None:
    run_id = result["stats"].get("run_id", "?")
    score  = result["result"].get("total_score", "?")
    level  = result["result"].get("risk_level", "?")

    report = format_telegram_report(result, result["stats"])

    risk_map = {
        "green":  ("🟢", "НИЗКИЙ"),
        "yellow": ("🟡", "СРЕДНИЙ"),
        "orange": ("🟠", "СУЩЕСТВЕННЫЙ"),
        "red":    ("🔴", "ВЫСОКИЙ"),
        "black":  ("⚫", "АВАРИЙНЫЙ"),
    }
    risk_emoji, risk_label = risk_map.get(level, ("❓", "НЕИЗВЕСТНО"))

    print(f"📤 Публикация прогона #{run_id} ({risk_emoji} {risk_label}, {score} очков)")
    await send_telegram_report(report)
    await notify_admin(
        f"✅ Автопубликация выполнена\n"
        f"Риск: {risk_emoji} {risk_label} | Очки: {score} | Прогон #{run_id}"
    )


async def main() -> None:
    interval = int(os.getenv("WATCH_INTERVAL", "60"))
    print(f"👀 Демон запущен. Проверка каждые {interval}с.")
    print(f"   data.json: {_find_data_json() or 'не найден'}")
    print("   Ctrl+C для остановки\n")

    last_published = _get_last_published()
    if last_published is not None:
        print(f"   Последний опубликованный прогон: #{last_published}")
    else:
        print("   Состояние не найдено — при первом обнаружении нового прогона опубликую")

    while True:
        path = _find_data_json()
        if path:
            result = _load_data_json(path)
            if result:
                current_run_id = result["stats"].get("run_id")
                if current_run_id is not None and current_run_id != last_published:
                    print(f"\n🆕 Новый прогон #{current_run_id} (был #{last_published}), публикую...")
                    try:
                        # Записываем ДО отправки — защита от повтора при рестарте
                        last_published = current_run_id
                        _set_last_published(current_run_id)
                        await _publish_once(result)
                    except Exception as e:
                        print(f"❌ Ошибка публикации: {e}")
                        try:
                            await notify_admin(f"❌ Демон: ошибка публикации прогона #{current_run_id}\n{e}")
                        except Exception:
                            pass
        else:
            print("⚠️  data.json не найден, жду...")

        await asyncio.sleep(interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Демон остановлен")
