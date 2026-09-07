# Portfolio Ranking

> Дата: 2026-09-07 | Аудитор: Claude Sonnet 4.6

---

## Методология оценки

**Business Value (1–10):** реальность бизнес-задачи, коммерческий потенциал  
**Technical Level (1–10):** архитектура, качество кода, тестируемость, maintainability  
**Reusability (1–10):** можно ли отдать новому клиенту без переписывания  
**Portfolio Value (1–10):** усиливает ли позиционирование автора  
**Readiness (1–10):** готовность к GitHub (secrets, docs, launch)  

**Target State:**
- `SHOWCASE` — витринный проект
- `SUPPORTING` — поддерживающий, GitHub-ready
- `NEEDS WORK` — есть потенциал, требует доработки
- `ARCHIVE` — архив

---

## Software Engineering Scores

| Project | Architecture | Code Quality | Maintainability | Security | Documentation | Testing | UX/UI | Deployability | Reusability | Business Value |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **finance-mcp-server** | 9 | 8 | 8 | 9 | 9 | 9 | 7 | 8 | 9 | 10 |
| **hr-breaker** | 9 | 9 | 8 | 8 | 9 | 9 | 8 | 8 | 8 | 8 |
| **svo-payments-bot** | 8 | 8 | 9 | 9 | 9 | 8 | 7 | 9 | 7 | 9 |
| **svo-payouts-website** | 8 | 8 | 8 | 9 | 8 | 8 | 8 | 10 | 7 | 9 |
| **finance-data-screener** | 8 | 8 | 7 | 8 | 9 | 7 | 7 | 9 | 7 | 9 |
| **rf-macro-risk-ai** | 7 | 8 | 7 | 8 | 9 | 7 | 7 | 8 | 7 | 8 |
| **fedresurs-mvp** | 7 | 7 | 7 | 7 | 9 | 9 | 6 | 7 | 6 | 9 |
| **fintech-ab-test-credit-offer** | 7 | 7 | 8 | 9 | 10 | 8 | 5 | 7 | 8 | 8 |
| **leadgen-n8n-system** | 8 | 7 | 6 | 7 | 8 | 5 | 6 | 7 | 6 | 8 |
| **mini-crm-fastapi-react** | 7 | 7 | 7 | 8 | 8 | 6 | 7 | 8 | 7 | 7 |
| **hotel-booking-n8n** | 6 | 6 | 6 | 7 | 9 | 7 | 6 | 5 | 7 | 7 |
| **tg-digest-pipeline** | 8 | 6 | 5 | 7 | 7 | 5 | 5 | 5 | 4 | 7 |
| **data-work-utilities** | 6 | 6 | 6 | 7 | 7 | 4 | 6 | 5 | 6 | 7 |
| **finsight** | 6 | 6 | 6 | 7 | 7 | 5 | 6 | 7 | 6 | 7 |
| **personal-rag-assistant** | 6 | 6 | 6 | 7 | 7 | 5 | 5 | 6 | 5 | 6 |
| **crewai-multiagent** | 6 | 6 | 5 | 6 | 6 | 4 | 5 | 6 | 5 | 6 |
| **team-ai-bot** | 6 | 6 | 6 | 7 | 7 | 5 | 5 | 7 | 5 | 6 |
| **bots-platform** | 6 | 6 | 5 | 5 | 5 | 3 | 5 | 5 | 4 | 6 |
| **bankrot-trades-scraper** | 5 | 5 | 5 | 6 | 7 | 5 | 5 | 6 | 5 | 6 |
| **superstore-retail-analytics** | 5 | 6 | 5 | 8 | 7 | 5 | 6 | 5 | 6 | 5 |

---

## Portfolio Value Matrix (0–5 по направлениям)

