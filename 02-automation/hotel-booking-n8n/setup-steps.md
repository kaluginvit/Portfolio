# Setup steps (Supabase + Tally + Gmail + n8n)

Этот файл — инструкция, которую можно использовать как “чеклист” для доведения проекта до полностью работоспособного состояния.

---

## 1) Supabase: развернуть схему и тестовые данные
1) Открыть Supabase → **SQL Editor**
2) Запустить скрипт:
   - `supabase-schema-and-seed.sql`
3) Проверить:
   - таблицы `rooms`, `bookings` созданы
   - в `rooms` есть 5–10 строк (seed)
   - в `bookings` есть `request_id` (unique) и `created_at` (default now)

---

## 2) Tally: форма и webhook
1) Создать форму “Booking request”
2) Поля (exact names):
   - `client_name`
   - `email`
   - `hotel_name`
   - `room_type`
   - `date_from`
   - `date_to`
3) Webhook:
   - указать URL вебхука n8n для Workflow A (`Tally Webhook`)
4) Сохранить пример payload (скрин/копипаст) для отчёта (раздел 7/14)

---

## 3) n8n: Credentials

### 3.1 Supabase credential
Создать credential **Supabase** (тип: `supabaseApi`):
- Supabase URL
- API Key (обычно service role для записи/обновления)

### 3.2 Gmail credential
Создать credential **Gmail** (OAuth2):
- подключить аккаунт, с которого будут отправляться письма

---

## 4) n8n: привязать креды к узлам

### Workflow A (`AzFAbnUvv6Hj9xzg`)
Проставить креды:
- в узлах Supabase: `Lookup booking by request_id`, `Find free room`, `Reserve room (conditional)`, `Create booking`
- в узлах Gmail: `Email client (no room)`, `Email client (confirmation)`, `Email manager (invalid input)` (опционально)

### Workflow B (`XEnOndzgYGruMNvQ`)
Проставить креды:
- Supabase: `Bookings (last 24h)`, `Bookings (pending)`, `Rooms (reserved)`
- Gmail: `Email manager (daily report)`

---

## 5) Быстрый smoke-тест
1) В Workflow A запустить тестовый webhook POST (можно из n8n UI или через Postman) с body:
   - `client_name`, `email`, `hotel_name`, `room_type`, `date_from`, `date_to`
2) Убедиться:
   - при наличии подходящей комнаты: `rooms.status` стал `reserved`, в `bookings` появилась строка, письмо ушло
   - при отсутствии: письмо “нет номеров”, без создания строки в `bookings`
3) В Workflow B сделать manual run:
   - письмо-отчёт уходит на `dir@kalugin-consulting.ru`

