# Выпускной проект: ИИ-скринер финансовых данных (Вариант C)

## Контекст

Курс «Профессия Вайб-кодер», финальный проект. Выбран вариант C —
«ИИ-разведчик данных». Конкретная реализация: финансовый дата-хаб для российского рынка.
Пользователь вводит запрос на естественном языке («Все акции с объёмом > 1 млрд за сегодня»),
ИИ-планировщик определяет источник и строит запрос, система забирает данные из трёх
открытых российских источников (MOEX ISS / ЦБ РФ / РБК RSS), сохраняет, показывает
витрину с графиками и экспортом. Стек — production-ready с расчётом на реальный деплой.

> **Синергия двух документов:** базовый план (production-стек: PostgreSQL, SQLAlchemy async,
> Alembic, pytest, ruff, mypy, structlog, nginx) + архитектурный документ дата-хаба
> (российские источники MOEX/ЦБ/РБК, коллекторы-паттерн, Recharts, 4 раздела UI).

---

## Ресурсы (нужны ДО старта)

| Ресурс | Где взять | Стоимость | Куда кладём |
|---|---|---|---|
| **ProxyAPI ключ** | proxyapi.ru | платно (≈$2–5 на весь проект) | `.env` → `OPENAI_API_KEY` + `OPENAI_BASE_URL` |
| **Docker Desktop** | docker.com/products/docker-desktop | бесплатно | установить локально |
| **Python 3.12+** | python.org | бесплатно | локально |
| **Node.js 20+** | nodejs.org | бесплатно | локально (для frontend build) |
| **Git + GitHub аккаунт** | github.com | бесплатно | для репозитория |
| **MOEX ISS API** | iss.moex.com/iss | **бесплатно, без ключа** | httpx async-запросы |
| **ЦБ РФ API** | cbr-xml-daily.ru | **бесплатно, без ключа** | httpx async-запросы |
| **РБК RSS** | rbc.ru/v10/finance.rss | **бесплатно, без ключа** | feedparser → normalize |

> Все три источника данных полностью бесплатны, не требуют регистрации и ключей.
> API-ключ нужен только для ProxyAPI (LLM).

---

## Архитектура

```
Browser (React SPA)
       │
       ▼
   nginx :80
       │
       ▼
 FastAPI :8000  ──── PostgreSQL :5432
       │                    │
       │              SQLAlchemy 2.0 (async)
       │              Alembic migrations
       │
       ├── /ai/plan_and_collect ──► ProxyAPI (gpt-4o-mini)
       │                              └── instructor → строгий JSON
       │                                   {source, api_url, fields, filters}
       │
       ├── /datasets/{id}/collect
       │       └── CollectorFactory → BaseCollector
       │               ├── MoexCollector  → iss.moex.com/iss
       │               ├── CbrCollector   → cbr-xml-daily.ru
       │               └── RbcCollector   → rbc.ru RSS → feedparser
       │
       └── audit middleware → audit_runs (каждый запрос)
```

**Docker Compose — 3 сервиса:**
```
postgres:16-alpine  ←→  backend (FastAPI)  ←→  frontend (nginx + React SPA)
```

---

## Технологический стек

### Backend
| Компонент | Технология | Зачем |
|---|---|---|
| Framework | FastAPI 0.115 + Python 3.12 | async, автодока, Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) | type-safe запросы |
| Migrations | Alembic | версионирование схемы |
| DB | PostgreSQL 16 | JSONB для записей, индексы |
| LLM | ProxyAPI → gpt-4o-mini | AI-планирование |
| Structured LLM | instructor 1.x | строгий JSON без лишнего кода |
| HTTP client | httpx (async) | запросы к MOEX, ЦБ РФ |
| RSS parser | feedparser | РБК RSS → нормализация |
| Validation | Pydantic v2 | схемы запросов/ответов |
| Logging | structlog | JSON-логи |
| Config | pydantic-settings | `.env` → typed config |
| **Источник 1** | **MOEX ISS API** | акции, облигации, фьючерсы, индексы |
| **Источник 2** | **ЦБ РФ API** | курсы валют (сегодня + архив) |
| **Источник 3** | **РБК RSS** | финансовые новости |

