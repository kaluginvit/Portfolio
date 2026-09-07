# Portfolio Inventory

> Дата аудита: 2026-09-07
> Всего проектов найдено: **29 активных** + **30 архивных** (итого 59)
> Автор: Виталий Калугин

---

## Легенда

**Готовность:** 🟢 Production | 🟡 MVP/Demo | 🟠 Прототип | 🔴 Незавершён  
**GitHub Fit:** ⭐⭐⭐ Отличный | ⭐⭐ Хороший | ⭐ Нужна доработка | ✗ Не подходит  
**Portfolio Value:** ⭐⭐⭐ Витрина | ⭐⭐ Поддерживающий | ⭐ Слабый  

---

## РАЗДЕЛ 01 — Data Analytics

---

### 1. data-work-utilities

| Поле | Значение |
|------|----------|
| **Путь** | `01-data-analytics/data-work-utilities/` |
| **Назначение** | Полностековый инструмент анализа данных: загрузка CSV/Excel/PDF → AI-анализ через LLM → визуализация |
| **Бизнес-задача** | Быстрый анализ данных без Excel/Python навыков: загрузил файл — получил инсайты |
| **Стек** | React (TypeScript, Vite) + Python (FastAPI) + OpenAI API |
| **Размер/сложность** | Medium. Полноценный full-stack с AI-сервисом |
| **Готовность** | 🟡 MVP |
| **Запускается** | Условно (нужен API ключ) |
| **Frontend** | ✅ React + Vite + TypeScript |
| **Backend** | ✅ Python FastAPI (`ai_service.py`, `main.py`) |
| **БД** | ❌ |
| **API** | ✅ REST |
| **AI** | ✅ LLM через OpenAI API |
| **Автоматизация** | ❌ |
| **Финансовая логика** | 🟡 (пример данных Car Sales CSV) |
| **Docker** | ❌ |
| **Документация** | ✅ README есть |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅ |
| **Секретные данные** | ❌ API ключи через env |
| **Хардкод путей/токенов** | ❌ |
| **Внешние зависимости** | OpenAI API |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 2. fedresurs-mvp

| Поле | Значение |
|------|----------|
| **Путь** | `01-data-analytics/fedresurs-mvp/` |
| **Назначение** | Оценка лотов банкротства по рыночным аналогам: статистический движок (P25/P50/P75) + LLM-агент с web-поиском |
| **Бизнес-задача** | Ручной поиск аналогов занимает 30-60 мин на лот. Инструмент автоматизирует оценку любого актива: квартира, оборудование, транспорт, дебиторка |
| **Стек** | Python (stdlib + Gemini/OpenRouter + Tavily/Brave/Google), Flask, SQLite, Docker |
| **Размер/сложность** | Medium-High. Два независимых движка оценки, 47 тестов, agentic loop |
| **Готовность** | 🟡 MVP (рабочий, но личный инструмент) |
| **Запускается** | ✅ (нужны API ключи) |
| **Frontend** | 🟡 HTML дашборд (`reports/dashboard.html`) + Flask web UI |
| **Backend** | ✅ Python scripts + Flask server |
| **БД** | ✅ SQLite (`fedresurs.sqlite3`) |
| **API** | 🟡 Flask REST + Fedresurs public API |
| **AI** | ✅ LLM agentic loop (Gemini/OpenRouter) + web search |
| **Автоматизация** | ✅ Batch valuation pipeline |
| **Финансовая логика** | ✅✅ Профессиональная оценка активов: P25/P50/P75, 4 сценария цены, discount-коэффициенты |
| **Docker** | ✅ Dockerfile есть |
| **Документация** | ✅ Подробный README с примерами |
| **Тесты** | ✅ 47 тестов (`test_valuation.py`) |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅ |
| **Секретные данные** | ❌ (API ключи через env) |
| **Хардкод путей/токенов** | 🟡 Пути к Chrome bookmarks захардкожены в tools |
| **Внешние зависимости** | Fedresurs API (публичный), LLM API, поисковые API |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 3. fintech-ab-test-credit-offer

