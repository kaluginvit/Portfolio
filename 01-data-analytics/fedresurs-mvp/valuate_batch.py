#!/usr/bin/env python3
"""
valuate_batch.py — пакетная оценка активных лотов через LLM + Tavily/Brave/Google.

Обрабатывает лоты в порядке срочности (самые горящие сначала).
На rate-limit ошибке Tavily останавливается, не сжигая квоту вхолостую.

Usage:
    python valuate_batch.py               # все без оценки, по срочности
    python valuate_batch.py --limit 30    # первые 30 самых срочных
    python valuate_batch.py --dry-run     # показать список без вызова API
    python valuate_batch.py --force       # переоценить уже оценённые
    python valuate_batch.py --provider brave
    python valuate_batch.py --delay 5     # пауза между лотами (сек)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("valuate_batch")

from valuate import (
    DB_PATH, DEFAULT_MODEL, SYSTEM_PROMPT, TOOLS,
    build_prompt, do_search, ensure_valuation_columns,
    format_search_results, load_lot_documents, make_llm_client, save_valuation,
)


# ── Urgency helpers ────────────────────────────────────────────────────────

def _parse_ru_date(s: str | None) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.datetime.strptime(s[:10], "%d.%m.%Y").date()
    except ValueError:
        return None


def _lot_urgency(lot: dict, schedule: list[dict]) -> int:
    """Days to nearest active deadline. 99999 if unknown."""
    today = dt.date.today()
    days_period = None
    for p in schedule:
        df  = _parse_ru_date(p["date_from"])
        dto = _parse_ru_date(p["date_to"])
        if df and dto and df <= today <= dto:
            days_period = (dto - today).days
            break
    app_d = _parse_ru_date(lot.get("app_end"))
    days_app = (app_d - today).days if app_d else None
    auc_d = _parse_ru_date(lot.get("auction_datetime"))
    days_auc = (auc_d - today).days if auc_d else None
    cands = [d for d in [days_period, days_app, days_auc] if d is not None and d >= 0]
    return min(cands) if cands else 99999


def fetch_queue(force: bool, browser: str | None = None) -> list[tuple[int, dict]]:
    """Returns [(urgency_days, lot), ...] sorted by urgency ascending."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    ensure_valuation_columns(db)

    where = "status = 'Активен'"
    if not force:
        where += " AND price_min IS NULL"
    if browser:
        where += f" AND source_browser = '{browser}'"

    lots = [dict(r) for r in db.execute(f"SELECT * FROM lots WHERE {where}")]
    schedules = [dict(r) for r in db.execute(
        "SELECT * FROM price_schedule ORDER BY lot_id, period_no"
    )]
    db.close()

    sched_by_lot: dict[str, list] = {}
    for s in schedules:
        sched_by_lot.setdefault(s["lot_id"], []).append(s)

    queue = [(
        _lot_urgency(lot, sched_by_lot.get(lot["lot_id"], [])),
        lot,
    ) for lot in lots]
    queue.sort(key=lambda x: x[0])
    return queue


# ── Valuation ─────────────────────────────────────────────────────────────

def _is_rate_limit(e: Exception) -> bool:
    msg = str(e).lower()
    return any(k in msg for k in ("rate limit", "quota", "429", "usage limit", "exceeded", "too many"))


