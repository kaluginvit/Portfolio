# Portfolio M2 Audit

> Дата: 2026-09-07
> Целевой уровень: крепкий Middle / Middle+
> Позиционирование: Corporate Finance × Business Analysis × Software Development × AI × Automation × Web
>
> Критерии уровня НЕ включают: Kubernetes, Kafka, Terraform, Spark, микросервисы, event sourcing, CQRS

---

## Методология M2 Score

**Оцениваемые категории с весами:**

| Категория | Вес | Применимость |
|-----------|:---:|:------------:|
| Business Problem & Domain | 15% | Всегда |
| Solution Design | 15% | Всегда |
| Implementation Quality | 20% | Всегда |
| Data / API / Integrations | 10% | Если применимо |
| Web / UI | 10% | Если применимо |
| AI / Automation | 10% | Если применимо |
| Reliability & Testing | 10% | Всегда |
| Deployability / Config / Security | 10% | Всегда |

Неприменимые категории исключаются, итог нормализуется к 100%.

**Шкала интерпретации:**

| Диапазон | Уровень |
|----------|---------|
| 90–100% | Strong M2 / Exemplary |
| 80–89% | M2 Confirmed |
| 70–79% | Good Middle / M2 Borderline |
| 60–69% | M1+/M2- |
| 40–59% | Junior+/M1 |
| <40% | Prototype / Educational |

---

## Showcase Projects — Детальные оценки

---

### 1. SVO System

**Path:** `03-ai-products/svo-payments-bot` + `04-web/svo-payouts-website`  
**Применимые категории:** BP, SD, IQ, Data, Web, Test, Deploy (AI/Automation — N/A, расчётная логика без LLM)

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 9/10 | Реальная production система с реальными пользователями. Два сценария квиза отражают реальное разнообразие пользователей |
| Solution Design | 9/10 | FSM в aiogram с persistence, App Router в Next.js, handlers/services/repos separation, localStorage для восстановления состояния |
| Implementation Quality | 8/10 | aiogram 3 async, aiosqlite WAL, TypeScript строго, Zod validation, React Hook Form, Framer Motion |
| Data/API | 8/10 | SQLite WAL+NORMAL synchronous, Telegram Bot API, webhook integration, file-based lead storage |
| Web/UI | 9/10 | Next.js 14 App Router, TypeScript, Tailwind v4, responsive, Playwright E2E (4 spec files), analytics events |
| Reliability/Testing | 8/10 | Vitest unit+integration (22 test files: calculator, quiz nav, Zod schemas), Playwright E2E, pytest scenarios |
| Deployability | 9/10 | GitHub Actions → GHCR → SSH deploy, nginx conf, Certbot инструкция, docker-compose с healthcheck, 4 CI workflows |

**Weighted score:** (9×15 + 9×15 + 8×20 + 8×10 + 9×10 + 8×10 + 9×10) / 90 × 100 = **86%**

**M2: Confirmed ✅**

**Что реально подтверждает M2:**
- Production код под реальным трафиком (единственный такой в портфолио)
- Full CI/CD pipeline написан с нуля и работает
- FSM с persistent state — нетривиальная архитектурная задача решена чисто
- Playwright E2E тесты покрывают весь user journey

**Что снижает M2:**
- svo-payments-bot имеет всего 2 test файла (test_scenarios + test_quiz_calculate), функциональных тестов мало
- Web/API layer в боте (webhook) документирован, но интеграционно не тестируется

**Что лишь проблема упаковки:** нет screenshots в README

---

### 2. hr-breaker