| Поле | Значение |
|------|----------|
| **Путь** | `01-data-analytics/fintech-ab-test-credit-offer/` |
| **Назначение** | Законченный кейс A/B-теста в финтех-приложении: перенос карточки «Кредитка дня» в ленте |
| **Бизнес-задача** | Проверить гипотезу: улучшает ли перенос карточки ключевые метрики (CR_apply, CTR, ARPU)? |
| **Стек** | Python (scipy, pandas, matplotlib, seaborn), SQL, Jupyter, Makefile, Docker |
| **Размер/сложность** | Medium. Методологически зрелый — user-level Welch t-test, MDE, sample size calculation |
| **Готовность** | 🟢 Завершён (полный pipeline + отчёт + notebook) |
| **Запускается** | ✅ `make all` без внешних зависимостей |
| **Frontend** | ❌ (HTML презентация есть) |
| **Backend** | ❌ (скрипты Python) |
| **БД** | ❌ (CSV файлы) |
| **API** | ❌ |
| **AI** | ❌ |
| **Автоматизация** | ✅ Makefile pipeline |
| **Финансовая логика** | ✅ Fintech product metrics, ARPU, conversion rate analysis |
| **Docker** | ✅ Dockerfile |
| **Документация** | ✅✅ Отличная: experiment_design.md, metrics_definition.md, limitations.md, final_report |
| **Тесты** | ✅ `test_data.py` + CI workflow |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅ |
| **Секретные данные** | ❌ |
| **Хардкод путей/токенов** | ❌ |
| **Внешние зависимости** | ❌ (полностью автономный) |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 4. superstore-retail-analytics

| Поле | Значение |
|------|----------|
| **Путь** | `01-data-analytics/superstore-retail-analytics/` |
| **Назначение** | EDA + интерактивный HTML-дашборд по retail-датасету Superstore |
| **Бизнес-задача** | Разведочный анализ продаж, прибыльности и трендов в ритейле |
| **Стек** | Python (pandas, plotly, python-pptx), Jupyter, HTML |
| **Размер/сложность** | Small-Medium. Один датасет, EDA + визуализация |
| **Готовность** | 🟡 MVP (без доработки для production) |
| **Запускается** | ✅ |
| **Frontend** | ✅ HTML dashboard (`superstore-dashboard.html`) |
| **Backend** | ❌ |
| **БД** | ❌ (CSV) |
| **API** | ❌ |
| **AI** | ❌ |
| **Автоматизация** | ❌ |
| **Финансовая логика** | ✅ Profit margins, category analysis, sales trends |
| **Docker** | ✅ |
| **Документация** | 🟡 README + INSIGHTS.md |
| **Тесты** | ✅ `test_data.py` |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅ |
| **Секретные данные** | ❌ |
| **Хардкод путей/токенов** | ❌ |
| **Внешние зависимости** | ❌ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 5. wb-sales-commercial-analysis

| Поле | Значение |
|------|----------|
| **Путь** | `01-data-analytics/wb-sales-commercial-analysis/` |
| **Назначение** | Коммерческий анализ продаж на Wildberries: скрипты обработки данных клиента |
| **Бизнес-задача** | Анализ SKU-уровня продаж, маржинальности, ABC-анализ для seller'а на WB |
| **Стек** | Python (pandas), CSV |
| **Размер/сложность** | Small. Реальный ONE-OFF проект |
| **Готовность** | 🟡 Рабочий, но под конкретного клиента |
| **Запускается** | 🟡 (требует конкретных CSV) |
| **Frontend** | ❌ |
| **Backend** | ❌ (скрипты) |
| **БД** | ❌ |
| **API** | ❌ |
| **AI** | ❌ |
| **Автоматизация** | ❌ |
| **Финансовая логика** | ✅ Commercial analysis, SKU profitability, returns analysis |
| **Docker** | ❌ |
| **Документация** | ✅ DATA_ANONYMIZATION.md + README |
| **Тесты** | ❌ |
| **.env.example** | ❌ |
| **Инструкции запуска** | 🟡 |
| **Секретные данные** | 🔴 Данные клиента (анонимизированы?) |
| **Хардкод путей/токенов** | 🟡 Пути к файлам |
| **Внешние зависимости** | ❌ |
| **GitHub Fit** | ⭐ (только после полной анонимизации) |
| **Portfolio Value** | ⭐ |

---

## РАЗДЕЛ 02 — Automation

---

### 6. bankrot-trades-scraper

| Поле | Значение |
|------|----------|
| **Путь** | `02-automation/bankrot-trades-scraper/` |
| **Назначение** | Скрапер торгов банкротства + SQLite хранение + HTML-интерфейс для review |
| **Бизнес-задача** | Мониторинг и сбор данных о торгах из Федресурса для дальнейшего анализа |
| **Стек** | Python (requests, sqlite3), Docker, HTML статик |
| **Размер/сложность** | Small-Medium |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ |
| **Frontend** | ✅ HTML review UI |
| **Backend** | ✅ Python scraper + Flask review server |
| **БД** | ✅ SQLite |
| **API** | ❌ |
| **AI** | ❌ |
| **Автоматизация** | ✅ Fetch scripts |
| **Финансовая логика** | ✅ Bankruptcy trades data |
| **Docker** | ✅ |
| **Документация** | ✅ README |
| **Тесты** | ✅ `test_core.py` |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 7. currency-travel-api

