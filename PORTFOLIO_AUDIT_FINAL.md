# Portfolio Audit — Final Report

> Дата: 2026-09-07  
> Пересмотрено: 2026-09-07

---

## Executive Summary

**Найдено проектов:** 59 (29 активных + 30 архивных)

| Tier | Кол-во | Описание |
|------|:------:|---------|
| **TIER A — Showcase** | 9 | Витринные проекты (SVO считается одним end-to-end кейсом) |
| **TIER B — Supporting** | 11 | Хорошие проекты для GitHub, не на главной витрине |
| **TIER C — Needs Work** | 9 | Потенциал есть, требуют доработки |
| **TIER D — Archive** | 30 | Образовательные материалы, прототипы |

**Production проекты:** 2 (svorazbor.ru, svo-payments-bot с CI/CD)  
**Проекты с тестами:** 14 из 29  
**Проекты с Docker:** 22 из 29  
**Проекты с .env.example:** 26 из 29

---

## Целевое позиционирование

**Strong Middle / Middle+ Applied Software Developer**  
**Corporate Finance & Business Analysis — Expert / Strong**

Специализация: Corporate Finance × Software Development × AI × Automation

Главный тезис:
> Понимаю бизнес и финансы — и могу самостоятельно превратить бизнес-задачу в работающий программный инструмент.

Портфолио показывает не «набор технологий», а **9 типов прикладных задач**, которые автор способен закрывать.

---

## Финальный список showcase — 9 типов задач

| # | Тип задачи | Проект |
|---|-----------|--------|
| 1 | Финансовая система / AI-слой | **finance-mcp-server** |
| 2 | AI-инструмент финансиста | **finance-data-screener** |
| 3 | Оценка активов / Financial valuation | **fedresurs-mvp** |
| 4 | Аналитика и A/B методология | **fintech-ab-test-credit-offer** |
| 5 | Macro analytics / scoring | **rf-macro-risk-ai** |
| 6 | AI agent / document processing | **hr-breaker** |
| 7 | B2B automation / n8n | **leadgen-n8n-system** |
| 8 | Production Web + Telegram (end-to-end) | **svo-payouts-website + svo-payments-bot** |
| 9 | Internal CRM / business system | **mini-crm-fastapi-react** |

**Почему SVO — один кейс:** пара website + bot показывает сильнее, чем два отдельных проекта. Один продукт, две точки доступа, полный CI/CD. Это демонстрирует способность построить систему целиком.

---

## Security Scan

| Проект | Статус |
|--------|--------|
| finance-mcp-server | ✅ SQLite локальный, ключей нет |
| svo-payments-bot | ✅ BOT_TOKEN только через env |
| svo-payouts-website | ✅ Чисто |
| finance-data-screener | ✅ PROXYAPI_KEY через env |
| hr-breaker | ✅ API ключи через .env |
| rf-macro-risk-ai | ✅ Ключи через env |
| fedresurs-mvp | ⚠️ Chrome bookmarks пути — локальные, безопасны |
| leadgen-n8n-system | ✅ Шаблоны без credentials |
| mini-crm-fastapi-react | ✅ google_settings.example.json — шаблон |
| bots-platform | ⚠️ Telegram API credentials — проверить .gitignore |
| wb-sales-commercial-analysis | 🔴 Данные клиента — не публиковать до анонимизации |
| 99-archive/password-generator | 🔴 .key файл и vault.db — не публиковать |

---

## Что было сделано в ходе аудита

### Новые документы

| Файл | Назначение |
|------|-----------|
| `PORTFOLIO_INVENTORY.md` | Инвентаризация 59 проектов по 25 параметрам |
| `PORTFOLIO_RANKING.md` | Tier A/B/C/D с оценками по 10 параметрам |
| `PORTFOLIO_GAP_ANALYSIS.md` | Gap analysis для каждого из 10 TIER A проектов |
| `PORTFOLIO_MATRIX.md` | Матрица компетенций |
| `PORTFOLIO_ARCHITECTURE.md` | Mermaid-схемы архитектуры |
| `PORTFOLIO_POSITIONING.md` | Уровень и narrative |
| `PORTFOLIO_AUDIT_FINAL.md` | Этот документ |
| `PORTFOLIO_PROGRESS.md` | Трекинг прогресса |

### README.md

Переписан полностью: убраны ссылки на несуществующие проекты, добавлены все showcase с описанием бизнес-задач, обновлено позиционирование.

---

## Что осталось

### Critical (перед публикацией)

