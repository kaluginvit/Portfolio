# Portfolio Final Classification

> Дата: 2026-09-07  
> M2 Scores: из `M2_UPGRADE_RESULT.md` (обновлённые) и `PORTFOLIO_M2_AUDIT.md`

---

## Таблица классификации

| Project / System | M2 % | Tier | Main Competency | Why | Destination |
|-----------------|-----:|------|-----------------|-----|-------------|
| **SVO System** (svo-payments-bot + svo-payouts-website) | 86% | **A** | Production E2E / Web / Backend | Единственный реально работающий production system. Full CI/CD, FSM, Playwright E2E, реальные пользователи. Уникален в портфолио. | Stay |
| **fintech-ab-test-credit-offer** | 85% | **A** | Data / Analytics / Finance | Лучший методологический аналитический кейс. Welch t-test, MDE, Makefile pipeline, CI — завершённый и воспроизводимый. | Stay |
| **leadgen-n8n-system** | 84% | **A** | Automation / n8n / Multi-LLM | Единственный глубокий n8n showcase. Shadow validation, multi-LLM consensus, warmth decay — системное мышление в автоматизации. | Stay |
| **hr-breaker** | 83% | **A** | AI Engineering / Python | Технически сильнейший проект. 192 теста, 8-слойный pipeline, Pydantic-AI, SSE streaming, anti-hallucination. | Stay |
| **finance-mcp-server** | 83% | **A** | Finance AI / MCP / Python | Флагман Finance × AI. MCP протокол, P&L/NPV/IRR в коде, 45 тестов, registry pattern без транспорта. | Stay |
| **fedresurs-mvp** | 82% | **A** | Finance Domain / Agentic AI | Глубокая предметная область — оценка при банкротстве. P25/P50/P75, 4 ценовых сценария, 64 теста. Уникальная ниша. | Stay |
| **finance-data-screener** | 80% | **A** | Full-Stack / Financial APIs | Полноценный full-stack: FastAPI + React TS + PostgreSQL + Alembic + 3 финансовых API + LLM planner. | Stay |
| **rf-macro-risk-ai** | 80% | **B** | Finance AI / LangChain | Сильный Finance AI с live demo. Но Finance+AI уже хорошо закрыт в Tier A (finance-mcp-server, fedresurs). Macro monitoring — уникальный angle. | Stay |
| **mini-crm-fastapi-react** | 78% | **B** | Full-Stack / Google OAuth | После M2 upgrade хорошее качество. Добавляет Google OAuth story. Но web уже закрыт SVO + screener. Tier B логичен. | Stay |
| **team-ai-bot** | 67% | **B** | RAG / Telegram / Corporate | Корпоративный RAG bot с Pinecone. Добавляет enterprise AI use case. Достаточно качественный для публичного показа. | Stay |
| **hotel-booking-n8n** | 64% | **B** | n8n Automation | Хорошо задокументированный n8n case (graduation project). Поддерживает leadgen, добавляет hospitality/ops automation angle. | Stay |
| **superstore-retail-analytics** | 63% | **B** | EDA / Dashboards / Retail | HTML dashboard — живой demo без сервера. Добавляет EDA/retail analytics angle, которого нет в Core. | Stay |
| **bankrot-trades-scraper** | 62% | **C** | Web Scraping / Data Collection | Companion к fedresurs-mvp. Показывает scraping + SQLite pipeline. Достаточно качественный, не стыдно держать публично. | Stay |
| **personal-rag-assistant** | 66% | **C** | RAG / Haystack / Pinecone | Показывает RAG architecture с Haystack + Docling + Pinecone. Другой tech stack vs team-ai-bot. GitHub-only норм. | Stay |
| **tg-digest-pipeline** | 62% | **C** | Complex Pipelines / Neo4j | Технически самый сложный личный инструмент (66py, Neo4j, Pinecone, LangChain). Не подходит для витрины, но интересен как code sample. | Stay |
| **finsight** | 60% | **C** | Claude API / React / Finance | Показывает прямую интеграцию Claude API в web-приложении. Простой, но функциональный. Docker compose работает. | Stay |
| **bots-platform** | 57% | **C** | Telegram Bots / Production | Реально работающие production боты (3 штуки). Нет тестов и Docker, но живой код. Держать публично, не показывать. | Stay |
| **dostaffkin** | 55% | **C** | Angular / Corporate Web | Единственный Angular проект. Добавляет frontend diversity. Docker compose, online demo. GitHub-only достаточно. | Stay |
| **data-work-utilities** | 57% | **D** | Full-Stack / AI | Нет тестов, нет Docker. Перекрывается finance-data-screener (который сильнее по всем осям). Не добавляет ничего нового. | Move |
| **wb-sales-commercial-analysis** | 50% | **D** | Data / Analytics | Заблокирован клиентскими данными. Нет Docker, нет тестов. Не подходит для публикации. | Move |
| **currency-travel-api** | 51% | **D** | Telegram Bot / Utility | Узкая утилита без тестов. Дублирует bot story, но слабее всех остальных ботов. Ничего не добавляет. | Move |
| **pptx-redesigner** | 42% | **D** | Python Scripts | Набор скриптов без тестов, без Docker, без внятной бизнес-задачи. Прототип. | Move |
| **yandex-google-sync** | 57% | **D** | Sync / Integration | Utility без тестов. Нишевая задача (Яндекс→Google), низкая business value для целевой аудитории. | Move |
| **autonomous-agents** | 43% | **D** | AI Platform | Нечёткая задача, нет тестов, прототип. Дублирует более сильные AI проекты. | Move |
| **crewai-multiagent** | 57% | **D** | CrewAI / Multi-Agent | Демо CrewAI без тестов. Значительно слабее hr-breaker. Дублирует AI story без добавления ценности. | Move |
| **seo-mcp-bot** | 52% | **D** | MCP / SEO | Нишевый MCP инструмент без тестов. OAuth ограничения. MCP story лучше закрыта finance-mcp-server. | Move |
| **team-tg-bot-vc** | 45% | **D** | Telegram Bot / Task Tracker | Слишком простой. Нет тестов. Не добавляет компетенции, которой нет в других проектах. | Move |
| **tg-catalog-analyzer** | 48% | **D** | LLM / Categorization | Узкий инструмент без тестов. Не имеет самостоятельной portfolio value. | Move |
| **site** (Astro portfolio) | 72% | **META** | Portfolio Site | Мета-проект: сам сайт-портфолио. Остаётся, не классифицируется. | Stay |

