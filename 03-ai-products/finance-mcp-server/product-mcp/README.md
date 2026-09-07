# product-mcp

Локальный **MCP-сервер** (Model Context Protocol) для хранения, импорта, выборки и расчётов по финансовым данным компании. Это тонкий **MCP-слой с tools**, без агента и без оркестрации: запрос → валидация → SQLite → ответ в JSON-подобных структурах.

## Что делает сервер

- Поднимает БД **SQLite** и каталоги `data/imports`, `data/exports`.
- При первом запуске создаёт таблицы и загружает **seed-данные** (две компании, P&amp;L / cash flow / balance за 12 месяцев, AR/AP, платежи, остатки ДС, договоры, инвестпроекты).
- Регистрирует **19 MCP tools** (официальный пакет `mcp`, транспорт **stdio**).
- Дублирует имена обработчиков в **Python registry** (`registry.py`) для вызова из будущего orchestration-agent без MCP-транспорта (функция `dispatch`).

## Доступные financial tools

| Tool | Назначение |
|------|------------|
| `health_check` | Статус, путь к БД, список tools, счётчики по таблицам |
| `list_companies` | Список компаний |
| `import_csv` | Импорт CSV в `financial_records` или `budget_records` |
| `import_contract` | Импорт TXT/PDF договора с эвристическим разбором полей |
| `list_financial_records` | Фильтры по типу отчёта, компании, датам, измерениям |
| `list_budget_records` | Бюджет с версией и фильтрами |
| `list_cash_positions` | Остатки на счетах |
| `list_contracts` | Договоры; `active_only` |
| `list_investment_projects` | Инвестиционные проекты |
| `calculate_kpis` | Выручка, OPEX, валовая прибыль, EBITDA, маржа, ДДС, AR/AP, cash |
| `plan_vs_fact` | Бюджет vs факт по категориям |
| `liquidity_forecast` | Простой прогноз ликвидности на N дней |
| `payment_calendar` | Платежи/поступления, `direction`, `overdue` |
| `contract_risk_scan` | Риски по договорам + запись в `alerts` |
| `evaluate_investment` | NPV, IRR, окупаемость, PI, текстовая рекомендация |
| `add_investment_project` | Добавление проекта |
| `find_records` | Поиск по полям финзаписей и договоров |
| `export_report` | Экспорт отчёта в `data/exports/` |
| `calculate` | Безопасный калькулятор (AST, без `eval`) |

JSON-схемы входов/выходов для интроспекции: `schemas.tool_bundles()` или `registry.introspection_json()`.

## Установка

Требуется **Python 3.11+**.

```bash
cd product-mcp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env` при необходимости и задайте `PRODUCT_MCP_DB_PATH` или оставьте путь по умолчанию `data/product_mcp.db`.

## Запуск

Из каталога `product-mcp`:

```bash
python server.py
```

Сервер использует **stdio** (ожидается запуск из MCP-клиента, например Cursor). Логи — в stderr.

Пример фрагмента конфигурации MCP (путь `cwd` замените на свой абсолютный):

```json
{
  "mcpServers": {
    "product-mcp": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "<absolute-path-to>/product-mcp"
    }
  }
}
```

Зависимости **FastAPI** и **uvicorn** включены в `requirements.txt` для совместимости и возможного будущего HTTP-слоя; текущая точка входа — только MCP stdio.

## Проверка seed-данных

После первого запуска или при пустой БД:

1. Вызовите tool **`health_check`** — в `counts_by_table` должны быть ненулевые счётчики.
2. **`list_companies`** — ожидаются `Demo Holdings OÜ` и `Subsidiary LLC`.
3. **`calculate_kpis`** с `period_start=2024-01-01`, `period_end=2024-12-31`, `company_name=Demo Holdings OÜ` — ненулевая выручка и EBITDA.

## Примеры вызова tools (из Python / агента)

Через реестр (без MCP):

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("product-mcp").resolve()))

