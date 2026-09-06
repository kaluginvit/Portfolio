"""Батчевое LLM-обогащение постов: entities + tags + insight (текстовый режим)."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

from tqdm import tqdm

from db import connect_rw, all_rows
from llm_client import call_llm

HERE = Path(__file__).parent

SYSTEM_PROMPT = (
    "Ты аналитик российской экономики и геополитики.\n"
    "Для каждого сообщения Telegram-канала верни JSON-массив объектов.\n"
    "Отвечай ТОЛЬКО валидным JSON без пояснений."
)

USER_PROMPT = (
    "Сообщения для анализа:\n{messages_json}\n\n"
    "Для каждого верни объект:\n"
    "{{\n"
    '  "message_id": <число>,\n'
    '  "entities": ["Роснефть", "Путин", "$10 млрд"],\n'
    '  "tags": ["энергетика", "санкции", "нефть"],\n'
    '  "insight": "Три предложения: суть поста и почему важно."\n'
    "}}\n"
    "entities — персоны, компании, страны, суммы.\n"
    "tags — 2-5 тематических тегов по-русски.\n"
    "insight — строго три предложения на русском."
)


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _parse_response(content: str) -> list[dict]:
    """Парсит JSON из ответа LLM. Устойчив к лишнему тексту после JSON."""
    # Убираем markdown-блоки
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)
    if match:
        content = match.group(1).strip()
    else:
        content = content.strip()

    decoder = json.JSONDecoder()
    data = None

    # Ищем массив [...]
    for m in re.finditer(r"\[", content):
        try:
            obj, _ = decoder.raw_decode(content, m.start())
            data = obj
            break
        except json.JSONDecodeError:
            continue

    # Ищем отдельные объекты {...} подряд
    if data is None:
        objects = []
        pos = 0
        while pos < len(content):
            idx = content.find("{", pos)
            if idx == -1:
                break
            try:
                obj, end = decoder.raw_decode(content, idx)
                if isinstance(obj, dict):
                    objects.append(obj)
                pos = end
            except json.JSONDecodeError:
                pos = idx + 1
        if objects:
            data = objects

    if data is None:
        return []

    if not isinstance(data, list):
        data = [data]

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        mid = item.get("message_id")
        if mid is None:
            continue
        results.append({
            "message_id": int(mid),
            "entities": item.get("entities") or [],
            "tags":     item.get("tags") or [],
            "insight":  item.get("insight") or "",
        })
    return results


def analyze_batch(rows: list[dict], max_tokens: int, temperature: float) -> list[dict]:
    batch_input = [
        {
            "message_id": r["message_id"],
            "date":       r["date"],
            "text":       (r.get("text") or "")[:2000],
        }
        for r in rows
    ]
    user_content = USER_PROMPT.format(
        messages_json=json.dumps(batch_input, ensure_ascii=False, indent=2)
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]
    # models=None → ротация по всем моделям из OPENROUTER_MODELS (все 3 × 2 ключа)
    content, _model, _usage = call_llm(
        messages,
        models=None,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return _parse_response(content)


def save_enrichments(con: sqlite3.Connection, results: list[dict], model: str) -> int:
    saved = 0
    for r in results:
        mid = r["message_id"]
        entities_json = json.dumps(r.get("entities") or [], ensure_ascii=False)
        tags_json     = json.dumps(r.get("tags") or [],     ensure_ascii=False)
        insight       = r.get("insight") or ""

        # Добавляем тег "фото" если пост содержит изображение
        if r.get("has_photo"):
            tags = r.get("tags") or []
            if "фото" not in tags:
                tags = list(tags) + ["фото"]
            tags_json = json.dumps(tags, ensure_ascii=False)

        con.execute(
            """INSERT OR REPLACE INTO enrichments
               (message_id, entities, tags, insight, llm_model, created_at)
               VALUES (?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%S','now'))""",
            (mid, entities_json, tags_json, insight, model),
        )
        con.execute("DELETE FROM enrichments_fts WHERE message_id = ?", (mid,))
        con.execute(
            "INSERT INTO enrichments_fts (message_id, insight, tags, entities) VALUES (?,?,?,?)",
            (mid, insight, tags_json, entities_json),
        )
        saved += 1

    con.commit()
    return saved