**Path:** `03-ai-products/hr-breaker`  
**Применимые категории:** все

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 8/10 | Чёткий use case, anti-hallucination — реальный differentiator, а не маркетинг |
| Solution Design | 9/10 | 8-layer plugin filter pipeline — архитектурно правильный подход, Pydantic-AI agents с четким разделением ролей |
| Implementation Quality | 9/10 | 95 Python файлов, чистые абстракции, CLI + Web + SSE стриминг, LiteLLM multi-provider |
| Data/API | 7/10 | FastAPI REST, SSE streaming, local profile storage, job scraper |
| Web/UI | 7/10 | Alpine.js web app с real-time прогрессом, preview PDF — функционально, не перегружено |
| AI/Automation | 9/10 | Pydantic-AI agents, 8-фильтровый pipeline (TF-IDF, vector similarity, hallucination detection, ATS simulation) |
| Reliability/Testing | 9/10 | **192 test functions** — лучший тест-сьют в портфолио: agents, filters, orchestration, PDF, translation |
| Deployability | 8/10 | uv packaging, Dockerfile, .env.example, multi-LLM provider через env |

**Weighted score:** (8×15 + 9×15 + 9×20 + 7×10 + 7×10 + 9×10 + 9×10 + 8×10) / 100 = **83%**

**M2: Confirmed ✅**

**Что реально подтверждает M2:**
- 192 test functions — объективно самый высокий test coverage в портфолио
- Plugin architecture для фильтров — расширяемая без изменения основного pipeline
- Hallucination detection как отдельный модуль — понимание проблемы AI-генерации

**Что снижает M2:**
- Нет docker-compose (только Dockerfile) — затрудняет запуск с одной командой
- SSE streaming — функционально, но нет fallback для медленных соединений

**Что лишь проблема упаковки:** нет скриншотов, sample-data добавлены но не продемонстрированы

---

### 3. finance-mcp-server

**Path:** `03-ai-products/finance-mcp-server`  
**Применимые категории:** все

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 9/10 | Реальная боль финансиста: задавать вопросы по своим данным из AI-ассистента. Предметная логика правильная |
| Solution Design | 9/10 | Registry pattern (вызов без MCP-транспорта), thin MCP layer над services, SQLite zero-deploy — обоснованные решения |
| Implementation Quality | 8/10 | 45 Python файлов, Pydantic модели, чёткое разделение tools/services/db/models/schemas |
| Data/API | 9/10 | MCP Protocol (Anthropic 2024), SQLite с правильной схемой, seed data для demo, import/export tools |
| Web/UI | 6/10 | Next.js UI существует (product-mcp-ui) но связь с MCP-сервером слабо документирована, UI optional |
| AI/Automation | 8/10 | MCP implementation технически корректен, 19 tools с JSON-схемами для интроспекции |
| Reliability/Testing | 8/10 | **45 test functions** по всем бизнес-слоям: KPI, plan/fact, liquidity, contracts, investments, negative cases |
| Deployability | 8/10 | .env.example, seed автоматический, ясные инструкции подключения к Claude Desktop/Cursor |

**Weighted score:** (9×15 + 9×15 + 8×20 + 9×10 + 6×10 + 8×10 + 8×10 + 8×10) / 100 = **83%**

**M2: Confirmed ✅**

**Что реально подтверждает M2:**
- P&L, Cash Flow, NPV/IRR реализованы как Python функции с корректной бизнес-логикой (не CRUD)
- Registry pattern позволяет тестировать без MCP-транспорта — правильное архитектурное решение
- Safe calculator через AST, не eval — понимание security в embedded contexts

**Что снижает M2:**
- Нет Dockerfile в корне и docker-compose — нет single-command запуска
- Web UI (product-mcp-ui) присутствует но слабо интегрирован с сервером в документации

**Что лишь проблема упаковки:** нет скриншотов ответа Claude Desktop

---

### 4. fintech-ab-test-credit-offer

