"""On-demand суммаризация результатов поиска через LLM."""

from __future__ import annotations

import json
from pathlib import Path

from llm_client import call_llm

HERE = Path(__file__).parent

_SYSTEM_PROMPT = (
    "Ты аналитик российской экономики и геополитики. "
    "Пишешь чёткие, конкретные аналитические резюме на русском языке. "
    "Ссылайся на факты из предоставленных постов."
)

_MAX_POST_CHARS = 500
_MAX_POSTS = 30


def summarize_results(
    query: str,
    posts: list[dict],
    model: str | None = None,
    max_tokens: int = 2000,
) -> str:
    """
    Подаёт query + топ-30 постов в LLM, возвращает структурированное резюме на русском.

    posts: список dict с ключами message_id, date, text, insight, tags
    Возвращает: чистый текст (не JSON).
    """
    if not posts:
        return "Нет результатов для суммаризации."

    # Ограничиваем количество постов
    posts_to_use = posts[:_MAX_POSTS]

    # Обрезаем текст каждого поста
    trimmed = []
    for p in posts_to_use:
        insight = (p.get("insight") or "").strip()
        text = (p.get("text") or "").strip()
        # Предпочитаем insight, если есть, иначе text
        body = insight if insight else text
        if len(body) > _MAX_POST_CHARS:
            body = body[:_MAX_POST_CHARS] + "..."
        trimmed.append({
            "date": p.get("date", ""),
            "insight": body,
            "tags": p.get("tags") or [],
        })

    posts_json = json.dumps(trimmed, ensure_ascii=False, indent=2)
    n = len(trimmed)

    user_content = (
        f"Запрос пользователя: {query}\n\n"
        f"Вот {n} постов из Telegram-канала «ИнфоПовод» по этой теме:\n"
        f"{posts_json}\n\n"
        "Напиши резюме на русском:\n"
        "- 2-3 абзаца: главные тезисы, динамика темы, ключевые цифры и факты\n"
        "- Маркированный список: 5-7 ключевых выводов\n"
        "Будь конкретен, ссылайся на факты из постов."
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    # Определяем модель: аргумент → config.json → дефолт клиента
    models: list[str] | None = None
    if model:
        models = [model]
    else:
        try:
            cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
            cfg_model = cfg.get("llm_model")
            if cfg_model:
                models = [cfg_model]
        except Exception:
            pass  # используем дефолт из llm_client

    content, _model_used, _usage = call_llm(
        messages,
        models=models,
        max_tokens=max_tokens,
        temperature=0.3,
    )

    return content.strip()
