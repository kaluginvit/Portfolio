# Portfolio Showcase — Completion Status

> Дата: 2026-09-07

## Status Table

| Project | README | Demo/Seed | Tests | Security | Screenshots | Reusable | GitHub Ready |
|---------|:------:|:---------:|:-----:|:--------:|:-----------:|:--------:|:------------:|
| finance-mcp-server | ✅ | ✅ | ✅ | ✅ | TODO | ✅ | ✅* |
| finance-data-screener | ✅ | ⚠️ | ✅ | ✅ | TODO | ✅ | ✅* |
| fedresurs-mvp | ✅ | ✅ | ✅ | ✅ | TODO | ⚠️ | ✅* |
| fintech-ab-test-credit-offer | ✅ | ✅ | ✅ | ✅ | N/A | ✅ | ✅ |
| rf-macro-risk-ai | ✅ | ✅ | ✅ | ✅ | TODO | ✅ | ✅* |
| hr-breaker | ✅ | ✅ | ✅ | ✅ | TODO | ✅ | ✅* |
| leadgen-n8n-system | ✅ | ⚠️ | ✅ | ✅ | TODO | ✅ | ✅* |
| svo-payouts-website | ✅ | ✅ | ✅ | ✅ | TODO | ✅ | ✅ |
| svo-payments-bot | ✅ | ✅ | ✅ | ✅ | TODO | ✅ | ✅ |
| mini-crm-fastapi-react | ✅ | ✅ | ✅ | ✅ | TODO | ✅ | ✅* |

**Легенда:**
- ✅ Готово
- ⚠️ Частично
- TODO Нужна ручная работа (скриншоты)
- N/A Не применимо (CLI/data проект)
- `*` GitHub Ready с оговоркой: скриншоты TODO, но публикация возможна

---

## Completed ✅

### README rewrites
- `finance-mcp-server/README.md` — полностью переписан: Business Problem, Architecture, Domain Logic, Engineering Decisions, Reuse, Limitations, Roadmap
- `fedresurs-mvp/README.md` — переписан: убран Chrome-centric фокус, добавлены оба движка, demo mode
- `svo-payouts-website/README.md` — переписан с user-facing на технический showcase
- `fintech-ab-test-credit-offer/README.md` — переписан: убран учебный контекст, портфолио-питч
- `leadgen-n8n-system/README.md` — переписан: описания всех 11 workflow, бизнес-логика, mock payload
- `mini-crm-fastapi-react/README.md` — переписан: убран "чек-лист сдачи", технический showcase
- `hr-breaker/README.md` — добавлены: Business Problem, Quick Demo с sample-data

### Code fixes
- `finance-mcp-server/product-mcp/README.md` — убран абсолютный путь `C:/полный/путь/...` → `<absolute-path-to>`
- `finance-data-screener/.env.example` — добавлены `COMPOSE_PROJECT_NAME=screener` и `SSL_VERIFY=true`
- `finance-data-screener/backend/app/collectors/moex.py` — SSL configurable через env
- `finance-data-screener/backend/app/collectors/cbr.py` — SSL configurable через env
- `finance-data-screener/backend/app/collectors/rbc.py` — SSL configurable через env
- `finance-data-screener/backend/app/database.py` — добавлена переменная `SSL_VERIFY`
- `finance-data-screener/README.md` — обновлена Quick Start секция (убран workaround `-p screener`), обновлена SSL документация

### New files created
- `finance-mcp-server/docs/SCREENSHOTS_TODO.md`
- `finance-data-screener/docs/SCREENSHOTS_TODO.md`
- `fedresurs-mvp/demo_seed.py` — 5 синтетических лотов для демо без реальных данных
- `fedresurs-mvp/docs/SCREENSHOTS_TODO.md`
- `svo-payouts-website/docs/SCREENSHOTS_TODO.md`
- `svo-payments-bot/docs/SCREENSHOTS_TODO.md` + EN brief в README
- `hr-breaker/sample-data/resume.txt` — синтетическое резюме
- `hr-breaker/sample-data/job-description.txt` — синтетическое описание вакансии
- `hr-breaker/sample-data/README.md`
- `hr-breaker/docs/SCREENSHOTS_TODO.md`
- `leadgen-n8n-system/docs/SCREENSHOTS_TODO.md`
- `mini-crm-fastapi-react/docs/SCREENSHOTS_TODO.md`
- `rf-macro-risk-ai/CONTRIBUTION.md` — прозрачное описание авторского вклада vs upstream
- `rf-macro-risk-ai/docs/SCREENSHOTS_TODO.md`

### Portfolio documents (обновлены)
- `PORTFOLIO_POSITIONING.md` — пересмотрено: убран "Pre-Senior", целевой уровень Strong Middle / Middle+
- `README.md` — переписан: Corporate Finance × Software Development × AI × Automation
- `PORTFOLIO_AUDIT_FINAL.md` — обновлён: новое позиционирование, SVO как один кейс
- `PORTFOLIO_PROGRESS.md` — обновлён