**Path:** `01-data-analytics/fintech-ab-test-credit-offer`  
**Применимые категории:** BP, SD, IQ, Data, Test, Deploy (Web — N/A, AI — N/A)

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 9/10 | Реалистичный fintech сценарий, метрики определены правильно (CR_apply как primary), MDE задан |
| Solution Design | 8/10 | Makefile pipeline с явными зависимостями, SQL + Python разделены, bootstrap augmentation обоснован |
| Implementation Quality | 8/10 | Чистый pandas/scipy код, ясная декомпозиция по модулям (processing/analysis/sample_size/viz/report) |
| Data | 9/10 | 4 SQL запроса с window functions, user-level aggregation, bootstrap траекторий (не построчный sampling) |
| Reliability/Testing | 8/10 | pytest, CI workflow (test + run-analysis), makefile проверяет воспроизводимость, limitations честно задокументированы |
| Deployability | 9/10 | `make all` без внешних зависимостей, Dockerfile, .env.example, полностью автономный |

**Weighted score:** (9×15 + 8×15 + 8×20 + 9×10 + 8×10 + 9×10) / 80 × 100 = **85%**

**M2: Confirmed ✅**

**Что реально подтверждает M2:**
- Welch t-test выбран и обоснован — понимание statistical assumptions, не просто "запустил тест"
- MDE analysis и sample size calculation — уровень product analytics
- Честное ограничение: "directional signal, не окончательное доказательство" — зрелость суждений

**Что снижает M2:**
- 1 Python test file (7 тестов) — pipeline тестирован через make, но unit coverage низкий
- Notebook + HTML presentation дублируют данные без явной роли каждого

**Что лишь проблема упаковки:** README нужно было очистить от учебного контекста (уже сделано)

---

### 5. finance-data-screener

**Path:** `04-web/finance-data-screener`  
**Применимые категории:** все

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 8/10 | Чёткий use case для аналитика: получить финансовые данные без знания API |
| Solution Design | 8/10 | LLM planner → collector → storage → audit — логичный пайплайн, AuditMiddleware как cross-cutting concern |
| Implementation Quality | 8/10 | SQLAlchemy 2.0 async, Alembic migrations, TypeScript React, Pydantic schemas, inspector pattern |
| Data/API | 9/10 | 3 data sources (MOEX ISS, ЦБ РФ, ТАСС), instructor для strict JSON, audit_runs таблица |
| Web/UI | 7/10 | React TypeScript, Tailwind, Recharts, TanStack Table — функционально, нет overcomplexity |
| AI/Automation | 8/10 | GPT-4o-mini + instructor: review flow при неоднозначности — правильный safety механизм |
| Reliability/Testing | 7/10 | **24 test functions** (health, CRUD datasets, AI query, audit) — хорошее покрытие API layer |
| Deployability | 8/10 | 3-сервисный docker-compose, Alembic entrypoint, .env.example с COMPOSE_PROJECT_NAME |

**Weighted score:** (8×15 + 8×15 + 8×20 + 9×10 + 7×10 + 8×10 + 7×10 + 8×10) / 100 = **80%**

**M2: Confirmed ✅**

**Что реально подтверждает M2:**
- Alembic migrations с entrypoint.sh — production-grade database management
- AuditMiddleware как cross-cutting concern — архитектурное мышление
- Review flow (needs_review) — понимание, что LLM может ошибиться

**Что снижает M2:**
- SSL_VERIFY=false было hardcoded (исправлено) — изначально неудачное решение
- Frontend тесты отсутствуют (только backend)

**Что лишь проблема упаковки:** нет скриншотов интерфейса

---

### 6. rf-macro-risk-ai

**Path:** `03-ai-products/rf-macro-risk-ai`  
**Применимые категории:** все

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 8/10 | Реальный финансовый monitoring use case, criteria.json показывает глубокое понимание macro risks |
| Solution Design | 7/10 | Pipeline понятен, multi-provider поддержка, decoupled Telegram reporter — хорошие решения |
| Implementation Quality | 7/10 | LangChain agent, scoring engine с cooldown/novelty, source registry — структурированный код |
| Data/API | 7/10 | Tavily web search, research_ledger для дедупликации источников, GitHub Pages export |
| Web/UI | 6/10 | GitHub Pages dashboard — статический, данные из JSON, работает как live demo |
| AI/Automation | 8/10 | LangChain agent с multi-LLM, criteria с weight/speed/freshness/source_policy — продуманный дизайн |
| Reliability/Testing | 6/10 | 2 test файла (criteria validation + source registry), ограниченное покрытие |
| Deployability | 8/10 | uv, .env.example, Dockerfile, MIT license, CONTRIBUTION.md |

