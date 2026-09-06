# ТЗ — ИИ-скринер финансовых данных

## Что строим

Пользователь вводит запрос на русском языке — например, «Все акции с объёмом > 1 млрд за сегодня». LLM разбирает запрос, определяет источник и строит URL. Система забирает данные, сохраняет и показывает витрину с графиками и экспортом.

## Источники данных (все бесплатные, без ключей)

| Источник | Что даёт | URL |
|---|---|---|
| MOEX ISS API | Акции, облигации, фьючерсы, индексы | iss.moex.com/iss |
| ЦБ РФ API | Курсы валют (сегодня + архив) | cbr-xml-daily.ru |
| РБК RSS | Финансовые новости | rbc.ru/v10/finance.rss |

## Стек

**Backend:** FastAPI 0.115 + Python 3.12 + SQLAlchemy 2.0 async + Alembic + PostgreSQL 16
**Frontend:** React 18 + TypeScript + Vite + Tailwind + shadcn/ui + Recharts + TanStack Table
**LLM:** gpt-4o-mini через ProxyAPI (base_url: api.proxyapi.ru) + instructor для строгого JSON
**Инфра:** Docker Compose — 3 сервиса (postgres, backend, frontend+nginx)

## Архитектура

```
Browser (React SPA)
       │
   nginx :80
       │
 FastAPI :8000 ──── PostgreSQL :5432
       │
       ├── POST /ai/plan_and_collect ──► ProxyAPI (gpt-4o-mini + instructor)
       │                                  └── {source, api_url, fields, filters, needs_review}
       │
       ├── POST /datasets/{id}/collect
       │       └── CollectorFactory → MoexCollector | CbrCollector | RbcCollector
       │
       └── audit middleware → audit_runs (каждый запрос логируется)
```

## База данных (4 таблицы)

- `datasets` — контейнеры для наборов данных
- `records` — нормализованные финансовые записи (JSONB)
- `agent_runs` — результаты работы LLM-планировщика
- `audit_runs` — полный аудит всех операций

## LLM-ответ (строгий JSON через instructor)

```json
{
  "source": "moex",
  "api_url": "https://iss.moex.com/iss/...",
  "fields_to_keep": ["SECID", "LAST", "VOLTODAY"],
  "filters": {"VOLTODAY": {"gt": 1000000000}},
  "confidence": "high",
  "needs_review": false,
  "plan_steps": ["..."]
}
```

`needs_review=true` → сбор не запускается, пользователю показывается причина.

## 4 раздела UI

1. **Наборы данных** — карточки с бейджем источника, дата, кол-во записей
2. **Сбор** — textarea запроса + PlanPreview + ReviewBanner при needs_review
3. **Витрина** — таблица + график (Recharts) + экспорт JSON/CSV
4. **Журнал** — timeline audit_runs с цветовыми бейджами

## Критерии сдачи

- `docker-compose up` поднимает всё с нуля, запуск ≤ 10 минут
- 10 тестовых запросов (7 корректных / 2 двусмысленных / 1 невыполнимый)
- pytest покрывает все API-эндпоинты
- Демо-видео 2–4 мин + защита 5–7 мин
