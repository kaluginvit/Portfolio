# Portfolio Project Census

> Дата: 2026-09-07
> Метод: рекурсивный осмотр директорий + фактическая проверка кода, тестов, конфигурации
> Предыдущие отчёты не использовались как источник числа проектов

---

## Методология определения границ проектов

**Независимый проект/система:** имеет собственную задачу, кодовую базу, может рассматриваться как отдельный продукт, инструмент или законченный case.

**Не считается отдельным проектом:** frontend + backend одного продукта, парные компоненты одной системы (website + bot), подпапки одного приложения, artifacts/generated, vendor code.

**Пограничные случаи:**
- `svo-payments-bot` + `svo-payouts-website` → **ОДИН SYSTEM** (одна бизнес-задача, парные компоненты)
- `finance-mcp-server` (product-mcp + product-mcp-ui) → **ОДИН SYSTEM** (сервер + опциональный UI)
- `bots-platform` (модератор + репортёр + сторож) → **ОДИН SYSTEM** (единая операционная платформа)
- `seo-mcp-bot` (mcp/ + yandex-wordstat-mcp/) → **ОДИН SYSTEM** (SEO MCP инструментарий)

---

## Полная таблица

| # | Project / System | Path(s) | Type | Status | Components | Independent Project? | Notes |
|---|-----------------|---------|------|--------|------------|:--------------------:|-------|
| **01-DATA-ANALYTICS** |
| 1 | data-work-utilities | 01-data-analytics/data-work-utilities | Full-stack tool | MVP | React+Python+AI, 2py+6ts, no tests, no docker | YES | Слабая deployability |
| 2 | fedresurs-mvp | 01-data-analytics/fedresurs-mvp | AI tool + analytics | MVP | Flask UI, 12py, 47 test fns, Dockerfile | YES | Chrome dependency |
| 3 | fintech-ab-test-credit-offer | 01-data-analytics/fintech-ab-test-credit-offer | Analytical case | Complete | 7py, Makefile, Dockerfile, CI | YES | Сильный analytical case |
| 4 | superstore-retail-analytics | 01-data-analytics/superstore-retail-analytics | EDA + dashboard | Complete | 2py, HTML dashboard, Dockerfile | YES | Стандартный публичный датасет |
| 5 | wb-sales-commercial-analysis | 01-data-analytics/wb-sales-commercial-analysis | Commercial analysis | One-off | 3py, no tests, no docker, client data risk | YES | Клиентские данные — не публиковать |
| **02-AUTOMATION** |
| 6 | bankrot-trades-scraper | 02-automation/bankrot-trades-scraper | Scraper + DB | MVP | 9py, Dockerfile, review UI | YES | Companion к fedresurs-mvp |
| 7 | currency-travel-api | 02-automation/currency-travel-api | Telegram bot | MVP | Python+aiogram, Dockerfile | YES | Simple utility |
| 8 | hotel-booking-n8n | 02-automation/hotel-booking-n8n | n8n automation | Demo/Graduation | n8n JSON exports, HTML form, 0py | YES | Выпускной проект курса n8n |
| 9 | leadgen-n8n-system | 02-automation/leadgen-n8n-system | n8n automation | Template | 11 workflow JSONs, docker-compose | YES | Сложная автоматизация |
| 10 | pptx-redesigner | 02-automation/pptx-redesigner | Python scripts | Prototype | ~6py scripts, no tests, no docker | YES | Набор скриптов, не система |
| 11 | yandex-google-sync | 02-automation/yandex-google-sync | Sync utility | MVP | Python, Dockerfile, no tests | YES | Utility без тестов |
| **03-AI-PRODUCTS** |
| 12 | autonomous-agents | 03-ai-products/autonomous-agents | AI platform | Prototype | FastAPI+HTML, docker-compose, unclear purpose | YES | Нечёткая задача |
| 13 | bots-platform | 03-ai-products/bots-platform | 3 Telegram bots | Production | 21py (3 sub-bots), no Docker, no tests | YES (system) | Реальные production боты |
| 14 | crewai-multiagent | 03-ai-products/crewai-multiagent | AI agent system | MVP | CrewAI+FastAPI, docker-compose, no tests | YES | Демо CrewAI |
| 15 | finance-mcp-server | 03-ai-products/finance-mcp-server | Finance AI layer | Production-quality | product-mcp(45py) + product-mcp-ui(Next.js), 45 test fns, Dockerfile | YES (system) | Флагман |
| 16 | hr-breaker | 03-ai-products/hr-breaker | AI tool | Production-quality | 95py, 192 test fns, Dockerfile, uv | YES | Технически сильнейший |
| 17 | personal-rag-assistant | 03-ai-products/personal-rag-assistant | RAG Telegram bot | MVP | 19py, 2 test files, Dockerfile | YES | Educational RAG demo |
| 18 | rf-macro-risk-ai | 03-ai-products/rf-macro-risk-ai | AI + finance analytics | Production | 9py, 2 test files, Dockerfile, live demo | YES | Fork-based, contribution documented |
| 19 | seo-mcp-bot | 03-ai-products/seo-mcp-bot | MCP tool | MVP | 2 sub-projects, no tests | YES (system) | Ограниченный OAuth |
| 20 | **SVO System** | 03-ai-products/svo-payments-bot + 04-web/svo-payouts-website | Web+Telegram system | Production | 57py+78ts, 22+2 test files, 4 CI workflows, live site | YES (system, 2 components) | Единственный production e2e system |
| 21 | team-ai-bot | 03-ai-products/team-ai-bot | RAG Telegram bot | MVP | 28py, 3 test files, docker-compose | YES | Corporate RAG |
| 22 | team-tg-bot-vc | 03-ai-products/team-tg-bot-vc | Task tracker bot | Prototype | Small Python, Dockerfile, no tests | YES | Too simple for showcase |
| 23 | tg-catalog-analyzer | 03-ai-products/tg-catalog-analyzer | LLM categorizer | MVP | ~6py, Dockerfile, no tests | YES | Narrow tool |
| 24 | tg-digest-pipeline | 03-ai-products/tg-digest-pipeline | RAG pipeline | Personal tool | 66py (complex), 1 test file, Dockerfile | YES | Personal, hard to showcase |
| **04-WEB** |
| 25 | dostaffkin | 04-web/dostaffkin | Corporate website | MVP | Angular, docker-compose, 0 tests, online demo | YES | Web competence demo |
| 26 | finance-data-screener | 04-web/finance-data-screener | Full-stack AI app | Production-quality | 31py+4ts, 24 test fns, docker-compose, CI | YES | Сильный full-stack |
| 27 | finsight | 04-web/finsight | AI data analyzer | MVP | 5py, React JSX, docker-compose, 1 test file | YES | Simple but functional |
| 28 | mini-crm-fastapi-react | 04-web/mini-crm-fastapi-react | CRM + Google OAuth | MVP | 24py+3ts, docker-compose, 1 test file | YES | Google integration differentiator |
| **SITE** |
| 29 | site | site/ | Portfolio website | Production | Astro+TypeScript, CI for GitHub Pages | YES (meta-project) | Собственный сайт |
| **99-ARCHIVE (выборка)** |
| A1 | ai-automation-lessons | 99-archive/ai-automation-lessons | Educational | Archive | Python lesson project | NO — Educational | |
| A2 | ai-bot-lessons | 99-archive/ai-bot-lessons | Educational | Archive | Python lesson | NO — Educational | |
| A3 | ai-coding-lessons | 99-archive/ai-coding-lessons | Educational | Archive | Python + Go server lesson | NO — Educational | Has interesting Go component |
| A4–A19 | *(15 lesson projects)* | 99-archive/api-lessons ... sqlite-lesson | Educational | Archive | Various lessons | NO — Educational | |
| A20 | ux-reviewer-agent | 99-archive/ux-reviewer-agent | Prototype | Archive | FastAPI+React, docker-compose, incomplete | Subproject/Prototype | Incomplete |
| A21 | local-ai-agent | 99-archive/local-ai-agent | Prototype | Archive | Python agent with memory | Experiment | |
| A22 | desktop-reminder | 99-archive/desktop-reminder | Utility | Archive | Tkinter app | Utility | |
| A23 | mini-booking-system | 99-archive/mini-booking-system | Prototype | Archive | Tkinter + PostgreSQL | Prototype | |
| A24 | password-generator | 99-archive/password-generator | Utility | Archive | Tkinter, .key file present | Utility | Не публиковать |
| A25 | recipe-search-bot | 99-archive/recipe-search-bot | Prototype | Archive | Telegram bot | Prototype | |
| A26 | recurring-payments-reminder | 99-archive/recurring-payments-reminder | Prototype | Archive | Telegram bot | Prototype | |
| A27 | expert-project | 99-archive/expert-project | Prototype | Archive | OpenAI assistant, Dockerfile | Prototype | |
| A28 | docker-vps-project | 99-archive/docker-vps-project | Educational | Archive | Telegram + Docker lesson | Educational | |
| A29 | loki-grafana-stack | 99-archive/loki-grafana-stack | Prototype | Archive | Single main.py stub | Prototype | Minimal |
| A30 | prompting-case | 99-archive/prompting-case | Research | Archive | Prompt comparison study | Research case | |