**Weighted score:** (8×15 + 7×15 + 7×20 + 7×10 + 6×10 + 8×10 + 6×10 + 8×10) / 100 = **71%**

**M2: Good Middle / Borderline ⚡**

**Что реально подтверждает M2:**
- criteria.json с 35 критериями (weight, speed, freshness, source_policy) — серьёзная domain work
- Scoring engine с severity multipliers и cooldown — не просто "pass/fail" логика
- Проект основан на upstream, авторский вклад задокументирован (CONTRIBUTION.md)

**Что снижает M2:**
- Всего 9 Python файлов — небольшой объём собственного кода
- 2 test файла — недостаточное покрытие для scoring logic
- BOT_REPORTER_DIR — локальная путь-зависимость

---

### 7. fedresurs-mvp

**Path:** `01-data-analytics/fedresurs-mvp`  
**Применимые категории:** все (Web/UI применимо: Flask UI + HTML dashboard)

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 9/10 | Реальная профессиональная задача: оценка активов при банкротстве по рыночным аналогам |
| Solution Design | 8/10 | Два независимых движка (статистический + LLM agentic) — правильное разделение для разных типов активов |
| Implementation Quality | 7/10 | stdlib-минимализм обоснован для локального инструмента, но несколько overlapping скриптов (fedresurs.py vs fedresurs_mvp.py) |
| Data/API | 8/10 | Fedresurs public API, multi-provider search (Tavily/Brave/Google/Jina), SQLite с идемпотентными миграциями |
| Web/UI | 5/10 | Flask UI + HTML dashboard — базовые, функциональные |
| AI/Automation | 8/10 | Agentic loop с self-directed searches, multi-provider LLM, batch processing |
| Reliability/Testing | 8/10 | **47 test functions**: parsers, classifiers, P25/P50/P75 calculations, price extraction |
| Deployability | 6/10 | Dockerfile, .env.example, demo_seed.py добавлен, но Chrome bookmarks — Windows-specific dependency |

**Weighted score:** (9×15 + 8×15 + 7×20 + 8×10 + 5×10 + 8×10 + 8×10 + 6×10) / 100 = **75%**

**M2: Good Middle / Borderline ⚡**

**Что реально подтверждает M2:**
- 4 price scenarios (auction/lot/wholesale/retail) — точное понимание оценочной методологии при банкротстве
- P25/P50/P75 с confidence levels по числу источников — профессиональный подход к неопределённости
- 47 тестов бизнес-логики — тестируется именно предметная область

**Что снижает M2:**
- Chrome bookmarks как основной input — Windows-only, ограничивает reusability
- fedresurs.py vs fedresurs_mvp.py — дублирование без четкой роли каждого файла
- Flask UI минимальный

**Что лишь проблема упаковки:** нет скриншотов, demo_seed уже добавлен

---

### 8. leadgen-n8n-system

**Path:** `02-automation/leadgen-n8n-system`  
**Применимые категории:** BP, SD, IQ, Data, AI/Automation, Test, Deploy (Web — N/A: n8n UI)

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 8/10 | Реалистичный B2B сценарий, правильно поставленная задача (не просто "рассылка") |
| Solution Design | 9/10 | 11 workflow с чёткими ролями, error handler как отдельный workflow, shadow validation — архитектурное мышление |
| Implementation Quality | 7/10 | n8n JSON ограничивают review кода, но структура workflow продуманная; docker-compose setup корректный |
| Data | 7/10 | PostgreSQL для state persistence, webhook integration |
| AI/Automation | 8/10 | Multi-LLM consensus (не один вызов), human-in-the-loop паттерн, warmth decay математика |
| Reliability/Testing | 5/10 | 1 test file — только структурная валидация JSON, без функциональных тестов |
| Deployability | 8/10 | docker-compose, .env.example, порядок импорта описан, mock payload задокументирован |

