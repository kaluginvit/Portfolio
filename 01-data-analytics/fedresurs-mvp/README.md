# Fedresurs MVP

Инструмент для оценки лотов банкротства по рыночным аналогам.

**Live Demo:** https://kaluginvit.github.io/Portfolio/fedresurs-mvp/

Ручной поиск аналогов занимает 30-60 минут на лот. При портфеле из 20-50 активных закладок — неподъёмно. Этот инструмент автоматизирует оценку через два независимых движка.

## Business Problem

Лоты на торгах банкротства выставляются без рыночного контекста: арбитражный управляющий публикует описание и начальную цену, но не сравнивает с рынком. Покупатель должен сам понять — переплачивает он или берёт с дисконтом.

**Проблема:** ручной поиск аналогов на Авито/ЦИАН занимает 30-60 минут на лот. При портфеле из 20-50 активных закладок — это несколько рабочих дней в месяц.

## Solution

Два независимых движка оценки для разных типов задач:

**1. Статистический движок** (`fedresurs_mvp.py`) — для недвижимости: парсит N1 и ЦИАН, собирает цены за м², считает P25/P50/P75 по аналогам близкой площади.

**2. LLM-агент** (`valuate.py`) — универсальный: модель сама формирует поисковые запросы через Tavily/Brave/Google, находит аналоги для любого типа актива (квартира, оборудование, транспорт, дебиторка) и возвращает 4 сценария цены.

> Оценки — ориентир для принятия решения об участии в торгах, не официальное заключение оценщика.

## Key Features

- **4 сценария цены** на каждый лот: `auction_price` / `lot_buyer` / `wholesale` / `retail` — стандарт профессионального оценщика при банкротстве
- **P25/P50/P75 по рыночным аналогам** + confidence level (low/medium/high) на основе числа источников
- **Agentic loop**: модель сама решает количество поисков (обычно 2-5 итераций)
- **Multi-provider**: Gemini / OpenRouter / Tavily / Brave / Google / Jina как fallback
- **Flask web UI** для оценки через браузер
- **47 тестов** на бизнес-логику оценки

## Architecture

```
Входные данные
├── Chrome bookmarks (закладки Федресурса) → --bookmarks flag
├── Прямой ID лота → python valuate.py <lot-id>
└── Demo seed → python demo_seed.py (5 синтетических лотов)
           │
           ▼
    SQLite (data/fedresurs.sqlite3)
           │
    ┌──────┴──────────┐
    │                 │
    ▼                 ▼
Статистический      LLM-агент
движок              (valuate.py)
P25/P50/P75         │
по аналогам         ├── Web Search (Tavily/Brave/Google)
                    ├── Agentic loop (2-5 итераций)
                    └── 4 price scenarios
           │
           ▼
    Flask UI (:5000) или CLI output
```

## Tech Stack

| Компонент | Технология |
|-----------|-----------|
| Language | Python 3.10+ |
| LLM | Gemini / OpenRouter (через API) |
| Search | Tavily / Brave / Google / Jina (fallback без ключа) |
| Database | SQLite |
| Web UI | Flask |
| Tests | pytest (47 тестов) |

## Business / Domain Logic

**Статистический движок:**
- `market_min = P25(цены за м² аналогов) * area`
- `market_mid = P50(цены за м² аналогов) * area`
- `market_max = P75(цены за м² аналогов) * area`
- `target_price = market_min * 0.90` — коэффициент запаса безопасности для покупателя на торгах

**Confidence levels:**
- `< 3` аналогов → оценки нет, `valuation_required`
- `3-5` аналогов → `confidence=low`
- `6-9` аналогов из 2+ источников → `confidence=medium`
- `10+` аналогов из 3+ источников → `confidence=high`

**4 сценария цены (LLM-движок):**
- `auction_price` — целевая цена для участия в торгах (70-80% от retail)
- `lot_buyer` — цена перекупщика (нижняя граница)
- `wholesale` — оптовая продажа партиями
- `retail` — розничная рыночная цена

**Автоматические решения по лотам:**
- `auction_interesting` — стартовая цена ≤ целевой → имеет смысл участвовать
- `overpriced_skip` → стартовая цена выше целевой
- `public_offer_wait_until_target` → публичное предложение, ждать снижения цены
- `public_offer_price_reached` → текущая цена попала в интересный период

## Project Structure

```
fedresurs-mvp/
├── fedresurs_mvp.py      # Основной скрипт: Chrome bookmarks → SQLite → статоценка
├── valuate.py            # LLM-оценка одного лота (agentic loop)
├── valuate_batch.py      # Пакетная LLM-оценка всех активных лотов
├── server.py             # Flask UI для браузерного доступа (:5000)
├── demo_seed.py          # 5 синтетических лотов для демо без реальных данных
├── fedresurs.py          # Расширенная версия (больше функций)
├── tests/
│   └── test_valuation.py # 47 тестов на бизнес-логику
├── data/                 # SQLite база (создаётся автоматически)
├── reports/
│   └── dashboard.html    # HTML-дашборд
└── tools/                # Утилиты для работы с Chrome bookmarks
```

## Quick Start

### Вариант A — Demo (без реальных данных Федресурса)