### Frontend
| Компонент | Технология |
|---|---|
| Framework | React 18 + TypeScript + Vite |
| Стили | Tailwind CSS + shadcn/ui |
| Data fetching | TanStack Query (React Query) |
| Таблицы | TanStack Table v8 (сортировка, фильтрация, пагинация) |
| **Графики** | **Recharts** (LineChart, BarChart, AreaChart) |
| HTTP | axios |
| Экспорт | papaparse (CSV) |

### Инфраструктура
| Компонент | Технология |
|---|---|
| Контейнеры | Docker + Docker Compose (**3 сервиса**: postgres, backend, frontend) |
| Reverse proxy | nginx (в frontend-контейнере) |
| Тесты | pytest + pytest-asyncio + httpx TestClient |
| Линтер | ruff + mypy |
| Pre-commit | pre-commit hooks |

---

## Схема базы данных

```sql
-- Наборы данных (контейнеры для записей)
CREATE TABLE datasets (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    name       TEXT NOT NULL,
    source     TEXT NOT NULL  -- 'moex' | 'cbr' | 'rbc'
);

-- Нормализованные финансовые записи
CREATE TABLE records (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    record_json JSONB NOT NULL
);
CREATE INDEX idx_records_dataset ON records(dataset_id, created_at DESC);

-- Результаты работы ИИ-планировщика
CREATE TABLE agent_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    query        TEXT,
    plan_json    JSONB,
    needs_review BOOLEAN DEFAULT FALSE,
    error        TEXT
);

-- Полный аудит всех операций
CREATE TABLE audit_runs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    action      TEXT NOT NULL,
    input       JSONB,
    output      JSONB,
    status      TEXT,  -- 'success' | 'error'
    error       TEXT,
    duration_ms INTEGER
);
CREATE INDEX idx_audit_action ON audit_runs(action, created_at DESC);
```

---

## ИИ-операция (строгий JSON)

**POST /ai/plan_and_collect**

Запрос: `{ "query": "string" }`

Системный промпт содержит описание трёх источников и их URL-паттернов.
Ответ (строгий JSON через instructor):
```json
{
  "plan_steps": [
    "Определить источник: MOEX",
    "Построить URL для всех акций TQBR",
    "Отфильтровать по VOLTODAY > 1000000000"
  ],
  "source": "moex",
  "api_url": "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json",
  "fields_to_keep": ["SECID", "SHORTNAME", "LAST", "VOLTODAY", "VALTODAY"],
  "filters": {"VOLTODAY": {"gt": 1000000000}},
  "confidence": "high|medium|low",
  "needs_review": false
}
```

**Когда needs_review=true:**
- `confidence="low"` — запрос неоднозначный
- запрос требует источника, которого нет (криптобиржа, закрытые данные)
- запрос слишком общий («покажи самое важное с рынка»)

**Доступные источники для планировщика:**

| source | Что даёт | Пример URL |
|---|---|---|
| `moex` | Акции, облигации, фьючерсы, индексы | `iss.moex.com/iss/engines/stock/...` |
| `cbr` | Курсы валют (сегодня + архив) | `cbr-xml-daily.ru/daily_json.js` |
| `rbc` | Финансовые новости (RSS) | `rbc.ru/v10/finance.rss` |

---

## 14 шагов (каждый — с вашим одобрением)

