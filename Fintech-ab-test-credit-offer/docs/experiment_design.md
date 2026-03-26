# Experiment design

## Goal
Проверить, увеличит ли перенос карточки `credit_of_day` вверх по ленте домашнего экрана:
- `CR_apply`
- `CTR`
- `ARPU`

## Hypothesis
Если карточку спецпредложения показывать выше в ленте, пользователи чаще увидят ее, чаще кликнут и чаще начнут / завершат оформление заявки.

## Variants
- **A_control:** карточка остается внизу ленты.
- **B_test:** карточка переносится выше.

## Unit of randomization
`client_id`

## Traffic split
Целевой дизайн по ТЗ: 50/50.

## Primary metric
`CR_apply = offer_apply / offer_impression`

## Secondary metrics
- `CTR = offer_click / offer_impression`
- `CR_home_apply = offer_apply / home_view`
- `ARPU = revenue / users`
- `Approval Rate = offer_approved / offer_apply`

## Constraints
- MDE = 2.5%
- duration = 7 days
- decision window is fixed because redesign follows immediately after experiment
