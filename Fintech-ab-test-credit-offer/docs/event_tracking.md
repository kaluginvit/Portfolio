# Event tracking

Исходный формат данных:

`dt | client_id | ab_group | event_type | offer_id | value`

## Event types
- `home_view`
- `offer_impression`
- `offer_click`
- `offer_apply`
- `offer_approved`
- `revenue`

## Expected semantics
- `home_view` — открытие домашнего экрана
- `offer_impression` — показ карточки
- `offer_click` — клик по карточке
- `offer_apply` — отправка заявки
- `offer_approved` — одобрение заявки
- `revenue` — денежный эффект

## User-day funnel
На уровне `dt × client_id × ab_group` строится таблица:

`dt_day | client_id | ab_group | home_view | impressions | clicks | applies | approvals | revenue`