| Поле | Значение |
|------|----------|
| **Путь** | `02-automation/currency-travel-api/` |
| **Назначение** | Telegram-бот для получения актуальных курсов валют |
| **Бизнес-задача** | Быстрый доступ к курсам валют через Telegram |
| **Стек** | Python (aiogram), Docker, SQLite |
| **Размер/сложность** | Small |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ |
| **Frontend** | ❌ (Telegram) |
| **Backend** | ✅ |
| **БД** | ✅ SQLite |
| **API** | ✅ Внешний currency API |
| **AI** | ❌ |
| **Финансовая логика** | ✅ Currency rates |
| **Docker** | ✅ |
| **Документация** | ✅ |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐ |

---

### 8. hotel-booking-n8n

| Поле | Значение |
|------|----------|
| **Путь** | `02-automation/hotel-booking-n8n/` |
| **Назначение** | Автоматизация бронирования отелей через n8n: форма → проверка номеров → бронь → email клиенту → ежедневный отчёт менеджеру |
| **Бизнес-задача** | Устранение ручных операций менеджера при обработке заявок на бронирование |
| **Стек** | n8n (JSON workflow), Supabase (PostgreSQL), HTML форма |
| **Размер/сложность** | Medium. Выпускной проект курса n8n. 2 workflow, email templates, тест-матрица |
| **Готовность** | 🟡 Демо/кейс |
| **Запускается** | ✅ (требует n8n + Supabase) |
| **Frontend** | ✅ HTML форма бронирования |
| **Backend** | ✅ n8n workflows |
| **БД** | ✅ Supabase (PostgreSQL) |
| **API** | ✅ Webhook |
| **AI** | ❌ |
| **Автоматизация** | ✅✅ n8n |
| **Финансовая логика** | ❌ |
| **Docker** | ❌ |
| **Документация** | ✅✅ Подробный отчёт, схема процесса, тест-матрица, email templates |
| **Тесты** | ✅ test-matrix.md |
| **.env.example** | ❌ |
| **Инструкции запуска** | ✅ setup-steps.md |
| **Секретные данные** | ❌ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 9. leadgen-n8n-system

| Поле | Значение |
|------|----------|
| **Путь** | `02-automation/leadgen-n8n-system/` |
| **Назначение** | 11 связанных n8n workflow для B2B лидогенерации: от Intent Radar до Live Dashboard |
| **Бизнес-задача** | Полная цепочка B2B воронки: сигнал → обогащение → AI-консенсус → human-in-loop → nurture → отчётность |
| **Стек** | n8n, JSON workflow exports, Docker Compose (n8n + PostgreSQL) |
| **Размер/сложность** | Large. 11 workflow, сложная архитектура с multi-LLM consensus |
| **Готовность** | 🟡 Шаблоны/демо |
| **Запускается** | ✅ (docker compose + import workflows) |
| **Frontend** | ❌ (n8n UI) |
| **Backend** | ✅ n8n workflows |
| **БД** | ✅ PostgreSQL (через n8n) |
| **API** | ✅ Webhooks |
| **AI** | ✅✅ Multi-LLM consensus, competitive intel |
| **Автоматизация** | ✅✅✅ |
| **Финансовая логика** | ❌ |
| **Docker** | ✅ docker-compose.yml |
| **Документация** | ✅ README с Mermaid-схемой |
| **Тесты** | ✅ `test_workflows.py` |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅ |
| **Секретные данные** | ❌ (шаблоны без секретов) |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 10. pptx-redesigner

| Поле | Значение |
|------|----------|
| **Путь** | `02-automation/pptx-redesigner/` |
| **Назначение** | Набор Python-инструментов для анализа и редизайна PowerPoint-презентаций |
| **Бизнес-задача** | Автоматическое улучшение визуального дизайна PPTX |
| **Стек** | Python (python-pptx, Pillow) |
| **Размер/сложность** | Small |
| **Готовность** | 🟠 Прототип |
| **Запускается** | ✅ |
| **Frontend** | ❌ |
| **Backend** | ❌ (скрипты) |
| **AI** | ❌ |
| **Документация** | ✅ README |
| **Тесты** | ❌ |
| **GitHub Fit** | ⭐ |
| **Portfolio Value** | ⭐ |

---

### 11. yandex-google-sync

| Поле | Значение |
|------|----------|
| **Путь** | `02-automation/yandex-google-sync/` |
| **Назначение** | Синхронизация Яндекс.Диск/Яндекс.Почта с Google Drive/Gmail |
| **Бизнес-задача** | Двусторонняя синхронизация данных между Яндекс и Google экосистемами |
| **Стек** | Python, Docker, OAuth (Yandex + Google) |
| **Размер/сложность** | Medium |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ (нужны OAuth credentials) |
| **Frontend** | ❌ |
| **Backend** | ✅ Python sync engine |
| **API** | ✅ Yandex API + Google API |
| **Docker** | ✅ |
| **Документация** | ✅ |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐ |

