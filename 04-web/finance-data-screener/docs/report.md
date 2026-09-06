# Технический отчёт — ИИ-скринер финансовых данных

## 1. Цель проекта

Разработать веб-приложение, в котором пользователь вводит запрос на естественном языке («Все акции с объёмом > 1 млрд рублей»), а система:
1. Разбирает запрос через LLM и строит план сбора данных
2. Показывает план пользователю для подтверждения
3. Собирает данные из открытых финансовых источников
4. Отображает результат в виде таблицы и графика с возможностью экспорта

---

## 2. Стек технологий

| Слой | Технология | Версия |
|---|---|---|
| Backend | FastAPI | 0.115.5 |
| Runtime | Python | 3.12 |
| ORM | SQLAlchemy async | 2.0.36 |
| Миграции | Alembic | 1.14.0 |
| База данных | PostgreSQL | 16 |
| LLM | gpt-4o-mini (ProxyAPI) | — |
| Структурированный вывод | instructor | 1.7.0 |
| HTTP-клиент | httpx | 0.28.1 |
| RSS-парсер | feedparser | 6.0.11 |
| Frontend | React + TypeScript | 18 + 5 |
| Сборщик | Vite | — |
| Стили | Tailwind CSS | — |
| UI-компоненты | shadcn/ui | — |
| Таблицы | TanStack Table | — |
| Графики | Recharts | — |
| Инфра | Docker Compose | — |
| Веб-сервер | nginx | — |
| Тесты | pytest + pytest-asyncio | 8.3.4 + 0.24.0 |

---

## 3. Архитектура

```
Browser (React SPA)
       │  HTTP :80
   nginx
       │  proxy /api/ → :8000
 FastAPI
       │
       ├── AuditMiddleware ─────────────────► audit_runs (каждый запрос)
       │
       ├── POST /ai/plan_and_collect ───────► ProxyAPI → gpt-4o-mini + instructor
       │                                       └── CollectionPlan (строгий JSON)
       │
       ├── POST /datasets/{id}/collect ─────► CollectorFactory
       │                                       ├── MoexCollector (ISS API)
       │                                       ├── CbrCollector (cbr-xml-daily.ru)
       │                                       └── RbcCollector (TASS RSS fallback)
       │
       └── PostgreSQL :5432
               ├── datasets
               ├── records (JSONB)
               ├── agent_runs
               └── audit_runs
```

### Поток данных (happy path)

1. Пользователь вводит запрос в `CollectPage`
2. Frontend → `POST /ai/plan_and_collect` → LLM строит `CollectionPlan`
3. LLM-ответ сохраняется в `agent_runs`, возвращается фронтенду
4. Frontend показывает `PlanPreview` — источник, URL, поля, фильтры
5. Если `needs_review=false` → кнопка «Собрать»
6. Frontend → `POST /datasets/{id}/collect` с `agent_run_id`
7. Backend берёт план из `agent_runs`, вызывает нужный коллектор
8. Данные сохраняются в `records` (JSONB)
9. Frontend перенаправляет на `ShowcasePage` → таблица + график

### Поток данных (needs_review)

Если LLM не уверен (двусмысленный запрос, нет источника) → `needs_review=true`.  
Frontend показывает `ReviewBanner` с причиной. Сбор не запускается.

---

## 4. Компоненты backend

### 4.1 Коллекторы (`app/collectors/`)

| Коллектор | Источник | Что возвращает |
|---|---|---|
| `MoexCollector` | MOEX ISS API | Акции, облигации, фьючерсы, индексы. Merge секций securities+marketdata по длине. |
| `CbrCollector` | cbr-xml-daily.ru/scripts/daily_json.js | ~40 курсов валют ЦБ РФ |
| `RbcCollector` | TASS RSS (fallback от РБК) | 100 финансовых новостей |
| `CollectorFactory` | — | `get(source)` возвращает нужный коллектор |

`BaseCollector` реализует универсальную фильтрацию: отбор нужных полей (`fields_to_keep`) и строк по условиям (`filters`: `gt`, `lt`, `eq`, `contains`).

### 4.2 LLM-сервис (`app/services/llm.py`)

Использует `instructor` поверх `AsyncOpenAI` с кастомным `base_url` ProxyAPI.  
Pydantic-модель `CollectionPlan` — строгая схема ответа:

```python
class CollectionPlan(BaseModel):
    source: Literal["moex", "cbr", "rbc"]
    api_url: str
    fields_to_keep: list[str]
    filters: dict[str, dict]
    confidence: Literal["high", "medium", "low"]
    needs_review: bool
    plan_steps: list[str]
```

Системный промпт содержит описание трёх источников, примеры URL для разных рынков MOEX, разъяснение `VALTODAY` vs `VOLTODAY`.

### 4.3 API-эндпоинты (`app/api/`)

