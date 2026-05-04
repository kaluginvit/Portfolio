# MCP + Telegram-бот: end-to-end пример

> **Проблема:** показать клиенту/команде, как именно ИИ-агент использует MCP для работы с реальной бизнес-БД (каталог товаров) — без зависшей в воздухе теории.  
> **Решение:** связка из двух частей — MCP-сервер `product-mcp` (SQLite + 4 инструмента: `list_products`, `find_product`, `add_product`, `calculate`) и Telegram-бот, в котором OpenAI Chat Completions сам решает, какой инструмент вызвать. Между ними — Streamable HTTP MCP.  
> **Стек:** Python 3.10+, MCP SDK, SQLite, OpenAI Chat Completions, aiogram, Streamable HTTP.  
> **Ценность:** рабочий end-to-end пример «LLM ↔ MCP ↔ БД», адаптируемый под любой каталог; тот же MCP-сервер можно подключить к Cursor/Claude Desktop по stdio без переписывания кода.

---

Два компонента:

1. **`mcp_server/`** — MCP-сервер **product-mcp** (SQLite, инструменты каталога и калькулятор).
2. **`telegram_bot/`** — Telegram-бот: **OpenAI Chat Completions** решает, вызывать ли инструменты; вызовы идут на MCP по **Streamable HTTP**.

## Требования

- Python 3.10+
- Учётная запись OpenAI (или совместимый API, см. `OPENAI_BASE_URL`)
- Токен бота от [@BotFather](https://t.me/BotFather)

## Ключи и `.env`

Создайте файл `.env` в корне проекта **или** в папке `telegram_bot/`:

```env
TELEGRAM_API_TOKEN=ваш_токен_бота
OPENAI_API_KEY=sk-...

# Необязательно (по умолчанию gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# URL MCP Streamable HTTP (путь /mcp по умолчанию у сервера)
MCP_BASE_URL=http://127.0.0.1:8765/mcp

# Необязательно: прокси к OpenAI-совместимому API
# OPENAI_BASE_URL=https://api.example.com/v1
```

Для MCP-сервера при необходимости:

```env
MCP_HOST=127.0.0.1
MCP_PORT=8765
```

## Установка зависимостей

```powershell
cd "путь\к\проекту\Урок по MCP\mcp_server"
pip install -r requirements.txt

cd "..\telegram_bot"
pip install -r requirements.txt
```

## Запуск

### Docker (рекомендуется для демо)

Из корня `mcp-lesson/` (рядом с `docker-compose.yml`):

1. Скопируйте [`.env.example`](./.env.example) в `.env`, задайте `TELEGRAM_API_TOKEN` и `OPENAI_API_KEY`.
2. `docker compose up --build` — поднимется **mcp_server** (порт **8765** на хосте) и **telegram_bot** с `MCP_BASE_URL=http://mcp_server:8765/mcp`.

Порт хоста можно переопределить: `MCP_PUBLISH_PORT=9876 docker compose up`.

### 1) MCP-сервер в режиме HTTP (для бота)

В отдельном терминале:

```powershell
cd "путь\к\проекту\Урок по MCP\mcp_server"
python server.py --http
```

Сервер слушает `http://127.0.0.1:8765/mcp` (если не меняли `MCP_HOST` / `MCP_PORT`).

Тот же сервер **без** `--http` работает по **stdio** (например, для Cursor):

```powershell
python server.py
```

Файл базы `mcp_server/products.db` создаётся автоматически; при первом запуске в таблицу добавляется 100 тестовых товаров.

### 2) Telegram-бот

```powershell
cd "путь\к\проекту\Урок по MCP\telegram_bot"
python bot.py
```

Убедитесь, что шаг 1 уже выполнен, иначе бот не сможет вызвать инструменты.

## Поведение бота

Пользователь пишет на естественном языке; модель при необходимости вызывает MCP-инструменты (`list_products`, `find_product`, `add_product`, `calculate`) и формирует структурированный ответ. Если запрос неоднозначен, модель задаёт уточняющий вопрос.

## Структура каталогов

```
mcp_server/
  server.py
  mcp_factory.py
  db.py
  tools.py
  products.db    # создаётся при запуске
  requirements.txt

telegram_bot/
  bot.py
  config.py
  mcp_client.py
  requirements.txt
```