```bash
pip install -r requirements.txt
cp .env.example .env
# Добавьте GEMINI_API_KEY или OPENROUTER_API_KEY в .env

# Заполнить базу синтетическими лотами
python demo_seed.py

# Запустить веб-интерфейс
python server.py
# Открыть http://localhost:5000
```

### Вариант B — С реальными данными (Chrome bookmarks)

```bash
pip install -r requirements.txt
cp .env.example .env
# Заполните ключи API в .env

# Синхронизация закладок Chrome с Федресурсом
# Если Chrome открыт на Windows — передать путь явно:
python fedresurs_mvp.py all --limit 15 --bookmarks "C:\Users\<USER>\AppData\Local\Google\Chrome\User Data\Default\Bookmarks"

# Или через переменную окружения LOCALAPPDATA (автоопределение):
python fedresurs_mvp.py all --limit 15
```

### LLM-оценка лота

```bash
# Оценить конкретный лот по ID
python valuate.py DEMO-001

# С альтернативным поиском
python valuate.py DEMO-001 --provider brave

# Пакетная оценка всех активных лотов
python valuate_batch.py --limit 20 --dry-run  # предпросмотр
python valuate_batch.py --limit 20             # запуск
```

## Configuration

`.env.example` содержит все переменные:

| Переменная | Описание |
|-----------|---------|
| `GEMINI_API_KEY` | Gemini API (рекомендуется, дешевле) |
| `OPENROUTER_API_KEY` | OpenRouter (альтернатива, доступ к любой модели) |
| `TAVILY_API_KEY` | Tavily поиск (опционально) |
| `BRAVE_API_KEY` | Brave Search API (опционально) |

Если ни один поисковый ключ не задан — используется Jina (без ключа, медленнее).

## Demo / Sample Data

```bash
python demo_seed.py
```

Добавляет 5 синтетических лотов:
- **DEMO-001:** квартира 2-комн, 54 м², Екатеринбург — `python valuate.py DEMO-001`
- **DEMO-002:** грузовик МАЗ-6430 — `python valuate.py DEMO-002`
- **DEMO-003:** производственное оборудование — `python valuate.py DEMO-003`
- **DEMO-004:** нежилое помещение 120 м², Москва — `python valuate.py DEMO-004`
- **DEMO-005:** дебиторская задолженность — `python valuate.py DEMO-005`

## Live Demo

**Live Demo:** https://kaluginvit.github.io/Portfolio/fedresurs-mvp/

Static demo uses synthetic lots and precomputed valuation results.

## Screenshots

→ `docs/SCREENSHOTS_TODO.md`

## Tests

```bash
python -m pytest tests/ -v
# 47 passed
```

Покрыты: парсинг JSON из LLM-ответа, классификатор активов, расчёт квантилей P25/P50/P75, извлечение цены из текста аналогов, очистка описания лота, построение промпта для LLM.

## Engineering Decisions

**Два независимых движка, не один:** статистический быстр и дёшев для однотипных активов (квартиры), LLM — универсален но дороже. Разделение позволяет использовать нужный инструмент в нужном случае.

**Agentic loop вместо одного запроса:** для оценки часто нужно несколько итераций поиска. Квартира: запрос на ЦИАН + запрос по м² + запрос по конкретному адресу. Оборудование: запрос на б/у рынок конкретной модели + запрос на торговые площадки. Модель сама решает, сколько поисков достаточно.

**SQLite вместо PostgreSQL:** инструмент работает на одной машине, данных — тысячи лотов. SQLite zero-deploy, данные в одном файле. При необходимости — замена коннектора.

**Python stdlib для HTTP:** `urllib.request` вместо `requests` — минимум зависимостей для инструмента, работающего локально.

## Security / Privacy

- Данные лотов хранятся локально (SQLite)
- API ключи через `.env` (не в коде)
- Запросы к поисковым API содержат только публичные описания лотов

## Reuse / Customization

Тип: **Production case → Reusable with config**

**Для нового пользователя:**
1. Установить зависимости, добавить ключи в `.env`
2. `python demo_seed.py` — добавить тестовые лоты
3. Или добавить реальные лоты через `valuate.py <lot-id>` с ID из Федресурса

**Чтобы изменить параметры оценки:**
- Коэффициент target_price (`0.90`) задан в `fedresurs_mvp.py`
- Пороги confidence (3/6/10 аналогов) задан там же
- Промпт для LLM в `valuate.py`

## Limitations

- Статистический движок работает только для недвижимости (нужна площадь и цена за м²)
- Chrome bookmarks как источник лотов — только Windows, требует Google Chrome
  - Альтернатива: флаг `--bookmarks /path/to/Bookmarks` для любого пути или `demo_seed.py`
- LLM-оценка зависит от доступности поисковых API (Tavily/Brave)
- Нет автоматического мониторинга изменения цен в ходе публичного предложения

## Roadmap

- Универсальный ввод лотов через веб-форму (без Chrome bookmarks)
- Интеграция с Федресурс API для автоматической загрузки лотов по поиску
- Сравнение нескольких лотов в одном отчёте
- Email/Telegram уведомление при достижении целевой цены