### Шаг 0 — Подготовка окружения
**Что делаем:** Инициализация git-репозитория в папке проекта. Чеклист установки всего необходимого. Проверяем ProxyAPI ключ. Создаём GitHub-репозиторий и делаем первый коммит.
**Результат:** `git init` выполнен, `.gitignore` создан, `docker --version` / `python --version` / `node --version` работают. Репозиторий на GitHub привязан. `.env.example` готов.
**Команды:**
```bash
git init "C:\_Рабочая_папка\ZeroCoder\Обучение\Профессия_Вайб-кодер\Итоговый проект"
# создать репозиторий на GitHub
git remote add origin https://github.com/<username>/<repo>.git
```
**Файлы:** `.gitignore`, `.env.example`
**Токены:** ~2K (только проверка и команды)

---

### Шаг 1 — Структура проекта + Docker Compose
**Что делаем:** Создаём каркас директорий, `docker-compose.yml` (app + postgres + redis + celery-worker + nginx), базовый `Dockerfile`.
**Результат:** `docker compose up` поднимает 5 сервисов. PostgreSQL и Redis доступны.
**Файлы:**
```
docker-compose.yml
Dockerfile
nginx/nginx.conf
backend/
  pyproject.toml
  app/__init__.py
  app/main.py (skeleton)
  app/core/config.py
  app/core/database.py
frontend/
  package.json (vite + react + ts)
```
**Токены:** ~15K

---

### Шаг 2 — База данных: модели + миграции
**Что делаем:** SQLAlchemy 2.0 async модели для всех 4 таблиц. Alembic init + первая миграция.
**Результат:** `alembic upgrade head` создаёт таблицы. CRUD-функции для всех моделей.
**Файлы:**
```
backend/app/models/dataset.py
backend/app/models/record.py
backend/app/models/agent_run.py
backend/app/models/audit_run.py
backend/app/crud/datasets.py
backend/app/crud/records.py
backend/app/crud/audit.py
migrations/versions/001_initial.py
```
**Токены:** ~20K

---

### Шаг 3 — Коллекторы данных (MOEX + ЦБ РФ + РБК)
**Что делаем:** Паттерн `BaseCollector ABC` + три конкретных коллектора. Каждый умеет принять `api_url` и `fields_to_keep` из ИИ-плана и вернуть нормализованный список записей.
**Результат:**
- `MoexCollector.collect(api_url, fields)` → список акций/облигаций/фьючерсов
- `CbrCollector.collect()` → курсы валют
- `RbcCollector.collect()` → финансовые новости из RSS
- `CollectorFactory.get(source)` → нужный коллектор по строке `'moex'|'cbr'|'rbc'`
**Файлы:**
```
backend/app/collectors/base.py       # BaseCollector ABC
backend/app/collectors/moex.py       # MOEX ISS API
backend/app/collectors/cbr.py        # ЦБ РФ API
backend/app/collectors/rbc.py        # РБК RSS + feedparser
backend/app/collectors/factory.py    # CollectorFactory
backend/app/schemas/finance.py       # нормализованная схема записи
tests/collectors/test_moex.py
tests/collectors/test_cbr.py
tests/collectors/test_rbc.py
```
**Токены:** ~22K

---

### Шаг 4 — LLM-сервис (ProxyAPI + instructor + строгий JSON)
**Что делаем:** Клиент ProxyAPI через OpenAI SDK (base_url). Сервис `AIPlanner` с instructor для строгого JSON. Логика `needs_review`. Запись в `agent_runs`.
**Результат:** `POST /ai/plan_and_collect` возвращает строгий JSON по схеме. Двусмысленный запрос → `needs_review=true` + причина в `agent_runs.error`.
**Файлы:**
```
backend/app/services/ai_planner.py
backend/app/schemas/ai_plan.py  (Pydantic модель для instructor)
backend/app/api/routes/ai.py
tests/services/test_ai_planner.py
```
**Токены:** ~22K

---