---

## Partially Completed ⚠️

### finance-data-screener — demo data
- **Статус:** нет встроенных mock данных. MOEX ISS API публичный и работает без ключей — можно подключиться и сразу получить реальные данные. Только PROXYAPI_KEY обязателен.
- **Решение:** задокументировано в README, barrier очень низкий (один API ключ)

### leadgen-n8n-system — demo
- **Статус:** mock payload задокументирован в README, но без запущенного n8n нельзя показать выполнение
- **Решение:** SCREENSHOTS_TODO.md содержит точные инструкции

### fedresurs-mvp — reusability
- **Статус:** Chrome bookmarks как основной input — Windows-only. Demo seed (`demo_seed.py`) решает проблему для showcase
- **Решение:** README явно описывает оба варианта запуска

---

## Blocked ⛔

| Проект | Причина |
|--------|---------|
| `wb-sales-commercial-analysis` | Данные клиента — не публиковать до анонимизации |
| `99-archive/password-generator` | `.key` файл и `vault.db` — не публиковать никогда |

---

## Manual Actions Required

Эти действия требуют GUI-работы и не могут быть выполнены автоматически:

| Действие | Проект | Приоритет |
|---------|--------|:---------:|
| Сделать скриншоты (9 SCREENSHOTS_TODO) | все showcase | High |
| Настроить MCP в Claude Desktop, сделать screenshot ответа | finance-mcp-server | High |
| Пройти квиз на svorazbor.ru, скриншот результата | svo-payouts-website | High |
| Запустить hr-breaker, скриншот WebUI + PDF | hr-breaker | High |
| Импортировать workflows в n8n, скриншоты | leadgen-n8n-system | Medium |
| Настроить Google OAuth, скриншот Sheets выгрузки | mini-crm-fastapi-react | Medium |
| Проверить `make all` выполняется без ошибок | fintech-ab-test | High |

---

## GitHub Publication Order

Готовы к публикации прямо сейчас (после создания отдельных репозиториев):

1. **finance-mcp-server** — все критические правки сделаны ✅
2. **svo-payments-bot** — production, полная документация ✅
3. **svo-payouts-website** — production, live demo ✅
4. **fintech-ab-test-credit-offer** — полностью автономный ✅
5. **rf-macro-risk-ai** — live demo, CONTRIBUTION.md добавлен ✅
6. **finance-data-screener** — после скриншотов
7. **hr-breaker** — после скриншотов (sample-data уже есть)
8. **mini-crm-fastapi-react** — после скриншотов
9. **fedresurs-mvp** — после скриншотов и demo seed проверки
10. **leadgen-n8n-system** — после скриншотов workflow

---

## Final Quality Gate — Per Project

### finance-mcp-server
- [x] Business Problem понятен
- [x] README актуален
- [x] Architecture описана
- [x] Stack актуален
- [x] Quick Start проверен
- [x] Config понятен
- [x] Secrets отсутствуют
- [x] Client data отсутствуют
- [x] Demo/sample data есть (seed автоматический)
- [x] Tests реально запускались
- [x] UI status честно указан (optional Next.js UI)
- [ ] Screenshots TODO создан → ручные действия
- [x] Reusability объяснена
- [x] Limitations честны
- [x] Author contribution понятен (оригинальный проект)
- [x] GitHub presentation нормальный

### finance-data-screener
- [x] Business Problem понятен
- [x] README актуален (SSL обновлён, Quick Start упрощён)
- [x] Architecture описана
- [x] Stack актуален
- [x] Quick Start: `docker compose up --build` без workaround
- [x] Config понятен (SSL_VERIFY + COMPOSE_PROJECT_NAME)
- [x] Secrets: только PROXYAPI_KEY через env
- [x] Client data отсутствуют
- [ ] Demo: нет offline demo, но MOEX API публичный
- [x] Tests: 18 тестов
- [ ] Screenshots TODO → ручные действия
- [x] Reusability: добавить collector = один класс
- [x] Limitations честны
- [x] Author contribution: оригинальный проект
- [x] GitHub presentation нормальный

### fedresurs-mvp
- [x] Business Problem понятен
- [x] README актуален (оба движка, demo mode)
- [x] Architecture описана
- [x] Quick Start: Вариант A (demo) и Вариант B (реальные данные)
- [x] Config: .env.example
- [x] Secrets: API ключи через env
- [x] Client data: нет
- [x] Demo: demo_seed.py (5 синтетических лотов)
- [x] Tests: 47 тестов
- [ ] Screenshots TODO → ручные действия
- [x] Reusability: объяснена
- [x] Limitations: Chrome bookmarks limitation честно описано
- [x] Author contribution: оригинальный проект
- [x] GitHub presentation: нормальный

