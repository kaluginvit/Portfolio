# Отель: заявки Tally → n8n → Supabase → почта

**Проблема:** собрать поток бронирований из формы (Tally), проверить данные, исключить дубли, найти номер, записать в БД и уведомить клиента и дирекцию — без ручного Excel.

**Решение:** связка **n8n** + **Supabase** (PostgreSQL) + почтовые шаблоны. Два основных workflow экспортированы в JSON; схема БД — SQL.

**Стек:** n8n (webhook, cron), Supabase, Tally, Gmail (по настройке).

**Ценность:** воспроизводимый поток «форма → валидация → дедуп → поиск номера → резерв → письма», плюс ежедневный отчёт менеджеру.

---

## Схемы процесса

Подробные диаграммы (Mermaid) — в [`process-diagram.mermaid.md`](./process-diagram.mermaid.md):

- **A)** обработка заявки: Tally → Webhook → валидация → дедуп → поиск комнаты → вставка брони → письма.  
- **B)** cron 18:00: выборки из Supabase → сводный e-mail.

---

## Файлы

| Файл | Назначение |
|------|------------|
| [`workflow-a.json`](./workflow-a.json), [`workflow-b.json`](./workflow-b.json) | Экспорт workflow n8n (импорт в свой инстанс) |
| [`supabase-schema-and-seed.sql`](./supabase-schema-and-seed.sql) | Схема и начальные данные |
| [`setup-steps.md`](./setup-steps.md) | Шаги настройки |
| [`links-and-materials.md`](./links-and-materials.md) | Ссылки и материалы |
| [`email-templates.md`](./email-templates.md) | Шаблоны писем (клиенту, дирекции, сводный) |
| [`postman-bodies.md`](./postman-bodies.md) | Примеры запросов для Postman / curl |
| [`process-diagram.mermaid.md`](./process-diagram.mermaid.md) | Mermaid-диаграммы процесса |
| [`test-matrix.md`](./test-matrix.md) | Матрица позитивных и негативных сценариев |
| [`_artifacts/`](./_artifacts/) | HTML-экспорты n8n (снимки workflow, не runtime) |

---

## Быстрый старт (для разработчика)

1. Поднять проект в **Supabase**, выполнить SQL из `supabase-schema-and-seed.sql`.  
2. Импортировать **workflow-a** и **workflow-b** в n8n, прописать credentials (Supabase, Gmail, Tally webhook).  
3. Настроить **Tally** на webhook URL из n8n.  
4. Прогнать тестовую заявку и проверить таблицы и почту.

---

## Демо / медиа

Добавьте скрины успешных **executions** в n8n и при необходимости — схему из Mermaid в виде PNG в папку `media/` (создайте при необходимости).

---

## Ограничения

- Секреты (Supabase service role, SMTP/OAuth) только в n8n / `.env` на стороне инстанса, не в git.  
- Логика номерного фонда и цен зависит от данных в БД — под ваш объект нужно подстроить сиды и узлы поиска.
