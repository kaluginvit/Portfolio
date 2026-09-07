# Screenshots TODO — mini-crm-fastapi-react

4 скриншота. Запустить: `docker compose up --build` + `cd frontend && npm run dev`

---

## 1. Список клиентов

**Файл:** `docs/screenshots/01-clients-list.png`

**Шаги:**
1. Запустить: `python fill_test_data.py`
2. Открыть http://localhost:5173
3. Перейти в «Клиенты»
4. Сделать скриншот таблицы с данными (имя, email, статус, дата)

---

## 2. Список сделок / задач

**Файл:** `docs/screenshots/02-deals-tasks.png`

**Шаги:**
1. Перейти в «Сделки» или «Задачи»
2. Сделать скриншот таблицы

---

## 3. Swagger / API docs

**Файл:** `docs/screenshots/03-swagger.png`

**Шаги:**
1. Открыть http://localhost:8000/docs
2. Сделать скриншот SwaggerUI со списком эндпоинтов

---

## 4. Выгрузка в Google Sheets (после OAuth)

**Файл:** `docs/screenshots/04-google-sheets-export.png`

**Шаги:**
1. Настроить Google OAuth (см. README)
2. Нажать «Выгрузить отчёт» в разделе Клиенты
3. Сделать скриншот с открытой Google Таблицей (скрыть реальные данные)