def run_valuation(lot: dict, model: str, openrouter_key: str | None,
                  tavily_key: str | None, brave_key: str | None,
                  google_api_key: str | None, google_cx: str | None,
                  provider: str, gemini_key: str | None = None) -> dict | None:
    from tavily import TavilyClient

    lot_id = lot["lot_id"]
    documents = load_lot_documents(lot_id)

    ai, is_gemini = make_llm_client(gemini_key, openrouter_key)
    tavily = TavilyClient(api_key=tavily_key) if tavily_key and provider == "tavily" else None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": build_prompt(lot, documents)},
    ]

    search_count = 0
    while True:
        kwargs: dict = {"model": model, "messages": messages, "tools": TOOLS}
        if not is_gemini:
            kwargs["extra_body"] = {"reasoning": {"effort": "high"}}
        for _attempt in range(5):
            try:
                response = ai.chat.completions.create(**kwargs)
                break
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower() or "quota" in str(e).lower():
                    wait = 35 * (2 ** _attempt)
                    logger.warning("Rate limit (попытка %d/5): жду %dс...", _attempt + 1, wait)
                    print(f"    [rate limit] жду {wait}с...")
                    time.sleep(wait)
                    if _attempt == 4:
                        raise
                else:
                    raise
        choice = response.choices[0]
        msg = choice.message
        messages.append(msg.model_dump(exclude_unset=True))

        if choice.finish_reason == "tool_calls":
            for tool_call in msg.tool_calls:
                if tool_call.function.name == "web_search":
                    query = json.loads(tool_call.function.arguments)["query"]
                    search_count += 1
                    print(f"    [{search_count}] {query}")
                    results = do_search(
                        query, provider, tavily, brave_key, google_api_key, google_cx
                    )
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      format_search_results(results),
                    })
        else:
            text = msg.content or ""
            start = text.find("{")
            end   = text.rfind("}") + 1
            if start != -1 and end > 0:
                try:
                    return json.loads(text[start:end])
                except (json.JSONDecodeError, ValueError):
                    pass
            return None


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Пакетная LLM-оценка лотов Федресурса")
    p.add_argument("--limit",    type=int,   default=None,  help="Максимум лотов за запуск")
    p.add_argument("--delay",    type=float, default=3.0,   help="Пауза между лотами (сек)")
    p.add_argument("--dry-run",  action="store_true",       help="Показать очередь без вызова API")
    p.add_argument("--force",    action="store_true",       help="Переоценить уже оценённые")
    p.add_argument("--model",    default=DEFAULT_MODEL,     help=f"Модель (default: {DEFAULT_MODEL})")
    p.add_argument("--provider", default=None, choices=["tavily", "brave", "google", "jina"])
    p.add_argument("--browser",  default=None, choices=["Chrome", "Chromium"], help="Фильтр по источнику")
    args = p.parse_args()

    # Keys
    gemini_key     = os.environ.get("GEMINI_API_KEY") or None
    openrouter_key = os.environ.get("OPENROUTER_API_KEY") or None
    tavily_key     = os.environ.get("TAVILY_API_KEY") or None
    brave_key      = os.environ.get("BRAVE_API_KEY") or None
    google_api_key = os.environ.get("GOOGLE_API_KEY") or None
    google_cx      = os.environ.get("GOOGLE_CX") or None

    provider = args.provider
    if not provider and not args.dry_run:
        if not gemini_key and not openrouter_key:
            print("Нужен GEMINI_API_KEY или OPENROUTER_API_KEY в .env"); sys.exit(1)
        if tavily_key:
            provider = "tavily"
        elif google_api_key and google_cx:
            provider = "google"
        elif brave_key:
            provider = "brave"
        else:
            provider = "jina"

    # Build queue
    queue = fetch_queue(args.force, args.browser)
    if args.limit:
        queue = queue[:args.limit]
    total = len(queue)

    print(f"Лотов к оценке: {total}  |  провайдер: {provider or '—'}  |  модель: {args.model}")
    print(f"Сортировка: по срочности (ближайший дедлайн — первый)\n")

    if args.dry_run:
        for i, (urg, lot) in enumerate(queue, 1):
            urg_str = f"{urg} дн" if urg < 99999 else "нет дат"
            desc = (lot.get("description") or "")[:65]
            trade = (lot.get("trade_type") or "")[:12]
            print(f"  {i:4d}. [{urg_str:>8}] {lot['lot_id']:22} [{trade}] {desc}")
        return

    ok_count = err_count = 0

    for i, (urg, lot) in enumerate(queue, 1):
        lid     = lot["lot_id"]
        urg_str = f"{urg} дн" if urg < 99999 else "—"
        desc    = (lot.get("description") or "")[:75]
        print(f"\n[{i}/{total}] {lid}  срочность: {urg_str}")
        print(f"  {desc}")

        try:
            result = run_valuation(
                lot, args.model, openrouter_key,
                tavily_key, brave_key, google_api_key, google_cx, provider,
                gemini_key=gemini_key,
            )
            if result:
                save_valuation(lid, result)
                lo = result.get("auction_price_min") or result.get("market_price_min") or 0
                hi = result.get("auction_price_max") or result.get("market_price_max") or 0
                fmt = lambda n: f"{n:,.0f}".replace(",", " ")
                conf = result.get("confidence", "?")
                print(f"  ✓  {fmt(lo)} — {fmt(hi)} ₽  [{conf}]")
                ok_count += 1
            else:
                print("  ⚠  модель не вернула корректный JSON")
                err_count += 1

        except Exception as e:
            if _is_rate_limit(e):
                logger.error("Rate limit hit после %d/%d лотов", i - 1, total)
                print(f"\n  ⛔  Rate limit — остановка после {i - 1}/{total} лотов")
                print(f"  Запустите позже или переключите провайдер: --provider brave")
                break
            logger.error("Ошибка при оценке лота %s: %s", lid, e)
            print(f"  ✗  Ошибка: {e}")
            err_count += 1

        if i < total:
            time.sleep(args.delay)

    print(f"\n{'═' * 50}")
    print(f"Готово: ✓ {ok_count}  ✗ {err_count}  из {min(i, total)}")
    print(f"Перезапустите `python fedresurs.py --no-fetch` чтобы обновить дашборд")


if __name__ == "__main__":
    main()