**Weighted score:** (8×15 + 9×15 + 7×20 + 7×10 + 8×10 + 5×10 + 8×10) / 90 × 100 = **77%**

**M2: Good Middle / Borderline ⚡**

**Что реально подтверждает M2:**
- Shadow validation workflow — серьёзный инженерный подход к production deployment
- Warmth decay + Global error handler показывают системное мышление
- 11 workflow как отдельные, заменяемые единицы

**Что снижает M2:**
- Нет функциональных тестов n8n workflows — только JSON validation
- Нет скриншотов Canvas с реальными flows (сложно оценить качество без них)

---

### 9. mini-crm-fastapi-react

**Path:** `04-web/mini-crm-fastapi-react`  
**Применимые категории:** все (AI — N/A)

| Категория | Оценка | Обоснование |
|-----------|:------:|-------------|
| Business Problem | 7/10 | Чёткая задача — внутренний CRM с Google Sheets выгрузкой. Google integration — реальный differentiator |
| Solution Design | 7/10 | FastAPI + React + Google OAuth, правильная роутинг структура, SECURITY.md |
| Implementation Quality | 7/10 | SQLAlchemy models, Pydantic schemas, TypeScript React, Google API integration |
| Data/API | 7/10 | Google Drive/Sheets API v3/v4, OAuth 2.0 Web Application flow, SQLite |
| Web/UI | 7/10 | React TypeScript, страницы Clients/Deals/Tasks/Settings/Reports, формы с фильтрацией |
| Reliability/Testing | 5/10 | 1 test file (smoke tests) — очень ограниченное покрытие |
| Deployability | 8/10 | docker-compose, SECURITY.md, fill_test_data.py, .env.example |

**Weighted score:** (7×15 + 7×15 + 7×20 + 7×10 + 7×10 + 5×10 + 8×10) / 90 × 100 = **69%**

**M2: M1+/M2- ⚠️**

**Что реально подтверждает M2:**
- Google OAuth 2.0 Web Application flow реализован полностью (не Service Account)
- SECURITY.md документирует работу с секретами — зрелость в отношении security
- Full-stack стек собран корректно

**Что снижает M2:**
- Smoke tests только — нет unit или integration тестов для бизнес-логики
- 24 Python файла, но функциональная глубина ограничена

---

## Все проекты — Сводная таблица M2

