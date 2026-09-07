# Screenshots TODO — leadgen-n8n-system

4 скриншота. Запустить: `docker compose up -d` → http://localhost:5678 → импорт workflow.

---

## 1. Обзор всех 11 workflow в n8n

**Файл:** `docs/screenshots/01-workflows-overview.png`

**Шаги:**
1. Открыть http://localhost:5678
2. Перейти в раздел Workflows
3. Убедиться, что импортированы все 11 workflow
4. Сделать скриншот списка (название, статус)

---

## 2. Workflow 03 — Multi-LLM Consensus

**Файл:** `docs/screenshots/02-multi-llm-consensus.png`

**Шаги:**
1. Открыть workflow `03-multi-llm-consensus`
2. Сделать скриншот Canvas с узлами (видна структура: несколько LLM-узлов → merge → decision)

---

## 3. Workflow 08 — Command Center / архитектура

**Файл:** `docs/screenshots/03-command-center.png`

**Шаги:**
1. Открыть workflow `08-command-center`
2. Сделать скриншот Canvas для демонстрации архитектуры

---

## 4. Тестовый запуск — execution log

**Файл:** `docs/screenshots/04-execution-log.png`

**Шаги:**
1. Открыть любой workflow (например 01)
2. Нажать "Test workflow", отправить mock payload
3. Открыть Executions
4. Сделать скриншот успешного выполнения с деревом шагов