---

## РАЗДЕЛ 03 — AI Products

---

### 12. autonomous-agents

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/autonomous-agents/` |
| **Назначение** | Платформа для запуска и управления автономными AI-агентами с web UI |
| **Бизнес-задача** | Единая точка управления различными AI-агентами через браузер |
| **Стек** | Python (FastAPI), HTML/CSS/JS, Docker |
| **Размер/сложность** | Medium |
| **Готовность** | 🟠 Прототип |
| **Запускается** | 🟡 |
| **Frontend** | ✅ Static HTML/JS |
| **Backend** | ✅ FastAPI |
| **Docker** | ✅ docker-compose |
| **Документация** | 🟡 README |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐ |
| **Portfolio Value** | ⭐ |

---

### 13. bots-platform

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/bots-platform/` |
| **Назначение** | Набор Telegram-ботов: модератор (нарушения), репортёр (публикации), сторож (мониторинг) |
| **Бизнес-задача** | Автоматизация модерации и управления Telegram-каналами/группами |
| **Стек** | Python (aiogram/telethon), uv, pyproject.toml |
| **Размер/сложность** | Medium |
| **Готовность** | 🟢 Рабочие боты (production) |
| **Запускается** | ✅ (нужны Telegram credentials) |
| **AI** | ✅ (LLM для проверки нарушений) |
| **Автоматизация** | ✅✅ |
| **Docker** | ❌ |
| **Документация** | 🟡 README (верхний уровень) |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **Секретные данные** | 🔴 Telegram API credentials — нужна осторожность |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 14. crewai-multiagent

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/crewai-multiagent/` |
| **Назначение** | Multi-agent SEO анализ с CrewAI: парсинг сайта → SEO анализ → рекомендации |
| **Бизнес-задача** | Автоматический SEO-аудит сайта с помощью нескольких специализированных AI-агентов |
| **Стек** | Python (CrewAI, FastAPI), Docker |
| **Размер/сложность** | Medium |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ |
| **Frontend** | ✅ Static HTML |
| **Backend** | ✅ FastAPI |
| **AI** | ✅✅ CrewAI multi-agent |
| **Docker** | ✅ docker-compose |
| **Документация** | ✅ README |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 15. finance-mcp-server ⭐ ВИТРИНА

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/finance-mcp-server/` |
| **Назначение** | MCP-сервер с 19 финансовыми инструментами поверх SQLite. Подключается к Claude Desktop/Cursor и отвечает на вопросы по P&L, Cash Flow, Balance Sheet, AR/AP, платежам и инвестпроектам |
| **Бизнес-задача** | Финансист задаёт вопросы по своим данным прямо из AI-ассистента, без экспорта CSV и промежуточных скриптов |
| **Стек** | Python (MCP SDK, SQLite, pydantic), Next.js (UI), Docker, pytest |
| **Размер/сложность** | Large. Сложная предметная логика, 19 tools, seed data, тесты |
| **Готовность** | 🟢 Production-quality |
| **Запускается** | ✅ `pip install -r requirements.txt && python server.py` |
| **Frontend** | ✅ Next.js UI (`product-mcp-ui/`) |
| **Backend** | ✅ Python MCP server |
| **БД** | ✅ SQLite + schema + seed data |
| **API** | ✅ MCP protocol + REST |
| **AI** | ✅✅ MCP integration (Claude Desktop/Cursor) |
| **Автоматизация** | ✅ |
| **Финансовая логика** | ✅✅✅ P&L, Cash Flow, Balance Sheet, NPV/IRR, ликвидность, договоры, бюджет vs факт |
| **Docker** | ✅ |
| **Документация** | ✅✅ Подробный README с примерами запросов |
| **Тесты** | ✅✅ Обширное покрытие (KPI, liquidity, contracts, investments, negative cases) |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅✅ |
| **Секретные данные** | ❌ (данные локальные) |
| **Хардкод путей/токенов** | 🟡 Абсолютный путь в примере подключения (не в коде) |
| **Внешние зависимости** | ❌ (локально) |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 16. hr-breaker ⭐ ВИТРИНА

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/hr-breaker/` |
| **Назначение** | AI-инструмент оптимизации резюме: любой формат на вход → ATS-friendly PDF на выход |
| **Бизнес-задача** | Адаптация резюме под конкретную вакансию с сохранением честности данных (антигаллюцинационный фильтр) |
| **Стек** | Python (Pydantic-AI, FastAPI, Click, WeasyPrint, LiteLLM), Alpine.js, uv, Docker |
| **Размер/сложность** | Large. Сложный multi-filter pipeline (8 фильтров), 30+ тестов, CLI + Web UI |
| **Готовность** | 🟢 Production-quality |
| **Запускается** | ✅ `uv sync && uv run hr-breaker serve` |
| **Frontend** | ✅ Alpine.js web app с real-time SSE прогрессом |
| **Backend** | ✅ FastAPI + orchestration engine |
| **БД** | ✅ Local profiles storage + index.json |
| **API** | ✅ FastAPI + SSE streaming |
| **AI** | ✅✅✅ Pydantic-AI agents, multiple LLM providers (LiteLLM), 8-layer filter pipeline |
| **Автоматизация** | ✅ CLI pipeline |
| **Финансовая логика** | ❌ |
| **Docker** | ✅ |
| **Документация** | ✅✅ README + архитектура в коде |
| **Тесты** | ✅✅✅ 30+ тестов (agent construction, filters, orchestration, PDF, translation...) |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅✅ |
| **Секретные данные** | ❌ (API ключи через env) |
| **Хардкод путей/токенов** | ❌ |
| **Внешние зависимости** | LLM API (Gemini/OpenAI/Anthropic) |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 17. personal-rag-assistant

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/personal-rag-assistant/` |
| **Назначение** | Telegram-бот с персональной долгосрочной памятью (RAG), поддержкой документов, Haystack-агентом |
| **Бизнес-задача** | Персональный AI-ассистент, помнящий историю диалога и работающий с собственными документами |
| **Стек** | Python (Haystack, Docling, Pinecone, aiogram), Docker |
| **Размер/сложность** | Medium-Large |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ (нужны Pinecone + LLM ключи) |
| **Frontend** | ❌ (Telegram) |
| **Backend** | ✅ Python pipelines |
| **БД** | ✅ Pinecone (векторная) |
| **AI** | ✅✅ RAG, Haystack agent, Docling |
| **Docker** | ✅ |
| **Документация** | ✅ README + ARCHITECTURE.md |
| **Тесты** | ✅ `test_ingestion_idempotency.py` |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 18. rf-macro-risk-ai ⭐ ВИТРИНА

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/rf-macro-risk-ai/` |
| **Назначение** | AI-агент для макро-оценки экономики РФ: 35 критериев, scoring, 6-месячный горизонт риска |
| **Бизнес-задача** | Автоматическое отслеживание рисков кризисного сценария для финансовых решений |
| **Стек** | Python (LangChain, LangGraph, Tavily), uv, Docker, GitHub Pages |
| **Размер/сложность** | Medium |
| **Готовность** | 🟢 Production (live demo на GitHub Pages) |
| **Запускается** | ✅ |
| **Frontend** | ✅ GitHub Pages static dashboard |
| **Backend** | ✅ Python LangChain agent |
| **API** | ✅ Tavily search API |
| **AI** | ✅✅ LangChain agent, multi-provider LLM (OpenAI/Gemini/GigaChat/Anthropic) |
| **Автоматизация** | ✅ Telegram publish pipeline |
| **Финансовая логика** | ✅✅✅ Macro risk scoring, 35 критериев по типу источника и скорости реагирования |
| **Docker** | ✅ |
| **Документация** | ✅✅ README + AGENTS.md |
| **Тесты** | ✅ `test_criteria_validation.py` + `test_source_registry.py` |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅ |
| **Секретные данные** | ❌ |
| **Хардкод путей/токенов** | 🟡 BOT_REPORTER_DIR — локальный путь |
| **Внешние зависимости** | LLM API + Tavily |
| **Demo** | ✅ kaluginvit.github.io/rf-macro-risk-ai |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 19. seo-mcp-bot

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/seo-mcp-bot/` |
| **Назначение** | MCP-сервер для Яндекс.Вордстат + SEO-анализ |
| **Бизнес-задача** | Интеграция Яндекс.Вордстат в AI-ассистент для SEO-анализа |
| **Стек** | Python (MCP), Docker |
| **Размер/сложность** | Small |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ |
| **AI** | ✅ MCP |
| **Docker** | ✅ |
| **Документация** | ✅ README |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐ |
| **Portfolio Value** | ⭐ |

