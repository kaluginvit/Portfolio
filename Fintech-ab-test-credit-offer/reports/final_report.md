# Final report

## 1. Objective
Проверить, влияет ли перенос карточки `credit_of_day` вверх в ленте на ключевые продуктовые метрики, прежде всего на `CR_apply`.

## 2. Experiment setup
- A_control: карточка остается внизу ленты
- B_test: карточка переносится вверх
- unit of randomization: `client_id`
- primary metric: `CR_apply`
- secondary metrics: `CTR`, `CR_home_apply`, `ARPU`, `Approval Rate`
- target MDE from specification: `2.5%`

## 3. Data preparation
Сырые события преобразованы в user-day funnel и далее в user-level dataset. Дополнительно выполнены quality checks по дубликатам, offer_id и revenue.

## 4. Key results

### Primary metric — CR_apply
- control mean: 0.0810
- test mean: 0.1264
- absolute diff: 0.0454
- relative uplift: 56.05%
- p-value: 9.00092e-14
- 95% CI: [0.0335, 0.0573]

### Secondary metrics
- CTR uplift: 110.29%
- ARPU uplift: 161.23%

## 5. Power and MDE
Для целевого `MDE = 2.5%` рекомендуемый размер выборки составляет примерно **1,140,100 пользователей на группу**.  
Это существенно больше, чем доступный объем независимого реального трафика в окне 7 дней.

## 6. Interpretation
В анализируемых данных тестовая группа показывает сильный положительный сигнал по `CR_apply` и `CTR`.  
Однако сам эксперимент в условиях жесткого 7-дневного окна недостаточно мощный для надежной проверки столь малого MDE на реальном независимом трафике.  
Поэтому корректная интерпретация результата — **directional positive signal with limited inferential power for the target MDE**.

## 7. Recommendation
- считать изменение перспективным;
- не использовать текущий кейс как безусловное основание для полного rollout;
- подтвердить результат на реальном трафике большей мощности либо пересогласовать MDE.

## 8. Quality checks snapshot
| check_name               |   value |
|:-------------------------|--------:|
| duplicate_rows           |       0 |
| missing_ab_group         |       0 |
| bad_offer_rows           |       0 |
| bad_home_offer_rows      |       0 |
| nonpositive_revenue_rows |       0 |
| unique_users             |   10000 |
| total_rows               |   20000 |
