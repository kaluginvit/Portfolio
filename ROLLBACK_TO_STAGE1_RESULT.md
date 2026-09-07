# Rollback to Stage 1 Result

> Date: 2026-09-07

---

## Found After Stage 1

После точки завершения Stage 1 (commit `563a55a`) обнаружено следующее в рабочем дереве:

### Unstaged changes (tracked files)
- `.github/workflows/build-images.yml` — Stage 1 CI fix (очистка матрицы, удаление мёртвых путей, добавление hr-breaker, rf-macro-risk-ai, finance-data-screener, mini-crm)
- `.github/workflows/deploy-svo-payments-bot.yml` — Stage 1 CI fix (check secrets → ready=true/false → deploy conditional)
- Множество удалённых Tier D файлов (перенесены в `_Portfolio_back`)
- README.md и другие modified tracked files (Stage 1 content)

### Untracked files
- M2 upgrade: `lot_source.py`, `workflow_utils.py`, `test_*.py`, `sample_data/`, `scripts/` и другие
- Planning/audit docs: `PORTFOLIO_*.md`, `GITHUB_*.md`, `M2_UPGRADE_RESULT.md`, `PORTFOLIO_PROGRESS.md`
- `docs/SCREENSHOTS_TODO.md` в 9 проектах

### DEPLOYMENT_PLAN.md
**Не существует.** Ошибочный VPS deployment plan Stage 2 был только в контексте разговора — он никогда не был записан в файл.

---

## Reverted

**Ничего не откатывалось.** Файлов, связанных с ошибочной VPS-схемой Stage 2, в рабочем дереве не найдено.

Ошибочная архитектурная предпосылка (новые portfolio demos → VPS) существовала исключительно в conversation context предыдущей сессии. В файловой системе она не материализована.

---

## Preserved

### M2 Upgrades ✅
- **mini-crm-fastapi-react** — `tests/test_api.py` (30 тестов, CRUD + validation + errors), M2 ~78%
- **rf-macro-risk-ai** — `tests/test_scoring.py` (52 теста), `scripts/replay_scoring.py`, `sample_data/`, M2 ~80%
- **fedresurs-mvp** — `lot_source.py` (LotSource/DemoSource/validate_lot), `tests/test_lot_source.py` (64 теста total), `demo_seed.py`, M2 ~82%
- **leadgen-n8n-system** — `workflow_utils.py` (warmth decay, error classify, idempotency, consensus), 43 теста, `mock_lead_payload.json`, M2 ~84%

### Portfolio Tiers ✅
- **Tier A** (7): SVO System, fintech-ab-test-credit-offer, leadgen-n8n-system, hr-breaker, finance-mcp-server, fedresurs-mvp, finance-data-screener
- **Tier B** (5): rf-macro-risk-ai, mini-crm-fastapi-react, team-ai-bot, hotel-booking-n8n, superstore-retail-analytics
- **Tier C** (6): personal-rag-assistant, bots-platform, bankrot-trades-scraper, tg-digest-pipeline, finsight, dostaffkin
- **Tier D** → `_Portfolio_back` (10): перенесены

### _Portfolio_back ✅
- 10 Tier D проектов
- `99-archive/` (30 объектов)
- Структура сохранена

### GitHub Cleanup ✅
- Profile README (kaluginvit/kaluginvit) сохранён
- Descriptions, topics, homepage URLs сохранены
- MIT licenses сохранены (svo-payouts-website, svo-payments-bot, fintech-ab-test-credit-offer, mini-crm-fastapi-react)
- Private repos (test_action, ai-finance-screener, finance-consulting-landing) сохранены

### CI Fixes ✅
- `build-images.yml` — очищенная matrix без мёртвых путей, корректный context mini-crm, активные hr-breaker/rf-macro/finance-data-screener
- `deploy-svo-payments-bot.yml` — check secrets → ready=true/false → deploy conditional (без secrets: зелёный + skipped; с secrets: deploy выполняется)

### Existing SVO Production ✅
- VPS + Docker + GHCR + SSH deploy + svorazbor.ru — сохранено
- Не является ошибкой Stage 2 (это существующий production)

---

## Git Status

HEAD: `563a55a` — site: update cases to 12 featured vitrine projects, remove stale entries

Working tree:
- Modified (unstaged): `.github/workflows/build-images.yml`, `.github/workflows/deploy-svo-payments-bot.yml`, READMEs, `site/src/data/cases.ts`
- Deleted (unstaged): Tier D project files (в `_Portfolio_back`)
- Untracked: M2 upgrade files + planning docs + SCREENSHOTS_TODO.md

Все изменения — корректный результат Stage 1.

---

## Final State

`Stage 1 restored.`

`GitHub cleanup preserved.`

`CI fixes preserved.`

`Existing SVO production deployment preserved.`

`Stage 2 has not started.`