---

### 20. svo-payments-bot ⭐ ВИТРИНА

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/svo-payments-bot/` |
| **Назначение** | Production Telegram-бот: калькулятор выплат СВО + лид-форма. Две ветки анкеты, FSM, SQLite, CI/CD |
| **Бизнес-задача** | Помочь семьям разобраться с выплатами и подать заявку на консультацию |
| **Стек** | Python (aiogram 3, aiosqlite), Docker, GitHub Actions, GHCR |
| **Размер/сложность** | Large. Production-ready: FSM persistence, webhook, CI/CD pipeline |
| **Готовность** | 🟢 Production |
| **Запускается** | ✅ `docker compose up -d --build` |
| **Frontend** | ❌ (Telegram) |
| **Backend** | ✅✅ Полноценный модульный backend |
| **БД** | ✅ SQLite с WAL, FSM storage |
| **API** | ✅ Telegram API + опциональный webhook |
| **AI** | ❌ (расчётная логика) |
| **Автоматизация** | ✅ CI/CD: build → GHCR → SSH deploy |
| **Финансовая логика** | ✅✅ Расчёт видов выплат, коэффициенты, дисклеймер |
| **Docker** | ✅✅ Dockerfile + docker-compose + docker-compose.deploy.yml |
| **Документация** | ✅✅ Подробный README с таблицей env, командами, CI-секции |
| **Тесты** | ✅ `test_scenarios.py` + `test_quiz_calculate.py` |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅✅ |
| **Секретные данные** | ❌ (только через env) |
| **Хардкод путей/токенов** | ❌ |
| **Внешние зависимости** | Telegram BotFather token |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 21. team-ai-bot

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/team-ai-bot/` |
| **Назначение** | Командный AI-бот в Telegram с RAG поверх истории чата, Pinecone |
| **Бизнес-задача** | Корпоративная база знаний + AI-поиск по истории переписки команды |
| **Стек** | Python (aiogram, Pinecone, OpenAI), Docker |
| **Размер/сложность** | Medium |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ |
| **AI** | ✅✅ RAG + Pinecone + summarization |
| **Docker** | ✅ docker-compose |
| **Документация** | ✅ README + architecture.png |
| **Тесты** | ✅ |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 22. team-tg-bot-vc

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/team-tg-bot-vc/` |
| **Назначение** | Простой Telegram-бот для управления задачами команды |
| **Бизнес-задача** | Базовый task tracker через Telegram |
| **Стек** | Python (aiogram), SQLite, Docker |
| **Размер/сложность** | Small |
| **Готовность** | 🟡 MVP |
| **GitHub Fit** | ⭐ |
| **Portfolio Value** | ⭐ |

---

### 23. tg-catalog-analyzer

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/tg-catalog-analyzer/` |
| **Назначение** | Анализ и рубрикация постов Telegram-каталога с помощью LLM |
| **Бизнес-задача** | Структурирование хаотичного каталога Telegram-постов |
| **Стек** | Python (aiogram, OpenRouter), Docker |
| **Размер/сложность** | Small |
| **Готовность** | 🟡 MVP |
| **GitHub Fit** | ⭐ |
| **Portfolio Value** | ⭐ |