### Шаг 5 — FastAPI: все эндпоинты + audit middleware
**Что делаем:** Все 4 эндпоинта по ТЗ + middleware, который пишет каждый запрос в `audit_runs` с `duration_ms`.
**Результат:** Swagger UI на `/docs` показывает все эндпоинты. Каждый вызов пишет в `audit_runs`.
**Эндпоинты:**
```
POST   /datasets                      → создать набор данных
POST   /ai/plan_and_collect           → ИИ-планирование
POST   /datasets/{id}/collect         → запустить сбор
GET    /datasets/{id}/records?limit=  → витрина
GET    /datasets                      → список наборов
GET    /audit                         → последние 100 аудит-записей
```
**Файлы:**
```
backend/app/api/routes/datasets.py
backend/app/api/routes/records.py
backend/app/api/routes/audit.py
backend/app/api/middleware/audit.py
backend/app/api/deps.py
backend/app/main.py (финальный)
tests/api/test_datasets.py
tests/api/test_collect.py
```
**Токены:** ~30K

---

### Шаг 6 — Структура проекта + финальная сборка backend
**Что делаем:** Связываем все роутеры в `main.py`, настраиваем CORS, lifespan (создание таблиц при старте). Проверяем, что `docker-compose up` поднимает все 3 сервиса и Swagger UI доступен на `/docs`.
**Результат:** Полностью рабочий backend — все 6 эндпоинтов отвечают, audit middleware пишет каждый запрос, коллекторы реально тянут данные с MOEX/ЦБ/РБК.
**Файлы:**
```
backend/app/main.py  (финальный: lifespan, CORS, all routers)
docker-compose.yml   (3 сервиса: postgres, backend, frontend-stub)
```
**Токены:** ~12K

---

### Шаг 7 — Frontend: Раздел 1 «Наборы данных»
**Что делаем:** Карточки датасетов с бейджем источника (MOEX / ЦБ РФ / РБК), количеством записей, датой обновления. Модальное окно создания (name + source dropdown).
**Результат:** Можно создать набор с указанием источника; карточки сразу обновляются.
**Файлы:**
```
frontend/src/pages/DatasetsPage.tsx
frontend/src/components/DatasetList.tsx   # карточки с бейджами
frontend/src/components/CreateDatasetModal.tsx
frontend/src/api/datasets.ts
```
**Токены:** ~18K

---

### Шаг 8 — Frontend: Раздел 2 «Сбор» + ReviewBanner
**Что делаем:** Выбор активного датасета → textarea запроса → кнопки «Спланировать» (показывает `PlanPreview`) и «Собрать». `ReviewBanner` при `needs_review=true`: причина + 3 подсказки как уточнить запрос + кнопка «Собрать» заблокирована.
**Результат:** При двусмысленном запросе пользователь видит конкретные рекомендации, а не просто ошибку.
**Файлы:**
```
frontend/src/pages/CollectPage.tsx
frontend/src/components/CollectPanel.tsx
frontend/src/components/PlanPreview.tsx   # шаги, URL, поля из ИИ-плана
frontend/src/components/ReviewBanner.tsx  # needs_review UI
```
**Токены:** ~20K

---

### Шаг 9 — Frontend: Раздел 3 «Витрина» + графики + экспорт
**Что делаем:** TanStack Table с сортировкой/фильтрацией/пагинацией. Переключатель «Таблица / График» — Recharts (LineChart для курсов/временных рядов, BarChart для объёмов). Кнопки «Скачать JSON» и «Скачать CSV». Развернуть строку → полный `record_json`.
**Результат:** Финансовые данные визуализируются как таблица и как график; экспорт одним кликом.
**Файлы:**
```
frontend/src/pages/VitrinaPage.tsx
frontend/src/components/Vitrina.tsx       # TanStack Table
frontend/src/components/FinanceChart.tsx  # Recharts LineChart/BarChart
frontend/src/components/RecordModal.tsx
frontend/src/components/ExportButtons.tsx
frontend/src/utils/export.ts
```
**Токены:** ~24K

---

