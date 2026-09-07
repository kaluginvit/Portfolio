# Portfolio Positioning

> Пересмотрено: 2026-09-07

---

## Целевой образ

**Финансовый консультант и прикладной разработчик.**

Специализация:

> Corporate Finance × Business Analysis × Python × AI × Automation × Web Development

Главный тезис:

> Понимаю бизнес и финансы — и могу самостоятельно превратить бизнес-задачу в работающий программный инструмент.

Клиенту или работодателю можно сказать:

> «Вот задача на стыке финансов, данных и разработки. Разберись и сделай работающий инструмент».

И автор способен: понять задачу → формализовать требования → разобраться в предметной области → спроектировать решение → написать Python/backend → сделать API → подключить внешние сервисы → работать с SQL → сделать web-интерфейс → использовать AI/LLM → построить автоматизацию → упаковать в Docker → развернуть → поддерживать.

---

## Как выглядит автор сейчас

**Strong Middle / Middle+ Applied Software Developer**  
**Corporate Finance & Business Analysis — Expert / Strong**

Профиль не «классический разработчик» и не «классический финансовый аналитик» — а человек с реальной финансовой экспертизой, который строит рабочие инструменты. Это редкое сочетание.

Два проекта в реальной эксплуатации (svorazbor.ru, svo-payments-bot), финансовые расчёты в коде которые понимает предметно, а не формально.

---

## Уровень по направлениям

### Corporate Finance — Expert / Strong

Понимает и умеет реализовывать:
- P&L, Cash Flow, Balance Sheet
- NPV, IRR, Payback Period, PI
- Budget vs Fact анализ
- Liquidity management и payment calendar
- Contract risk assessment
- Unit economics, A/B metrics (CR_apply, ARPU)
- Оценка активов при банкротстве (P25/P50/P75, 4 сценария цены)
- Macro risk scoring по множеству критериев

Это **реальное преимущество** — разработчик без финансового бэкграунда не напишет такой код, потому что не понимает смысл показателей.

---

### Business Analysis — Strong

- Формализует бизнес-задачу в требования
- Разбивает на компоненты и выбирает архитектуру
- Понимает бизнес-процессы (CRM, лидогенерация, бронирование, расчёты выплат)
- Пишет документацию с бизнес-контекстом, а не просто технические описания

---

### Python — Strong Middle

**Есть:**
- Модульная архитектура (handlers/services/repositories/states)
- Async (aiogram 3, aiosqlite, FastAPI async)
- Pydantic модели и валидация
- CLI (Click), конфигурация через env/dataclasses
- uv как пакетный менеджер
- Тест-сьюты реального объёма (47 тестов fedresurs-mvp, 30+ hr-breaker, 18 finance-data-screener)
- SQLAlchemy 2.0, Alembic миграции

---

### Backend — Middle+

**Есть:**
- FastAPI (finance-data-screener, hr-breaker, mini-crm, autonomous-agents)
- aiogram 3 FSM (svo-payments-bot)
- Middleware (AuditMiddleware)
- SSE streaming (hr-breaker)
- Repository pattern, Layered architecture
- Webhook integration (svo-payments-bot, svo-payouts-website)

---

### Data / SQL — Strong Middle

**Есть:**
- A/B тест с правильной методологией (user-level Welch t-test, MDE, power analysis)
- SQL: window functions, CTEs, GROUP BY (fintech-ab-test)
- pandas (EDA, aggregations, ETL)
- SQLAlchemy 2.0 async, Alembic
- SQLite production usage (svo-payments-bot, fedresurs-mvp, finance-mcp-server)
- PostgreSQL (finance-data-screener, leadgen-n8n)
- Структурированные датасеты и их обработка

---

### AI / LLM — Middle+

**Есть:**
- MCP Protocol — инструменты для Claude Desktop/Cursor (finance-mcp-server, seo-mcp-bot)
- LangChain + LangGraph agentic loop (rf-macro-risk-ai, fedresurs-mvp)
- Pydantic-AI agents (hr-breaker)
- LiteLLM multi-provider (hr-breaker)
- RAG + Pinecone (personal-rag-assistant, team-ai-bot)
- `instructor` для строгого JSON из LLM
- Hallucination detection (hr-breaker)
- Multi-agent pipeline (hr-breaker, crewai-multiagent)

---

### Automation — Middle+

