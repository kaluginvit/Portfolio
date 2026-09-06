# Валюта для путешественника (Telegram-бот)

Telegram-бот для конвертации валют в поездках: кросс-курсы через [exchangerate.host](https://exchangerate.host), история запросов в SQLite.

## Стек

Python, pyTelegramBotAPI, SQLite, exchangerate.host API

## Быстрый старт

```bash
pip install -r requirements.txt
cp .env.example .env   # заполнить токены
python bot.py
```

## Настройка `.env`

```env
TELEGRAM_BOT_TOKEN=your_bot_token
EXCHANGERATE_API_KEY=your_api_key
```

## Структура

| Файл | Назначение |
|------|-----------|
| `bot.py` | Точка входа, FSM-диалог с пользователем |
| `current_api.py` | Запросы к exchangerate.host |
| `currencies.py` | Справочник валют и пар |
| `database.py` | История запросов (SQLite) |