| Project | Finance | Python | SQL | AI | API | Automation | Backend | Frontend | DevOps | Product |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **finance-mcp-server** | 5 | 5 | 4 | 4 | 4 | 3 | 5 | 3 | 3 | 4 |
| **finance-data-screener** | 5 | 4 | 4 | 4 | 5 | 3 | 5 | 4 | 4 | 4 |
| **fintech-ab-test-credit-offer** | 4 | 4 | 5 | 0 | 0 | 3 | 0 | 2 | 2 | 4 |
| **rf-macro-risk-ai** | 4 | 4 | 2 | 4 | 3 | 3 | 3 | 3 | 3 | 3 |
| **fedresurs-mvp** | 4 | 4 | 3 | 4 | 3 | 3 | 3 | 2 | 2 | 4 |
| **hr-breaker** | 0 | 5 | 0 | 5 | 4 | 4 | 4 | 3 | 3 | 4 |
| **svo-payments-bot** | 3 | 5 | 3 | 0 | 3 | 3 | 5 | 0 | 4 | 4 |
| **svo-payouts-website** | 3 | 2 | 0 | 0 | 3 | 2 | 3 | 5 | 4 | 5 |
| **leadgen-n8n-system** | 0 | 2 | 2 | 3 | 3 | 5 | 3 | 0 | 3 | 4 |
| **mini-crm-fastapi-react** | 2 | 4 | 3 | 0 | 4 | 2 | 4 | 4 | 3 | 4 |
| **hotel-booking-n8n** | 0 | 0 | 2 | 0 | 2 | 5 | 0 | 2 | 0 | 3 |
| **tg-digest-pipeline** | 3 | 4 | 3 | 5 | 3 | 4 | 4 | 2 | 2 | 3 |
| **data-work-utilities** | 2 | 3 | 0 | 3 | 3 | 0 | 3 | 3 | 0 | 3 |
| **finsight** | 3 | 3 | 0 | 3 | 3 | 0 | 3 | 3 | 3 | 3 |
| **personal-rag-assistant** | 0 | 3 | 0 | 4 | 2 | 2 | 3 | 0 | 2 | 2 |
| **crewai-multiagent** | 0 | 3 | 0 | 4 | 3 | 3 | 3 | 2 | 2 | 3 |
| **bankrot-trades-scraper** | 3 | 3 | 3 | 0 | 2 | 3 | 2 | 2 | 2 | 2 |
| **superstore-retail-analytics** | 3 | 3 | 2 | 0 | 0 | 2 | 0 | 3 | 0 | 2 |
| **wb-sales-commercial-analysis** | 4 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

---

## TIER A — SHOWCASE

Витринные проекты. Максимально широкий диапазон компетенций.

| Rank | Project | Business Value | Technical Level | Reusability | Portfolio Value | Readiness | Target State |
|------|---------|:-:|:-:|:-:|:-:|:-:|:------:|
| 1 | **finance-mcp-server** | 10 | 9 | 9 | 10 | 9 | SHOWCASE |
| 2 | **svo-payments-bot** | 9 | 9 | 7 | 9 | 9 | SHOWCASE |
| 3 | **svo-payouts-website** | 9 | 8 | 7 | 9 | 10 | SHOWCASE |
| 4 | **finance-data-screener** | 9 | 8 | 7 | 9 | 9 | SHOWCASE |
| 5 | **hr-breaker** | 8 | 9 | 8 | 9 | 9 | SHOWCASE |
| 6 | **rf-macro-risk-ai** | 8 | 8 | 7 | 8 | 8 | SHOWCASE |
| 7 | **fintech-ab-test-credit-offer** | 8 | 7 | 8 | 8 | 9 | SHOWCASE |
| 8 | **fedresurs-mvp** | 9 | 7 | 6 | 8 | 7 | SHOWCASE |
| 9 | **leadgen-n8n-system** | 8 | 7 | 6 | 8 | 7 | SHOWCASE |
| 10 | **mini-crm-fastapi-react** | 7 | 7 | 7 | 7 | 7 | SHOWCASE |

### Что покрывает TIER A

| Класс компетенции | Проект |
|-------------------|--------|
| Corporate Finance / Management Accounting | finance-mcp-server |
| Financial Analytics + AI + Full-stack | finance-data-screener |
| Statistical Analysis / A/B / Data Science | fintech-ab-test-credit-offer |
| AI/LLM + Macro Analytics | rf-macro-risk-ai |
| AI Agent + Financial Domain | fedresurs-mvp |
| AI Engineer (Pydantic-AI, multi-agent) | hr-breaker |
| Automation / n8n | leadgen-n8n-system |
| Full-stack CRM + OAuth | mini-crm-fastapi-react |
| Production Telegram Bot + CI/CD | svo-payments-bot |
| Production Website + E2E + VPS Deploy | svo-payouts-website |

