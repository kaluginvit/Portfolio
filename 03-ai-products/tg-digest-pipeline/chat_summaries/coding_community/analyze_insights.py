"""
Анализ текстов сообщений за последние 8 недель через MiniMax M3 (OpenRouter).
Выявляет топ-темы, инструменты, боли, тренды сообщества.

Использование:
    uv run python chat_summaries/coding_community/analyze_insights.py
    uv run python chat_summaries/coding_community/analyze_insights.py --since 2026-07-01 --until 2026-08-29
"""

import argparse
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from llm_client import call_llm

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = Path(__file__).parent / 'messages.db'
OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)
_ENV_PATH = Path(__file__).parents[2] / '.env'

PROMPT_TEMPLATE = """Ты аналитик Telegram-сообщества разработчиков и AI-энтузиастов (вайбкодинг + n8n).

Проанализируй {count} сообщений за период {since} — {until} и дай подробный структурированный отчёт.

Требования к отчёту:
- Каждый раздел развёрнутый, не менее 5-10 пунктов
- Конкретные примеры, цитаты, названия из сообщений
- Количественные оценки где возможно (упоминаний, участников, частота)
- Не обобщай — пиши конкретно что именно говорили люди
- Минимум 4000-6000 слов в итоговом отчёте

Формат ответа (строго Markdown):

## Топ-темы
Топ-15 тем. Для каждой: название, подробное описание (3-5 предложений) что именно обсуждали, какие конкретные вопросы поднимались, какие мнения звучали, примеры из сообщений.

## Популярные инструменты и сервисы
Полный список упомянутых инструментов по категориям:
- AI-модели (с числом упоминаний и контекстом использования)
- Агентские харнессы и IDE
- Платформы и API-провайдеры
- Инфраструктура и деплой
- n8n-ноды и интеграции
Для каждого: что говорили, как используют, плюсы/минусы по мнению участников.

## Боли и проблемы
Топ-15 болей. Для каждой: описание проблемы, как часто встречается, что предлагали как решение, остаётся ли нерешённой.

## Тренды периода
8-10 трендов. Для каждого: описание, откуда появился, как развивался в течение периода, примеры конкретных обсуждений.

## Инсайты
10-12 нетривиальных наблюдений. Каждый инсайт — абзац с пояснением почему это важно и что из этого следует.

## Топ-обсуждения
7-10 наиболее ярких или содержательных дискуссий. Для каждой: тема, краткий пересказ (5-7 предложений), ключевые позиции участников, чем завершилось.

## Цитаты периода
10-15 наиболее ярких, показательных или смешных цитат из сообщений (дословно или близко к тексту).

## Динамика периода
Как менялись темы и настроения от июля к августу. Что было горячим в начале и угасло, что появилось ближе к концу.

---

СООБЩЕНИЯ:
{messages}"""


def load_messages(since: str, until: str) -> list[dict]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT m.date, m.sender_name, m.text, m.source_peer_id
            FROM messages_filtered m
            WHERE m.date >= ? AND m.date <= ?
            ORDER BY m.date
            """,
            (since, until),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def format_messages(messages: list[dict]) -> str:
    parts = []
    for m in messages:
        date = (m['date'] or '')[:10]
        sender = m['sender_name'] or 'anon'
        text = (m['text'] or '').strip()
        if text:
            parts.append(f"[{date}] {sender}: {text}")
    return '\n\n'.join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--since', default=None, help='С даты YYYY-MM-DD (по умолчанию -8 недель)')
    parser.add_argument('--until', default=None, help='По дату YYYY-MM-DD (по умолчанию сегодня)')
    parser.add_argument('--out', type=Path, default=OUT_DIR / 'insights_8w.md')
    args = parser.parse_args()

    until = args.until or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    since = args.since or (datetime.now(timezone.utc) - timedelta(weeks=8)).strftime('%Y-%m-%d')

    print(f'Период: {since} — {until}')
    messages = load_messages(since, until)
    print(f'Сообщений: {len(messages)}')

    text = format_messages(messages)
    total_chars = len(text)
    print(f'Символов: {total_chars:,} (~{total_chars // 4:,} токенов)')

    prompt = PROMPT_TEMPLATE.format(
        count=len(messages),
        since=since,
        until=until,
        messages=text,
    )

    result, model_used, usage = call_llm(
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=16000,
        env_path=_ENV_PATH,
    )
    print(f'Токены: in={usage.get("tokens_input", "?")} out={usage.get("tokens_output", "?")}')

    # Archive previous report before overwriting
    if args.out.exists():
        archived = args.out.with_name(f'insights_8w_{args.out.stat().st_mtime:.0f}.md')
        # Use date from file content header if possible, otherwise mtime
        existing = args.out.read_text(encoding='utf-8')
        m = re.search(r'(\d{4}-\d{2}-\d{2}) —', existing)
        date_tag = m.group(1) if m else datetime.now(timezone.utc).strftime('%Y-%m-%d')
        archived = args.out.with_name(f'insights_{date_tag}.md')
        args.out.rename(archived)
        print(f'Архив: {archived.name}')

    header = (
        f'# Инсайты сообщества: {since} — {until}\n\n'
        f'_Источник: {len(messages)} отфильтрованных сообщений '
        f'(vibecoding + n8n) | Модель: {model_used}_\n\n'
    )
    out_text = header + result
    args.out.write_text(out_text, encoding='utf-8')
    print(f'\nГотово: {args.out}')


if __name__ == '__main__':
    main()
