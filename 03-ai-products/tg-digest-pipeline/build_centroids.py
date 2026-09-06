"""
build_centroids.py — построение центроидов смысловых ниш.

Для каждой ниши: берёт посты по тегам → эмбеддирует insight+tags →
усредняет векторы → нормализует → сохра��яет в vectors/centroids.pkl.

Использование:
    python build_centroids.py [--sample 500]
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"
OUT_PATH = HERE / "vectors" / "centroids.pkl"

NICHES: list[dict] = [
    {"label": "Геополитика/Война",    "tags": ["геополитика", "санкции", "сша"]},
    {"label": "Экономика РФ",         "tags": ["экономика", "инфляция", "бюджет", "рубль"]},
    {"label": "Энергетика/Сырьё",     "tags": ["нефть", "энергетика", "экспорт"]},
    {"label": "Финансы/Рынки",        "tags": ["инвестиции", "фондовый рынок", "банки"]},
    {"label": "Промышленность",       "tags": ["промышленность", "импортозамещение"]},
    {"label": "Технологии/AI",        "tags": ["технологии"]},
    {"label": "Китай/Азия",           "tags": ["китай"]},
    {"label": "Макро/Статистика",     "tags": ["макроэкономика", "статистика", "демография"]},
    {"label": "Познавательное",       "tags": ["история", "наука", "образование", "социология"]},
    {"label": "Юмор/Ирония",          "tags": ["юмор", "ирония"]},
]

MODEL_NAME = "deepvk/USER-bge-m3"
BATCH_SIZE = 64


def _parse_tags(val) -> list[str]:
    if not val:
        return []
    try:
        items = json.loads(val) if isinstance(val, str) else val
        return [str(t).lower().strip() for t in items if t]
    except Exception:
        return []


def _load_posts_for_niche(niche_tags: list[str], sample: int) -> list[str]:
    """Загружает insight+tags текст для постов с тегами ниши."""
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT insight, tags FROM enrichments WHERE insight IS NOT NULL"
    ).fetchall()
    con.close()

    niche_set = set(niche_tags)
    texts = []
    for insight, tags_raw in rows:
        post_tags = _parse_tags(tags_raw)
        if niche_set & set(post_tags):
            text = f"{insight or ''} {' '.join(post_tags)}".strip()
            if text:
                texts.append(text)

    if sample > 0 and len(texts) > sample:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(texts), size=sample, replace=False)
        texts = [texts[i] for i in idx]

    return texts


def build_centroids(sample: int = 500) -> None:
    from embed_client import encode, is_server_up
    if is_server_up():
        print("embed_server доступен.")
    else:
        print("embed_server недоступен — модель будет загружена локально.")

    centroids: list[dict] = []

    for niche in NICHES:
        label = niche["label"]
        tags  = niche["tags"]
        print(f"[{label}] теги: {tags}")

        texts = _load_posts_for_niche(tags, sample)
        print(f"  Постов: {len(texts)}", end=" ", flush=True)

        if not texts:
            print("→ пропуск (нет данных)")
            continue

        vecs = encode(texts)

        centroid = vecs.mean(axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid /= norm

        centroids.append({"label": label, "tags": tags, "centroid": centroid})
        print(f"→ центроид {centroid.shape}, norm={np.linalg.norm(centroid):.4f}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        pickle.dump(centroids, f)

    print(f"\nСохранено {len(centroids)} центроидов → {OUT_PATH}")

    # Быстрая проверка: cosine similarity между нишами
    print("\n--- Матрица схожести ниш ---")
    labels = [c["label"] for c in centroids]
    vecs   = np.stack([c["centroid"] for c in centroids])
    sim    = vecs @ vecs.T
    col_w  = max(len(l) for l in labels) + 2
    header = " " * col_w + "  ".join(f"{l[:8]:>8}" for l in labels)
    print(header)
    for i, row_label in enumerate(labels):
        row = f"{row_label:<{col_w}}" + "  ".join(f"{sim[i,j]:8.3f}" for j in range(len(labels)))
        print(row)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=0, help="Макс. постов на нишу (0=все)")
    args = parser.parse_args()
    build_centroids(sample=args.sample)