---

## TIER B — SUPPORTING

Хорошие проекты для GitHub, но не на главной витрине.

| Rank | Project | Причина классификации |
|------|---------|----------------------|
| B1 | **hotel-booking-n8n** | Сильная документация, хороший n8n кейс, но выпускной проект курса |
| B2 | **tg-digest-pipeline** | Технически сложный, но личный инструмент — сложно презентовать |
| B3 | **finsight** | Простой но рабочий — хорошо как быстрый демо-кейс Claude API + full-stack |
| B4 | **team-ai-bot** | Корпоративный RAG бот — хороший supporting кейс |
| B5 | **data-work-utilities** | Хороший full-stack + AI, но нужна доработка |
| B6 | **personal-rag-assistant** | Учебный RAG кейс, хорошая архитектура, но нишевый |
| B7 | **superstore-retail-analytics** | Понятный EDA кейс, легко воспроизвести |
| B8 | **crewai-multiagent** | CrewAI демо — хорошо как quick demo |
| B9 | **bots-platform** | Реальные production боты, но плохо документированы |
| B10 | **bankrot-trades-scraper** | Связан с fedresurs-mvp, может быть частью той же истории |
| B11 | **site** (portfolio website) | Мета-проект: сам портфолио-сайт |

---

## TIER C — NEEDS WORK

Потенциал есть, но требуют серьёзной доработки перед публикацией.

| Project | Главная проблема |
|---------|-----------------|
| **wb-sales-commercial-analysis** | Данные клиента — нужна полная анонимизация или переработка на синтетике |
| **autonomous-agents** | Неясное назначение, нет тестов, прототипный код |
| **dostaffkin** | Angular, ограниченная бизнес-ценность для портфолио, нет тестов |
| **yandex-google-sync** | Нишевая утилита, нужны credentials для демо |
| **pptx-redesigner** | Набор скриптов без архитектуры, нет тестов |
| **currency-travel-api** | Простая утилита, нет тестов |
| **team-tg-bot-vc** | Слишком простой для витрины |
| **tg-catalog-analyzer** | Узкоспециализированный, зависит от конкретного контента |
| **seo-mcp-bot** | Неполный (Яндекс OAuth сложен для демо) |

---

## TIER D — ARCHIVE

Образовательные материалы, прототипы, одноразовые эксперименты.

**Физически не удалять.** Хранить в `99-archive/`.

| Проект | Тип |
|--------|-----|
| ai-automation-lessons | Учебный |
| ai-bot-lessons | Учебный |
| ai-coding-lessons | Учебный |
| api-lessons | Учебный |
| api-testing-bot | Учебный |
| auto-deploy-lesson | Учебный |
| db-lessons | Учебный |
| desktop-reminder | Прототип |
| docker-lessons | Учебный |
| docker-vps-project | Учебный |
| expert-project | Прототип |
| langchain-lesson-1 | Учебный |
| langchain-lesson-2 | Учебный |
| llm-lessons | Учебный |
| local-ai-agent | Прототип |
| loki-grafana-stack | Прототип |
| mcp-practice | Учебный |
| memory-lessons | Учебный |
| mini-booking-system | Прототип |
| password-generator | Утилита |
| postgres-lessons | Учебный |
| prompting-case | Исследование |
| python-modules-lessons | Учебный |
| python-oop-practice | Учебный |
| rag-lessons | Учебный |
| recipe-search-bot | Прототип |
| recurring-payments-reminder | Прототип |
| sql-lessons | Учебный |
| sqlite-lesson | Учебный |
| ux-reviewer-agent | Прототип (незавершён) |

---

## Итог

**TIER A:** 10 проектов — покрывают все ключевые компетенции  
**TIER B:** 11 проектов — хороший GitHub, не на витрине  
**TIER C:** 9 проектов — нужна доработка  
**TIER D:** 30 проектов — архив (оставить на месте)