| Rank | Project/System | M2 % | Уровень | Portfolio % | Reusability % | Business Value | Type | Current Showcase? | Recommendation |
|------|---------------|:----:|---------|:-----------:|:-------------:|:-------------:|------|:-----------------:|----------------|
| 1 | **SVO System** | 86% | M2 Confirmed | 88% | 65% | Очень высокий | Production | ✅ | KEEP |
| 2 | **hr-breaker** | 83% | M2 Confirmed | 83% | 85% | Высокий | Production-quality | ✅ | KEEP |
| 3 | **finance-mcp-server** | 83% | M2 Confirmed | 82% | 85% | Очень высокий | Production-quality | ✅ | KEEP |
| 4 | **fintech-ab-test** | 85% | M2 Confirmed | 87% | 70% | Высокий | Complete case | ✅ | KEEP |
| 5 | **finance-data-screener** | 80% | M2 Confirmed | 80% | 75% | Высокий | Production-quality | ✅ | KEEP |
| 6 | **leadgen-n8n-system** | 77% | Good Middle | 75% | 75% | Высокий | Template | ✅ | KEEP |
| 7 | **fedresurs-mvp** | 75% | Good Middle | 78% | 60% | Очень высокий | Production-quality | ✅ | KEEP |
| 8 | **rf-macro-risk-ai** | 71% | Good Middle | 80% | 80% | Высокий | Production | ✅ | KEEP |
| 9 | **mini-crm-fastapi-react** | 69% | M1+/M2- | 73% | 70% | Средний | MVP | ✅ | QUESTIONABLE |
| 10 | **hotel-booking-n8n** | 64% | M1+/M2- | 68% | 80% | Средний | Demo | ❌ | PROMOTE to supporting |
| 11 | **team-ai-bot** | 67% | M1+/M2- | 65% | 60% | Средний | MVP | ❌ | SUPPORTING |
| 12 | **personal-rag-assistant** | 66% | M1+/M2- | 65% | 55% | Средний | MVP | ❌ | SUPPORTING |
| 13 | **tg-digest-pipeline** | 62% | M1+/M2- | 40% | 25% | Средний | Personal tool | ❌ | ARCHIVE/PRIVATE |
| 14 | **bankrot-trades-scraper** | 62% | M1+/M2- | 58% | 50% | Средний | MVP | ❌ | SUPPORTING |
| 15 | **finsight** | 60% | M1+/M2- | 65% | 65% | Средний | MVP | ❌ | SUPPORTING |
| 16 | **superstore-retail-analytics** | 63% | M1+/M2- | 72% | 60% | Средний | EDA case | ❌ | SUPPORTING |
| 17 | **site (Astro portfolio)** | 72% | Good Middle | 80% | N/A | Высокий | Meta | N/A | META |
| 18 | **bots-platform** | 57% | Junior+/M1 | 42% | 30% | Средний | Production | ❌ | KEEP private |
| 19 | **data-work-utilities** | 57% | Junior+/M1 | 55% | 50% | Средний | MVP | ❌ | NO |
| 20 | **yandex-google-sync** | 57% | Junior+/M1 | 57% | 55% | Низкий | Utility | ❌ | NO |
| 21 | **crewai-multiagent** | 57% | Junior+/M1 | 55% | 50% | Средний | Demo | ❌ | NO |
| 22 | **dostaffkin** | 55% | Junior+/M1 | 55% | 50% | Низкий | Website | ❌ | CONSIDER для web demo |
| 23 | **wb-sales-commercial-analysis** | 50% | Junior+/M1 | 35% | 30% | Средний | One-off | ❌ | BLOCKED (client data) |
| 24 | **currency-travel-api** | 51% | Junior+/M1 | 52% | 55% | Низкий | Utility | ❌ | NO |
| 25 | **seo-mcp-bot** | 52% | Junior+/M1 | 50% | 55% | Низкий | Niche | ❌ | NO |
| 26 | **tg-catalog-analyzer** | 48% | Prototype | 45% | 35% | Низкий | Narrow | ❌ | NO |
| 27 | **team-tg-bot-vc** | 45% | Prototype | 42% | 40% | Низкий | Simple | ❌ | NO |
| 28 | **autonomous-agents** | 43% | Prototype | 40% | 35% | Низкий | Unclear | ❌ | NO |
| 29 | **pptx-redesigner** | 42% | Prototype | 40% | 40% | Низкий | Scripts | ❌ | NO |

---

## Screenshot Audit

| Project | Screenshot Value | Required? | Best Demonstration |
|---------|:----------------:|:---------:|-------------------|
| SVO System | Высокая | YES | Live svorazbor.ru + bot UI flow |
| hr-breaker | Высокая | YES | Web UI → processing → PDF result |
| finance-mcp-server | Высокая | YES | Claude Desktop: вопрос → MCP tool response |
| fintech-ab-test | Низкая | NO | nbviewer notebook + final_report.md достаточны |
| finance-data-screener | Средняя | NICE TO HAVE | Коллекция данных + chart в Showcase |
| rf-macro-risk-ai | Низкая | NO | GitHub Pages live demo достаточен |
| fedresurs-mvp | Средняя | NICE TO HAVE | CLI output: 4 price scenarios |
| leadgen-n8n-system | Высокая | YES | n8n Canvas скриншоты workflow |
| mini-crm-fastapi-react | Средняя | NICE TO HAVE | UI таблицы + Google Sheets export |
| hotel-booking-n8n | Средняя | NICE TO HAVE | n8n workflow Canvas |
| team-ai-bot | Низкая | NO | README достаточен |
| superstore-retail-analytics | Низкая | NO | HTML dashboard = живой demo |
| finsight | Низкая | NO | docker compose + curl достаточно |