---

## Итоговый подсчёт

### Активные независимые проекты/системы: **29**

| Категория | Кол-во |
|-----------|:------:|
| Полноценные production-level системы | 5 |
| MVP/рабочие инструменты | 14 |
| Прототипы / незавершённые | 5 |
| Утилиты / узкоспециализированные | 3 |
| Мета-проект (сайт портфолио) | 1 |
| Учебные проекты в активных папках | 1 |

### Архивные материалы: **30**

| Категория | Кол-во |
|-----------|:------:|
| Образовательные/учебные | 19 |
| Прототипы с какой-то функциональностью | 11 |

### Системы с несколькими компонентами

| System | Components |
|--------|-----------|
| SVO System | svo-payments-bot + svo-payouts-website |
| finance-mcp-server | product-mcp (server) + product-mcp-ui (Next.js) |
| bots-platform | модератор + репортёр + сторож |
| seo-mcp-bot | mcp/ + yandex-wordstat-mcp/ |

### Итог по категориям

```
Активных независимых проектов/систем:  29
  из них: компоненты в составе систем:   7 (считаются как 4 системы)
Archive (educational):                  19
Archive (prototypes):                   11
ИТОГО объектов:                         59
```

---

## Ключевые наблюдения

1. **Число проектов не изменилось:** фактически 59 объектов, как и в предыдущем аудите. Разница только в том, что теперь SVO считается одной системой из двух компонентов.

2. **Реальное производство:** только 2 системы реально эксплуатируются — SVO System (svorazbor.ru + Telegram-бот) и site (kaluginvit.github.io).

3. **Тесты значительно варьируются:** от 192 функций (hr-breaker) до нуля (dostaffkin, wb-sales, hotel-booking-n8n).

4. **Docker/Deploy:** 22 из 29 активных проектов имеют Dockerfile или docker-compose; 7 не имеют ни того ни другого.

5. **Client data risk:** wb-sales-commercial-analysis содержит данные клиента и не готова к публикации без анонимизации.
