# Portfolio Gap Analysis — TIER A Projects

> Анализ того, чего не хватает каждому showcase-проекту до профессионального публичного уровня.

---

## 1. finance-mcp-server

### Сейчас
MCP-сервер с 19 финансовыми инструментами (P&L, Cash Flow, Balance Sheet, NPV/IRR, ликвидность, договоры, бюджет vs факт). Python + SQLite + обширные тесты + seed data + Next.js UI. Отличная документация.

### Проблемы

- README содержит абсолютный путь (`C:/полный/путь/к/product-mcp`) в примере конфига Claude Desktop — надо заменить на `<your-path>`
- Next.js UI (`product-mcp-ui/`) не полностью подключён к MCP-серверу: нет явного описания интеграции между ними
- Нет скриншотов реальной работы (Claude Desktop + запрос → ответ)
- Нет `docker-compose.yml` на корневом уровне — только отдельные Dockerfile'ы
- Финансовая логика в README описана хорошо, но нет секции "Business Case" с реальным сценарием использования финансистом

### До уровня showcase не хватает

**Critical:**
- [ ] Убрать абсолютный путь из README → заменить на плейсхолдер
- [ ] Добавить 2-3 скриншота: Claude Desktop задаёт вопрос → ответ MCP-инструмента

**Important:**
- [ ] `docker-compose.yml` для single-command запуска MCP-сервера
- [ ] Раздел "Business Case" в README: описать типовой рабочий день финансиста с этим инструментом
- [ ] Прояснить связь `product-mcp` ↔ `product-mcp-ui` — либо объединить в один docker-compose, либо явно объяснить, что UI — опциональная часть

**Nice to have:**
- [ ] Пример `criteria` кастомизации (как добавить свою компанию в seed)
- [ ] GitHub Actions CI для тестов
- [ ] Roadmap: PostgreSQL backend, multi-user, Auth

### Оценка объёма доработки
**Small** — документация уже хорошая, нужны мелкие правки и скриншоты

---

## 2. svo-payments-bot

### Сейчас
Production Telegram-бот с FSM, SQLite WAL, двумя ветками анкеты, webhook, CI/CD (GitHub Actions → GHCR → SSH deploy). Полноценный модульный backend. Тесты. Отличная документация.

### Проблемы

- README на русском — для английского GitHub-аудитора нужен хотя бы краткий английский блок
- Бизнес-контекст может быть чувствительным для части аудитории — но это уместно для портфолио
- Нет скриншотов интерфейса бота (Telegram UI)
- Финансовая/расчётная логика (`calculators/payments.py`) не описана в README — важный differentiator
- Название `svo-payments-bot` специфично — в описании репозитория нужен более нейтральный pitch: "production Telegram quiz bot with FSM and CRM lead collection"

### До уровня showcase не хватает

**Critical:**
- [ ] Добавить 3-4 скриншота интерфейса бота (начало квиза → результат → лид-форма)
- [ ] Краткий английский блок в README (или отдельный `README_EN.md`)

**Important:**
- [ ] Описать расчётную логику в README: какие виды выплат, как формируется сумма
- [ ] Добавить раздел "Architecture" с диаграммой FSM → handlers → DB → webhook

**Nice to have:**
- [ ] Demo mode: бот с mock данными для тестирования без реального BOT_TOKEN
- [ ] GitHub topics: `aiogram`, `telegram-bot`, `fsm`, `python`, `docker`, `ci-cd`

### Оценка объёма доработки
**Small** — проект уже production-ready, нужно дооформить презентацию

---

## 3. svo-payouts-website

### Сейчас
Live production сайт (svorazbor.ru). Next.js 14, TypeScript, Playwright E2E, Docker, nginx. Полная CI/CD до VPS. Связан с `svo-payments-bot`.

### Проблемы

- README ориентирован на конечного пользователя ("если вы не разработчик...") — не на технический аудитории GitHub
- Техническая документация спрятана в `web/README.md` — надо поднять на верхний уровень
- Нет скриншотов сайта в README (хотя есть живой сайт!)
- Нет раздела "Engineering Decisions" — почему Next.js, почему такая архитектура квиза

### До уровня showcase не хватает

**Critical:**
- [ ] Переписать корневой README как технический showcase: бизнес-задача → архитектура → стек → live demo
- [ ] Добавить 3-4 скриншота сайта (главная → квиз → результат → форма)

**Important:**
- [ ] Раздел "Engineering Decisions": Next.js App Router, Playwright, VPS vs Vercel
- [ ] Секция "Business Metrics": что даёт лендинг, как работает воронка

**Nice to have:**
- [ ] Mermaid-диаграмма: пользователь → квиз → webhook → CRM
- [ ] Lighthouse score скриншот (performance, accessibility)

### Оценка объёма доработки
**Small** — сайт отличный, нужно переориентировать README

---

## 4. finance-data-screener

### Сейчас
Full-stack AI financial data screener: FastAPI + PostgreSQL + React + TypeScript + GPT-4o-mini + Docker. LLM-планировщик + 3 источника данных (MOEX, ЦБ, ТАСС) + аудит. 18 тестов.