---

## Этап 8. Web Development

**Оценка: SUFFICIENT**

| Web Project | Стек | Сложность | Уровень |
|-------------|------|:---------:|---------|
| svo-payouts-website | Next.js 14 + TypeScript + Tailwind + Playwright | HIGH | Strong |
| finance-data-screener frontend | React + TypeScript + TanStack + Recharts | MEDIUM | Good |
| mini-crm-fastapi-react frontend | React + TypeScript | MEDIUM | Good |
| dostaffkin | Angular + TypeScript | MEDIUM | Good |
| finsight frontend | React + JSX (not TS) | LOW | Moderate |
| data-work-utilities frontend | React + TypeScript | LOW | Moderate |

**Что доказывает:**
- Next.js с App Router, Playwright E2E, CI/CD — production-grade frontend
- React TypeScript с proper state management
- Angular SPA

**Чего не хватает:**
- Нет чистого landing page / marketing site showcase (site/ — Astro, но он про автора, не case)
- Нет примера сложного CSS/animation frontend
- dostaffkin (единственный Angular кейс) имеет M2 = 55% — слабоват как showcase

**Рекомендация:** web development **достаточно доказан** через svo-payouts-website (production Next.js с E2E). Отдельного "web-only" showcase не нужно.

---

## Этап 9. Best Finance × Software Cases

Проекты, где финансовая логика **реализована в коде** (не только упоминается в README):

| # | Project | Что именно в коде |
|---|---------|-------------------|
| 1 | **finance-mcp-server** | P&L: revenue-cogs=gross_profit→margin%. Cash Flow. NPV через дисконтирование. IRR методом бисекции. Liquidity forecast: opening_cash + Σinflows - Σoutflows. Contract risk scan с категоризацией. Plan vs Fact с отклонениями в % |
| 2 | **fintech-ab-test-credit-offer** | CR_apply = offer_apply/offer_impression. User-level Welch t-test. MDE calculation. Sample size by power analysis. ARPU. Approval rate. Bootstrap траекторий (не построчный sampling) |
| 3 | **fedresurs-mvp** | P25/P50/P75 квантили по рыночным аналогам. target_price = P25 × area × 0.90. Confidence levels (low/medium/high) по числу источников. 4 price scenarios: auction/lot/wholesale/retail. Decision logic: auction_interesting / overpriced_skip / public_offer_wait |
| 4 | **rf-macro-risk-ai** | Weighted scoring: 35 criteria × weight. Severity multipliers (quiet/watch/triggered/critical). Cooldown/novelty ledger. Deposit access risk block (5 criteria с отдельными весами bank_holidays=40, payment_infrastructure=20...) |
| 5 | **SVO System** | Расчёт федеральных выплат по видам с коэффициентами. Regional надбавки. "Цена ожидания" для branch B. Payout breakdown по категориям. |
| 6 | **finance-data-screener** | MOEX ISS API: securities + marketdata join. ЦБ РФ daily JSON. LLM-планировщик → structured collection plan. Audit log с duration |

---

## Этап 11. Пересборка Showcase

### KEEP (8 проектов)

1. **finance-mcp-server** — флагман Finance × AI × Python
2. **SVO System** — единственный production end-to-end system
3. **hr-breaker** — strongest technical project (192 tests, AI engineering)
4. **fintech-ab-test-credit-offer** — best Data/Analytics case
5. **finance-data-screener** — full-stack financial AI app
6. **rf-macro-risk-ai** — Finance × AI с live demo
7. **fedresurs-mvp** — Finance domain depth (bankruptcy valuation)
8. **leadgen-n8n-system** — B2B automation / n8n thinking