---

## Итог по тирам

### Tier A — Core Showcase (7)

| # | Project | M2 % | Главная компетенция |
|---|---------|-----:|---------------------|
| 1 | SVO System | 86% | Production E2E / Backend + Web |
| 2 | fintech-ab-test-credit-offer | 85% | Data Analytics / Finance |
| 3 | leadgen-n8n-system | 84% | Automation / n8n |
| 4 | hr-breaker | 83% | AI Engineering / Python |
| 5 | finance-mcp-server | 83% | Finance AI / MCP |
| 6 | fedresurs-mvp | 82% | Finance Domain / Agentic AI |
| 7 | finance-data-screener | 80% | Full-Stack / Financial APIs |

**Покрытые компетенции:** Corporate Finance, Business Analysis, Python, Data/SQL, AI/LLM, Automation, Backend, Web, API/Integrations, Production Delivery

### Tier B — More Projects (5)

| # | Project | M2 % | Главная компетенция |
|---|---------|-----:|---------------------|
| 1 | rf-macro-risk-ai | 80% | Macro Risk AI / LangChain |
| 2 | mini-crm-fastapi-react | 78% | CRM / Google OAuth |
| 3 | team-ai-bot | 67% | Corporate RAG / Telegram |
| 4 | hotel-booking-n8n | 64% | n8n Automation / Ops |
| 5 | superstore-retail-analytics | 63% | EDA / Dashboards |

### Tier C — GitHub Only (6)

| # | Project | M2 % | Почему GitHub-only |
|---|---------|-----:|--------------------|
| 1 | personal-rag-assistant | 66% | RAG architecture demo, другой tech stack |
| 2 | bots-platform | 57% | Реальный production code, нет тестов |
| 3 | bankrot-trades-scraper | 62% | Companion к fedresurs, scraping pipeline |
| 4 | tg-digest-pipeline | 62% | Сложный pipeline, личный контекст |
| 5 | finsight | 60% | Claude API + React demo |
| 6 | dostaffkin | 55% | Angular diversity, docker + demo |

### Tier D — Portfolio_back (10)

| # | Project | M2 % | Причина |
|---|---------|-----:|---------|
| 1 | data-work-utilities | 57% | Нет тестов/Docker, перекрывается screener |
| 2 | wb-sales-commercial-analysis | 50% | Клиентские данные, нет тестов |
| 3 | crewai-multiagent | 57% | Слабее hr-breaker, дублирует AI story |
| 4 | yandex-google-sync | 57% | Нишевая утилита, нет тестов |
| 5 | currency-travel-api | 51% | Узкая утилита, нет тестов |
| 6 | seo-mcp-bot | 52% | Ограниченный, нет тестов |
| 7 | tg-catalog-analyzer | 48% | Узкий инструмент, нет тестов |
| 8 | team-tg-bot-vc | 45% | Слишком простой |
| 9 | autonomous-agents | 43% | Прототип, нечёткая задача |
| 10 | pptx-redesigner | 42% | Набор скриптов, прототип |

---

## Проверка: A + B + C + D + META = всего проектов

```
Tier A:    7
Tier B:    5
Tier C:    6
Tier D:   10
META:      1 (site)
─────────────
ИТОГО:    29  ✓  (= независимых активных проектов по Census)
```

Также в `_Portfolio_back` переносятся материалы `99-archive/` (30 объектов: 19 учебных + 11 прототипов) — они не классифицированы по тирам, так как не являются независимыми проектами по Census.

---

## Спорные решения (топ-5)

1. **rf-macro-risk-ai → Tier B (не A).**  
   После M2 upgrade стал 80% — формально M2 Confirmed. Но Finance+AI уже закрыт finance-mcp-server и fedresurs. Fork-based с 9 собственными Python-файлами — небольшой объём. Tier B даёт ему публичность без размытия Core.

2. **mini-crm-fastapi-react → Tier B (не A).**  
   После upgrade — 78%. Google OAuth — реальный differentiator. Но web уже сильно закрыт SVO (production) и finance-data-screener (full-stack). В Tier A это был бы "восьмой веб-проект" вместо фокуса.

3. **bots-platform → Tier C (не D).**  
   Реально работающие production боты. Несмотря на отсутствие тестов и Docker, живой production-код имеет ценность как code sample. Держать публично, не показывать.

4. **tg-digest-pipeline → Tier C (не D).**  
   Технически самый сложный личный инструмент (Neo4j + Pinecone + LangChain + 66py). Низкая reusability, но интересен как code sample для технических читателей. Без публичного контекста работает как "hidden gem".

5. **team-ai-bot → Tier B (не C).**  
   M2: 67% — формально не M2 Confirmed. Но корпоративный RAG-бот (28py, Pinecone, docker-compose, 3 test files) добавляет enterprise AI use case, которого нет в Core в явном виде (hr-breaker — не enterprise RAG). Хорошо документирован, понятная задача.
