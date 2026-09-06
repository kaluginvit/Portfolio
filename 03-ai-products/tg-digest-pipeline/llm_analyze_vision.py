"""Батчевое LLM-обогащение постов: entities + tags + insight + photo."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sqlite3
from pathlib import Path

from tqdm import tqdm

from db import connect_rw, all_rows
from llm_client import call_llm

HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Промпты
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "Ты аналитик российской экономики и геополитики.\n"
    "Для каждого сообщения Telegram-канала верни JSON-массив объектов.\n"
    "Отвечай ТОЛЬКО валидным JSON без пояснений."
)

_USER_PROMPT_TEXT = (
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

_USER_PROMPT_VISION = (
    "Проанализируй пост с изображением.\n\n"
    "Данные поста:\n{message_json}\n\n"
    "Верни объект:\n"
    "{{\n"
    '  "message_id": <число>,\n'
    '  "entities": ["Роснефть", "Путин", "$10 млрд"],\n'
    '  "tags": ["энергетика", "фото"],\n'
    '  "insight": "Три предложения: суть поста включая содержание фото и почему важно.",\n'
    '  "photo_description": "Что изображено на фото.",\n'
    '  "photo_objects": ["объект1", "объект2"],\n'
    '  "photo_text": "Текст на картинке если есть, иначе пустая строка"\n'
    "}}\n"
    "entities — персоны, компании, страны, суммы.\n"
    "tags — 2-5 тематических тегов по-русски, ВСЕГДА включая тег \"фото\".\n"
    "insight — строго три предложения на русском, включая описание картинки.\n"
    "photo_description — подробное описание изображения.\n"
    "photo_objects — список объектов/субъектов на фото.\n"
    "photo_text — текст, видимый на картинке, или пустая строка."
)

VISION_MODEL = "minimax/minimax-m3:free"
TEXT_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "poolside/laguna-s-2.1:free",
]

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _load_photo_b64(photo_path: Path) -> str | None:
    """Читает фото и возвращает base64-строку, или None если файл не найден."""
    try:
        return base64.b64encode(photo_path.read_bytes()).decode()
    except (FileNotFoundError, OSError):
        return None


# ---------------------------------------------------------------------------
# Построение сообщений для LLM
# ---------------------------------------------------------------------------


def _build_vision_messages(row: dict, b64: str) -> list[dict]:
    """Строит multimodal messages для одного поста с фото."""
    msg_data = {
        "message_id": row["message_id"],
        "date": row["date"],
        "text": (row.get("text") or "")[:2000],
    }
    user_text = _USER_PROMPT_VISION.format(
        message_json=json.dumps(msg_data, ensure_ascii=False, indent=2)
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": user_text},
            ],
        },
    ]


def _build_text_messages(rows: list[dict]) -> list[dict]:
    """Строит текстовые messages для батча постов без фото."""
    batch_input = [
        {
            "message_id": r["message_id"],
            "date": r["date"],
            "text": (r.get("text") or "")[:2000],
        }
        for r in rows
    ]
    user_content = _USER_PROMPT_TEXT.format(
        messages_json=json.dumps(batch_input, ensure_ascii=False, indent=2)
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# Парсинг ответа
# ---------------------------------------------------------------------------


def _parse_response(content: str) -> list[dict]:
    """Парсит JSON из ответа LLM, обрабатывает ```json блоки и лишний текст."""
    # Убираем markdown-блоки
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)
    if match:
        content = match.group(1).strip()
    else:
        content = content.strip()

    decoder = json.JSONDecoder()
    data = None

    # Сначала пробуем найти массив [...] и взять первый валидный
    for m in re.finditer(r"\[", content):
        try:
            obj, _ = decoder.raw_decode(content, m.start())
            data = obj
            break
        except json.JSONDecodeError:
            continue

    # Если массива нет — ищем объект {...} и собираем все подряд
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
        tqdm.write(f"  [parse] не удалось извлечь JSON из ответа")
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
        result = {
            "message_id": int(mid),
            "entities": item.get("entities") or [],
            "tags": item.get("tags") or [],
            "insight": item.get("insight") or "",
        }
        # photo-поля присутствуют только в vision-ответах
        if "photo_description" in item:
            result["photo_description"] = item.get("photo_description") or ""
            result["photo_objects"] = item.get("photo_objects") or []
            result["photo_text"] = item.get("photo_text") or ""
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Анализ батчей
# ---------------------------------------------------------------------------


def analyze_batch_vision(
    rows: list[dict],
    max_tokens: int,
    temperature: float,
) -> list[dict]:
    """
    Обрабатывает посты с фото по одному (multimodal).
    Если файл фото не найден — обрабатывает как текстовый пост.
    Возвращает список обогащённых записей.
    """
    results: list[dict] = []
    text_fallback: list[dict] = []

    for row in rows:
        photo_field = row.get("photo")
        b64: str | None = None

        if photo_field:
            photo_path = HERE / photo_field
            b64 = _load_photo_b64(photo_path)

        if b64 is None:
            # Файл не найден — уйдёт в текстовый анализ
            text_fallback.append(row)
            continue

        messages = _build_vision_messages(row, b64)
        content, _model, _usage = call_llm(
            messages,
            models=[VISION_MODEL],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        parsed = _parse_response(content)
        results.extend(parsed)

    # Fallback для постов, у которых фото не найдено
    if text_fallback:
        tqdm.write(f"  [vision→text fallback] {len(text_fallback)} постов без фото")
        fb_results = analyze_batch_text(text_fallback, max_tokens, temperature)
        results.extend(fb_results)

    return results


def analyze_batch_text(
    rows: list[dict],
    max_tokens: int,
    temperature: float,
) -> list[dict]:
    """
    Обрабатывает текстовые посты батчем.
    Возвращает список обогащённых записей.
    """
    messages = _build_text_messages(rows)
    content, _model, _usage = call_llm(
        messages,
        models=TEXT_MODELS,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return _parse_response(content)


# ---------------------------------------------------------------------------
# Сохранение
# ---------------------------------------------------------------------------


def save_enrichments(
    con: sqlite3.Connection,
    results: list[dict],
    model: str,
) -> int:
    """
    INSERT OR REPLACE в enrichments + опционально photo_enrichments + UPDATE enrichments_fts.
    Возвращает количество сохранённых записей.
    """
    saved = 0
    for r in results:
        mid = r["message_id"]
        entities_json = json.dumps(r.get("entities") or [], ensure_ascii=False)
        tags_json = json.dumps(r.get("tags") or [], ensure_ascii=False)
        insight = r.get("insight") or ""

        con.execute(
            """
            INSERT OR REPLACE INTO enrichments
                (message_id, entities, tags, insight, llm_model, created_at)
            VALUES
                (?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%S','now'))
            """,
            (mid, entities_json, tags_json, insight, model),
        )

        # photo_enrichments — только если пришли photo-поля
        if "photo_description" in r:
            objects_json = json.dumps(r.get("photo_objects") or [], ensure_ascii=False)
            con.execute(
                """
                INSERT OR REPLACE INTO photo_enrichments
                    (message_id, description, objects, text_on_image, llm_model, created_at)
                VALUES
                    (?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%S','now'))
                """,
                (
                    mid,
                    r.get("photo_description") or "",
                    objects_json,
                    r.get("photo_text") or "",
                    model,
                ),
            )

        # Обновляем FTS
        con.execute("DELETE FROM enrichments_fts WHERE message_id = ?", (mid,))
        con.execute(
            "INSERT INTO enrichments_fts (message_id, insight, tags, entities) VALUES (?, ?, ?, ?)",
            (mid, insight, tags_json, entities_json),
        )
        saved += 1

    con.commit()
    return saved


# ---------------------------------------------------------------------------
# Основной цикл
# ---------------------------------------------------------------------------


def run_analyze(
    db_path: Path,
    batch_size: int = 80,
    limit: int = 0,
    force: bool = False,
) -> dict:
    """
    Основной цикл обогащения.

    - Читает messages_filtered (если нет — messages)
    - Разбивает на два потока: с фото (vision) и без фото (text)
    - batch_size для vision = 20, для text = batch_size (по умолчанию 80)
    - При RuntimeError (rate limit) — сохраняет прогресс, выходит
    - Авторедукция батча при пустом ответе (делить вдвое)
    - Возвращает {"processed": N, "errors": M, "stopped_rate_limit": bool}
    """
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    max_tokens = int(cfg.get("max_tokens", 12000))
    temperature = float(cfg.get("temperature", 0.3))

    con = connect_rw(db_path)

    # Определяем источник
    source_table = "messages_filtered" if _table_exists(con, "messages_filtered") else "messages"
    print(f"Источник: {source_table}")

    # Колонка has_photo может отсутствовать — проверим схему
    cols = {row["name"] for row in all_rows(con, f"PRAGMA table_info({source_table})")}
    has_photo_col = "has_photo" in cols
    photo_col = "photo" in cols

    if force:
        base_sql = f"SELECT * FROM {source_table} ORDER BY message_id"
        rows = all_rows(con, base_sql)
    else:
        rows = all_rows(
            con,
            f"""
            SELECT m.*
            FROM {source_table} m
            LEFT JOIN enrichments e ON e.message_id = m.message_id
            WHERE e.message_id IS NULL
            ORDER BY m.message_id
            """,
        )

    if limit > 0:
        rows = rows[:limit]

    total = len(rows)
    if total == 0:
        print("Нет записей для обогащения.")
        con.close()
        return {"processed": 0, "errors": 0, "stopped_rate_limit": False}

    # Разбиваем на два потока
    if has_photo_col:
        vision_rows = [r for r in rows if r.get("has_photo")]
        text_rows = [r for r in rows if not r.get("has_photo")]
    else:
        vision_rows = []
        text_rows = rows

    vision_batch_size = 20
    text_batch_size = batch_size

    print(
        f"Всего: {total} | vision: {len(vision_rows)} (батч={vision_batch_size})"
        f" | text: {len(text_rows)} (батч={text_batch_size})"
    )

    processed = 0
    errors = 0
    stopped_rate_limit = False

    # ------------------------------------------------------------------
    # Вспомогательная функция обработки одного батча
    # ------------------------------------------------------------------

    def _process_batch(
        batch: list[dict],
        batch_fn,
        batch_idx: int,
        current_bs: int,
        bar: tqdm,
    ) -> tuple[int, int, bool, int]:
        """Обрабатывает один батч. Возвращает (processed_delta, errors_delta, stopped, new_bs)."""
        nonlocal processed
        _proc = 0
        _err = 0
        _stopped = False
        _new_bs = current_bs

        try:
            results = batch_fn(batch, max_tokens, temperature)
        except RuntimeError as exc:
            if "недоступны" in str(exc).lower() or "rate limit" in str(exc).lower():
                tqdm.write("  Все модели исчерпали rate limit — остановка. Прогресс сохранён.")
                return _proc, _err, True, _new_bs
            tqdm.write(f"  [error] батч {batch_idx}: {exc}")
            return _proc, len(batch), False, _new_bs
        except Exception as exc:
            tqdm.write(f"  [error] батч {batch_idx}: {exc}")
            return _proc, len(batch), False, _new_bs

        if not results:
            new_size = max(5, len(batch) // 2)
            if new_size < len(batch):
                tqdm.write(f"  [warn] Пустой ответ — уменьшаю батч: {len(batch)} → {new_size}")
                _new_bs = new_size
                sub_batches = [batch[i: i + new_size] for i in range(0, len(batch), new_size)]
                for ssb in sub_batches:
                    try:
                        r2 = batch_fn(ssb, max_tokens, temperature)
                        if r2:
                            saved = save_enrichments(con, r2, VISION_MODEL if batch_fn is analyze_batch_vision else TEXT_MODELS[0])
                            _proc += saved
                            bar.set_postfix_str(f"сохр:{processed + _proc}")
                    except RuntimeError:
                        return _proc, _err, True, _new_bs
                    except Exception as exc2:
                        tqdm.write(f"  [error] retry: {exc2}")
            else:
                tqdm.write(f"  [warn] батч {batch_idx}: пустой ответ, пропускаем")
                _err += len(batch)
            return _proc, _err, False, _new_bs

        model_label = VISION_MODEL if batch_fn is analyze_batch_vision else TEXT_MODELS[0]
        saved = save_enrichments(con, results, model_label)
        _proc += saved
        missing = len(batch) - saved
        if missing > 0:
            tqdm.write(f"  [warn] батч {batch_idx}: {missing} записей без ответа от LLM")

        return _proc, _err, False, _new_bs

    # ------------------------------------------------------------------
    # Vision поток
    # ------------------------------------------------------------------

    if vision_rows:
        v_batches = [vision_rows[i: i + vision_batch_size] for i in range(0, len(vision_rows), vision_batch_size)]
        current_vbs = vision_batch_size

        bar_v = tqdm(
            v_batches,
            desc="Vision (фото)",
            unit="батч",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] сохр:{postfix}",
        )
        bar_v.set_postfix_str(f"{processed}")

        for idx, batch in enumerate(v_batches, 1):
            if current_vbs < len(batch):
                sub_batches = [batch[i: i + current_vbs] for i in range(0, len(batch), current_vbs)]
            else:
                sub_batches = [batch]

            for sb in sub_batches:
                d_proc, d_err, stopped, current_vbs = _process_batch(
                    sb, analyze_batch_vision, idx, current_vbs, bar_v
                )
                processed += d_proc
                errors += d_err
                if stopped:
                    stopped_rate_limit = True
                    break

            bar_v.update(1)
            bar_v.set_postfix_str(f"{processed}")

            if stopped_rate_limit:
                break

        bar_v.close()

    # ------------------------------------------------------------------
    # Text поток
    # ------------------------------------------------------------------

    if text_rows and not stopped_rate_limit:
        t_batches = [text_rows[i: i + text_batch_size] for i in range(0, len(text_rows), text_batch_size)]
        current_tbs = text_batch_size

        bar_t = tqdm(
            t_batches,
            desc="Text (текст) ",
            unit="батч",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] сохр:{postfix}",
        )
        bar_t.set_postfix_str(f"{processed}")

        for idx, batch in enumerate(t_batches, 1):
            if current_tbs < len(batch):
                sub_batches = [batch[i: i + current_tbs] for i in range(0, len(batch), current_tbs)]
            else:
                sub_batches = [batch]

            for sb in sub_batches:
                d_proc, d_err, stopped, current_tbs = _process_batch(
                    sb, analyze_batch_text, idx, current_tbs, bar_t
                )
                processed += d_proc
                errors += d_err
                if stopped:
                    stopped_rate_limit = True
                    break

            bar_t.update(1)
            bar_t.set_postfix_str(f"{processed}")

            if stopped_rate_limit:
                break

        bar_t.close()

    con.close()
    print(f"\nГотово. Обработано: {processed}, ошибок: {errors}")
    return {"processed": processed, "errors": errors, "stopped_rate_limit": stopped_rate_limit}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM-обогащение постов (entities + tags + insight + photo)"
    )
    parser.add_argument("--limit", type=int, default=0, help="Обработать только N записей (0 = все)")
    parser.add_argument("--force", action="store_true", help="Обогатить все, включая уже обработанные")
    parser.add_argument("--db", type=Path, default=HERE / "data" / "messages.db", help="Путь к БД")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=80,
        help="Размер батча для текстовых постов (vision всегда 20)",
    )
    args = parser.parse_args()

    result = run_analyze(
        db_path=args.db,
        batch_size=args.batch_size,
        limit=args.limit,
        force=args.force,
    )
    if result["stopped_rate_limit"]:
        print("Завершено досрочно: rate limit.")


if __name__ == "__main__":
    main()