import registry
registry.dispatch("list_companies", {})
registry.dispatch("calculate_kpis", {
    "period_start": "2024-01-01",
    "period_end": "2024-12-31",
    "company_name": "Demo Holdings OÜ",
})
```

## Пример `import_csv`

CSV должен содержать колонки **даты** (`date`, `record_date`, `period`, …) и **суммы** (`amount`, `value`, …). Опционально: `category`, `company`, `currency`, …

Для типа **`budget`** строки пишутся в `budget_records` (`statement_type='budget'`), версия — через параметр `version` или колонку.

```python
registry.dispatch("import_csv", {
    "file_path": "C:/path/to/data/imports/sample_pnl.csv",
    "statement_type": "pnl",
    "company_name": "Demo Holdings OÜ",
})
```

## Пример `liquidity_forecast`

```python
registry.dispatch("liquidity_forecast", {
    "days": 90,
    "company_name": "Demo Holdings OÜ",
})
```

Ответ: `opening_cash`, суммарные притоки/оттоки за окно, `daily_projection`, `risk_flags`.

## Пример `contract_risk_scan`

```python
registry.dispatch("contract_risk_scan", {})
```

Возвращает списки договоров по категориям риска и создаёт записи в таблице **`alerts`**.

## Пример `evaluate_investment`

Проект с id `1` из seed:

```python
registry.dispatch("evaluate_investment", {"project_id": 1})
```

`scenario_json` в БД задаётся как JSON с ключом **`cash_flows`**: массив денежных потоков по периодам после инвестиции. NPV считается при ставке `discount_rate` (%), IRR — методом бисекции по десятичной ставке.

## Использование как backend для orchestration-agent

1. **Через MCP**: в конфигурации клиента укажите команду `python` и аргумент `server.py` с `cwd` = каталог `product-mcp`. Агент вызывает tools по протоколу MCP.
2. **Через Python**: импортируйте `registry.dispatch(name, arguments)` или вызывайте функции из `tools.*` напрямую; схемы — `schemas.tool_bundles()` для валидации аргументов на стороне оркестратора.
3. Сервер **не** содержит сценариев рассуждения: вся логика — в явных tools и сервисах (`services/`).

## Структура проекта

Соответствует заданной схеме: `server.py`, `config.py`, `db.py`, `models.py`, `schemas.py`, `registry.py`, `seed.py`, `services/`, `tools/`, `utils/`, `data/imports`, `data/exports`.

## Автоматические тесты

Тесты изолированы: отдельная SQLite в `tmp_path`, свои каталоги импорта/экспорта, подмена путей через `monkeypatch` (pytest) или `tests/support/bootstrap.py` (сценарный раннер).

### Установка dev-зависимостей

```bash
cd product-mcp
pip install -r requirements-dev.txt
```

### Запуск pytest

Из каталога `product-mcp` (чтобы сработали `pytest.ini` и `pythonpath`):

```bash
pytest
pytest -q
pytest --maxfail=1
pytest tests/test_startup.py -v
```

Опционально покрытие:

```bash
pytest --cov=. --cov-report=term-missing
```

### Сценарный harness

Последовательные интеграционные проверки без pytest (отдельный временный каталог и БД):

```bash
python scripts/run_scenarios.py
```

Отчёт в машиночитаемом виде: **`test_reports/scenario_report.json`** (timestamp, summary passed/failed, список сценариев, при падении — `error` и `traceback`).

Сценарии: `startup_and_seed`, `registry_integrity`, импорт P&L/бюджета, `calculate_kpis`, `plan_vs_fact`, `liquidity_forecast`, импорт договора + `contract_risk_scan`, добавление и оценка инвестпроекта, негативный `calculate`, `export_report` (JSON на диск).

### Что покрыто автоматически

- Smoke: инициализация БД, seed, `health_check`, `list_companies`.
- Реестр tools: имена, схемы, отсутствие дубликатов в bundles.
- Импорт CSV/договоров, невалидные файлы, контролируемые ошибки.
- KPI, plan vs fact, ликвидность, календарь платежей, договоры и риски, инвестиции, безопасный калькулятор, экспорт отчётов.
- Негативные кейсы: неизвестный tool, неверные параметры, отсутствующие сущности.

### Ограничения текущего набора

- Нет полноценного e2e через MCP stdio-транспорт; проверки идут через `registry.dispatch` и те же обработчики, что и у MCP.
- Subprocess-smoke «запуск `server.py`» не входит в обязательный минимум; при необходимости его можно добавить отдельно.
- Данные и пути полностью тестовые; результаты не гарантируют корректность продакшен-конфигурации.

## Лицензия

Внутренний / учебный проект; при необходимости добавьте свою лицензию.