---

### 24. tg-digest-pipeline

| Поле | Значение |
|------|----------|
| **Путь** | `03-ai-products/tg-digest-pipeline/` |
| **Назначение** | RAG-пайплайн Telegram-канала: сбор постов → фильтрация → семантический поиск → граф знаний Neo4j → дайджест → Pinecone |
| **Бизнес-задача** | Автоматическая обработка и структурирование контента из Telegram-каналов (финансы, coding) |
| **Стек** | Python (Telethon, LangChain, Pinecone, Neo4j, FastAPI, Jinja2), SQLite, uv |
| **Размер/сложность** | Extra Large. Сложнейший личный инструмент с множеством независимых пайплайнов |
| **Готовность** | 🟡 Рабочий личный инструмент |
| **Запускается** | 🟡 (требует Telegram session + многих API) |
| **Frontend** | ✅ Flask web UI |
| **Backend** | ✅✅ Множество скриптов |
| **БД** | ✅ SQLite + Pinecone + Neo4j |
| **AI** | ✅✅✅ Embeddings, RAG, LLM summarization, clustering |
| **Финансовая логика** | ✅ Финансовые каналы, обработка финансового контента |
| **Docker** | ✅ |
| **Документация** | ✅ README (технический) |
| **Тесты** | ✅ `test_schema.py` |
| **.env.example** | ✅ |
| **Секретные данные** | 🔴 Telegram session файлы (в .gitignore) |
| **GitHub Fit** | ⭐⭐ (сложно показать без личного контекста) |
| **Portfolio Value** | ⭐⭐ |

---

## РАЗДЕЛ 04 — Web

---

### 25. dostaffkin

| Поле | Значение |
|------|----------|
| **Путь** | `04-web/dostaffkin/` |
| **Назначение** | Сайт стаффинговой компании (Angular) |
| **Бизнес-задача** | Корпоративный сайт для компании по подбору персонала |
| **Стек** | Angular, Node.js, Docker |
| **Размер/сложность** | Medium |
| **Готовность** | 🟡 MVP |
| **Запускается** | 🟡 (нужен сборка Angular) |
| **Frontend** | ✅✅ Angular |
| **Backend** | ✅ Node.js backend |
| **БД** | ❌ |
| **Docker** | ✅ docker-compose |
| **Документация** | ✅ README |
| **Тесты** | ❌ |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐ |

---

### 26. finance-data-screener ⭐ ВИТРИНА

| Поле | Значение |
|------|----------|
| **Путь** | `04-web/finance-data-screener/` |
| **Назначение** | AI-скринер финансовых данных: пользователь вводит запрос на русском → LLM строит план сбора → система собирает данные с MOEX/ЦБ/новости → интерактивная витрина с графиком + экспорт |
| **Бизнес-задача** | Доступный финансовый data-сбор для аналитиков без знания API — просто текстовый запрос |
| **Стек** | FastAPI + PostgreSQL + Alembic + React + TypeScript + Tailwind + Recharts + GPT-4o-mini + Docker |
| **Размер/сложность** | Large. Полный стек, 3 источника данных, LLM-планировщик, аудит, 18 тестов |
| **Готовность** | 🟢 Production-quality |
| **Запускается** | ✅ `docker compose -p screener up --build` |
| **Frontend** | ✅✅ React + TypeScript + Tailwind + Recharts |
| **Backend** | ✅✅ FastAPI async, SQLAlchemy 2.0 |
| **БД** | ✅✅ PostgreSQL + Alembic миграции |
| **API** | ✅✅ REST + MOEX ISS + ЦБ РФ + ТАСС |
| **AI** | ✅✅ GPT-4o-mini + instructor (строгий JSON) |
| **Автоматизация** | ✅ Data collection pipeline |
| **Финансовая логика** | ✅✅✅ MOEX stocks/bonds, ЦБ currency rates, news |
| **Docker** | ✅✅ 3-сервисный docker-compose |
| **Документация** | ✅✅ Подробный README с curl примерами, SQL запросами |
| **Тесты** | ✅✅ 18 тестов (health, CRUD, audit) |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅✅ |
| **Секретные данные** | ❌ (только ProxyAPI key через env) |
| **Хардкод путей/токенов** | ❌ |
| **Внешние зависимости** | ProxyAPI (OpenAI-compatible) |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 27. finsight

| Поле | Значение |
|------|----------|
| **Путь** | `04-web/finsight/` |
| **Назначение** | Web-приложение: загрузка CSV/Excel → AI-анализ (Claude) → интерактивный чат по данным |
| **Бизнес-задача** | Быстрый финансовый анализ данных через разговорный интерфейс |
| **Стек** | FastAPI + React (JSX) + Claude API + Docker |
| **Размер/сложность** | Small-Medium |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ docker compose up |
| **Frontend** | ✅ React |
| **Backend** | ✅ FastAPI |
| **AI** | ✅ Claude API |
| **Docker** | ✅ docker-compose |
| **Документация** | ✅ README + screenshots |
| **Тесты** | ✅ `test_api.py` |
| **.env.example** | ✅ |
| **GitHub Fit** | ⭐⭐ |
| **Portfolio Value** | ⭐⭐ |

---

### 28. mini-crm-fastapi-react ⭐ ВИТРИНА

| Поле | Значение |
|------|----------|
| **Путь** | `04-web/mini-crm-fastapi-react/` |
| **Назначение** | Mini-CRM: клиенты, сделки, задачи + интеграция Google Drive/Sheets через OAuth |
| **Бизнес-задача** | Компактная CRM-система с выгрузкой отчётов в Google Sheets |
| **Стек** | FastAPI + SQLite + React (TypeScript) + Google OAuth + Docker |
| **Размер/сложность** | Medium-Large |
| **Готовность** | 🟡 MVP |
| **Запускается** | ✅ `docker compose up --build` |
| **Frontend** | ✅✅ React TypeScript |
| **Backend** | ✅✅ FastAPI |
| **БД** | ✅ SQLite |
| **API** | ✅ REST + Google Drive/Sheets API |
| **AI** | ❌ |
| **Docker** | ✅ |
| **Документация** | ✅✅ README + SECURITY.md |
| **Тесты** | ✅ smoke tests |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅✅ |
| **Секретные данные** | ❌ (templates с .example, .gitignore) |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

### 29. svo-payouts-website ⭐ ВИТРИНА

