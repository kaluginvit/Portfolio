# Finance MCP Server

MCP-сервер с 19 финансовыми инструментами поверх SQLite. Подключается к Claude Desktop или Cursor и отвечает на вопросы по P&L, Cash Flow, Balance Sheet, ликвидности, договорам и инвестпроектам — без экспорта CSV, без промежуточных скриптов.

**Live demo:** спросите у Claude Desktop: *«Какая EBITDA у Demo Holdings OÜ за 2024 год?»* — ответ придёт из локальной БД.

## Business Problem

Финансист работает с данными в таблицах и хочет задавать по ним вопросы прямо из AI-ассистента. Стандартный путь: выгрузить CSV → загрузить в ChatGPT → ждать ответа. Это медленно, небезопасно для данных и не масштабируется.

**С этим сервером:** AI-ассистент вызывает инструменты напрямую как функции. Данные никуда не уходят — вся база локальная.

## Solution

19 MCP tools поверх SQLite-базы с готовыми финансовыми расчётами. Сервер подключается к Claude Desktop или Cursor через стандарт MCP (Anthropic, 2024). Первый запуск автоматически создаёт демо-данные: 2 компании, 12 месяцев P&L / Cash Flow / Balance Sheet, платежи, договоры, инвестпроекты.

## Key Features

| Tool | Что делает |
|------|------------|
| `calculate_kpis` | Выручка, OPEX, валовая прибыль, EBITDA, маржа, AR/AP, cash-остаток за период |
| `plan_vs_fact` | Бюджет vs факт по категориям с отклонениями в рублях и % |
| `liquidity_forecast` | Прогноз ликвидности на N дней по остаткам и плановым платежам |
| `payment_calendar` | Плановые платежи/поступления, фильтр по направлению и просрочке |
| `contract_risk_scan` | Автоматическая категоризация рисков по договорам + запись в alerts |
| `evaluate_investment` | NPV, IRR, срок окупаемости, PI с текстовой рекомендацией |
| `export_report` | Выгрузка любого отчёта в JSON/TXT на диск |
| + 12 others | `health_check`, `list_companies`, `import_csv`, `import_contract`, `find_records`, `calculate`, ... |

## Architecture

```
┌──────────────────────┐
│  Claude Desktop /    │
│  Cursor (MCP client) │
└──────────┬───────────┘
           │ MCP stdio transport
           ▼
┌──────────────────────────────┐
│  server.py  (stdio entry)    │
│  ┌──────────────────────┐    │
│  │  Registry — 19 tools │    │
│  └─────────┬────────────┘    │
│  ┌─────────▼────────────┐    │
│  │     Services         │    │
│  │  finance / treasury  │    │
│  │  investment / contract│   │
│  │  reporting           │    │
│  └─────────┬────────────┘    │
│  ┌─────────▼────────────┐    │
│  │  db.py  —  SQLite    │    │
│  └──────────────────────┘    │
└──────────────────────────────┘
           │ optional
           ▼
┌──────────────────────┐
│  product-mcp-ui/     │
│  Next.js dashboard   │
└──────────────────────┘
```

**Registry pattern:** все tools доступны через `registry.dispatch(name, args)` без MCP-транспорта — это позволяет тестировать логику изолированно и вызывать инструменты из Python-кода/агентов.

## Tech Stack

| Компонент | Технология |
|-----------|-----------|
| Runtime | Python 3.11+ |
| MCP | `mcp` (официальный пакет Anthropic), stdio transport |
| База данных | SQLite (локальная, zero-deploy) |
| Schemas/models | Pydantic |
| Tests | pytest |
| Optional UI | Next.js (product-mcp-ui/) |

## Business / Domain Logic

Сервер реализует финансовые расчёты уровня управленческого учёта:

**P&L:** `revenue − cogs = gross_profit → gross_margin%; revenue − opex = ebitda → ebitda_margin%`

**Liquidity forecast:** `cash_today + Σ(inflows) − Σ(outflows) = projected_cash`; `risk_flag` при отрицательном балансе на горизонте.

**Investment evaluation:** NPV через дисконтирование денежных потоков; IRR методом бисекции; `PI = NPV / investment + 1`; `payback_period` в месяцах.

**Contract risk scan:** классификация по `expiry_days`, `amount`, `counterparty_type` → риски `critical / high / medium / low`; результат пишется в `alerts`.

**Safe calculator:** математические выражения через AST без `eval` — безопасно для production.

## Project Structure

```
finance-mcp-server/
├── product-mcp/          # MCP-сервер (Python) — основное
│   ├── server.py         # Точка входа, stdio-транспорт
│   ├── registry.py       # Реестр: вызов tools без MCP (для тестов/агентов)
│   ├── tools/            # 19 MCP tools (тонкий слой над сервисами)
│   ├── services/         # Бизнес-логика: finance, treasury, investment, contract, reporting
│   ├── db.py             # SQLite: схема, коннектор, helpers
│   ├── seed.py           # Demo-данные: 2 компании, 12 месяцев истории
│   ├── models.py         # Pydantic модели
│   ├── schemas.py        # JSON-схемы tools для интроспекции
│   ├── tests/            # pytest — покрытие бизнес-логики
│   └── scripts/
│       └── run_scenarios.py  # Интеграционный harness без pytest
└── product-mcp-ui/       # Next.js dashboard (опционально)
    ├── src/              # React + TypeScript
    └── ...
```

