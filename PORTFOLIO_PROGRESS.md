# Portfolio Progress

> Обновлено: 2026-09-07

---

## Статус: Аудит ✅ · Позиционирование ✅ · Showcase доводка ✅ · M2 Upgrade ✅ · Final Sort ✅ · Скриншоты ⏳

---

## Audited ✅

Все 29 активных проектов/систем и 30 архивных проверены.  
Создан `PORTFOLIO_PROJECT_CENSUS.md` — фактический census с нуля.  
Создан `PORTFOLIO_M2_AUDIT.md` — M2 Score для всех 29 проектов.

---

## Позиционирование ✅

**Strong Middle / Middle+ Applied Software Developer**  
**Corporate Finance & Business Analysis — Expert / Strong**

Специализация: **Corporate Finance × Software Development × AI × Automation**

---

## Final Sort ✅ (2026-09-07)

`PORTFOLIO_FINAL_CLASSIFICATION.md` — полная таблица классификации.

### Tier A — Core Showcase (7)

| # | Тип | Проект |
|---|-----|--------|
| 1 | Production Web + Telegram (e2e) | **SVO System** (86%) |
| 2 | Аналитика / A/B методология | **fintech-ab-test-credit-offer** (85%) |
| 3 | B2B automation / n8n | **leadgen-n8n-system** (84%) |
| 4 | AI agent / document processing | **hr-breaker** (83%) |
| 5 | Финансовая система / AI-слой | **finance-mcp-server** (83%) |
| 6 | Оценка активов | **fedresurs-mvp** (82%) |
| 7 | Full-stack / Financial APIs | **finance-data-screener** (80%) |

### Tier B — More Projects (5)
rf-macro-risk-ai, mini-crm-fastapi-react, team-ai-bot, hotel-booking-n8n, superstore-retail-analytics

### Tier C — GitHub Only (6)
personal-rag-assistant, bots-platform, bankrot-trades-scraper, tg-digest-pipeline, finsight, dostaffkin

### Tier D → _Portfolio_back (10)
data-work-utilities, wb-sales-commercial-analysis, crewai-multiagent, yandex-google-sync, currency-travel-api, seo-mcp-bot, tg-catalog-analyzer, team-tg-bot-vc, autonomous-agents, pptx-redesigner

### Перенесено
- 10 Tier D проектов → `_Portfolio_back/`
- 99-archive (30 объектов) → `_Portfolio_back/99-archive/`

---

## M2 Scores ✅

| Проект | M2 | Статус |
|--------|:--:|--------|
| SVO System | 86% | ✅ Production, live |
| fintech-ab-test-credit-offer | 85% | ✅ |
| leadgen-n8n-system | **84%** | ✅ upgraded |
| hr-breaker | 83% | ✅ 192 тестa |
| finance-mcp-server | 83% | ✅ 45 тестов |
| fedresurs-mvp | **82%** | ✅ upgraded |
| rf-macro-risk-ai | **80%** | ✅ upgraded |
| finance-data-screener | 80% | ✅ |
| mini-crm-fastapi-react | **78%** | ✅ upgraded |

---

## Showcase READMEs ✅

- [x] finance-mcp-server/README.md — переписан: Business Problem, Architecture, Domain Logic
- [x] fedresurs-mvp/README.md — переписан: оба движка, demo mode
- [x] svo-payouts-website/README.md — технический showcase
- [x] fintech-ab-test-credit-offer/README.md — portfolio case (убран учебный контекст)
- [x] leadgen-n8n-system/README.md — 11 workflow + бизнес-логика + mock payload
- [x] mini-crm-fastapi-react/README.md — убран "чек-лист сдачи"
- [x] hr-breaker/README.md — Business Problem + Quick Demo
- [x] svo-payments-bot/README.md — EN brief добавлен

---

## Code Fixes ✅