### Шаг 9б — Frontend: Раздел 4 «Журнал»
**Что делаем:** Timeline последних 100 операций из `audit_runs`. Фильтр по `status=error` и `action`. Цветовые бейджи: зелёный (success) / красный (error) / жёлтый (needs_review). Развернуть запись → вход / выход / ошибка / время выполнения.
**Результат:** Полная прозрачность — пользователь видит каждое действие системы.
**Файлы:**
```
frontend/src/pages/AuditPage.tsx
frontend/src/components/AuditLog.tsx
frontend/src/components/AuditBadge.tsx
```
**Токены:** ~14K

---

### Шаг 10 — Тестовые данные (10 запросов по ТЗ)
**Что делаем:** Файл `tests_data/queries.jsonl` с 10 запросами по российскому рынку: **7 корректных / 2 двусмысленных / 1 невыполнимый**. README-таблица с ожиданиями.

**Формат каждой строки** (точно по ТЗ):
```jsonl
{"dataset_name":"demo","query":"...","expected_needs_review":false,"why":"..."}
```

**Состав (7 / 2 / 1):**
```
1. {"dataset_name":"demo","query":"Все акции первого котировального списка MOEX","expected_needs_review":false,"why":"Чёткий запрос, известный endpoint MOEX"}
2. {"dataset_name":"demo","query":"История SBER за последние 30 дней","expected_needs_review":false,"why":"Тикер и период указаны явно"}
3. {"dataset_name":"demo","query":"Все ОФЗ с доходностью выше 15%","expected_needs_review":false,"why":"Тип инструмента и фильтр заданы"}
4. {"dataset_name":"demo","query":"Фьючерсы на нефть","expected_needs_review":false,"why":"Класс инструмента определён однозначно"}
5. {"dataset_name":"demo","query":"Топ-10 акций по объёму торгов сегодня","expected_needs_review":false,"why":"MOEX, сортировка по VOLTODAY, limit 10"}
6. {"dataset_name":"demo","query":"Курс доллара, евро и юаня на сегодня","expected_needs_review":false,"why":"ЦБ РФ, три валюты, дата = сегодня"}
7. {"dataset_name":"demo","query":"Последние финансовые новости РБК","expected_needs_review":false,"why":"РБК RSS, без фильтров — собрать ленту"}
8. {"dataset_name":"demo","query":"Покажи самое важное с рынка","expected_needs_review":true,"why":"Двусмысленный: нет критерия важности"}
9. {"dataset_name":"demo","query":"Собери данные по рынку и сделай вывод","expected_needs_review":true,"why":"Двусмысленный: нет конкретного объекта и действия"}
10. {"dataset_name":"demo","query":"Собери закрытую статистику всех брокеров за год","expected_needs_review":true,"why":"Невыполнимый: данных нет в открытых источниках"}
```

**README-таблица тестов** (обязательна по ТЗ):
| № | query | expected_needs_review | почему | что считается успехом |
|---|---|---|---|---|
| 1–7 | см. выше | false | запрос конкретный | данные сохранены в records |
| 8–9 | см. выше | true | двусмысленный | needs_review=true, сбор не запущен |
| 10 | см. выше | true | невыполнимый | needs_review=true, причина в аудите |

**Файлы:**
```
tests_data/queries.jsonl
tests_data/README_tests.md
```
**Токены:** ~8K

---

### Шаг 11 — pytest: тестовое покрытие
**Что делаем:** Автоматические тесты по критериям приёмки из ТЗ. Конфигурация `conftest.py` с тестовой БД.
**Покрытие:**
- `test_create_dataset` — POST /datasets возвращает dataset_id
- `test_collect_saves_records` — сбор сохраняет записи, GET /records показывает их
- `test_ambiguous_query_needs_review` — 2+ запроса → needs_review=true
- `test_collect_blocked_on_review` — при needs_review сбор не запускается
- `test_export_json` — экспорт возвращает валидный JSON
- `test_audit_runs_created` — 10+ запусков в audit_runs
**Файлы:**
```
tests/conftest.py
tests/api/test_datasets.py
tests/api/test_collect.py
tests/api/test_ai.py
tests/api/test_export.py
tests/api/test_audit.py
```
**Токены:** ~25K

