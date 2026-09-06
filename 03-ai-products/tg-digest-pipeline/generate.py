"""
generate.py — генерация поста в авторском стиле через RAG + few-shot.

Алгоритм:
1. Ищет top_k авторских постов (#имеюссообщить) похожих на тему
2. Собирает контекст из кластера (топ-3 поста по views)
3. Строит промпт system + few-shot + context + задание
4. Вызывает LLM через OpenRouter
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"
INDEX_PATH = HERE / "vectors" / "text.index"
META_PATH  = HERE / "vectors" / "text_meta.pkl"

SYSTEM_PROMPT = """Ты — Виталий Калугин, финансовый аналитик и автор Telegram-канала @kaluginprofit.
Пиши от первого лица, как будто это твой личный пост.

СТИЛЬ:
- Провокационность и прямота: называй вещи своими именами, не стесняйся резких оценок
- Агрессия к официальным нарративам: сомневайся, критикуй, указывай на противоречия
- Личная позиция: "я считаю", "по-моему", "очевидно для всех кроме ЦБ" — без нейтральности
- Конкретные цифры и факты — твоё оружие против демагогии
- Короткие абзацы, резкие переходы, иногда риторические вопросы
- Разговорный тон: можно с иронией, сарказмом, даже грубовато
- Длина: 150-400 слов

ЗАПРЕЩЕНО (ИИ-маркеры, которые выдают не-человека):
- "Следует отметить", "Важно подчеркнуть", "Стоит отметить"
- "Таким образом", "В заключение", "Подводя итог"
- "Несомненно", "Безусловно", "Очевидно"
- "С одной стороны... с другой стороны" — это трусливая балансировка
- "Эксперты отмечают", "Аналитики считают" — говори сам
- Заголовки и маркированные списки внутри поста
- Начинать с названия темы или с имени существительного без зачина
- Слащавые выводы в конце ("остаётся только надеяться...")

Пиши ТОЛЬКО текст поста. Никаких вводных фраз типа "Вот пост:" или "Конечно!"."""

USER_TEMPLATE = """ПРИМЕРЫ МОИХ ПОСТОВ (стиль, тон, подача — ориентируйся на них):

{examples}

---

КОНТЕКСТ СОБЫТИЯ (факты из источников — используй их, но подай по-своему):

{context}

---

Напиши пост об этом событии. Возьми провокационный угол, не нейтральный. Опирайся на цифры из контекста."""


def _get_author_ids(db_path: Path) -> set[int]:
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT message_id FROM user_tags WHERE tag='#имеюссообщить'"
    ).fetchall()
    con.close()
    return {r[0] for r in rows}


def find_similar_author_posts(topic: str, db_path: Path = DB_PATH, top_k: int = 7) -> list[dict]:
    """Ищет авторские посты похожие на тему через гибридный поиск."""
    from search import hybrid_search
    author_ids = _get_author_ids(db_path)
    if not author_ids:
        return []

    # Берём больше результатов для фильтрации
    results = hybrid_search(
        topic, top_k=80,
        db_path=db_path,
        index_path=INDEX_PATH,
        meta_path=META_PATH,
    )
    author_results = [r for r in results if r.get("message_id") in author_ids]
    return author_results[:top_k]


def get_cluster_posts(cluster_id: int, db_path: Path = DB_PATH, top_n: int = 5) -> list[dict]:
    """Получает топ-N постов кластера по views."""
    con = sqlite3.connect(db_path)
    rows = con.execute(
        """SELECT channel_title, channel_username, date, text, views
           FROM collector_queue
           WHERE cluster_id = ?
           ORDER BY views DESC
           LIMIT ?""",
        (cluster_id, top_n),
    ).fetchall()
    con.close()
    return [
        {
            "channel": r[0] or r[1] or "?",
            "date": (r[2] or "")[:10],
            "text": r[3] or "",
            "views": r[4] or 0,
        }
        for r in rows
    ]


def get_cluster_label(cluster_id: int, db_path: Path = DB_PATH) -> str:
    """Получает label кластера из story_clusters."""
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT label, niche FROM story_clusters WHERE id=?", (cluster_id,)
    ).fetchone()
    con.close()
    if not row:
        return ""
    return f"{row[1]}: {row[0]}" if row[1] else row[0] or ""


def build_prompt(
    topic: str,
    author_examples: list[dict],
    cluster_posts: list[dict],
) -> list[dict]:
    examples_text = "\n\n---\n\n".join(
        f"[Пост автора]\n{ex['text']}"
        for ex in author_examples
        if ex.get("text")
    ) or "(примеры не найдены)"

    context_text = "\n\n".join(
        f"[{p['channel']}, {p['date']}, {p['views']:,} views]\n{p['text'][:500]}"
        for p in cluster_posts
        if p.get("text")
    ) or f"Тема: {topic}"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_TEMPLATE.format(
            examples=examples_text,
            context=context_text,
        )},
    ]


def generate_post(
    topic: str,
    cluster_id: int | None = None,
    db_path: Path = DB_PATH,
    top_k: int = 7,
    temperature: float = 0.7,
) -> dict:
    """
    Генерирует пост в авторском стиле.

    Returns:
        {"draft": str, "model": str, "author_examples_used": int, "cluster_posts_used": int}
    """
    from llm_client import call_llm

    # 1. Авторские примеры
    author_examples = find_similar_author_posts(topic, db_path=db_path, top_k=top_k)

    # 2. Контекст кластера
    cluster_posts: list[dict] = []
    if cluster_id is not None:
        cluster_label = get_cluster_label(cluster_id, db_path=db_path)
        query_topic = cluster_label or topic
        cluster_posts = get_cluster_posts(cluster_id, db_path=db_path, top_n=5)
    else:
        query_topic = topic

    # 3. Промпт
    messages = build_prompt(query_topic, author_examples, cluster_posts)

    # 4. Генерация
    content, model_used, usage = call_llm(
        messages=messages,
        max_tokens=1024,
        temperature=temperature,
    )

    return {
        "draft": content.strip(),
        "model": model_used,
        "author_examples_used": len(author_examples),
        "cluster_posts_used": len(cluster_posts),
    }
