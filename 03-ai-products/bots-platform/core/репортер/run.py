"""
Запуск анализа макро-рисков и публикация результата в Telegram-канал.

Использует движок из Money_alert_AI (путь задаётся через MONEY_ALERT_SRC в .env).

Запуск:
    python run.py                             # анализ + публикация (провайдер из .env)
    python run.py --provider gigachat         # явно указать провайдер
    python run.py --from-file                 # читать EXPORT_WEB_JSON / ../Money_alert_AI/docs/data.json
    python run.py --from-file path/data.json  # читать конкретный файл
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Файл хранит message_id последнего опубликованного поста
_STATE_FILE = Path(__file__).parent / "last_post_state.json"


def _load_post_state() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_post_state(run_id: int, message_id: int, chat_id: str) -> None:
    state = {
        "run_id": run_id,
        "message_id": message_id,
        "chat_id": chat_id,
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"💾 Состояние сохранено: run_id={run_id}, message_id={message_id}")


def _validate_data(data: dict) -> list[str]:
    """Проверяет data.json перед публикацией. Возвращает список ошибок."""
    errors: list[str] = []

    # 1. criteria_registry не пустой
    registry = data.get("criteria_registry", [])
    if not registry:
        errors.append("criteria_registry пустой — веса критериев неизвестны")

    # 2. total_score совпадает с суммой весов triggered
    if registry:
        registry_by_id = {c["id"]: c for c in registry}
        triggered = data.get("triggered_criteria", [])
        triggered_ids = [t["id"] if isinstance(t, dict) else t for t in triggered]
        expected = sum(registry_by_id.get(cid, {}).get("weight", 0) for cid in triggered_ids)
        actual = data.get("total_score", 0)
        if expected > 0 and actual != expected:
            errors.append(
                f"total_score={actual} не совпадает с суммой весов triggered={expected}"
            )

    # 3. history последней записи совпадает с текущим run_id + score
    run_id = data.get("run_id")
    score = data.get("total_score", 0)
    level = data.get("risk_level", "")
    history = data.get("history", [])
    if history and run_id is not None:
        last = history[-1]
        if last.get("run_id") == run_id:
            if last.get("total_score") != score:
                errors.append(
                    f"history[-1].total_score={last.get('total_score')} != total_score={score}"
                )
            if last.get("risk_level") != level:
                errors.append(
                    f"history[-1].risk_level={last.get('risk_level')} != risk_level={level}"
                )

    return errors

# Подключаем движок Money_alert_AI через путь из .env
_src = os.getenv("MONEY_ALERT_SRC")
if not _src:
    _fallback = Path(__file__).parent.parent.parent.parent / "Money_alert_AI" / "src"
    if _fallback.exists():
        _src = str(_fallback)
    else:
        raise SystemExit(
            "❌ Не задана переменная MONEY_ALERT_SRC в .env\n"
            "   Пример: MONEY_ALERT_SRC=C:\\path\\to\\Money_alert_AI\\src"
        )

sys.path.insert(0, _src)

from telegram_publisher import (  # noqa: E402
    format_telegram_report,
    send_telegram_report,
    notify_admin,
    _make_bot,
)
import re as _re


def _find_data_json() -> str | None:
    """Ищет data.json: EXPORT_WEB_JSON → ../Money_alert_AI/docs/data.json."""
    export_path = os.getenv("EXPORT_WEB_JSON")
    if export_path and Path(export_path).exists():
        return export_path
    fallback = Path(_src).parent / "docs" / "data.json"
    if fallback.exists():
        return str(fallback)
    return None


def _load_data_json(path: str) -> dict | None:
    """Читает data.json и конвертирует в формат, ожидаемый format_telegram_report."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл не найден: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return None

    # data.json — плоская структура; оборачиваем в {"result": {...}, "stats": {...}}

    # Строим индекс: id -> {weight, name} из criteria_registry
    registry_by_id: dict[str, dict] = {
        c["id"]: c for c in data.get("criteria_registry", [])
    }
    # Строим индекс rationale из criteria_status
    status_by_id: dict[str, dict] = {
        s["id"]: s for s in data.get("criteria_status", [])
    }

    # triggered_criteria может быть списком строк (id) или списком объектов
    raw_triggered = data.get("triggered_criteria", [])
    triggered_criteria: list[dict] = []
    for item in raw_triggered:
        if isinstance(item, str):
            cid = item
            reg = registry_by_id.get(cid, {})
            st  = status_by_id.get(cid, {})
            triggered_criteria.append({
                "id":       cid,
                "name":     reg.get("name", cid),
                "weight":   f"+{reg['weight']}" if reg.get("weight") else "",
                "evidence": st.get("rationale", ""),
            })
        elif isinstance(item, dict):
            triggered_criteria.append(item)

    return {
        "result": {
            "risk_level":          data.get("risk_level", "unknown"),
            "total_score":         data.get("total_score", 0),
            "confidence":          data.get("confidence"),
            "deposit_access_risk": data.get("deposit_access_risk", "green"),
            "triggered_criteria":  triggered_criteria,
            "summary":             data.get("summary", ""),
            "positive_trends":     data.get("positive_trends", []),
            "negative_trends":     data.get("negative_trends", []),
            "key_risks_6m":        data.get("key_risks_6m", []),
            "watchlist":           data.get("watchlist", []),
            "sources":             [],
        },
        "stats": {
            **data.get("stats", {}),
            "run_id":        data.get("run_id"),
            "steps":         len(data.get("criteria_registry", [])) or data.get("stats", {}).get("steps", 0),
            "history_trend": "",
        },
    }