### Проблемы

- SSL verification отключён (`verify=False`) — в README есть объяснение (корпоративный SSL), но для публичного репозитория это смотрится как security smell
- `docker compose` требует флага `-p screener` из-за кириллицы в пути — это ограничение локальной среды, не должно быть в инструкции по умолчанию
- Нет скриншотов интерфейса
- Нет mock-данных для demo без API ключа

### До уровня showcase не хватает

**Critical:**
- [ ] Добавить скриншоты всех 4 разделов (Наборы данных, Сбор, Витрина, Журнал)
- [ ] Объяснить `-p screener` как workaround или добавить `.env` с `COMPOSE_PROJECT_NAME`

**Important:**
- [ ] Demo-данные: предзаполненные датасеты для демонстрации без API
- [ ] Раздел "Architecture" с Mermaid-диаграммой

**Nice to have:**
- [ ] `make` команды (Makefile) для упрощения запуска
- [ ] Проверить SSL: рассмотреть добавление сертификата или явный `VERIFY_SSL=false` в env

### Оценка объёма доработки
**Small** — технически проект хорош, нужны скриншоты и мелкие правки

---

## 5. hr-breaker

### Сейчас
Технически самый сложный проект: Pydantic-AI agents, 8-уровневый filter pipeline, FastAPI + CLI, 30+ тестов, multi-LLM support (LiteLLM), WeasyPrint PDF, Alpine.js UI. Отличная архитектура.

### Проблемы

- README на английском (хорошо для международной аудитории), но нет секции "Business Case" — зачем нужен этот инструмент и кому
- Нет скриншотов web UI
- Нет sample resume + sample job description для быстрого демо без собственных данных
- LICENSE есть (хорошо), но нет roadmap
- Не очевидно, как запустить без уже имеющегося резюме

### До уровня showcase не хватает

**Critical:**
- [ ] Добавить 2-3 скриншота web UI (upload → processing → download PDF)
- [ ] Добавить sample resume (`sample_data/resume.txt`) и sample job description для demo

**Important:**
- [ ] Секция "Business Problem" в README: конкретный pain point
- [ ] Roadmap секция
- [ ] `docker-compose.yml` для простого запуска без uv

**Nice to have:**
- [ ] GitHub Pages demo или скриншоты PDF output
- [ ] Описание каждого из 8 фильтров в отдельной секции

### Оценка объёма доработки
**Small-Medium** — нужны sample данные и скриншоты

---

## 6. rf-macro-risk-ai

### Сейчас
LangChain-агент: 35 макро-критериев, multi-LLM, scoring (4 уровня риска), GitHub Pages dashboard. Активный проект с live demo.

### Проблемы

- Проект базируется на другом репозитории (Rai220/money_alert_ai) — это честно указано, но снижает "оригинальность" в глазах технического ревьюера. Нужно явно показать, что было добавлено.
- Путь к Telegram-репортёру (`BOT_REPORTER_DIR=../Бот_репортер`) — локальная зависимость, которая не работает у других
- AGENTS.md есть, но нет описания scoring алгоритма в главном README
- Нет автоматического запуска по расписанию (cron/schedule)

### До уровня showcase не хватает

**Critical:**
- [ ] Явно показать diff от оригинального репозитория: что именно добавлено (35 критериев, multi-provider, scoring, GitHub Pages)
- [ ] Убрать/задокументировать локальную зависимость `BOT_REPORTER_DIR`

**Important:**
- [ ] Описать scoring алгоритм в README (веса, пороги, типы критериев)
- [ ] GitHub Actions cron для автоматического запуска
- [ ] Секция "Limitations": что агент не умеет, когда нельзя доверять результату

**Nice to have:**
- [ ] Граф истории оценок прямо в README (SVG из GitHub Pages)
- [ ] Unit тесты на scoring логику

### Оценка объёма доработки
**Medium** — нужно явно показать авторский вклад

---

## 7. fintech-ab-test-credit-offer

### Сейчас
Методологически зрелый A/B-тест кейс: user-level Welch t-test, MDE, sample size calculation, SQL, Python pipeline, Jupyter notebook, подробная документация. Полностью автономный (`make all`).

### Проблемы

- Нет интерактивного элемента — только статичные артефакты (CSV, MD, PNG)
- README ориентирован на академический контекст ("ТЗ курсового/финального проекта")
- Синтетический датасет — нужно явно позиционировать это как сильный методологический выбор
- Нет раздела "Engineering Decisions": почему Makefile, почему Welch t-test vs Mann-Whitney

### До уровня showcase не хватает

**Critical:**
- [ ] Переориентировать README: убрать учебный контекст ("ТЗ курсового"), позиционировать как portfolio data science case
- [ ] Добавить раздел с итоговыми графиками прямо в README (5-6 key visuals)

**Important:**
- [ ] Секция "Engineering Decisions": выбор метода, работа с синтетическим датасетом
- [ ] nbviewer ссылка в README на showcased notebook (уже есть, подчеркнуть)

**Nice to have:**
- [ ] HTML-версия финального отчёта (уже есть `presentation.html`) — сделать ссылку на GitHub Pages
- [ ] Секция "What I would do differently" / "Key learnings"

