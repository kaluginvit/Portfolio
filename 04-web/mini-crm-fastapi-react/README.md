# Mini CRM

Внутренняя CRM-система: клиенты, сделки, задачи — с выгрузкой отчётов напрямую в Google Sheets через OAuth.

## Business Problem

Небольшие команды часто ведут клиентскую базу в таблицах. Это работает до момента, когда нужно: связать клиента со сделками, поставить задачи по клиенту, выгрузить отчёт для руководителя не вручную.

CRM закрывает этот gap: связанные сущности, простой интерфейс, кнопка «Выгрузить отчёт» → новая Google Таблица в нужной папке Drive.

## Solution

FastAPI backend + React TypeScript frontend + Google Drive/Sheets OAuth. Единственная команда запуска — `docker compose up --build`.

## Key Features

- CRUD для клиентов, сделок и задач с фильтрацией
- Выгрузка любого раздела в Google Sheets одной кнопкой → ссылка на таблицу
- Google OAuth flow (Web Application credentials)
- SQLite с автоматической инициализацией схемы
- Тестовый seed: 250+ строк через `fill_test_data.py`

## Architecture

```
React (TypeScript) :5173
        │  Vite dev proxy
        ▼
FastAPI :8000
  ├── /clients      CRUD
  ├── /deals        CRUD
  ├── /tasks        CRUD
  ├── /reports      → Google Sheets export
  ├── /auth/google  OAuth flow
  └── /health

SQLite (data/crm.db)
  └── Docker volume → ./data/

Google APIs
  ├── Google Drive API   (create folder, upload)
  └── Google Sheets API  (create spreadsheet, write data)
```

## Tech Stack

| Слой | Технологии |
|------|-----------|
| Backend | FastAPI, Python 3.11+, SQLAlchemy |
| Frontend | React 18, TypeScript, Vite |
| Database | SQLite (docker volume) |
| Integration | Google Drive API v3, Google Sheets API v4, OAuth 2.0 |
| Container | Docker + Docker Compose |

## Project Structure

```
mini-crm-fastapi-react/
├── backend/          # FastAPI
│   ├── routers/      # clients, deals, tasks, reports, auth
│   ├── models.py     # SQLAlchemy models
│   ├── schemas.py    # Pydantic schemas
│   └── main.py
├── frontend/         # React TypeScript
│   └── src/
│       ├── pages/    # Clients, Deals, Tasks, Settings, Reports
│       └── api/      # axios клиент
├── google_integration/
│   ├── oauth_service.py
│   ├── google_drive.py
│   ├── google_sheets.py
│   └── report_generator.py
├── scripts/
│   └── smoke_curl.ps1
├── tests/
│   └── test_api_smoke.py
├── docker-compose.yml
└── SECURITY.md
```

## Quick Start

```bash
# 1. Клонировать, перейти в директорию проекта
git clone <repo-url>
cd mini-crm-fastapi-react

# 2. Backend через Docker
docker compose up --build
# API: http://localhost:8000/docs
# Health: http://localhost:8000/health

# 3. Frontend (отдельный терминал)
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
```

## Configuration

`.env.example` → `.env`:

| Переменная | По умолчанию | Описание |
|-----------|:------------:|---------|
| `DATABASE_URL` | `sqlite:///./data/crm.db` | Путь к SQLite |
| `CORS_ORIGINS` | `http://localhost:5173` | Разрешённые origins |

Google credentials не в `.env` — настраиваются через UI (раздел «Настройки Google»).

## Google Drive Integration Setup

1. В [Google Cloud Console](https://console.cloud.google.com):
   - Включить Google Drive API и Google Sheets API
   - Создать OAuth 2.0 Client ID (тип Web application)
   - Добавить Authorized redirect URI: `http://localhost:8000/auth/google/callback`
   - Скачать JSON с client_id/secret

2. В интерфейсе CRM → **Настройки Google**:
   - Указать путь к JSON файлу
   - Указать ID папки на Google Drive (из URL после `folders/`)
   - Нажать «Войти через Google»

3. `data/google_token.pickle` создаётся автоматически (в `.gitignore`)

Подробнее: `SECURITY.md`

## Demo / Sample Data

```bash
# Заполнить 250+ тестовых записей (при запущенном API)
python fill_test_data.py
```

Количество строк: `CRM_SEED_ROWS` env (по умолчанию 250).

## Screenshots

→ `docs/SCREENSHOTS_TODO.md`

## Tests

```bash
# Smoke тесты API
$env:PYTHONPATH="."
$env:CRM_SKIP_INIT_DB="1"
python -m pytest tests/ -q

# Ручная проверка API
.\scripts\smoke_curl.ps1

# Проверка Google Drive (после OAuth)
python scripts/check_google_drive.py
```

## Engineering Decisions

**SQLite вместо PostgreSQL:** для внутреннего инструмента небольшой команды PostgreSQL избыточен. SQLite в Docker volume с автоматической схемой — проще в поддержке, backup = `cp`.

**OAuth через Web Application (не Service Account):** пользователь явно авторизует доступ к своему Drive/Sheets. Это важно для внутреннего инструмента — не нужно выдавать сервисный аккаунт доступ ко всему Drive.

**Google Sheets вместо email/PDF:** отчёт сразу оказывается в привычном инструменте, доступен для совместного редактирования, сохраняется в Drive.

## Security

Подробно: `SECURITY.md`

- `client_secret.json` и `google_token.pickle` — не коммитятся (`.gitignore`)
- `data/crm.db` — не коммитится
- Только `*.example.json` шаблоны в репозитории

## Reuse / Customization

Тип: **Reusable internal tool**

**Для адаптации под новую предметную область:**
- Добавить сущности в `backend/models.py` и `backend/schemas.py`
- Добавить router в `backend/routers/`
- Добавить страницу в `frontend/src/pages/`
- Google integration остаётся без изменений

## Limitations

- SQLite: один writer, не подходит для >10 одновременных пользователей
- Google OAuth в тестовом режиме GCP: требуется добавить email пользователей в Test Users
- Нет аутентификации пользователей (внутренний инструмент без auth)
- Нет пагинации на больших объёмах данных (>10K записей)

## Roadmap

- JWT auth для multi-user режима
- Pagination + search на больших объёмах
- PostgreSQL backend (замена SQLite коннектора)
- Email-уведомления о задачах (дедлайны)