---

### Шаг 12 — Docker production + README
**Что делаем:** Production `Dockerfile` (multi-stage build), финальный `docker-compose.yml`, `nginx.conf`, `.env.example`. README с инструкцией запуска ≤ 10 минут.
**README содержит (точно по ТЗ):**
- Быстрый старт (5 команд, запуск ≤ 10 минут)
- Описание переменных окружения
- curl-примеры: `POST /datasets`, `POST /ai/plan_and_collect`, `POST /datasets/{id}/collect`
- **Где лежит БД и как посмотреть данные/аудит** (путь к файлу SQLite или `docker exec` для PostgreSQL)
- **Как воспроизвести ручную проверку**: конкретный тест (запрос №8 или №9 из queries.jsonl) + ожидаемый результат
- Таблица тестов: № → query → expected_needs_review → почему → что считается успехом
- Мини-экономика: до/после (время + стоимость 100 операций)
**Файлы:**
```
Dockerfile (multi-stage: builder + runtime)
docker-compose.yml (production)
docker-compose.dev.yml (dev с hot reload)
nginx/nginx.conf
.env.example
README.md
```
**Токены:** ~15K

---

### Шаг 13 — Демо-материалы + отчёт
**Что делаем:** Заполненный отчёт по шаблону курса. Сценарий демо-видео. Сценарий защиты 5–7 минут.

**Сценарий демо-видео (2–4 мин) — обязательные 4 блока по ТЗ:**
1. **Успешный сценарий**: создать датасет → ввести корректный запрос → собрать данные → показать `records_saved`
2. **Ручная проверка**: ввести запрос №8 ("Покажи самое важное с рынка") → показать ReviewBanner с причиной + заблокированную кнопку "Собрать"
3. **Витрина данных**: открыть раздел "Витрина" → таблица с записями → развернуть одну запись → полный `record_json`
4. **Экспорт**: нажать "Скачать JSON" (и/или CSV) → файл скачался

**Шаблон отчёта** (все поля из ТЗ):
- Название, ценность, 3 сценария, точки доступа API, схема данных
- ИИ-операция: схема JSON + температура + когда needs_review
- Контроль качества: что валидируется на входе/выходе
- План внедрения за 1 день
- Мини-экономика (время до/после + стоимость 100 операций)
- Риски и меры снижения (минимум 5)
- 3 строки для портфолио (проблема/решение/результат)
- Сложности и как решал(а), план развития

**Файлы:**
```
docs/report.md        (отчёт по шаблону курса)
docs/demo_script.md   (сценарий демо-видео 2–4 мин)
docs/defense.md       (тезисы защиты 5–7 мин)
```
**Токены:** ~10K

---

## Итого по ресурсам

### Что нужно сделать ДО первого шага

| # | Действие | Ссылка |
|---|---|---|
| 1 | Получить ProxyAPI ключ | proxyapi.ru |
| 2 | Установить Docker Desktop | docker.com |
| 3 | Установить Python 3.12 | python.org |
| 4 | Установить Node.js 20 LTS | nodejs.org |
| 5 | Создать репозиторий на GitHub | github.com |
| 6 | Установить Git | git-scm.com |

### Переменные окружения (`.env.example`)
```env
# LLM (ProxyAPI — OpenAI-совместимый)
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
LLM_MODEL=gpt-4o-mini

# База данных
POSTGRES_USER=datahub
POSTGRES_PASSWORD=datahub_secret
POSTGRES_DB=datahub
DATABASE_URL=postgresql+asyncpg://datahub:datahub_secret@postgres:5432/datahub

# Приложение
APP_ENV=production
SECRET_KEY=change_me_in_production

# Источники данных (ключи не нужны — все открытые)
MOEX_BASE_URL=https://iss.moex.com/iss
CBR_BASE_URL=https://www.cbr-xml-daily.ru
RBC_RSS_URL=https://rbc.ru/v10/finance.rss
```