| Задача | Проект | Трудозатраты |
|--------|--------|:---:|
| Убрать абсолютный путь из README | finance-mcp-server | 5 мин |
| Добавить краткий EN блок | svo-payments-bot | 30 мин |
| Переписать README как технический showcase | svo-payouts-website | 1-2 ч |
| Переписать README: убрать "ТЗ курса" | fintech-ab-test | 1-2 ч |
| Переписать README: убрать "чек-лист сдачи" | mini-crm-fastapi-react | 1-2 ч |
| Уточнить авторский вклад vs original repo | rf-macro-risk-ai | 30 мин |
| Добавить COMPOSE_PROJECT_NAME в env | finance-data-screener | 5 мин |
| Не публиковать vault.db, .key | 99-archive/password-generator | — |
| Анонимизировать данные клиента | wb-sales-commercial-analysis | 2-4 ч |

### Important (улучшат восприятие)

| Задача | Проект | Трудозатраты |
|--------|--------|:---:|
| Скриншоты интерфейса | все 9 TIER A | 1-2 ч каждый |
| Seed/demo data | fedresurs-mvp, hr-breaker, mini-crm, leadgen | 2-4 ч каждый |
| docker-compose на корне | finance-mcp-server | 1 ч |
| Business Case раздел | finance-mcp-server | 30 мин |
| Скриншоты n8n workflows | leadgen-n8n-system | 1 ч |

---

## Technical Strengths

Что реально подтверждено кодом:

**1. Finance domain expertise**  
P&L, Cash Flow, NPV/IRR, A/B metrics, bankruptcy valuation. Разработчик без финансового бэкграунда не напишет такой код.

**2. Production deployment**  
svorazbor.ru и svo-payments-bot с CI/CD доказывают способность довести проект до эксплуатации.

**3. AI/LLM engineering применяется осмысленно**  
MCP, Pydantic-AI, LangChain/LangGraph, RAG, multi-provider — там, где это даёт бизнес-ценность, а не ради галочки.

**4. Реальные тест-сьюты**  
fedresurs-mvp (47 тестов), hr-breaker (30+), finance-data-screener (18) — тесты покрывают бизнес-логику.

**5. n8n automation на системном уровне**  
11-workflow система с multi-LLM consensus, shadow validation, error handling.

**6. Статистическая методология**  
A/B тест с правильным методом (Welch t-test), MDE, sample size — уровень продуктового аналитика.

---

## Technical Profile (без Enterprise-оверинжиниринга)

Портфолио **не требует** для своего класса задач: Kubernetes, Kafka, Terraform, Spark, gRPC, GraphQL, CQRS, event sourcing, микросервисов. Все решения соразмерны задачам.

Что есть в нужном объёме для прикладного разработчика:
- Docker + docker-compose — 22 из 29 проектов
- CI/CD (GitHub Actions) — 2 production проекта с full pipeline
- PostgreSQL + Alembic — там, где нужна реляционная БД
- SQLite — там, где достаточно файловой БД

---

## Portfolio Narrative

**Для клиента:**
> Специализация на стыке финансовой экспертизы и разработки. Беру бизнес-задачу в финансах или смежных областях, формализую требования и строю рабочий инструмент. Понимаю предметную область изнутри — это позволяет строить точные инструменты, а не просто «автоматизировать по ТЗ».

**Для работодателя:**
> Сильный прикладной Middle с редким сочетанием: финансовая предметная экспертиза + уверенный Python/backend + AI/automation. Два проекта в production, тест-сьюты, Docker, CI/CD. Дашь задачу на стыке финансов и разработки — доведёт до результата без ручного ведения.

---

## GitHub Deployment Plan

| Очередь | Проект | Статус |
|---------|--------|:------:|
| 1 | finance-mcp-server | ⏳ Ready after path fix |
| 2 | svo-payments-bot | ⏳ Ready after screenshots |
| 3 | fintech-ab-test-credit-offer | ⏳ Ready after README rewrite |
| 4 | rf-macro-risk-ai | ⏳ Ready after authorship clarification |
| 5 | svo-payouts-website | ⏳ Ready after README rewrite |
| 6 | finance-data-screener | ⏳ Ready after screenshots + compose fix |
| 7 | hr-breaker | ⏳ Ready after sample data |
| 8 | mini-crm-fastapi-react | ⏳ Ready after README rewrite |
| 9 | fedresurs-mvp | ⏳ Needs seed data |
| 10 | leadgen-n8n-system | ⏳ Needs screenshots |

---

*Аудит завершён 2026-09-07. Следующий шаг: Phase 1 Quick wins (~1-2 дня).*
