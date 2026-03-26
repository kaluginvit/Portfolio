# Metrics definition

## Primary metric
### CR_apply
`offer_apply / offer_impression`

Почему primary:
- приоритетно указан в ТЗ;
- ближе к бизнес-результату, чем CTR;
- чувствителен к изменению позиции карточки.

## Secondary metrics
### CTR
`offer_click / offer_impression`

### CR_home_apply
`offer_apply / home_view`

### ARPU
`revenue / unique users`

### Approval Rate
`offer_approved / offer_apply`

## Statistical logic
- метрики считаются на уровне пользователя;
- для сравнения средних используется Welch t-test;
- для оценки мощности строится MDE curve;
- размер выборки подбирается для `CR_apply`.
