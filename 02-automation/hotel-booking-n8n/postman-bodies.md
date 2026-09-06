# Postman bodies для Webhook (Workflow A)

Workflow A (Webhook): **`GP-HotelBooking-A-Webhook`**  
Path: `hotel-booking`  
Method: **POST**  

## Headers
- `Content-Type: application/json`

> URL берёте из ноды Webhook в n8n (Test/Production URL).

---

## 1) T1 (found) — номер должен найтись (seed в Supabase)

```json
{
  "client_name": "Иван Петров",
  "email": "ivan.petrov@example.com",
  "hotel_name": "Hotel_Aurora",
  "room_type": "standard",
  "date_from": "2026-05-10",
  "date_to": "2026-05-14"
}
```

Ожидание:
- `rooms.status` для подходящей строки станет `reserved`
- появится строка в `bookings`
- уйдёт письмо “подтверждение”

---

## 2) T2 (not found) — номер НЕ должен найтись

```json
{
  "client_name": "Иван Петров",
  "email": "ivan.petrov@example.com",
  "hotel_name": "Hotel_Aurora",
  "room_type": "suite",
  "date_from": "2026-05-10",
  "date_to": "2026-05-14"
}
```

Ожидание:
- запись в `bookings` **не** создаётся
- письмо “нет свободных номеров”

---

## 3) T3 (duplicate) — дубль (повторить T1 тем же payload)

```json
{
  "client_name": "Иван Петров",
  "email": "ivan.petrov@example.com",
  "hotel_name": "Hotel_Aurora",
  "room_type": "standard",
  "date_from": "2026-05-10",
  "date_to": "2026-05-14"
}
```

Ожидание:
- новая запись в `bookings` **не** создаётся (anti-duplicate по `request_id`)

---

## 4) T4 (invalid) — невалидный payload (нет email)

```json
{
  "client_name": "Иван Петров",
  "hotel_name": "Hotel_Aurora",
  "room_type": "standard",
  "date_from": "2026-05-10",
  "date_to": "2026-05-14"
}
```

Ожидание:
- бронь не создаётся
- (если Gmail настроен) уйдёт письмо менеджеру о невалидном вводе

