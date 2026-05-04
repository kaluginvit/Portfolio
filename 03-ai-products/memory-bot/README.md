# Memory Bot

Минималистичный Telegram-бот с **памятью на SQLite**: короткие тезисы о пользователе и ответы через LLM-proxy. Это **не** полный RAG-пайплайн с Pinecone и документами — для такого сценария см. [`personal-rag-assistant`](../personal-rag-assistant/).

## Запуск

Скопируйте `.env.example` в `.env`, задайте токены. Локально: `python main.py`. Либо `docker compose up` по [`docker-compose.yml`](./docker-compose.yml).
