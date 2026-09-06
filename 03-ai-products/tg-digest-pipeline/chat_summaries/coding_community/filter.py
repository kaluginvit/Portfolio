"""
Build the derived `messages_filtered` table for coding_community.

Safe to rerun: recreates only `messages_filtered` from raw `messages`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.local_gate import rebuild_filtered, print_stats

DB_PATH = Path(__file__).parent / "messages.db"
MIN_LEN = 80

KEYWORDS = [
    # Vibe coding / ИИ-разработка
    "vibe", "cursor", "copilot", "windsurf", "claude", "gpt", "chatgpt",
    "llm", "агент", "автоматизац", "нейросет", "prompt", "промпт",
    "openai", "anthropic", "gemini", "код", "разработ", "програм",
    # Инструменты разработки
    "python", "javascript", "typescript", "react", "fastapi", "docker",
    "api", "бэкенд", "фронтенд", "деплой", "github", "n8n",
    # AI-инструменты (расширено)
    "lovable", "bolt", "replit", "devin", "cline", "aider", "mcp",
    "deepseek", "mistral", "llama", "grok", "perplexity",
    # Инфраструктура / интеграции
    "supabase", "vercel", "webhook", "интеграц", "парс", "скрейп",
    "телеграм бот", "тг бот", "tilda", "тильда", "wordpress",
    # Монетизация / бизнес
    "монетизац", "продукт", "стартап", "saas", "клиент", "продаж",
    "доход", "выручк", "заработ", "фриланс",
    # Кейсы и проекты
    "кейс", "токен", "контекст", "задач", "заказ", "бюджет", "оффер",
]


def main():
    stats = rebuild_filtered(DB_PATH, KEYWORDS, MIN_LEN, filter_on_analyzed_at=True)
    print_stats(stats, MIN_LEN)


if __name__ == "__main__":
    main()
