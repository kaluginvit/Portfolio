"""
cluster_queue.py — кластеризация collector_queue для детекции трендов.

Эмбеддинги сохраняются в collector_queue.embedding (BLOB).
Повторный запуск пересчитывает только новые посты.

Использование:
    python cluster_queue.py              # только pending
    python cluster_queue.py --all        # все статусы
    python cluster_queue.py --eps 0.35   # настроить порог
    python cluster_queue.py --embed-only # только посчитать эмбеддинги, без кластеризации
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE    = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"

MODEL_NAME  = "deepvk/USER-bge-m3"
DEFAULT_EPS = 0.28
MIN_SAMPLES = 2
NOISE_ABSORB_THRESHOLD = 0.45  # cosine similarity для поглощения шума в ближайший кластер

STORY_CLUSTERS_DDL = """
CREATE TABLE IF NOT EXISTS story_clusters (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    label         TEXT,
    niche         TEXT,
    post_count    INTEGER DEFAULT 0,
    channel_count INTEGER DEFAULT 0,
    total_views   INTEGER DEFAULT 0,
    max_views     INTEGER DEFAULT 0,
    score         REAL DEFAULT 0,
    clustered_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);
"""


def _migrate(con: sqlite3.Connection) -> None:
    con.executescript(STORY_CLUSTERS_DDL)
    for col_sql in [
        "ALTER TABLE collector_queue ADD COLUMN cluster_id INTEGER DEFAULT -1",
        "ALTER TABLE collector_queue ADD COLUMN embedding BLOB",
    ]:
        try:
            con.execute(col_sql)
            con.commit()
        except sqlite3.OperationalError:
            pass



def _embed_new(con: sqlite3.Connection, all_statuses: bool) -> int:
    """Считает эмбеддинги только для постов без embedding. Возвращает кол-во новых."""
    where = "WHERE embedding IS NULL" if all_statuses else "WHERE embedding IS NULL AND status='pending'"
    rows = con.execute(
        f"SELECT id, text FROM collector_queue {where} ORDER BY id"
    ).fetchall()

    if not rows:
        print("Все эмбеддинги уже посчитаны.", flush=True)
        return 0

    print(f"Новых постов без эмбеддинга: {len(rows)}", flush=True)
    from embed_client import encode

    texts = [r[1] or "" for r in rows]
    ids   = [r[0] for r in rows]

    batch_size = 32
    total = len(texts)
    for i in range(0, total, batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_ids   = ids[i:i+batch_size]
        vecs = encode(batch_texts)
        for row_id, vec in zip(batch_ids, vecs):
            con.execute(
                "UPDATE collector_queue SET embedding=? WHERE id=?",
                (vec.tobytes(), row_id)
            )
        con.commit()
        done = min(i + batch_size, total)
        print(f"  {done}/{total}", flush=True)

    return len(rows)


def _load_vecs(con: sqlite3.Connection, all_statuses: bool) -> tuple[list[dict], np.ndarray]:
    status_filter = "" if all_statuses else "AND status='pending'"
    rows = con.execute(
        f"SELECT id, views, forwards, centroid_label, channel_id, channel_title, text, embedding "
        f"FROM collector_queue WHERE embedding IS NOT NULL {status_filter} ORDER BY id"
    ).fetchall()

    posts, vecs = [], []
    for r in rows:
        if not r[7]:
            continue
        vec = np.frombuffer(r[7], dtype="float32")
        posts.append({
            "id": r[0], "views": r[1] or 0, "forwards": r[2] or 0,
            "centroid_label": r[3] or "", "channel_id": r[4],
            "channel_title": r[5] or "?", "text": r[6] or "",
        })
        vecs.append(vec)

    return posts, np.vstack(vecs) if vecs else np.empty((0, 1024), dtype="float32")


def _absorb_noise(vecs: np.ndarray, labels: np.ndarray, threshold: float) -> np.ndarray:
    """Назначает шумовые посты (label=-1) в ближайший кластер если similarity > threshold."""
    labels = labels.copy()
    cluster_ids = [c for c in set(labels) if c != -1]
    if not cluster_ids:
        return labels

    centroids = np.array([
        vecs[labels == cid].mean(axis=0) for cid in cluster_ids
    ], dtype="float32")
    centroids /= np.linalg.norm(centroids, axis=1, keepdims=True).clip(1e-9)

    noise_mask = labels == -1
    if not noise_mask.any():
        return labels

    noise_vecs = vecs[noise_mask].copy()
    noise_vecs /= np.linalg.norm(noise_vecs, axis=1, keepdims=True).clip(1e-9)

    sims = noise_vecs @ centroids.T
    best_sim = sims.max(axis=1)
    best_idx = sims.argmax(axis=1)

    absorbed = 0
    for idx, sim, cidx in zip(np.where(noise_mask)[0], best_sim, best_idx):
        if sim >= threshold:
            labels[idx] = cluster_ids[cidx]
            absorbed += 1

    print(f"Поглощено шумовых постов: {absorbed}/{noise_mask.sum()} (threshold={threshold})", flush=True)
    return labels


def _cluster(vecs: np.ndarray, eps: float) -> np.ndarray:
    from sklearn.cluster import DBSCAN
    dist = (1.0 - (vecs @ vecs.T)).clip(0, 2).astype("float64")
    return DBSCAN(eps=eps, min_samples=MIN_SAMPLES, metric="precomputed", n_jobs=1).fit_predict(dist)


def _build_clusters(posts: list[dict], labels: np.ndarray) -> list[dict]:
    from collections import defaultdict
    import math
    groups: dict[int, list] = defaultdict(list)
    for post, label in zip(posts, labels):
        groups[int(label)].append(post)

    clusters = []
    for cid, group in groups.items():
        if cid == -1:
            continue
        total_views   = sum(p["views"] for p in group)
        max_views     = max(p["views"] for p in group)
        channel_count = len({p["channel_id"] for p in group})
        niche = Counter(p["centroid_label"] for p in group).most_common(1)[0][0]
        top_post = max(group, key=lambda p: p["views"])
        label_text = top_post["text"].replace("\n", " ")[:120].strip()
        score = channel_count * math.log(total_views + 1)
        clusters.append({
            "cluster_id": cid, "label": label_text, "niche": niche,
            "post_count": len(group), "channel_count": channel_count,
            "total_views": total_views, "max_views": max_views,
            "score": round(score, 2),
        })

    clusters.sort(key=lambda c: c["score"], reverse=True)
    return clusters


def run(db_path: Path = DB_PATH, all_statuses: bool = False,
        eps: float = DEFAULT_EPS, embed_only: bool = False) -> None:
    con = sqlite3.connect(db_path)
    _migrate(con)

    new_count = _embed_new(con, all_statuses)

    if embed_only:
        print(f"Готово. Новых эмбеддингов: {new_count}")
        con.close()
        return

    posts, vecs = _load_vecs(con, all_statuses)
    if len(posts) == 0:
        print("Нет постов с эмбеддингами для кластеризации.")
        con.close()
        return

    print(f"Кластеризуем {len(posts)} постов (eps={eps}) …", flush=True)
    labels = _cluster(vecs, eps)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = int((labels == -1).sum())
    print(f"Кластеров: {n_clusters}, шум до поглощения: {n_noise}", flush=True)

    labels = _absorb_noise(vecs, labels, NOISE_ABSORB_THRESHOLD)
    n_noise_after = int((labels == -1).sum())
    print(f"Шум после поглощения: {n_noise_after}", flush=True)

    # Сбрасываем старые cluster_id
    con.executemany("UPDATE collector_queue SET cluster_id=-1 WHERE id=?",
                    [(p["id"],) for p in posts])
    # Пишем новые
    for post, label in zip(posts, labels):
        con.execute("UPDATE collector_queue SET cluster_id=? WHERE id=?",
                    (int(label), post["id"]))
    con.commit()

    # Пересобираем story_clusters
    con.execute("DELETE FROM story_clusters")
    clusters = _build_clusters(posts, labels)
    for c in clusters:
        con.execute(
            "INSERT INTO story_clusters (id, label, niche, post_count, channel_count, total_views, max_views, score) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (c["cluster_id"], c["label"], c["niche"], c["post_count"],
             c["channel_count"], c["total_views"], c["max_views"], c["score"])
        )
    con.commit()
    con.close()

    print(f"\nТоп-10 историй:")
    for c in clusters[:10]:
        print(f"  [{c['cluster_id']:3}] {c['niche']:<25} {c['channel_count']}ч  "
              f"{c['total_views']:>8} views  score={c['score']:.1f}")
        print(f"        {c['label'][:80]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all",        action="store_true")
    parser.add_argument("--eps",        type=float, default=DEFAULT_EPS)
    parser.add_argument("--db",         type=Path,  default=DB_PATH)
    parser.add_argument("--embed-only", action="store_true")
    args = parser.parse_args()
    run(db_path=args.db, all_statuses=args.all, eps=args.eps, embed_only=args.embed_only)
