# Final recommendation logic

## Decision rule

### Positive directional outcome
Используется, если `CR_apply` и `CTR` выше в тестовой группе, а downside по дополнительным метрикам отсутствует.

### Confirmatory outcome
Используется только если эксперимент обладает достаточной мощностью для согласованного MDE.

## Recommendation for this case
- primary metric: `CR_apply`
- observed effect: positive
- decision strength: directional, not fully confirmatory for `MDE = 2.5%`
- next step: validate on larger independent traffic or revise MDE / test duration
