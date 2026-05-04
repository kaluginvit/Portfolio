# ИИ-продукты

Боты в Telegram, RAG-ассистенты, мультиагенты и MCP-серверы — всё, что ориентировано на пользователя или на ИИ-клиента (Cursor, Claude и т.д.).

## Как не путать похожие Telegram-боты

| Проект | Отличие |
|--------|---------|
| [`personal-rag-assistant`](./personal-rag-assistant/) | Полный RAG: Pinecone, Haystack, документы (Docling), долговременная память в диалоге |
| [`team-ai-bot`](./team-ai-bot/) | Запись обсуждения в группе, Pinecone + Haystack, вопросы по контексту чата, summary |
| [`team-tg-bot-vc`](./team-tg-bot-vc/) | Простой командный список задач в SQLite, без LLM/RAG |
| [`memory-bot`](./memory-bot/) | Память через SQLite-тезисы и LLM; узкий сценарий, не полный RAG-пайплайн как у ассистента выше |
| [`weather-tg-bot`](./weather-tg-bot/) | Бот погоды (типовой мини-кейс) |

Учебные варианты «диалоговый ассистент / с памятью» на том же стеке, что и `personal-rag-assistant`, из портфолио убраны как дубликаты; эталонный кейс — **`personal-rag-assistant`**.

## Проекты

| Папка | Кратко |
|--------|--------|
| [`audio-transcriber`](./audio-transcriber/) | Транскрибация аудио (faster-whisper) |
| [`crewai-multiagent`](./crewai-multiagent/) | Мультиагентная схема CrewAI |
| [`finance-mcp-server`](./finance-mcp-server/) | MCP-сервер для финансовых сценариев |
| [`memory-bot`](./memory-bot/) | Лёгкий бот с памятью на SQLite |
| [`personal-rag-assistant`](./personal-rag-assistant/) | Персональный RAG-ассистент в Telegram |
| [`seo-mcp-bot`](./seo-mcp-bot/) | MCP для Yandex Wordstat и SEO |
| [`smart-text-helper`](./smart-text-helper/) | Помощник по тексту |
| [`svo-payments-bot`](./svo-payments-bot/) | Чат-бот по выплатам (парный с сайтом в `04-web`) |
| [`team-ai-bot`](./team-ai-bot/) | AI-бот для командного чата (Haystack + Pinecone) |
| [`team-tg-bot-vc`](./team-tg-bot-vc/) | Бот списка задач для команды |
| [`tg-catalog-analyzer`](./tg-catalog-analyzer/) | Анализ каталогов через OpenRouter |
| [`weather-tg-bot`](./weather-tg-bot/) | Погода в Telegram |