---

## Оценка затрат токенов

### Claude Code (claude-sonnet-4-6) — сессии написания кода

| Шаг | ~Input токены | ~Output токены | ~Стоимость ($) |
|---|---|---|---|
| 0 — Подготовка | 3K | 1K | $0.02 |
| 1 — Docker + scaffold | 8K | 5K | $0.10 |
| 2 — БД + миграции | 12K | 8K | $0.16 |
| 3 — Коллекторы MOEX/ЦБ/РБК | 10K | 8K | $0.16 |
| 4 — LLM-сервис | 15K | 10K | $0.22 |
| 5 — FastAPI эндпоинты | 20K | 12K | $0.30 |
| 6 — Финальная сборка backend | 12K | 8K | $0.16 |
| 7 — Frontend раздел 1 | 12K | 10K | $0.21 |
| 8 — Frontend раздел 2 | 14K | 10K | $0.23 |
| 9 — Frontend раздел 3 | 14K | 10K | $0.23 |
| 10 — Тестовые данные | 5K | 3K | $0.07 |
| 11 — pytest | 18K | 12K | $0.27 |
| 12 — Docker + README | 10K | 8K | $0.18 |
| 13 — Документация | 8K | 5K | $0.13 |
| **ИТОГО** | **~161K** | **~110K** | **~$2.44** |

> Цены: claude-sonnet-4-6 = $3/1M input, $15/1M output

### ProxyAPI (gpt-4o-mini) — реальные вызовы LLM в приложении

| Использование | Кол-во запросов | ~Стоимость |
|---|---|---|
| Тестирование 10 запросов × 5 итераций | 50 | ~$0.02 |
| Отладка и разработка | ~100 | ~$0.04 |
| Демо + финальные прогоны | ~50 | ~$0.02 |
| **ИТОГО ProxyAPI** | **~200** | **~$0.08** |

### Суммарно
| Статья | Сумма |
|---|---|
| Claude Code (разработка) | ~$2.44 |
| ProxyAPI (работа приложения) | ~$0.08 |
| **Итого** | **~$2.52** |

> Возможны отклонения ±50% в зависимости от количества правок и итераций.

---

## Критерии приёмки (из ТЗ) — чеклист

**API:**
- [ ] `POST /datasets` создаёт набор и возвращает `dataset_id`
- [ ] `POST /datasets/{id}/collect` сохраняет записи в `records` (MOEX / ЦБ РФ / РБК)
- [ ] `GET /datasets/{id}/records` показывает витрину
- [ ] `POST /ai/plan_and_collect` возвращает строгий JSON по схеме (с полем `source`)
- [ ] 2+ запроса приводят к `needs_review=true` и сбор не запускается автоматически

**Frontend:**
- [ ] Раздел 1: карточки датасетов с бейджем источника
- [ ] Раздел 2: ReviewBanner при `needs_review=true`, кнопка заблокирована
- [ ] Раздел 3: таблица + переключатель «График» (Recharts) + экспорт JSON/CSV
- [ ] Раздел 4: журнал аудита с цветовыми бейджами

**Данные и качество:**
- [ ] Реально работает сбор с MOEX ISS API
- [ ] Реально работает сбор с ЦБ РФ API
- [ ] Реально работает сбор с РБК RSS
- [ ] В `audit_runs` видно 10+ запусков и причины ручной проверки
- [ ] 10 тестовых запросов в `tests_data/queries.jsonl`

**Упаковка:**
- [ ] `docker-compose up` поднимает 3 сервиса с нуля
- [ ] README: запуск ≤ 10 минут
- [ ] `.env.example` без секретов

**Сдача:**
- [ ] Демо-видео 2–4 мин
- [ ] Защита 5–7 мин (видео)
- [ ] Заполненный отчёт по шаблону курса