| Поле | Значение |
|------|----------|
| **Путь** | `04-web/svo-payouts-website/` |
| **Назначение** | Production сайт для семей погибших участников СВО: квиз → расчёт выплат → лид-форма |
| **Бизнес-задача** | Помочь людям разобраться с системой выплат и подать заявку на консультацию |
| **Стек** | Next.js 14, TypeScript, Tailwind, Playwright E2E, Docker, nginx, VPS CI/CD |
| **Размер/сложность** | Large. Живой production сайт (svorazbor.ru) |
| **Готовность** | 🟢 Production (svorazbor.ru) |
| **Запускается** | ✅ |
| **Frontend** | ✅✅✅ Next.js, responsive, mobile-first |
| **Backend** | ✅ API routes |
| **БД** | ❌ (лиды через webhook) |
| **API** | ✅ Webhook integration |
| **AI** | ❌ |
| **Docker** | ✅✅ Docker + nginx конфиги |
| **Документация** | ✅✅ README + RELATED.md + deploy docs |
| **Тесты** | ✅✅ Playwright E2E (4 spec files), Vitest |
| **.env.example** | ✅ |
| **Инструкции запуска** | ✅✅ |
| **Секретные данные** | ❌ |
| **Хардкод путей/токенов** | ❌ |
| **Внешние зависимости** | ❌ |
| **Demo** | ✅ LIVE: svorazbor.ru |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ |

---

## РАЗДЕЛ — Site (Portfolio Website)

### 30. site (portfolio-site)

| Поле | Значение |
|------|----------|
| **Путь** | `site/` |
| **Назначение** | Персональный сайт-портфолио на Astro |
| **Стек** | Astro, TypeScript, Tailwind |
| **Готовность** | 🟢 Production |
| **GitHub Fit** | ⭐⭐⭐ |
| **Portfolio Value** | ⭐⭐⭐ (мета-проект) |

---

## РАЗДЕЛ 99 — Archive (Educational & Prototypes)

Все проекты в `99-archive/` классифицированы как **TIER D — ARCHIVE**.

| # | Проект | Тип | Примечание |
|---|--------|-----|------------|
| 31 | `ai-automation-lessons` | Учебный | AI-автоматизация, учебный бот |
| 32 | `ai-bot-lessons` | Учебный | Telegram бот с LLM, образовательный |
| 33 | `ai-coding-lessons` | Учебный | Python REST API + Go user server, учебный |
| 34 | `api-lessons` | Учебный | Основы API (currency, weather), CLI |
| 35 | `api-testing-bot` | Учебный | Тестирование GigaChat/Chutes API |
| 36 | `auto-deploy-lesson` | Учебный | Минимальный Docker deploy |
| 37 | `db-lessons` | Учебный | SQL, SQLite — задания и решения |
| 38 | `desktop-reminder` | Прототип | Desktop reminder app (Tkinter) |
| 39 | `docker-lessons` | Учебный | Базовый Docker контейнер |
| 40 | `docker-vps-project` | Учебный | Telegram бот с деплоем на VPS |
| 41 | `expert-project` | Прототип | OpenAI-based expert assistant |
| 42 | `langchain-lesson-1` | Учебный | Первые шаги LangChain |
| 43 | `langchain-lesson-2` | Учебный | LangChain агент |
| 44 | `llm-lessons` | Учебный | LLM API, prompts, Telegram бот |
| 45 | `local-ai-agent` | Прототип | Локальный AI агент с памятью |
| 46 | `loki-grafana-stack` | Прототип | Логирование (Loki + Grafana) |
| 47 | `mcp-practice` | Учебный | MCP practice (coin flip API) |
| 48 | `memory-lessons` | Учебный | Память LLM (short/long/hybrid) |
| 49 | `mini-booking-system` | Прототип | Mini booking system (Tkinter + PostgreSQL) |
| 50 | `password-generator` | Утилита | Password manager (Tkinter) |
| 51 | `postgres-lessons` | Учебный | PostgreSQL, pgdriver, задания |
| 52 | `prompting-case` | Исследование | Сравнение промптов (temp 0.1 vs 1.0) |
| 53 | `python-modules-lessons` | Учебный | Основы Python модулей |
| 54 | `python-oop-practice` | Учебный | OOP практика (task/project models) |
| 55 | `rag-lessons` | Учебный | RAG с Pinecone, образовательный |
| 56 | `recipe-search-bot` | Прототип | Telegram бот поиска рецептов |
| 57 | `recurring-payments-reminder` | Прототип | Напоминалка платежей (Telegram) |
| 58 | `sql-lessons` | Учебный | SQL задания (window functions, CTE, etc.) |
| 59 | `sqlite-lesson` | Учебный | SQLite basics, IMDB dataset |
| 60 | `ux-reviewer-agent` | Прототип | UX reviewer с LLM (незавершён) |

---

## Сводная таблица

| Категория | Кол-во |
|-----------|--------|
| Активные проекты (01-04) | 29 |
| Archive | 30 |
| **Итого** | **59** |
| TIER A кандидаты | 8 |
| TIER B | 11 |
| TIER C | 10 |
| TIER D (archive) | 30 |