def run_analyze(
    db_path: Path,
    batch_size: int = 80,
    limit: int = 0,
    force: bool = False,
) -> dict:
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    max_tokens  = int(cfg.get("max_tokens",  12000))
    temperature = float(cfg.get("temperature", 0.3))

    con = connect_rw(db_path)
    source = "messages_filtered" if _table_exists(con, "messages_filtered") else "messages"

    if force:
        rows = all_rows(con, f"SELECT m.message_id, m.date, m.text, m.has_photo FROM {source} m ORDER BY m.message_id")
    else:
        rows = all_rows(con, f"""
            SELECT m.message_id, m.date, m.text, m.has_photo
            FROM {source} m
            LEFT JOIN enrichments e ON e.message_id = m.message_id
            WHERE e.message_id IS NULL
            ORDER BY m.message_id
        """)

    if limit > 0:
        rows = rows[:limit]

    total = len(rows)
    if total == 0:
        print("Нет записей для обогащения.")
        con.close()
        return {"processed": 0, "errors": 0, "stopped_rate_limit": False}

    batches = [rows[i:i + batch_size] for i in range(0, total, batch_size)]
    print(f"Всего: {total} постов | {len(batches)} батчей | batch_size={batch_size}")

    processed = 0
    errors = 0
    stopped = False
    current_bs = batch_size

    bar = tqdm(total=len(batches), desc="Обогащение", unit="батч",
               bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] сохр:{postfix}")
    bar.set_postfix_str(str(processed))

    for idx, batch in enumerate(batches, 1):
        # Если batch_size уменьшился — дробим
        sub_batches = [batch[i:i+current_bs] for i in range(0, len(batch), current_bs)] if current_bs < len(batch) else [batch]

        for sub in sub_batches:
            try:
                results = analyze_batch(sub, max_tokens, temperature)
            except RuntimeError as exc:
                tqdm.write(f"⛔ Все модели исчерпали rate limit — остановка. Прогресс сохранён.")
                stopped = True
                break
            except Exception as exc:
                tqdm.write(f"  [error] батч {idx}: {exc}")
                errors += len(sub)
                continue

            if not results:
                new_bs = max(5, len(sub) // 2)
                if new_bs < len(sub):
                    tqdm.write(f"  [warn] Пустой ответ — уменьшаю батч: {len(sub)} → {new_bs}")
                    current_bs = new_bs
                    for ssub in [sub[i:i+new_bs] for i in range(0, len(sub), new_bs)]:
                        try:
                            r2 = analyze_batch(ssub, max_tokens, temperature)
                            if r2:
                                saved = save_enrichments(con, r2, "rotation")
                                processed += saved
                        except RuntimeError:
                            stopped = True
                            break
                        except Exception as e:
                            tqdm.write(f"  [error] retry: {e}")
                    if stopped:
                        break
                else:
                    errors += len(sub)
                continue

            saved = save_enrichments(con, results, "rotation")
            processed += saved
            miss = len(sub) - saved
            if miss:
                tqdm.write(f"  [warn] батч {idx}: {miss} без ответа")

        bar.update(1)
        bar.set_postfix_str(str(processed))
        if stopped:
            break

    bar.close()
    con.close()
    print(f"\nГотово. Обработано: {processed}, ошибок: {errors}")
    return {"processed": processed, "errors": errors, "stopped_rate_limit": stopped}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--limit",      type=int,  default=0,    help="Лимит постов (0=все)")
    p.add_argument("--force",      action="store_true",     help="Переобработать уже готовые")
    p.add_argument("--batch-size", type=int,  default=80,   help="Размер батча")
    p.add_argument("--db",         type=Path, default=HERE / "data" / "messages.db")
    args = p.parse_args()

    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    result = run_analyze(args.db, batch_size=args.batch_size, limit=args.limit, force=args.force)
    if result["stopped_rate_limit"]:
        print("Остановлено по rate limit — запусти завтра снова.")


if __name__ == "__main__":
    main()
