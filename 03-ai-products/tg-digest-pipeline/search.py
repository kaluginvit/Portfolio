"""
search.py — семантический, ключевой и гибридный поиск по архиву канала.

Использование:
    python search.py "запрос" [--mode semantic|keyword|hybrid] [--top 20]
                              [--db data/messages.db]
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import warnings
from pathlib import Path
from typing import Optional

import numpy as np

from db import connect_readonly

HERE = Path(__file__).parent

DEFAULT_DB    = HERE / "data" / "messages.db"
DEFAULT_INDEX = HERE / "vectors" / "text.index"
DEFAULT_META  = HERE / "vectors" / "text_meta.pkl"

PINECONE_INDEX_NAME = "infopovod"
MODEL_NAME = "deepvk/USER-bge-m3"

# ---------------------------------------------------------------------------
# Singleton для модели — загружается один раз при первом обращении
# ---------------------------------------------------------------------------

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _row_to_dict(
    msg: dict,
    enr: Optional[dict],
    score: Optional[float] = None,
) -> dict:
    """Собирает единый dict из строк messages + enrichments."""
    result = {
        "message_id":    msg.get("message_id"),
        "date":          msg.get("date"),
        "text":          msg.get("text"),
        "forwarded_from": msg.get("forwarded_from"),
        "entities":      enr.get("entities") if enr else None,
        "tags":          enr.get("tags")     if enr else None,
        "insight":       enr.get("insight")  if enr else None,
        "score":         score,
    }
    return result


def _fetch_by_ids(
    con,
    message_ids: list[int],
    scores: dict[int, float],
) -> list[dict]:
    """Достаёт messages + enrichments для списка id, сохраняет порядок scores."""
    if not message_ids:
        return []

    placeholders = ",".join("?" * len(message_ids))

    msgs = {
        r["message_id"]: dict(r)
        for r in con.execute(
            f"SELECT * FROM messages WHERE message_id IN ({placeholders})",
            message_ids,
        ).fetchall()
    }

    enrs = {
        r["message_id"]: dict(r)
        for r in con.execute(
            f"SELECT * FROM enrichments WHERE message_id IN ({placeholders})",
            message_ids,
        ).fetchall()
    }

    results = []
    for mid in message_ids:
        if mid not in msgs:
            continue
        results.append(_row_to_dict(msgs[mid], enrs.get(mid), scores.get(mid)))
    return results


# ---------------------------------------------------------------------------
# semantic_search
# ---------------------------------------------------------------------------

def _pinecone_search(q_vec: np.ndarray, top_k: int) -> tuple[list[int], dict[int, float]]:
    """Поиск через Pinecone. Возвращает (ids, scores)."""
    from dotenv import load_dotenv
    load_dotenv(HERE / ".env")
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(PINECONE_INDEX_NAME)
    resp = index.query(vector=q_vec[0].tolist(), top_k=top_k, include_metadata=False)
    hits_ids = [int(m["id"]) for m in resp.matches]
    scores = {int(m["id"]): float(m["score"]) for m in resp.matches}
    return hits_ids, scores


def _faiss_search(q_vec: np.ndarray, top_k: int,
                  index_path: Path, meta_path: Path) -> tuple[list[int], dict[int, float]]:
    """Поиск через локальный FAISS. Возвращает (ids, scores)."""
    import faiss
    with open(index_path, "rb") as f:
        idx = faiss.deserialize_index(np.frombuffer(f.read(), dtype="uint8"))
    with open(meta_path, "rb") as f:
        meta: list[int] = pickle.load(f)
    k = min(top_k, idx.ntotal)
    distances, indices = idx.search(q_vec, k)
    hits_ids, scores = [], {}
    for dist, i in zip(distances[0], indices[0]):
        if i < 0 or i >= len(meta):
            continue
        mid = meta[i]
        hits_ids.append(mid)
        scores[mid] = float(dist)
    return hits_ids, scores


def semantic_search(
    query: str,
    top_k: int = 20,
    db_path: Path = DEFAULT_DB,
    index_path: Path = DEFAULT_INDEX,
    meta_path: Path = DEFAULT_META,
) -> list[dict]:
    """
    Векторный поиск: Pinecone (primary) → FAISS (fallback).

    Возвращает list[dict]:
        {message_id, date, text, forwarded_from, entities, tags, insight, score}
    """
    model = _get_model()
    q_vec = model.encode([query], normalize_embeddings=True).astype("float32")

    try:
        hits_ids, scores = _pinecone_search(q_vec, top_k)
    except Exception as e:
        warnings.warn(f"Pinecone недоступен ({e}), переключаюсь на FAISS.", stacklevel=2)
        if not index_path.exists() or not meta_path.exists():
            warnings.warn("FAISS-индекс не найден. Запустите `python pipeline.py --embed`.", stacklevel=2)
            return []
        hits_ids, scores = _faiss_search(q_vec, top_k, index_path, meta_path)

    con = connect_readonly(db_path)
    results = _fetch_by_ids(con, hits_ids, scores)
    con.close()
    return results


# ---------------------------------------------------------------------------
# keyword_search
# ---------------------------------------------------------------------------

def keyword_search(
    query: str,
    top_k: int = 20,
    db_path: Path = DEFAULT_DB,
    **_kwargs,
) -> list[dict]:
    """
    Полнотекстовый поиск через FTS5.
    Ищет в enrichments_fts (insight, tags, entities) и messages_fts (text).
    Объединяет результаты: enrichments_fts имеет приоритет.
    """
    con = connect_readonly(db_path)

    # Запрос к enrichments_fts
    try:
        enr_rows = con.execute(
            """
            SELECT ef.message_id,
                   bm25(enrichments_fts) AS score
              FROM enrichments_fts ef
             WHERE enrichments_fts MATCH ?
             ORDER BY score
             LIMIT ?
            """,
            (query, top_k),
        ).fetchall()
    except Exception:
        enr_rows = []

    # Запрос к messages_fts
    try:
        msg_rows = con.execute(
            """
            SELECT mf.message_id,
                   bm25(messages_fts) AS score
              FROM messages_fts mf
             WHERE messages_fts MATCH ?
             ORDER BY score
             LIMIT ?
            """,
            (query, top_k),
        ).fetchall()
    except Exception:
        msg_rows = []

    # Объединяем: enrichments_fts приоритетнее, дедупликация
    seen: dict[int, float] = {}
    ordered_ids: list[int] = []

    for r in enr_rows:
        mid, sc = r[0], r[1]
        if mid not in seen:
            seen[mid] = float(sc)
            ordered_ids.append(mid)

    for r in msg_rows:
        mid, sc = r[0], r[1]
        if mid not in seen:
            seen[mid] = float(sc)
            ordered_ids.append(mid)

    # Обрезаем до top_k
    ordered_ids = ordered_ids[:top_k]
    scores = {mid: seen[mid] for mid in ordered_ids}

    results = _fetch_by_ids(con, ordered_ids, scores)
    con.close()
    return results


# ---------------------------------------------------------------------------
# hybrid_search
# ---------------------------------------------------------------------------

def hybrid_search(
    query: str,
    top_k: int = 20,
    db_path: Path = DEFAULT_DB,
    index_path: Path = DEFAULT_INDEX,
    meta_path: Path = DEFAULT_META,
) -> list[dict]:
    """
    Объединяет результаты semantic_search и keyword_search.
    Дедупликация по message_id.
    Семантические результаты имеют приоритет (идут первыми).
    """
    sem_results = semantic_search(query, top_k=top_k, db_path=db_path,
                                  index_path=index_path, meta_path=meta_path)
    kw_results  = keyword_search(query,  top_k=top_k, db_path=db_path)

    seen: set[int] = set()
    merged: list[dict] = []

    for item in sem_results:
        mid = item["message_id"]
        if mid not in seen:
            seen.add(mid)
            merged.append(item)

    for item in kw_results:
        mid = item["message_id"]
        if mid not in seen:
            seen.add(mid)
            # score от keyword — отрицательный bm25, переводим в None чтобы
            # не путать с cosine similarity
            item = {**item, "score": item.get("score")}
            merged.append(item)

    return merged[:top_k]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_results(results: list[dict]) -> None:
    if not results:
        print("Результатов не найдено.")
        return
    for i, r in enumerate(results, 1):
        score_str = f"{r['score']:.4f}" if r.get("score") is not None else "—"
        date  = (r.get("date") or "")[:10]
        fwd   = f"  fwd: {r['forwarded_from']}" if r.get("forwarded_from") else ""
        text  = (r.get("text") or "")[:120].replace("\n", " ")
        insight = (r.get("insight") or "")[:100]
        print(f"[{i:2}] id={r['message_id']} score={score_str} {date}{fwd}")
        print(f"      {text}")
        if insight:
            print(f"      insight: {insight}")
        print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Поиск по архиву канала")
    parser.add_argument("query",               help="Текст запроса")
    parser.add_argument("--mode",   default="hybrid",
                        choices=["semantic", "keyword", "hybrid"],
                        help="Режим поиска (default: hybrid)")
    parser.add_argument("--top",    type=int, default=20,  help="Количество результатов")
    parser.add_argument("--db",     type=Path, default=DEFAULT_DB)
    parser.add_argument("--index",  type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--meta",   type=Path, default=DEFAULT_META)
    args = parser.parse_args()

    if args.mode == "semantic":
        results = semantic_search(args.query, top_k=args.top,
                                  db_path=args.db,
                                  index_path=args.index,
                                  meta_path=args.meta)
    elif args.mode == "keyword":
        results = keyword_search(args.query, top_k=args.top, db_path=args.db)
    else:
        results = hybrid_search(args.query, top_k=args.top,
                                db_path=args.db,
                                index_path=args.index,
                                meta_path=args.meta)

    print(f"Режим: {args.mode} | Запрос: «{args.query}» | Найдено: {len(results)}\n")
    _print_results(results)