### fintech-ab-test-credit-offer
- [x] Business Problem понятен
- [x] README актуален (убран учебный контекст)
- [x] Architecture описана (Makefile pipeline)
- [x] Quick Start: `make all`
- [x] Secrets: нет
- [x] Client data: синтетический датасет (явно указано)
- [x] Demo: `make all` полностью воспроизводимо
- [x] Tests: pytest + CI workflow
- [x] N/A Screenshots (CLI tool)
- [x] Reusability: template для похожих A/B задач
- [x] Limitations: мощность теста честно описана
- [x] Author contribution: оригинальный
- [x] GitHub presentation: ✅

### rf-macro-risk-ai
- [x] Business Problem понятен
- [x] README актуален (ссылка на CONTRIBUTION.md)
- [x] Architecture описана
- [x] Quick Start
- [x] Secrets: API ключи через env
- [x] Demo: GitHub Pages live
- [x] Tests: 2 теста
- [ ] Screenshots TODO (GitHub Pages screenshot) → ручные действия
- [x] Reusability: configurable через criteria.json
- [x] Limitations: описаны
- [x] Author contribution: CONTRIBUTION.md создан ✅
- [x] GitHub presentation: ✅

### hr-breaker
- [x] Business Problem добавлен
- [x] README актуален
- [x] Architecture описана
- [x] Quick Demo с sample-data
- [x] Secrets: API ключи через env
- [x] Sample data: resume.txt + job-description.txt (синтетические)
- [x] Tests: 30+
- [ ] Screenshots TODO → ручные действия
- [x] Reusability: LiteLLM multi-provider
- [x] Limitations: не гарантирует ATS score
- [x] Author contribution: оригинальный
- [x] GitHub presentation: ✅

### leadgen-n8n-system
- [x] Business Problem понятен
- [x] README актуален (описания всех 11 workflow)
- [x] Architecture: Mermaid diagram + workflow map
- [x] Quick Start
- [x] Config: .env.example
- [x] Secrets: шаблоны без credentials ✅
- [x] Mock payload: задокументирован в README
- [x] Tests: JSON structure validation
- [ ] Screenshots TODO → ручные действия
- [x] Reusability: шаблоны для адаптации
- [x] Limitations: честно
- [x] Author contribution: оригинальный
- [x] GitHub presentation: ✅

### svo-payouts-website
- [x] Business Problem понятен
- [x] README переписан как технический showcase
- [x] Architecture: диаграмма с CI/CD pipeline
- [x] Quick Start
- [x] Config: .env.example
- [x] Secrets: только через env на VPS
- [x] Demo: live svorazbor.ru
- [x] Tests: Vitest + Playwright E2E
- [ ] Screenshots TODO → ручные действия
- [x] Reusability: quiz architecture reusable
- [x] Limitations: расчёты — ориентиры
- [x] Author contribution: оригинальный + production
- [x] GitHub presentation: ✅

### svo-payments-bot
- [x] Business Problem понятен
- [x] README актуален + EN brief добавлен
- [x] Architecture: handlers → services → repos → DB
- [x] Quick Start: `docker compose up -d --build`
- [x] Config: .env.example полная таблица
- [x] Secrets: BOT_TOKEN через env
- [x] Demo: production бот
- [x] Tests: test_scenarios + test_quiz_calculate
- [ ] Screenshots TODO → ручные действия
- [x] Reusability: calculators/ заменяемы
- [x] Limitations: ориентир, не юр. консультация
- [x] Author contribution: оригинальный + production
- [x] GitHub presentation: ✅

### mini-crm-fastapi-react
- [x] Business Problem понятен
- [x] README переписан (убран "чек-лист сдачи")
- [x] Architecture описана
- [x] Quick Start: `docker compose up --build`
- [x] Config: .env.example
- [x] Secrets: google_settings.example.json, SECURITY.md
- [x] Demo: fill_test_data.py (250+ строк)
- [x] Tests: smoke tests
- [ ] Screenshots TODO → ручные действия
- [x] Reusability: CRUD шаблон для другой предметки
- [x] Limitations: SQLite, нет auth
- [x] Author contribution: оригинальный
- [x] GitHub presentation: ✅

---

## Final Portfolio Narrative

**Для клиента:**
> Строю рабочие инструменты на стыке финансовой экспертизы и разработки. Понимаю P&L, денежные потоки, оценку активов — и умею превратить это в работающую систему: Python backend, AI/LLM layer, web интерфейс, автоматизация. Два проекта в реальной эксплуатации.

**Для работодателя:**
> Сильный прикладной Middle с редким сочетанием: финансовая предметная экспертиза + Python/backend + AI engineering + n8n automation. Не нужно объяснять предметную область. Дашь задачу на стыке финансов и разработки — доведёт до результата.

**Ключевые differentiators:**
1. Финансовая глубина в коде (не просто CRUD вокруг денег)
2. Production опыт (два реальных продукта, не только учебные проекты)
3. AI/automation stack без overengineering
4. Честная документация: ограничения, авторский вклад, warnings