async def _edit_existing_post(report: str, message_id: int, chat_id: str) -> bool:
    """Редактирует существующий пост в канале. Возвращает True при успехе."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return False
    try:
        bot = _make_bot(token)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=report,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        print(f"✅ Пост отредактирован (message_id={message_id})")
        return True
    except Exception as exc:
        if "parse entities" in str(exc).lower():
            try:
                bot2 = _make_bot(token)
                plain = _re.sub(r"<[^>]+>", "", report)
                await bot2.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=plain,
                    disable_web_page_preview=True,
                )
                print(f"✅ Пост отредактирован (plain, message_id={message_id})")
                return True
            except Exception as exc2:
                print(f"❌ Ошибка редактирования (plain): {exc2}")
                return False
        print(f"⚠️ Не удалось отредактировать пост: {exc}")
        return False


async def _publish_result(result: dict, raw_data: dict | None = None, *, force_publish: bool = False) -> None:
    """Форматирует отчёт и отправляет/редактирует в канале.

    Логика:
    - Если тот же run_id уже опубликован → редактировать существующий пост.
    - Иначе → опубликовать новый пост и сохранить message_id.
    """
    report     = format_telegram_report(result, result["stats"])
    score      = result["result"].get("total_score", 0)
    risk_level = result["result"].get("risk_level", "unknown")
    stats      = result["stats"]
    run_id     = stats.get("run_id")

    risk_map = {
        "green":  ("🟢", "НИЗКИЙ"),
        "yellow": ("🟡", "СРЕДНИЙ"),
        "orange": ("🟠", "СУЩЕСТВЕННЫЙ"),
        "red":    ("🔴", "ВЫСОКИЙ"),
        "black":  ("⚫", "АВАРИЙНЫЙ"),
    }
    risk_emoji, risk_label = risk_map.get(risk_level, ("❓", "НЕИЗВЕСТНО"))

    # ── Валидация данных перед публикацией ──────────────────────────────────
    if raw_data is not None:
        errors = _validate_data(raw_data)
        if errors:
            for err in errors:
                print(f"❌ Ошибка валидации: {err}")
            raise SystemExit(
                "❌ Публикация отменена: данные не прошли валидацию.\n"
                "   Исправьте ошибки выше и запустите снова."
            )
        print(f"✅ Валидация пройдена (score={score}, triggered={len(raw_data.get('triggered_criteria', []))})")

    # ── Проверка: этот run_id уже публиковался? ─────────────────────────────
    state = _load_post_state()
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID", "")
    already_published = (
        state.get("run_id") == run_id
        and state.get("message_id")
        and state.get("chat_id") == chat_id
    )

    if already_published and not force_publish:
        existing_msg_id = state["message_id"]
        print(f"♻️  run_id={run_id} уже опубликован (message_id={existing_msg_id}), редактирую...")
        edited = await _edit_existing_post(report, existing_msg_id, chat_id)
        if edited:
            await notify_admin(
                f"♻️ Пост обновлён (run #{run_id})\n"
                f"Риск: {risk_emoji} {risk_label}, очки: {score}"
            )
        else:
            print("⚠️ Редактирование не удалось — пост уже опубликован, новый не создаём")
            await notify_admin(f"⚠️ Не удалось обновить пост run #{run_id} (message_id={existing_msg_id})")
        return

    # ── Новый пост ──────────────────────────────────────────────────────────
    print(f"📤 Публикация в канал (риск: {risk_emoji} {risk_label}, очки: {score})")
    message_id = await send_telegram_report(report)
    if message_id and chat_id and run_id is not None:
        _save_post_state(run_id, message_id, chat_id)

    await notify_admin(
        f"✅ Пост опубликован (run #{run_id})\n"
        f"Риск: {risk_emoji} {risk_label}, очки: {score}\n"
        f"Время: {stats.get('time_seconds', 0):.0f}с, "
        f"поисков: {stats.get('tool_calls', 0)}"
    )


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Запуск анализа макро-рисков + публикация в ТГ"
    )
    parser.add_argument(
        "--provider",
        choices=["gigachat", "openai", "gemini", "anthropic"],
        default=os.getenv("MODEL_PROVIDER", "openai"),
        help="Провайдер LLM (игнорируется при --from-file)",
    )
    parser.add_argument(
        "--criteria",
        default=os.getenv("CRITERIA_FILE", "criteria.json"),
        help="Файл критериев относительно корня Money_alert_AI (игнорируется при --from-file)",
    )
    parser.add_argument(
        "--from-file",
        nargs="?",
        const="AUTO",
        metavar="PATH",
        help=(
            "Читать готовый результат из data.json вместо запуска анализа. "
            "Без аргумента — автопоиск через EXPORT_WEB_JSON или "
            "../Money_alert_AI/docs/data.json"
        ),
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Публиковать в канал принудительно (даже если score > 0)",
    )
    args = parser.parse_args()

    # ── Режим: подхватить готовый data.json ──────────────────────────────────
    if args.from_file is not None:
        path = args.from_file if args.from_file != "AUTO" else _find_data_json()
        if not path:
            raise SystemExit(
                "❌ Не найден data.json.\n"
                "   Задай EXPORT_WEB_JSON в .env или передай путь явно:\n"
                "   python run.py --from-file path/to/data.json"
            )
        print(f"📂 Читаю результат из: {path}")
        result = _load_data_json(path)
        if result is None:
            return
        run_id = result["stats"].get("run_id", "?")
        score  = result["result"].get("total_score", "?")
        level  = result["result"].get("risk_level", "?")
        print(f"   Прогон #{run_id} | риск: {level} | очки: {score}")
        raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
        await _publish_result(result, raw_data=raw_data, force_publish=args.publish)
        return

    # ── Режим: запустить анализ, затем опубликовать ───────────────────────────
    from lc_money_alert_bot import run_agent  # noqa: E402  # lazy import — тяжёлые зависимости
    from analysis_core import Logger  # noqa: E402

    provider_labels = {
        "gigachat": "GigaChat",
        "openai":   "OpenAI",
        "gemini":   "Gemini",
        "anthropic": "Anthropic",
    }
    provider_label = provider_labels.get(args.provider, args.provider)

    criteria_path = args.criteria
    if not Path(criteria_path).is_absolute():
        criteria_path = str(Path(_src).parent / criteria_path)

    with Logger() as logger:
        logger.log(f"📁 Лог: {logger.log_file}")
        await notify_admin(f"🚀 Начата генерация отчёта ({provider_label})...")

        try:
            result = await run_agent(criteria_path, logger, provider=args.provider)
        except Exception as e:
            error_detail = (
                logger.last_assistant_text.strip()
                if getattr(logger, "last_assistant_text", "")
                else str(e)
            )
            error_msg = f"❌ Агент упал:\n\n{error_detail}"
            logger.log(error_msg)
            await notify_admin(error_msg)
            return

        await _publish_result(result, force_publish=args.publish)
        logger.log(f"📁 Лог сохранён: {logger.log_file}")
        logger.log(f"💾 Состояние поста: {_STATE_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