**Есть:**
- 11-workflow n8n система с multi-LLM consensus и human-in-the-loop
- Graduation project n8n с полной документацией
- Python automation pipelines (fedresurs batch, tg-digest)
- CI/CD GitHub Actions

---

### Frontend / Web — Middle

**Есть:**
- React TypeScript (finance-data-screener, mini-crm)
- Next.js 14 App Router (svo-payouts-website)
- Tailwind CSS
- Playwright E2E тесты
- Vite build, Alpine.js (hr-breaker)
- Адаптивная верстка
- Angular (dostaffkin)

---

### DevOps — Working Middle

**Есть:**
- Docker + docker-compose (22 из 29 активных проектов)
- CI/CD GitHub Actions (build → GHCR → SSH deploy)
- nginx конфиги
- VPS production deploy
- GitHub Pages

Достаточно для самостоятельного развёртывания и поддержки рабочих систем.

---

### Product Development — Middle+

**Есть:**
- User research → system design → реализация (svo-payouts-website)
- Business case writing в документации
- Roadmap мышление
- Честная интерпретация ограничений (fintech-ab-test)
- Demo/seed data для воспроизводимости

---

## Типы задач, которые автор закрывает

Портфолио показывает следующие прикладные классы:

| Класс задачи | Пример |
|-------------|--------|
| Финансовая система / AI-слой | finance-mcp-server |
| AI-инструмент финансиста | finance-data-screener |
| Аналитика и A/B методология | fintech-ab-test-credit-offer |
| Оценка активов / Financial valuation | fedresurs-mvp |
| Production website + Telegram | svo-payouts-website + svo-payments-bot |
| AI agent / document processing | hr-breaker |
| Macro analytics / scoring | rf-macro-risk-ai |
| B2B automation / n8n | leadgen-n8n-system |
| Internal CRM / business system | mini-crm-fastapi-react |

---

## Reusability по проектам

| Проект | Тип | Адаптация |
|--------|-----|-----------|
| finance-mcp-server | Reusable internal tool | Подключить к другому набору данных, изменить seed — готово |
| finance-data-screener | Configurable solution | Добавить новый collector — отдельный класс |
| hr-breaker | Reusable product | Конфиг модели через env, другой провайдер — тот же код |
| rf-macro-risk-ai | Configurable solution | Сменить criteria.json — другая предметная область |
| fedresurs-mvp | Production case → Reusable with config | Сменить источник данных — нужен новый collector |
| fintech-ab-test-credit-offer | Analytical case study | Шаблон для аналогичного A/B анализа |
| svo-payments-bot | Production case → Reusable with config | Другие расчёты — меняется только calculators/ |
| svo-payouts-website | Production case | Переиспользуем quiz architecture для нового домена |
| leadgen-n8n-system | Reusable template | Импортировать workflows, настроить credentials |
| mini-crm-fastapi-react | Reusable internal tool | CRUD + Google integration — шаблон под новую предметку |

---

## Narrative — для клиента

> Специализация на системах, где важна финансовая предметная логика: инструменты для управленческого учёта, оценки активов, аналитики, автоматизации финансовых процессов. Умею построить решение от бизнес-задачи до рабочей системы — без посредников между аналитиком и разработчиком, потому что это один человек.

## Narrative — для работодателя

> Сильный прикладной Middle, которому не нужно объяснять предметную область. Понимает P&L, денежные потоки, финансовую аналитику — и умеет это реализовывать в коде. Два проекта в production, тест-сьюты, Docker, CI/CD. Дашь задачу на стыке финансов и разработки — доведёт до результата.

---

## GitHub Deployment Plan

**Фаза 1 — Quick wins (~1-2 дня):**
1. finance-mcp-server — исправить абс. путь → publish
2. svo-payments-bot — скриншоты + EN блок → publish
3. fintech-ab-test-credit-offer — переписать pitch → publish
4. rf-macro-risk-ai — уточнить авторский вклад → publish

**Фаза 2 — Polish (~3-5 дней):**
5. svo-payouts-website — README rewrite → скриншоты → publish
6. finance-data-screener — скриншоты + COMPOSE fix → publish
7. hr-breaker — sample data → скриншоты → publish
8. mini-crm-fastapi-react — README rewrite → скриншоты → publish

**Фаза 3 — Demo data (~5-10 дней):**
9. fedresurs-mvp — seed data → demo mode → publish
10. leadgen-n8n-system — скриншоты + описания workflows → publish