- [x] finance-mcp-server/product-mcp/README.md — абс. путь → `<absolute-path-to>`
- [x] finance-data-screener/.env.example — `COMPOSE_PROJECT_NAME` + `SSL_VERIFY`
- [x] finance-data-screener collectors — SSL configurable через env
- [x] finance-data-screener/README.md — Quick Start упрощён

---

## M2 Upgrade ✅

| Проект | Что добавлено | Тесты |
|--------|--------------|:-----:|
| mini-crm-fastapi-react | `tests/test_api.py` — 26 тестов (CRUD, validation, errors) | 30 ✅ |
| rf-macro-risk-ai | `tests/test_scoring.py` — 44 теста + `replay_scoring.py` + `sample_data/` | 52 ✅ |
| fedresurs-mvp | `lot_source.py` (LotSource/DemoSource/validate_lot) + `test_lot_source.py` — 17 тестов | 64 ✅ |
| leadgen-n8n-system | `workflow_utils.py` (warmth decay, error classify, idempotency, consensus) + 39 тестов | 43 ✅ |

---

## New Files ✅

- [x] `fedresurs-mvp/demo_seed.py` — 5 синтетических лотов
- [x] `fedresurs-mvp/lot_source.py` — LotSource abstraction
- [x] `hr-breaker/sample-data/` — resume.txt + job-description.txt
- [x] `rf-macro-risk-ai/CONTRIBUTION.md` — авторский вклад vs upstream
- [x] `rf-macro-risk-ai/scripts/replay_scoring.py` — replay без LLM
- [x] `rf-macro-risk-ai/sample_data/sample_criteria_status.json`
- [x] `leadgen-n8n-system/workflow_utils.py` — Code-node logic
- [x] `leadgen-n8n-system/tests/mock_lead_payload.json`
- [x] 9× `docs/SCREENSHOTS_TODO.md` — точные сценарии
- [x] `PORTFOLIO_PROJECT_CENSUS.md`
- [x] `PORTFOLIO_M2_AUDIT.md`
- [x] `M2_UPGRADE_RESULT.md`

---

## Screenshots ⏳ (ручная работа)

| Проект | Файл | Приоритет |
|--------|------|:---------:|
| finance-mcp-server | docs/SCREENSHOTS_TODO.md | High |
| hr-breaker | docs/SCREENSHOTS_TODO.md | High |
| svo-payments-bot | docs/SCREENSHOTS_TODO.md | High |
| leadgen-n8n-system | docs/SCREENSHOTS_TODO.md | High |
| finance-data-screener | docs/SCREENSHOTS_TODO.md | Medium |
| svo-payouts-website | docs/SCREENSHOTS_TODO.md | Medium |
| fedresurs-mvp | docs/SCREENSHOTS_TODO.md | Medium |
| mini-crm-fastapi-react | docs/SCREENSHOTS_TODO.md | Medium |
| rf-macro-risk-ai | docs/SCREENSHOTS_TODO.md | Low (GitHub Pages уже есть) |

---

## GitHub Publication ⏳

Готовы к публикации (порядок):

1. **finance-mcp-server** ✅ готов
2. **svo-payments-bot** ✅ готов
3. **svo-payouts-website** ✅ готов (live: svorazbor.ru)
4. **fintech-ab-test-credit-offer** ✅ готов
5. **rf-macro-risk-ai** ✅ готов (live: GitHub Pages)
6. **hr-breaker** ⏳ скриншоты
7. **finance-data-screener** ⏳ скриншоты
8. **mini-crm-fastapi-react** ⏳ скриншоты
9. **fedresurs-mvp** ⏳ скриншоты
10. **leadgen-n8n-system** ⏳ скриншоты + n8n Canvas

---

## Blocked ⛔

- **wb-sales-commercial-analysis** — данные клиента, не публиковать
- **99-archive/password-generator** — `.key` + `vault.db`, не публиковать никогда

---

## Remaining ⏳

- Скриншоты для 7 Tier A проектов (ручные действия по SCREENSHOTS_TODO.md)
- GitHub topics при создании репозиториев