## Quick Start

**Требования:** Python 3.11+

```bash
cd product-mcp
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

**Проверка (без MCP-клиента):**

```python
import sys
sys.path.insert(0, "product-mcp")
import registry

# Здоровье сервера
print(registry.dispatch("health_check", {}))

# EBITDA за 2024 год
print(registry.dispatch("calculate_kpis", {
    "period_start": "2024-01-01",
    "period_end": "2024-12-31",
    "company_name": "Demo Holdings OÜ",
}))
```

## Configuration

**MCP-подключение к Claude Desktop** — добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "finance-mcp": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "<absolute-path-to>/product-mcp"
    }
  }
}
```

Замените `<absolute-path-to>` на реальный путь к папке `product-mcp`. Файл конфига:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Cursor:** те же настройки в Features → MCP.

**Env variables** (опционально, `.env.example` в `product-mcp/`):

| Переменная | По умолчанию | Описание |
|-----------|:------------:|---------|
| `PRODUCT_MCP_DB_PATH` | `data/product_mcp.db` | Путь к SQLite-файлу |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

## Demo / Sample Data

Seed-данные создаются автоматически при первом запуске:

- **Demo Holdings OÜ** — основная компания: P&L, Cash Flow, Balance за 12 мес 2024
- **Subsidiary LLC** — дочерняя структура
- Договоры с разными уровнями риска, инвестпроекты, платёжный календарь

**Попробуйте спросить у Claude Desktop:**
- *«Какая маржа EBITDA у Demo Holdings в Q3 2024?»*
- *«Какие договоры истекают в ближайший месяц?»*
- *«Оцени инвестпроект 1: NPV и IRR»*
- *«Прогноз ликвидности на 30 дней»*
- *«Сравни бюджет и факт по категориям за год»*

**Импорт собственных данных** через `import_csv`:
```python
registry.dispatch("import_csv", {
    "file_path": "/path/to/your/pnl.csv",
    "statement_type": "pnl",
    "company_name": "Your Company",
})
```

## Screenshots

→ `docs/SCREENSHOTS_TODO.md`

## Tests

```bash
cd product-mcp
pip install -r requirements-dev.txt
pytest -q
```

Покрытие: инициализация БД, seed (idempotency), KPI, plan vs fact, ликвидность, договоры и риски, инвестиционная оценка, безопасный калькулятор, экспорт отчётов, негативные кейсы.

**Интеграционный сценарный harness** (без pytest):
```bash
python scripts/run_scenarios.py
```

## Engineering Decisions

**SQLite вместо PostgreSQL:** данные финансиста конфиденциальны, должны оставаться на машине. SQLite — zero-deploy: база = один файл, backup — это `cp`. При необходимости миграция на PostgreSQL: только замена коннектора в `db.py`.

**Registry pattern:** все tools доступны через `registry.dispatch(name, args)` без MCP stdio. Это даёт: 1) тестирование без mock MCP-клиента; 2) вызов из Python-агентов без MCP-транспорта; 3) инструменты остаются чистыми функциями.

**Thin MCP layer:** server.py и tools/ — тонкая оболочка над services/. Вся бизнес-логика в services/, не в MCP-обработчиках. Это позволяет переиспользовать сервисы независимо от транспорта.

**MCP Protocol** (Anthropic, 2024): один раз написал — подключается в Claude Desktop, Cursor, Continue и любой MCP-совместимый клиент.

## Security / Privacy

- Данные остаются локально — SQLite-файл на вашей машине, ни один байт не уходит в cloud
- Конфигурация через `.env` — никаких ключей в коде
- Safe calculator использует AST, не `eval` — нет code injection

## Reuse / Customization

Тип: **Reusable internal tool**

**Для нового пользователя/клиента:**
1. `cd product-mcp && pip install -r requirements.txt`
2. Добавить в конфиг MCP-клиента с нужным `cwd`
3. Загрузить свои данные через `import_csv` или изменить `seed.py`

**Чтобы добавить новую компанию:** использовать `import_csv` с `company_name` своей компании.

**Чтобы заменить seed-данные:** отредактировать `product-mcp/seed.py` — определены константы с датами и суммами.

**Optional UI** (`product-mcp-ui/`): отдельное Next.js-приложение для визуализации данных из той же SQLite-базы. Запускается независимо от MCP-сервера, читает данные напрямую через API.

## Limitations

- Нет multi-user: база одного пользователя, одного файла
- Нет auth: если MCP-клиент имеет доступ, он имеет доступ ко всем данным
- Импорт CSV: требует соответствия колонок ожидаемой схеме (date, amount, category, company)
- LLM-зависимость: качество ответов определяется тем MCP-клиентом, с которым работаете
- Нет e2e теста через MCP stdio-транспорт (тесты идут через registry.dispatch)

## Roadmap

- PostgreSQL backend (замена коннектора в db.py)
- Multi-company import из корпоративных систем (1С, SAP CSV exports)
- Budgeting module: ввод планов прямо через MCP tools
- Auth layer для network deployment
