# Бот-репортер

Автоматизированный публикатор отчётов из [Money_alert_AI](../../../Money_alert_AI) в Telegram-канал.

## Что делает

- Читает результат анализа из `Money_alert_AI/docs/data.json`
- Форматирует отчёт (уровень риска, критерии, тренды, watchlist)
- Публикует в Telegram-канал и уведомляет админа
- Может работать по расписанию (демон) или запускаться вручную

## Файлы

| Файл | Назначение |
|------|------------|
| `run.py` | Запуск анализа + публикация (или только публикация из готового файла) |
| `daemon.py` | Автопубликация по расписанию каждый день в заданное время |
| `telegram_publisher.py` | Форматирование и отправка сообщений в Telegram |

## Установка

```bash
uv sync
```

## Настройка

Скопируй `.env.example` в `.env` и заполни:

```bash
cp .env.example .env
```

Обязательные переменные:

```env
MONEY_ALERT_SRC=C:\_Рабочая_папка\Проекты_программирование\Money_alert_AI\src
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=-100xxxxxxxxxx
TELEGRAM_ADMIN_CHAT_ID=xxxxxxxxx
TAVILY_API_KEY=tvly-xxxxx
```

## Запуск

### Разовая публикация (анализ + публикация)

```bash
uv run python run.py
uv run python run.py --provider gigachat
```

### Публикация из готового data.json (без запуска анализа)

```bash
uv run python run.py --from-file
uv run python run.py --from-file path/to/data.json
```

### Демон (по расписанию)

```bash
# Установить время в .env: SCHEDULE_TIME=09:00
uv run python daemon.py
```

## Пайплайн

```
Money_alert_AI → docs/data.json
        ↓
   run.py / daemon.py
        ↓
telegram_publisher.py → Telegram-канал + уведомление админу
```

## Часть платформы

Входит в [боты-платформа](../../) вместе с модератором и сторожем.