### QUESTIONABLE

- **mini-crm-fastapi-react** (M2: 69%) — добавляет web + Google integration, но слабые тесты. Полезен если нужен ninth "business app" кейс. Держать как supporting.

### PROMOTE TO SUPPORTING (на GitHub, не на витрине)

- **hotel-booking-n8n** — хороший n8n case с документацией, поддерживает leadgen
- **superstore-retail-analytics** — HTML dashboard как живой demo
- **finsight** — quick demo of financial AI + Claude API integration

### REMOVE FROM MAIN SHOWCASE

- **bots-platform** — реальные production боты, но нет тестов, нет Docker, плохо документированы
- **tg-digest-pipeline** — технически впечатляет, но личный инструмент с нулевой reusability
- **crewai-multiagent** — слабее hr-breaker, дублирует AI story
- Всё с M2 < 55%

---

## Этап 13. Общая оценка

### Overall M2 Confidence: **82%**

Пять проектов — finance-mcp-server, hr-breaker, SVO System, fintech-ab-test, finance-data-screener — уверенно доказывают Middle. Ещё три (leadgen, fedresurs, rf-macro-risk-ai) на хорошей Borderline. Этого достаточно для позиции "крепкий Middle".

### Finance + Tech: **90%**

Самый сильный аспект портфолио. Финансовая логика реализована в коде корректно и предметно-осмысленно в 6 проектах.

### Web Development: **72%** (SUFFICIENT)

svo-payouts-website + finance-data-screener frontend + mini-crm достаточно. Нет ultra-strong pure frontend showcase, но это не критично для заявленного позиционирования.

### AI / Automation: **82%**

hr-breaker (Pydantic-AI, 8-filter pipeline), finance-mcp-server (MCP), leadgen-n8n (multi-LLM consensus), rf-macro-risk-ai (LangChain) — хороший диапазон.

### Applied Business Software: **80%**

Реальные задачи, рабочий код, production deployment. Не toy examples.

---

### Ответы на ключевые вопросы

**1. Доказывает ли портфолио уровень крепкого Middle?**
Да. Однозначно.

**2. На сколько процентов?**
82% — с запасом выше порога Middle.

**3. Какие 5 проектов лучше всего это доказывают?**
1. hr-breaker (192 тестa, сложная AI архитектура)
2. SVO System (production, E2E, CI/CD)
3. finance-mcp-server (Finance domain depth, MCP, 45 тестов)
4. fintech-ab-test-credit-offer (методология + pipeline)
5. finance-data-screener (full-stack, async, Alembic, LLM)

**4. Какие текущие showcase слабее остальных?**
mini-crm-fastapi-react (M2: 69%) — тесты слабые. rf-macro-risk-ai (M2: 71%) — небольшой объём авторского кода.

**5. Есть ли сильные невитринные проекты?**
Нет — все M2 80%+ уже в showcase. hotel-booking-n8n (M2: 64%) — хороший supporting.

**6. Достаточно ли доказан web development?**
Да — svo-payouts-website производственный Next.js с Playwright достаточен.

**7. Где реально нужны screenshots?**
Обязательно: hr-breaker (web UI), leadgen-n8n (Canvas), SVO System (bot + site flow), finance-mcp-server (Claude Desktop response).

**8. Каков минимальный объём работ перед публикацией?**
- 4 screenshot sets (обязательно)
- Убедиться что .gitignore не пропустит клиентские данные в wb-sales
- Проверить что все .env.example актуальны
- Создать GitHub repos с topics

**Итог:** портфолио доказывает Middle+. Флагманский кластер (5 M2-Confirmed проектов) сильный. Finance × Tech — реальный differentiator.
