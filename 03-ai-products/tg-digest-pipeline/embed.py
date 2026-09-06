"""
embed.py — генерация эмбеддингов и загрузка в Pinecone + локальный FAISS-кэш.

Модели:
  Текст:   deepvk/USER-bge-m3 (локально, 1024 dims)
  Vision:  nvidia/llama-nemotron-embed-vl-1b-v2 (OpenRouter, отложено)

Индексы:
  Pinecone: "infopovod" (cosine, 1024 dims, serverless)
  FAISS:    vectors/text.index + vectors/text_meta.pkl (локальный кэш для search.py)

Использование:
    python embed.py [--rebuild] [--only text|vision] [--no-pinecone] [--no-faiss]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm

from db import connect_readonly

load_dotenv()

HERE = Path(__file__).parent
DEFAULT_DB  = HERE / "data" / "messages.db"
VECTORS_DIR = HERE / "vectors"

TEXT_INDEX_PATH = VECTORS_DIR / "text.index"
TEXT_META_PATH  = VECTORS_DIR / "text_meta.pkl"
PINECONE_IDS_PATH = VECTORS_DIR / "pinecone_ids.pkl"

VISION_INDEX_PATH = VECTORS_DIR / "vision.index"
VISION_META_PATH  = VECTORS_DIR / "vision_meta.pkl"

TEXT_DIM    = 1024
TEXT_BATCH  = 64
PINE_BATCH  = 100   # рекомендуемый batch для Pinecone upsert
VISION_BATCH = 32

PINECONE_INDEX_NAME = "infopovod"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# утилиты
# ---------------------------------------------------------------------------

def _parse_json_field(val) -> list[str]:
    if not val:
        return []
    if isinstance(val, list):
        items = val
    else:
        try:
            items = json.loads(val)
        except Exception:
            return []
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(str(i) for i in item if i)
        elif item:
            result.append(str(item))
    return result


def _load_pinecone_ids() -> set[int]:
    if PINECONE_IDS_PATH.exists():
        with open(PINECONE_IDS_PATH, "rb") as f:
            return pickle.load(f)
    return set()


def _save_pinecone_ids(ids: set[int]) -> None:
    VECTORS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PINECONE_IDS_PATH, "wb") as f:
        pickle.dump(ids, f)


def _load_faiss(index_path: Path, meta_path: Path):
    if index_path.exists() and meta_path.exists():
        with open(index_path, "rb") as f:
            idx = faiss.deserialize_index(np.frombuffer(f.read(), dtype="uint8"))
        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
        log.info("FAISS загружен: %d векторов", idx.ntotal)
        return idx, set(meta), meta
    return None, set(), []


def _save_faiss(index, meta: list, index_path: Path, meta_path: Path) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "wb") as f:
        f.write(faiss.serialize_index(index).tobytes())
    with open(meta_path, "wb") as f:
        pickle.dump(meta, f)
    log.info("FAISS сохранён: %s (%d векторов)", index_path.name, index.ntotal)


def _build_metadata(row: dict, msg: dict) -> dict:
    """Формирует метаданные для Pinecone-вектора."""
    tags     = _parse_json_field(row.get("tags"))
    entities = _parse_json_field(row.get("entities"))
    insight  = (row.get("insight") or "")[:400]
    date_str = (msg.get("date") or "")[:10]

    try:
        dt = datetime.fromisoformat(date_str)
        year, month, quarter, dow = dt.year, dt.month, (dt.month - 1) // 3 + 1, dt.weekday()
    except Exception:
        year, month, quarter, dow = 0, 0, 0, 0

    text = msg.get("text") or ""
    text_len = len(text) if isinstance(text, str) else 0

    return {
        # идентификация
        "message_id":           row["message_id"],
        "date":                 date_str,
        "year":                 year,
        "month":                month,
        "quarter":              quarter,
        "day_of_week":          dow,
        # источник
        "forwarded_from":       msg.get("forwarded_from") or "",
        "has_photo":            bool(msg.get("has_photo")),
        # ОСИНТ: оригинал
        "original_message_id":  msg.get("original_message_id") or 0,
        "original_date":        (msg.get("original_date") or "")[:10],
        "post_author":          msg.get("post_author") or "",
        # ОСИНТ: метрики
        "views":                msg.get("views") or 0,
        "forwards":             msg.get("forwards") or 0,
        # обогащение
        "tags":                 tags,
        "entities":             entities,
        "insight":              insight,
        "tags_count":           len(tags),
        "entities_count":       len(entities),
        "llm_model":            row.get("llm_model") or "",
        # текстовые сигналы
        "text_len":             text_len,
        "has_links":            bool(msg.get("links")),
        # источник записи
        "source":               msg.get("source") or "channel",
        # кластеризация (заполним позже)
        "cluster_id":           -1,
        "cluster_label":        "",
    }


# ---------------------------------------------------------------------------
# text index
# ---------------------------------------------------------------------------

def _build_text_index(
    db_path: Path,
    model_name: str,
    rebuild: bool,
    use_pinecone: bool,
    use_faiss: bool,
) -> None:
    log.info("=== TEXT INDEX ===")

    # --- загружаем уже проиндексированные ID ---
    pine_ids  = set() if rebuild else _load_pinecone_ids()
    faiss_idx, faiss_known, faiss_meta = (None, set(), []) if rebuild else _load_faiss(TEXT_INDEX_PATH, TEXT_META_PATH)

    already_done = pine_ids if use_pinecone else faiss_known

    # --- читаем из БД ---
    con = connect_readonly(db_path)
    rows = con.execute("""
        SELECT e.message_id, e.insight, e.tags, e.entities, e.llm_model,
               m.date, m.text, m.forwarded_from, m.has_photo, m.links,
               m.original_message_id, m.original_date, m.post_author,
               m.views, m.forwards,
               COALESCE(m.source, 'channel') AS source
          FROM enrichments e
          JOIN messages m ON m.message_id = e.message_id
         ORDER BY e.message_id
    """).fetchall()
    con.close()

    new_rows = [r for r in rows if r["message_id"] not in already_done]
    log.info("В enrichments: %d, новых: %d", len(rows), len(new_rows))

    if not new_rows:
        log.info("Нет новых записей.")
        return

    # --- загружаем модель ---
    log.info("Загрузка модели %s …", model_name)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    log.info("Модель загружена.")

    dim = model.get_sentence_embedding_dimension() or TEXT_DIM

    if use_faiss and faiss_idx is None:
        faiss_idx = faiss.IndexFlatIP(dim)

    # --- инициализируем Pinecone ---
    pine_index = None
    if use_pinecone:
        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        existing = [idx.name for idx in pc.list_indexes()]
        if PINECONE_INDEX_NAME not in existing:
            log.info("Создаю Pinecone-индекс '%s' …", PINECONE_INDEX_NAME)
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=dim,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        pine_index = pc.Index(PINECONE_INDEX_NAME)
        log.info("Pinecone-индекс '%s' готов.", PINECONE_INDEX_NAME)

    # --- генерируем эмбеддинги и уплоадим ---
    texts = [
        (f"{r['insight'] or ''} {' '.join(_parse_json_field(r['tags']))}").strip()
        for r in new_rows
    ]

    pine_buffer: list[dict]  = []
    faiss_vecs:  list        = []
    faiss_ids:   list[int]   = []
    new_pine_ids: set[int]   = set()

    batches = [
        (texts[i:i+TEXT_BATCH], new_rows[i:i+TEXT_BATCH])
        for i in range(0, len(texts), TEXT_BATCH)
    ]

    for batch_texts, batch_rows in tqdm(batches, desc="embed", unit="batch"):
        vecs = model.encode(
            batch_texts,
            batch_size=TEXT_BATCH,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).astype("float32")

        for vec, row in zip(vecs, batch_rows):
            mid = row["message_id"]
            meta = _build_metadata(dict(row), dict(row))

            if use_pinecone:
                pine_buffer.append({
                    "id":       str(mid),
                    "values":   vec.tolist(),
                    "metadata": meta,
                })
                new_pine_ids.add(mid)

                if len(pine_buffer) >= PINE_BATCH:
                    pine_index.upsert(vectors=pine_buffer)
                    pine_buffer.clear()

            if use_faiss:
                faiss_vecs.append(vec)
                faiss_ids.append(mid)

    # остаток Pinecone
    if use_pinecone and pine_buffer:
        pine_index.upsert(vectors=pine_buffer)

    # сохраняем Pinecone ID-сет
    if use_pinecone:
        pine_ids |= new_pine_ids
        _save_pinecone_ids(pine_ids)
        log.info("Pinecone: загружено %d новых, итого %d", len(new_pine_ids), len(pine_ids))

    # сохраняем FAISS
    if use_faiss and faiss_vecs:
        faiss_idx.add(np.vstack(faiss_vecs))
        faiss_meta.extend(faiss_ids)
        _save_faiss(faiss_idx, faiss_meta, TEXT_INDEX_PATH, TEXT_META_PATH)


# ---------------------------------------------------------------------------
# vision index (без изменений — FAISS, OpenRouter)
# ---------------------------------------------------------------------------

def _build_vision_index(db_path: Path, api_key: str, model_name: str, rebuild: bool) -> None:
    log.info("=== VISION INDEX ===")

    existing, known_ids, meta = (None, set(), []) if rebuild else _load_faiss(VISION_INDEX_PATH, VISION_META_PATH)

    con = connect_readonly(db_path)
    rows = con.execute("""
        SELECT e.message_id, e.insight, e.tags, pe.description
          FROM enrichments e
          JOIN photo_enrichments pe ON pe.message_id = e.message_id
         ORDER BY e.message_id
    """).fetchall()
    con.close()

    new_rows = [r for r in rows if r["message_id"] not in known_ids]
    log.info("Визуальных: %d, новых: %d", len(rows), len(new_rows))

    if not new_rows:
        log.info("Нет новых записей.")
        return

    import openai
    client = openai.OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    texts = [
        (f"{r['insight'] or ''} {' '.join(_parse_json_field(r['tags']))} {r['description'] or ''}").strip()
        for r in new_rows
    ]
    ids = [r["message_id"] for r in new_rows]

    dim: Optional[int] = None
    index = existing
    all_vecs, valid_ids = [], []

    for i in tqdm(range(0, len(texts), VISION_BATCH), desc="vision embed", unit="batch"):
        batch_texts = texts[i:i+VISION_BATCH]
        batch_ids   = ids[i:i+VISION_BATCH]
        try:
            resp = client.embeddings.create(model=model_name, input=batch_texts)
            vecs = np.array([item.embedding for item in resp.data], dtype="float32")
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs /= np.where(norms == 0, 1.0, norms)
            if dim is None:
                dim = vecs.shape[1]
                if index is None:
                    index = faiss.IndexFlatIP(dim)
            all_vecs.append(vecs)
            valid_ids.extend(batch_ids)
        except Exception as exc:
            log.error("Ошибка батча vision (ids=%s): %s", batch_ids, exc)

    if all_vecs and index is not None:
        index.add(np.vstack(all_vecs))
        meta.extend(valid_ids)
        _save_faiss(index, meta, VISION_INDEX_PATH, VISION_META_PATH)
        log.info("VISION: %d новых, итого %d", len(valid_ids), index.ntotal)


# ---------------------------------------------------------------------------
# публичный API
# ---------------------------------------------------------------------------

def build_index(
    db_path: Path = DEFAULT_DB,
    rebuild: bool = False,
    only: str | None = None,
    use_pinecone: bool = True,
    use_faiss: bool = True,
) -> None:
    cfg_path = HERE / "config.json"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    text_model   = cfg.get("embed_model_text",   "deepvk/USER-bge-m3")
    vision_model = cfg.get("embed_model_vision",  "nvidia/llama-nemotron-embed-vl-1b-v2:free")
    api_key      = (os.environ.get("OPENROUTER_API_KEYS", "").split(",")[0]).strip()

    VECTORS_DIR.mkdir(parents=True, exist_ok=True)

    if only in (None, "text"):
        _build_text_index(db_path, text_model, rebuild, use_pinecone, use_faiss)

    if only in (None, "vision"):
        if not api_key:
            log.error("OPENROUTER_API_KEYS не задан — vision index пропущен")
        else:
            _build_vision_index(db_path, api_key, vision_model, rebuild)


# кэш для search.py
_indexes_cache: dict = {}


def get_all_indexes() -> dict:
    global _indexes_cache
    if "text" not in _indexes_cache:
        if TEXT_INDEX_PATH.exists() and TEXT_META_PATH.exists():
            idx = faiss.read_index(str(TEXT_INDEX_PATH))
            with open(TEXT_META_PATH, "rb") as f:
                meta = pickle.load(f)
            _indexes_cache["text"] = {"index": idx, "meta": meta}
        else:
            _indexes_cache["text"] = None
    if "vision" not in _indexes_cache:
        if VISION_INDEX_PATH.exists() and VISION_META_PATH.exists():
            idx = faiss.read_index(str(VISION_INDEX_PATH))
            with open(VISION_META_PATH, "rb") as f:
                meta = pickle.load(f)
            _indexes_cache["vision"] = {"index": idx, "meta": meta}
        else:
            _indexes_cache["vision"] = None
    return _indexes_cache


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генерация эмбеддингов → Pinecone + FAISS")
    parser.add_argument("--db",          type=Path, default=DEFAULT_DB)
    parser.add_argument("--rebuild",     action="store_true", help="Перестроить с нуля")
    parser.add_argument("--only",        choices=["text", "vision"], default=None)
    parser.add_argument("--no-pinecone", action="store_true", help="Не писать в Pinecone")
    parser.add_argument("--no-faiss",    action="store_true", help="Не писать в FAISS")
    args = parser.parse_args()

    build_index(
        db_path=args.db,
        rebuild=args.rebuild,
        only=args.only,
        use_pinecone=not args.no_pinecone,
        use_faiss=not args.no_faiss,
    )
