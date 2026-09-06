# Finance MCP Server

MCP-сервер с 19 финансовыми инструментами поверх SQLite — подключается к Claude Desktop или Cursor и отвечает на вопросы по P&L, Cash Flow, Balance Sheet, AR/AP, платежам и инвестпроектам без экспорта и скриптов.

## Проблема

Финансист работает с данными в таблицах и хочет задавать по ним вопросы прямо из AI-ассистента: "Какая у нас EBITDA за Q3?", "Какие договоры истекают в этом месяце?", "Посчитай NPV по проекту 2". Стандартный путь — выгрузить CSV, загрузить в ChatGPT, дождаться ответа. Это медленно, небезопасно для данных и не масштабируется.

## Решение

19 MCP-инструментов поверх локального SQLite. Данные не покидают машину. AI-ассистент вызывает tools напрямую — как функции — и получает структурированные JSON-ответы. Никакого экспорта, никаких промежуточных скриптов.

## Возможности

| Tool | Что делает |
|------|------------|
| `calculate_kpis` | Выручка, OPEX, валовая прибыль, EBITDA, маржа, AR/AP, остаток денег за период |
| `plan_vs_fact` | Бюджет vs факт по категориям с отклонениями в абсолюте и % |
| `liquidity_forecast` | Прогноз ликвидности на N дней по остаткам и плановым платежам |
| `payment_calendar` | Плановые платежи и поступления, фильтр по направлению и просрочке |
| `contract_risk_scan` | Автоматическая категоризация рисков по договорам + запись в alerts |
| `evaluate_investment` | NPV, IRR, срок окупаемости, PI с текстовой рекомендацией |
| `export_report` | Выгрузка любого отчёта в JSON/TXT на диск |

Полный список: `health_check`, `list_companies`, `import_csv`, `import_contract`, `list_financial_records`, `list_budget_records`, `list_cash_positions`, `list_contracts`, `list_investment_projects`, `find_records`, `add_investment_project`, `calculate`.

## Быстрый старт

**Требования:** Python 3.11+

```bash
cd product-mcp
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**Подключение к Claude Desktop** — добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "finance-mcp": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "C:/полный/путь/к/product-mcp"
    }
  }
}
```

**Подключение к Cursor** — то же самое в настройках MCP раздела Features.

После подключения спросите: *"Какая EBITDA у Demo Holdings OÜ за 2024 год?"* — сервер вернёт расчёт из seed-данных.

## Проверка после запуска

```python
# Через registry без MCP-транспорта:
import sys
sys.path.insert(0, "product-mcp")
import registry

registry.dispatch("health_check", {})
registry.dispatch("calculate_kpis", {
    "period_start": "2024-01-01",
    "period_end": "2024-12-31",
    "company_name": "Demo Holdings OÜ",
})
```

## Почему MCP + SQLite

**MCP (Model Context Protocol)** — открытый стандарт Anthropic для подключения инструментов к AI-ассистентам (2024). Работает в любом MCP-совместимом клиенте: Claude Desktop, Cursor, Continue, собственный агент. Один раз написал — подключается везде.

**SQLite** — zero-deploy: данные в одном файле, не нужен сервер, не нужна инфраструктура. Идеально для локального финансового агента: конфиденциальные данные не уходят за пределы машины, backup — это `cp`. При необходимости миграция на PostgreSQL — только замена коннектора в `db.py`.

## Структура

```
finance-mcp-server/
├── product-mcp/          # MCP-сервер (Python)
│   ├── server.py         # Точка входа, stdio-транспорт
│   ├── tools/            # 19 MCP tools (тонкий слой над сервисами)
│   ├── services/         # Бизнес-логика: finance, treasury, investment, contract
│   ├── db.py             # SQLite: схема, коннектор, helpers
│   ├── seed.py           # Demo-данные: 2 компании, 12 месяцев P&L/CF/Balance
│   ├── registry.py       # Python-реестр для вызова tools без MCP-транспорта
│   └── tests/            # pytest: smoke, KPI, liquidity, contracts, investments
└── product-mcp-ui/       # Next.js UI (опционально) для визуализации данных
```

## Тесты

```bash
cd product-mcp
pip install -r requirements-dev.txt
pytest -q
```

Покрытие: инициализация БД, seed (idempotency), KPI, plan vs fact, ликвидность, договоры и риски, инвестиционная оценка, безопасный калькулятор, экспорт отчётов, негативные кейсы.