### Оценка объёма доработки
**Small** — документация хорошая, нужно переориентировать pitch

---

## 8. fedresurs-mvp

### Сейчас
Оценка лотов банкротства: статистический движок (P25/P50/P75) + LLM-агент с web-поиском. 47 тестов. Flask web UI. SQLite. Реальная финансовая логика оценщика.

### Проблемы

- Жёсткая зависимость от Chrome bookmarks формата (tools/convert_chrome_bookmarks_old_fedresurs.py)
- Без реальных данных из Chrome демо невозможно показать
- Нет seed data / sample лотов для демонстрации
- HTML дашборд (`reports/dashboard.html`) не подключён к live Flask серверу
- Несколько скриптов (fedresurs.py vs fedresurs_mvp.py) — неясно, какой из них основной

### До уровня showcase не хватает

**Critical:**
- [ ] Добавить seed data: 5-10 тестовых лотов в SQLite для demo без Fedresurs
- [ ] Прояснить в README разницу fedresurs.py vs fedresurs_mvp.py — что использовать
- [ ] Demo mode: `python server.py --demo` с предзаполненными данными

**Important:**
- [ ] Вынести захардкоженные пути Chrome bookmarks в `.env`/config
- [ ] Скриншоты HTML дашборда в README

**Nice to have:**
- [ ] Docker-compose с уже инициализированной SQLite базой
- [ ] Связать с `bankrot-trades-scraper` в README (комплементарные инструменты)

### Оценка объёма доработки
**Medium** — нужна demo data и переработка входного интерфейса

---

## 9. leadgen-n8n-system

### Сейчас
11 связанных n8n workflow для B2B лидогенерации. Docker Compose (n8n + PostgreSQL). Mermaid-схема в README. Тесты на валидацию workflow JSON.

### Проблемы

- Workflows — шаблоны: без реального n8n инстанса их сложно оценить
- Нет скриншотов n8n UI с реальными запусками workflow
- Нет объяснения business logic каждого workflow (что именно делает intent radar, как работает consensus)
- Тесты проверяют только структуру JSON, не логику
- Media папка пустая (`media/README.md` — placeholder)

### До уровня showcase не хватает

**Critical:**
- [ ] Добавить скриншоты n8n (каждый из 11 workflow или хотя бы ключевые 3-4)
- [ ] Описать бизнес-логику каждого workflow: что на входе, что на выходе, как связаны

**Important:**
- [ ] Пример реального запуска: mock input → что произошло → output
- [ ] Раздел "Configuration Guide": что нужно настроить в credentials для минимального запуска

**Nice to have:**
- [ ] Video walkthrough (Loom/GIF) — для n8n это особенно эффективно
- [ ] Шаблонные данные для тестового прогона (без реального CRM)

### Оценка объёма доработки
**Medium** — нужны визуальные материалы

---

## 10. mini-crm-fastapi-react

### Сейчас
FastAPI + SQLite + React (TypeScript) + Google Drive/Sheets OAuth + Docker. Smoke тесты. SECURITY.md. Хорошая документация.

### Проблемы

- Google OAuth требует регистрации приложения в GCP — это барьер для demo
- Нет скриншотов UI
- Нет seed данных в Docker (нужно запускать отдельный скрипт)
- README в стиле "чек-лист для сдачи на платформе" — не portfolio-oriented

### До уровня showcase не хватает

**Critical:**
- [ ] Переписать README: убрать "чек-лист сдачи", позиционировать как продукт
- [ ] Добавить скриншоты: список клиентов, сделки, форма, Google Sheets выгрузка

**Important:**
- [ ] Seed данные в `docker-compose.yml` (entrypoint запускает `fill_test_data.py`)
- [ ] Раздел "Architecture" с диаграммой: React → FastAPI → SQLite + Google API

**Nice to have:**
- [ ] Mock Google Auth mode для demo без реального GCP
- [ ] Roadmap: auth (JWT), notifications, reporting

### Оценка объёма доработки
**Medium** — нужны скриншоты и переориентация README

---

## Quality Gates Check — Итог по TIER A

| Project | Бизнес ясна | Архитектура ясна | Нет секретов | Нет абс. путей | README полный | Инструкция | Demo/seed | Reusable | Запускается |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| finance-mcp-server | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ |
| svo-payments-bot | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| svo-payouts-website | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| finance-data-screener | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| hr-breaker | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| rf-macro-risk-ai | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| fintech-ab-test-credit-offer | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fedresurs-mvp | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ |
| leadgen-n8n-system | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| mini-crm-fastapi-react | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ✅ | ✅ |

**Легенда:** ✅ готово | ⚠️ нужна правка | ❌ отсутствует

### Главные приоритеты:
1. **Скриншоты** — отсутствуют у большинства проектов (быстро исправляется)
2. **Demo/seed data** — отсутствует у 5 из 10 проектов (Medium effort)
3. **README переориентация** — у 3 проектов (svo-payouts-website, fintech-ab-test, mini-crm)
4. **Абсолютные пути** — точечные правки в 3 проектах