| Метод | URL | Назначение |
|---|---|---|
| GET | /health | Проверка работоспособности |
| POST | /datasets | Создать датасет |
| GET | /datasets | Список датасетов |
| GET | /datasets/{id} | Один датасет |
| POST | /datasets/{id}/collect | Запустить сбор |
| GET | /datasets/{id}/records | Записи датасета |
| POST | /ai/plan_and_collect | LLM-планирование |
| GET | /audit | Журнал всех операций |

### 4.4 Audit middleware (`app/middleware/audit.py`)

`BaseHTTPMiddleware` Starlette — логирует каждый запрос в `audit_runs`:
`endpoint`, `method`, `status_code`, `duration_ms`, `request_body`, `error_message`.

---

## 5. Компоненты frontend

| Файл | Назначение |
|---|---|
| `DatasetsPage.tsx` | Карточки датасетов, создание через модальное окно |
| `CollectPage.tsx` | State machine (idle→planning→planned→collecting→done→error) |
| `ShowcasePage.tsx` | TanStack Table + Recharts BarChart + экспорт JSON/CSV |
| `AuditPage.tsx` | Timeline audit_runs с бейджами метода и статуса |
| `PlanPreview.tsx` | Показ плана LLM перед запуском сбора |
| `ReviewBanner.tsx` | Жёлтый баннер при needs_review=true |
| `Badge.tsx` | Цветовые бейджи источников (moex/cbr/rbc) |
| `Layout.tsx` | Навигация, 4 вкладки |

---

## 6. База данных

### Схема таблиц

**datasets** — контейнеры для наборов данных  
`id, name, query, source, created_at`

**records** — финансовые записи  
`id, dataset_id, data (JSONB), collected_at`

**agent_runs** — результаты работы LLM  
`id, dataset_id, query, plan (JSONB), needs_review, confidence, created_at`

**audit_runs** — аудит всех операций  
`id, endpoint, method, status_code, duration_ms, request_body, error_message, created_at`

### Ключевые решения

- `records.data` — JSONB, т.к. схема записей различается для MOEX/ЦБ/ТАСС
- Alembic-миграция написана вручную (`0001_initial_tables.py`), без autogenerate — гарантирует работу при первом `docker compose up`
- `entrypoint.sh`: `alembic upgrade head` → `uvicorn` — миграции запускаются при каждом старте

---

## 7. Инфраструктура

### docker-compose.yml

```
postgres:16        → порт 5432
backend:python3.12 → порт 8000 (через entrypoint.sh)
frontend:nginx     → порт 80 (multi-stage build, proxy /api/)
```

### Запуск

```bash
cp .env.example .env        # вписать PROXYAPI_KEY
docker compose -p screener up --build
# → http://localhost
```

Первый билд: ≤10 минут. Повторный: ~30 секунд.

**Примечание:** флаг `-p screener` обязателен, т.к. путь к проекту содержит кириллицу.

---

## 8. Тестирование

### Автотесты (pytest)

18 тестов, 0 предупреждений, время выполнения ~1.2 сек.

| Файл | Что тестирует |
|---|---|
| `test_health.py` | GET /health → 200 |
| `test_datasets.py` | CRUD датасетов, сбор записей, список записей |
| `test_audit.py` | Audit middleware — запись в audit_runs после каждого запроса |

Запуск:
```bash
docker compose -p screener exec backend pytest tests/ -v
```

### Тестовые запросы (10 штук)

`tests_data/queries.jsonl` — 10 запросов в трёх категориях:

| Категория | Кол-во | Пример |
|---|---|---|
| Корректные | 7 | «Акции с объёмом > 1 млрд», «Курс USD», «ОФЗ» |
| Двусмысленные | 2 | «Акции с хорошими дивидендами», «Лучшие акции» |
| Невыполнимые | 1 | «Цена биткоина» |

---

## 9. Ключевые технические решения

| Решение | Обоснование |
|---|---|
| `instructor` для LLM-вывода | Гарантирует схему ответа без ручного парсинга |
| JSONB для записей | Разная схема у MOEX/ЦБ/ТАСС, JSONB даёт гибкость |
| TASS вместо РБК RSS | РБК заблокировал серверные запросы (Qrator антибот) |
| Merge секций MOEX по длине | ISS возвращает securities и marketdata раздельно |
| `verify=False` в httpx | Корпоративный антивирус перехватывает SSL в Docker |
| `-p screener` в docker compose | Кириллица в пути к проекту ломает автоопределение имени |

---

## 10. Критерии сдачи — выполнение

| Критерий | Статус |
|---|---|
| docker compose up поднимает всё с нуля, ≤10 мин | Выполнено |
| 10 тестовых запросов (7/2/1) | Выполнено |
| pytest покрывает все API-эндпоинты | Выполнено (18/18) |
| Демо-видео 2–4 мин | Шаг 13 |
| Защита 5–7 мин | Шаг 13 |
