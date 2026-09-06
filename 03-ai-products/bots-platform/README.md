# Bots Platform

Три независимых Telegram-бота для управления командой и автоматической публикации AI-аналитики.

## Состав

| Бот | Назначение |
|-----|-----------|
| `модератор` | Автомодерация чата: проверка нарушений, фильтры, банлист |
| `репортер` | Публикация AI-анализа из [rf-macro-risk-ai](../../03-ai-products/rf-macro-risk-ai/) в Telegram-канал |
| `сторож` | Мониторинг участников: уходы, перекрытия, спам, сохранение ID |

## Стек

Python 3.11+, [Modal](https://modal.com) (serverless-деплой), `httpx`, `uv`

## Запуск

Каждый бот запускается независимо из своей папки:

```bash
cd core/<бот>
cp .env.example .env   # заполнить токены
uv sync
uv run python <точка_входа>.py
```

Точки входа: `модератор` → `bot.py`, `репортер` → `run.py`, `сторож` → `spam_watcher.py`

## Структура

```
core/
  модератор/   # bot.py, modal_app.py, check_violations.py
  репортер/    # run.py, daemon.py, telegram_publisher.py
  сторож/      # spam_watcher.py, check_*.py, ban_saved.py
```
