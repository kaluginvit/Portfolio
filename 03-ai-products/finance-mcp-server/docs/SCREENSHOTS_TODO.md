# Screenshots TODO — finance-mcp-server

Необходимо сделать 3-4 скриншота для README.

---

## 1. Claude Desktop: вопрос → ответ MCP

**Файл:** `docs/screenshots/01-claude-kpi-query.png`

**Шаги:**
1. Запустить сервер: `cd product-mcp && python server.py`
2. Открыть Claude Desktop с настроенным MCP
3. Задать вопрос: *«Какая EBITDA у Demo Holdings OÜ за 2024 год?»*
4. Сделать скриншот: окно Claude Desktop с ответом, включая вызов tool `calculate_kpis`

---

## 2. Список доступных инструментов

**Файл:** `docs/screenshots/02-tools-list.png`

**Шаги:**
1. В Claude Desktop нажать иконку инструментов / спросить: *«Какие финансовые инструменты у тебя есть?»*
2. Сделать скриншот со списком 19 tools и их описаниями

---

## 3. Plan vs Fact сравнение

**Файл:** `docs/screenshots/03-plan-vs-fact.png`

**Шаги:**
1. Задать вопрос: *«Покажи отклонение бюджет/факт за 2024 год»*
2. Сделать скриншот с ответом `plan_vs_fact`

---

## 4. Cursor MCP integration (опционально)

**Файл:** `docs/screenshots/04-cursor-mcp.png`

**Шаги:**
1. Открыть Cursor с настроенным MCP
2. В чате задать финансовый вопрос
3. Сделать скриншот
