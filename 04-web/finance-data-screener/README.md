# ИИ-скринер финансовых данных

Приложение для сбора и анализа финансовых данных с помощью LLM. Пользователь вводит запрос на русском языке — система автоматически определяет источник, строит URL запроса и возвращает структурированные данные с графиком.

## Возможности

- **Умный планировщик** — gpt-4o-mini разбирает произвольный текстовый запрос и строит план сбора данных
- **3 источника данных** — MOEX ISS API (акции/облигации), ЦБ РФ (курсы валют), ТАСС RSS (новости)
- **Review Flow** — при неоднозначных запросах система показывает причину и не запускает сбор без подтверждения
- **Витрина данных** — интерактивная таблица + автоматический график (Recharts) + экспорт JSON/CSV
- **Аудит** — каждый API-запрос логируется в `audit_runs` с duration и телом ответа
- **18 тестов** — полное покрытие всех API-эндпоинтов через pytest

## Архитектура

```
Browser (React SPA)
       │
   nginx :80
       │
 FastAPI :8000 ──── PostgreSQL :5432
       │
       ├── POST /ai/plan_and_collect ──► ProxyAPI (gpt-4o-mini + instructor)
       │
       ├── POST /datasets/{id}/collect ──► MoexCollector | CbrCollector | RbcCollector
       │
       └── AuditMiddleware → audit_runs
```

## Стек

| Слой | Технологии |
|---|---|
| Backend | FastAPI 0.115, Python 3.12, SQLAlchemy 2.0 async, Alembic, PostgreSQL 16 |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts, TanStack Table |
| LLM | gpt-4o-mini через ProxyAPI + `instructor` для строгого JSON |
| Инфра | Docker Compose — 3 сервиса |

## Быстрый старт

### Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (включает Docker Compose)
- Ключ [ProxyAPI](https://proxyapi.ru) (~$2–5 на счету, модель gpt-4o-mini)

### Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd <repo-folder>

# 2. Создать файл .env
cp .env.example .env
# Открыть .env и вписать свой PROXYAPI_KEY

# 3. Поднять все сервисы
docker compose -p screener up --build
```

> **Важно:** команды `docker compose` в этом проекте всегда требуют флага `-p screener` из-за кириллицы в пути. Без него Docker Compose не может определить имя проекта.

После запуска откройте http://localhost

Первый билд занимает ~5–8 минут (скачивание образов + npm install + pip install). Повторный запуск — ~30 секунд.

### Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```env
POSTGRES_USER=screener
POSTGRES_PASSWORD=screener_pass
POSTGRES_DB=screener_db

PROXYAPI_KEY=your_key_here          # обязательно
PROXYAPI_BASE_URL=https://api.proxyapi.ru/openai/v1
```

## Использование

### 1. Создать набор данных
Перейдите в раздел **«Наборы данных»** → кнопка **«Создать»** → введите название.

### 2. Собрать данные
Раздел **«Сбор»** → выберите набор → введите запрос на русском:

```
Все акции MOEX с объёмом торгов > 1 млрд рублей за сегодня
Курсы валют ЦБ РФ на сегодня
Последние финансовые новости
```

LLM покажет план (источник, URL, поля, фильтры). При `needs_review=false` — нажмите **«Собрать»**.

### 3. Просмотреть результаты
Раздел **«Витрина»** → выберите набор → таблица + график + экспорт в JSON/CSV.

### 4. Журнал запросов
Раздел **«Журнал»** — timeline всех API-запросов с бейджами метода/статуса и длительностью.

## API

Swagger UI: http://localhost:8000/docs

| Метод | Эндпоинт | Описание |
|---|---|---|
| GET | `/health` | Проверка работоспособности |
| POST | `/datasets` | Создать набор данных |
| GET | `/datasets` | Список всех наборов |
| GET | `/datasets/{id}` | Один набор |
| POST | `/datasets/{id}/collect` | Запустить сбор данных |
| GET | `/datasets/{id}/records` | Записи набора |
| POST | `/ai/plan_and_collect` | Построить план через LLM |
| GET | `/audit` | Журнал всех запросов |

## Тесты

```bash
# Запустить тесты внутри контейнера
docker compose -p screener exec backend pytest tests/ -v
```

Покрытие: 18 тестов — `/health`, CRUD датасетов, аудит.

## Структура проекта

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI роутеры (datasets, ai, audit)
│   │   ├── collectors/   # MoexCollector, CbrCollector, RbcCollector
│   │   ├── middleware/   # AuditMiddleware
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── schemas/      # Pydantic схемы
│   │   ├── services/     # LLM-сервис (instructor + ProxyAPI)
│   │   └── main.py
│   ├── alembic/          # Миграции БД
│   ├── tests/            # pytest тесты
│   ├── entrypoint.sh     # alembic upgrade head → uvicorn
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/          # axios клиент
│   │   ├── components/   # Badge, Layout, DatasetCard, PlanPreview, ReviewBanner
│   │   └── pages/        # Datasets, Collect, Showcase, Audit
│   └── nginx.conf        # проксирует /api/ → backend:8000
├── docker-compose.yml
├── .env.example
└── README.md
```

## База данных: где лежит и как смотреть данные/аудит

PostgreSQL 16 работает в контейнере `postgres` (порт 5432, данные в Docker volume `pgdata`).

### Подключиться через psql

```bash
docker compose -p screener exec postgres psql -U screener -d screener_db
```

### Полезные SQL-запросы

```sql
-- Наборы данных
SELECT id, name, source, created_at FROM datasets ORDER BY created_at DESC;

-- Записи датасета
SELECT id, source, collected_at, data FROM records
WHERE dataset_id = '<uuid>' ORDER BY collected_at DESC LIMIT 10;

-- Аудит последних 20 запросов
SELECT endpoint, method, status_code, duration_ms, created_at
FROM audit_runs ORDER BY created_at DESC LIMIT 20;

-- Запросы с ручной проверкой
SELECT query, needs_review, confidence, created_at
FROM agent_runs WHERE needs_review = true ORDER BY created_at DESC;

-- Ошибки (status >= 400)
SELECT endpoint, method, status_code, error, created_at
FROM audit_runs WHERE status_code >= 400 ORDER BY created_at DESC;
```

### Через API (без psql)

```bash
# Журнал аудита (последние 100 запросов)
curl http://localhost/api/audit

# Записи датасета
curl http://localhost/api/datasets/<id>/records
```

## Управление контейнерами

```bash
# Запустить
docker compose -p screener up --build

# Запустить в фоне
docker compose -p screener up --build -d

# Остановить
docker compose -p screener down

# Остановить и удалить данные БД
docker compose -p screener down -v

# Логи
docker compose -p screener logs -f backend

# Пересобрать один сервис
docker compose -p screener up --build backend
```

## Примеры запросов (curl)

```bash
# 1. Создать набор данных
curl -X POST http://localhost/api/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "Валютные курсы", "query": "Курсы валют ЦБ РФ"}'
# → {"id":"...","name":"Валютные курсы",...}

# 2. Запланировать сбор через LLM (сохраняет план в agent_runs)
curl -X POST http://localhost/api/ai/plan_and_collect \
  -H "Content-Type: application/json" \
  -d '{"query": "Все акции MOEX с объёмом торгов больше 1 млрд рублей"}'
# → {"agent_run_id":"...","plan":{"source":"moex","needs_review":false,...}}

# 3. Запустить сбор (использует agent_run_id из шага 2)
curl -X POST http://localhost/api/datasets/1/collect \
  -H "Content-Type: application/json" \
  -d '{"agent_run_id": "<agent_run_id из шага 2>"}'
# → {"dataset_id":"1","records_saved":42,"source":"moex"}

# 4. Получить собранные записи
curl "http://localhost/api/datasets/1/records"
# → [{"id":"...","data":{...},"collected_at":"..."}]

# 5. Посмотреть журнал аудита
curl http://localhost/api/audit
# → [{"endpoint":"/datasets","method":"POST","status_code":201,"duration_ms":12,...}]
```

## Как воспроизвести ручную проверку (needs_review=true)

Отправьте двусмысленный запрос, на который LLM не может дать уверенный ответ:

```bash
# Запрос без чёткого критерия — LLM вернёт needs_review=true
curl -X POST http://localhost/api/ai/plan_and_collect \
  -H "Content-Type: application/json" \
  -d '{"query": "Акции с хорошими дивидендами"}'
# → {"plan":{"needs_review":true,"review_reason":"MOEX ISS не содержит данных о дивидендах",...}}

# Или невыполнимый запрос
curl -X POST http://localhost/api/ai/plan_and_collect \
  -H "Content-Type: application/json" \
  -d '{"query": "Цена биткоина и эфириума в реальном времени"}'
# → {"plan":{"needs_review":true,"confidence":"low",...}}
```

При `needs_review=true`:
- Поле `review_reason` содержит причину
- В веб-панели раздел «Сбор» показывает жёлтый баннер с причиной
- Кнопка «Собрать» не появляется — сбор заблокирован

Все запросы (включая заблокированные) фиксируются в `audit_runs`. Проверить:
```bash
curl http://localhost/api/audit
```

## Источники данных

| Источник | Что возвращает | Примечание |
|---|---|---|
| [MOEX ISS API](https://iss.moex.com/iss) | Акции, облигации, фьючерсы, индексы | Секции `securities` + `marketdata` объединяются |
| [ЦБ РФ](https://cbr-xml-daily.ru) | Курсы 34 валют | JSON-ответ, без ключа |
| [ТАСС RSS](https://tass.ru/rss/v2.xml) | До 100 финансовых новостей | Fallback вместо РБК (Qrator-защита) |

> SSL-проверка отключена (`verify=False`) из-за корпоративного SSL-перехвата. Данные публичные и не чувствительные.
