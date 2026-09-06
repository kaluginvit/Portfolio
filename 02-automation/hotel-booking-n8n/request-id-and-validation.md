# `request_id` и валидация входа (спецификация)

## 1) Назначение
`request_id` нужен для защиты от дублей: если одна и та же заявка повторно пришла из формы (повторная отправка, ретрай, двойной клик), сценарий **не создаёт вторую бронь**.

## 2) Формула `request_id`
Базовый вариант (человекочитаемый, без хеша):

```
request_id = lower(trim(email)) + "|" +
             lower(trim(hotel_name)) + "|" +
             lower(trim(room_type)) + "|" +
             date_from + "|" + date_to
```

Рекомендуемый вариант (хеш для аккуратности):
- собрать строку как выше
- применить SHA-256/MD5 в ноде Code (n8n) и сохранить хеш как `request_id`

## 3) Хранение
В Supabase таблице `bookings` поле `request_id` должно быть **unique**.

## 4) Правила валидации входа (Webhook payload)
### Обязательные поля
- `client_name` (непустая строка)
- `email` (непустая строка, формат email)
- `hotel_name` (непустая строка)
- `room_type` (непустая строка)
- `date_from` (дата, ожидаем `YYYY-MM-DD` или приводим к этому формату)
- `date_to` (дата)

### Правила дат
- `date_from < date_to` (заезд строго раньше выезда)
- диапазон не “в прошлом” (опционально)

### Допустимые статусы
- `rooms.status`: `free`, `reserved`
- `bookings.status`: `reserved`, (опционально `confirmed`, `cancelled`)
- `bookings.payment_status`: `pending`, (опционально `paid`)

## 5) Рекомендованное поведение при ошибке
- если не хватает обязательных полей → завершить сценарий без создания брони
- (опционально) уведомить менеджера о некорректной заявке
- зафиксировать ошибку в execution log n8n

## 6) Пример (для тестов)
Вход:
- email: `Test@Example.com`
- hotel_name: `Hotel_Aurora`
- room_type: `standard`
- date_from: `2026-05-10`
- date_to: `2026-05-14`

Normalized string:
`test@example.com|hotel_aurora|standard|2026-05-10|2026-05-14`

