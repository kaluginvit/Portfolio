---
name: Portfolio thematic restructure
overview: "Сессия 1: реструктуризация и гигиена. Сессия 2: 8 флагманов первой волны. Сессия 3: вторая волна флагманов, корневая витрина README, минимальные README по не-флагманам. Сессия 4 (Этап 6+7): пересборка архива — 7 проектов промоутятся в направления, оставшийся архив сжимается до 15 «keep» с потенциалом доводки, 15 «remove» удаляются из репо (локально остаются)."
todos:
  - id: gitignore-and-cleanup
    content: "Сессия 1: создать корневой .gitignore, удалить .venv/venv/node_modules/.next/__pycache__/.pytest_cache/логи (~30 000 файлов)"
    status: completed
  - id: secrets-cleanup
    content: "Сессия 1: удалить .env, google_token.json, yandex_token.json, .sync_state из исходных папок"
    status: completed
  - id: absorb-nested-git
    content: "Сессия 1: удалить вложенные .git в «Сайт СВО» и «Чат-бот по выплатам СВО_new» (пользователь подтвердил)"
    status: completed
  - id: create-categories
    content: "Сессия 1: создать 6 категорийных папок (01-data-analytics, 02-automation, 03-ai-products, 04-web, 05-ai-consulting, 99-archive)"
    status: completed
  - id: git-mv-rename
    content: "Сессия 1: перенести все 30+ подпроектов через git mv с переименованием на latin-kebab по карте"
    status: completed
  - id: cleanup-empty-folders
    content: "Сессия 1: удалить опустевшие исходные папки (Уроки_VC, Проекты_VC, _Проекты, и т.д.)"
    status: completed
  - id: stage-1-commit
    content: "Сессия 1: коммит «chore: thematic restructure of portfolio» и push в origin/main"
    status: completed
  - id: category-readmes
    content: "Сессия 2: README.md в каждой категорийной папке (обзор + список кейсов)"
    status: completed
  - id: flagship-leadgen
    content: "Сессия 2 — флагман A1: leadgen-n8n-system — обзор 11 workflow в README, mermaid-схема, скрины"
    status: completed
  - id: flagship-svo-pair
    content: "Сессия 2 — флагман A2: svo-payouts-website + svo-payments-bot — спарка лендинг+бот как один кейс"
    status: completed
  - id: flagship-yandex-google-sync
    content: "Сессия 2 — флагман A3: yandex-google-sync — Dockerfile, чистка .env, инструкция OAuth"
    status: completed
  - id: flagship-seo-mcp
    content: "Сессия 2 — флагман A4: seo-mcp-bot — описание MCP-сервера, инструкция подключения к Cursor/Claude"
    status: completed
  - id: flagship-wb-commercial
    content: "Сессия 2 — флагман A5: wb-sales-commercial-analysis — скрин отчёта, обезличить данные если нужно"
    status: completed
  - id: flagship-superstore
    content: "Сессия 2 — флагман A6: superstore-retail-analytics — скрины, GitHub Pages, INSIGHTS.md"
    status: completed
  - id: flagship-team-bot
    content: "Сессия 2 — флагман A7: team-ai-bot — Dockerfile, docker-compose, раздел «Деплой»"
    status: completed
  - id: flagship-rag-assistant
    content: "Сессия 2 — флагман A8: personal-rag-assistant — удалить .venv, Dockerfile, одна entrypoint"
    status: completed
  - id: flagship-wave-2
    content: "Сессия 3 — вторая волна: hotel-booking-tally-supabase, barista-payroll-sheets, audio-transcriber, fintech-ab-test, ai-in-accounting"
    status: completed
  - id: non-flagship-cleanup
    content: "Сессия 3: минимальная косметика для ~15 не-флагман проектов (4-блочный README + чистка)"
    status: completed
  - id: root-readme
    content: "Сессия 3: корневой README.md — hero, бейджи, карточки категорий, контакты, featured-блок"
    status: completed
  - id: rename-repo-optional
    content: (Опционально) На GitHub имя репозитория привести к Portfolio — если ещё не сделано
    status: pending
  - id: git-mv-7
    content: "Этап 6.1: перенести 7 папок из 99-archive через git mv (mcp-lesson, autonomous-agents → 03-ai-products; mortgage-calculator, n8n-bpmn-notes, github-actions-setup → 02-automation; pdf-checker → 03-ai-products; postgres-work → 04-web)"
    status: completed
  - id: dedup-autonomous-local
    content: "Этап 6.2: удалить 99-archive/autonomous-agents-local/ (дубль autonomous-agents)"
    status: completed
  - id: merge-go-server
    content: "Этап 6.3: влить 99-archive/go-server-mini/ внутрь 99-archive/ai-coding-lessons/ как Go-аналог Python API (демонстрация языкового паритета)"
    status: completed
  - id: readme-promoted-automation
    content: "Этап 6.4: README у 3 промо-проектов в 02-automation (mortgage-calculator — финрасчёты; n8n-bpmn-notes — методика BPMN; github-actions-setup — CI/CD-шаблон)"
    status: completed
  - id: readme-promoted-ai
    content: "Этап 6.5: README у 3 промо-проектов в 03-ai-products (mcp-lesson, autonomous-agents, pdf-checker) — проблема/решение/стек/демо"
    status: completed
  - id: readme-promoted-web
    content: "Этап 6.6: README у 04-web/postgres-work — описание fullstack-кейса с PostgreSQL"
    status: completed
  - id: readme-cats-update
    content: "Этап 6.7: обновить категорийные README 02-automation/03-ai-products/04-web — добавить промо-проекты в таблицы"
    status: completed
  - id: readme-root-update
    content: "Этап 6.8: корневой README.md — добавить промо-проекты в карточки/featured-блок где уместно"
    status: completed
  - id: archive-prune-cached
    content: "Этап 7.1: git rm -r --cached на 15 «remove» папок в 99-archive (api-testing-bot, auto-deploy-lesson, autonomous-agents-local, db-lessons, docker-lessons, langchain-lesson-1, langchain-lesson-2, llm-lessons, local-ai-agent, loki-grafana-stack, python-modules-lessons, python-oop-practice, recipe-search-bot, sql-lessons, sqlite-lesson) — локально файлы остаются"
    status: completed
  - id: gitignore-prune
    content: "Этап 7.2: дописать 15 удалённых путей в корневой .gitignore (под секцией # Pruned archive)"
    status: completed
  - id: readme-archive-rebuild
    content: "Этап 7.3: переписать 99-archive/README.md — список 15 «keep» с описаниями (9 полузавершённых продуктов + 6 методических артефактов с кодом)"
    status: completed
  - id: commit-push-final
    content: "Этап 6+7 финал: 2 коммита (chore(archive): promote 7 + chore(archive): prune to 15) и git push origin main без force"
    status: completed
isProject: false
---

## Стратегия

Цель — продающее портфолио. Инструменты:
1. **Тематическая навигация** — рекрутёр/клиент за 5 секунд понимает, что вы умеете.
2. **Флагманские кейсы** доведены до prod-вида (Docker, демо, скрины, чистый README).
3. **Учебные артефакты** не выкидываем (вы выбрали `all_kept`), но прячем во «второй ряд» так, чтобы они не размывали витрину.
4. **Латиница в URL, русский в заголовках** (выбор `latin_with_titles`).

Работа разбита на 5 этапов; внутри плана только структура и каркас, контентная доводка текстов в README идёт после подтверждения.

## Целевая структура (Вариант C — 5 направлений + архив)

```
_Portfolio/                              ← репозиторий kaluginvit-svg/Portfolio
├── README.md                            ← витрина (карточки 5 направлений + контакты)
├── .gitignore                           ← общий: .venv, venv, node_modules, .next, __pycache__, .env, *.log
├── ASSETS/                              ← общие медиа: аватар, шапка, иконки
│
├── 01-data-analytics/                   ← Аналитика и работа с данными
│   ├── README.md
│   ├── superstore-retail-analytics/     ← из «Бизнес_аналитика»                           (ФЛАГМАН A6)
│   ├── wb-sales-commercial-analysis/    ← из «Задание» — реальный коммерческий анализ WB (ФЛАГМАН A5)
│   ├── fintech-ab-test-credit-offer/    ← из «Fintech-ab-test-credit-offer»; единый кейс A/B (ТЗ: docs/)
│   ├── wb-tailoring-test-analysis/      ← из «Тестовый швейный»
│   ├── customer-segmentation/           ← сегментация пользователей
│   ├── marketplace-unit-economics/      ← юнит-экономика маркетплейса
│   ├── product-metrics/                 ← продуктовые метрики
│   ├── python-business-analytics/
│   ├── python-business-case/
│   ├── sql-business-case/
│   ├── reviews-sentiment/               ← анализ отзывов
│   └── data-work-utilities/             ← из «_Проекты\Работа с данными»
│       (↑ дубликаты data-analyst-final-* удалены; единый кейс — fintech-ab-test-credit-offer + ТЗ в docs/)
│
├── 02-automation/                       ← Автоматизация процессов
│   ├── README.md
│   ├── leadgen-n8n-system/              ← из «Лидогенерация» — 11 связанных workflow      (ФЛАГМАН A1)
│   ├── yandex-google-sync/              ← из «ИзЯндексаВГугл» — sync с OAuth и БД          (ФЛАГМАН A3)
│   ├── hotel-booking-tally-supabase/    ← из «Итоговый проект_n8n»                        (флагман 2-й волны)
│   ├── barista-payroll-sheets/          ← из «Скрипты для таблиц»                          (флагман 2-й волны)
│   ├── bankrot-trades-scraper/          ← из «Scrapling» — парсер торгов + Flask UI
│   ├── pptx-redesigner/                 ← из «Презентация» — утилита редизайна слайдов
│   ├── n8n-ma03-homework/               ← из «Проекты_n8n\MA03_ДЗ»
│   ├── weather-api/                     ← из «Проекты_VC\Погода-API»
│   └── currency-travel-api/             ← из «Проекты_VC\Валюта в путешествиях API»
│
├── 03-ai-products/                      ← ИИ-продукты: боты, RAG, агенты, MCP
│   ├── README.md
│   ├── seo-mcp-bot/                     ← из «SEO-бот» — MCP-серверы Yandex Wordstat       (ФЛАГМАН A4)
│   ├── svo-payments-bot/                ← из «Чат-бот по выплатам СВО_new»                 (ФЛАГМАН A2, парный с сайтом)
│   ├── team-ai-bot/                     ← из «Уроки_VC\Диалоговый бот для команды»         (ФЛАГМАН A7)
│   ├── personal-rag-assistant/          ← из «Уроки_VC\Диалоговый бот - поиск_по_данным»   (ФЛАГМАН A8)
│   ├── audio-transcriber/               ← из «Транскрибатор» — faster-whisper              (флагман 2-й волны)
│   ├── tg-catalog-analyzer/             ← из «Каталоги ТГ» — анализ TG через OpenRouter
│   ├── finance-mcp-server/              ← из «Проекты_VC\Финансовый MCP»
│   ├── crewai-multiagent/               ← из «_Проекты\Проект CrewAI»
│   ├── smart-text-helper/               ← из «Проекты_VC\Умный текст-помощник»
│   ├── weather-tg-bot/                  ← из «Проекты_VC\Погода в ТГ-боте»
│   ├── team-tg-bot-vc/                  ← из «Проекты_VC\ТГ-бот_для_команды»
│   ├── memory-bot/                      ← из «Уроки_VC\Бот с памятью» (узкий сценарий, не полный RAG)
│   └── (dialog-bot-assistant / dialog-bot-with-memory удалены как дубли personal-rag-assistant)
│
├── 04-web/                              ← Сайты и фронтенд-продукты
│   ├── README.md
│   ├── svo-payouts-website/             ← из «Сайт СВО» — Next.js + квиз                   (ФЛАГМАН A2, парный с ботом)
│   └── dostaffkin/                      ← Angular + Express: доставка, PostgreSQL
│
├── 05-ai-consulting/                    ← Стратегии и кейсы внедрения ИИ
│   ├── README.md
│   └── ai-in-accounting-strategic-plan/ ← из «ИИ в бухгалтерии»                            (флагман 2-й волны)
│
└── 99-archive/                          ← Учебные артефакты и эксперименты
    ├── README.md
    ├── api-lessons/                     ← из «Уроки_VC\Уроки с API»
    ├── postgres-lessons/                ← из «Уроки_VC\Уроки с PostgreSQL»
    └── go-server-mini/                  ← из «Уроки_VC\Уроки с AI_3 (кодинг)\go-server»
```

Принцип нумерации `01-…99-` — папки в GitHub UI и в файловом менеджере сортируются именно в этом порядке, что само по себе работает как «иерархия важности». Архив с префиксом `99-` уезжает в самый низ.

### Логика распределения спорных проектов

- **API-сервисы без ИИ** (`weather-api`, `currency-travel-api`) — в `02-automation` (утилитарный сервис в чьём-то workflow).
- **Простые боты** (`weather-tg-bot`) — в `03-ai-products` (для пользователя это бот в Telegram).
- **MCP-серверы** (`finance-mcp-server`, `seo-mcp-bot`) — в `03-ai-products` (интерфейс именно для AI-агентов).
- **`Сайт СВО` + `Чат-бот по выплатам СВО_new`** — это **связанная пара** одного клиентского продукта. В корневом README они представляются **как один кейс** «Калькулятор выплат СВО» с двумя артефактами (web + bot), даже физически живут в разных категориях.
- **Парсер банкротных торгов** — в `02-automation` (это автоматизация сбора публичных данных, а не «ИИ-продукт»).
- **Утилита редизайна PPTX** — в `02-automation` (автоматизация рутинной работы с презентациями), а не в архиве.
- **Учебный Go-сервер**, уроки API, уроки PostgreSQL — в `99-archive`.

### Связанные пары и кросс-ссылки

`svo-payouts-website` и `svo-payments-bot` дополнительно ссылаются друг на друга через `RELATED.md` или раздел «Парный проект» в каждом из README. В корневой витрине комплект подаётся как один кейс «Калькулятор выплат СВО — лендинг + Telegram-бот».

## Этап 1. Гигиена и каркас

Действия в строгом порядке:

**1.1. Корневой `.gitignore`** со списком: `**/.venv/`, `**/venv/`, `**/__pycache__/`, `**/.pytest_cache/`, `**/.mypy_cache/`, `**/.ruff_cache/`, `**/node_modules/`, `**/.next/`, `**/.env`, `**/.env.local`, `*.log`, `*.sqlite3`, `**/.sync_state/`, `**/.DS_Store`, `**/google_token.json`, `**/yandex_token.json`, `**/dist/`, `**/build/`, `**/*.tsbuildinfo`.

**1.2. Чистка мусора на диске** (порядка ~30 000 лишних файлов суммарно):
- `Уроки_VC\Диалоговый бот - поиск_по_данным\.venv\` (~9000 файлов Haystack/torch)
- `Транскрибатор\.venv\` + `Транскрибатор\venv\` (~10000 файлов faster-whisper/tokenizers, **двойная** venv)
- `Scrapling\venv\` (~2300 файлов Flask)
- `Каталоги ТГ\.venv\` (~1800 файлов aiogram)
- `Чат-бот по выплатам СВО_new\.venv\` + `.pytest_cache\` (~1700 файлов pytest)
- `Сайт СВО\web\node_modules\` + `\.next\` (десятки тысяч файлов сборки Next.js)
- Все `__pycache__`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache` по дереву
- Локальные SQLite (`bot_state.sqlite3`), `*.log`

**1.3. Чистка секретов из репо** (критично перед публикацией):
- `ИзЯндексаВГугл\.env`, `ИзЯндексаВГугл\google_token.json`, `ИзЯндексаВГугл\.sync_state\` (Яндекс/Google токены)
- `SEO-бот\yandex-wordstat-mcp\.env`
- `Каталоги ТГ\.env` (OpenRouter)
- Любые другие `.env` в подпапках — оставить **только** `.env.example`.

**1.4. Абсорбция вложенных git-репозиториев** (пользователь подтвердил `absorb`):
- `Сайт СВО\.git\` → удалить.
- `Чат-бот по выплатам СВО_new\.git\` → удалить.
- **Риск:** локальная история коммитов этих двух проектов в основном репозитории портфолио теряется. Если на GitHub есть отдельные публичные репо с этим кодом, они не пострадают.

**1.5. Каркас:** создать 6 категорийных папок (`01-data-analytics`, `02-automation`, `03-ai-products`, `04-web`, `05-ai-consulting`, `99-archive`).

**1.6. Перемещение** подпроектов в категории с переименованием на латиницу-kebab через `git mv` (сохраняет историю файлов). Карта переименования — в дереве выше.

**1.7. Удаление опустевших исходных папок:** `Уроки_VC`, `Проекты_VC`, `_Проекты`, `Проекты_n8n`, `Проекты`, `Бизнес_аналитика`, `Скрипты для таблиц`, `Итоговый проект_n8n`, `ИИ в бухгалтерии`, `Лидогенерация`, `ИзЯндексаВГугл`, `SEO-бот`, `Сайт СВО`, `Чат-бот по выплатам СВО_new`, `Транскрибатор`, `Scrapling`, `Каталоги ТГ`, `Презентация`, `Тестовый швейный`, `Задание`.

**1.8. Минимум в каждой подпапке:** `README.md` (где нет — заглушка по единому шаблону), `.env.example` (если код использует `.env`), `requirements.txt`/`package.json` с фиксированными версиями.

После Этапа 1 пушим **первый коммит** «chore: thematic restructure of portfolio» — это уже даёт чистый каркас на GitHub.

## Этап 2. Продакшен-доводка флагманов (8 кейсов первой волны)

Единый шаблон README для всех: **проблема → решение → стек → ценность → как запустить → демо → ограничения**. Плюс кейс-специфика.

### A1 — leadgen-n8n-system (главный флагман автоматизации)
Источник: [Лидогенерация](Лидогенерация). 11 связанных n8n workflow от intent-radar до live dashboard.
- README — карта 11 потоков с описанием каждого блока («что делает», «триггер», «выход») и mermaid-схемой связей между ними.
- В `media/` — скрин общего dashboard и схемы 1-2 workflow в n8n.
- Подраздел «Бизнес-результат» — что эта система делает в воронке: AI-консенсус, прогрев, охлаждение, эскалация.
- Чек-лист «Что нужно для запуска у себя»: переменные окружения, какие сервисы LLM/CRM подключить.

### A2 — svo-payouts-website + svo-payments-bot (комплексный кейс «Калькулятор выплат СВО»)
Источники: [Сайт СВО](Сайт СВО) + [Чат-бот по выплатам СВО_new](Чат-бот по выплатам СВО_new).
- В корневой витрине — **один кейс** с двумя ссылками («Веб-калькулятор» и «Telegram-бот»).
- В каждом из подпроектов — раздел «Парный продукт» с обратной ссылкой и кратким описанием.
- Сайт: после чистки `node_modules`/`.next` — Vercel-деплой и кнопка «Открыть демо» в README.
- Бот: Dockerfile + один скрин квиза + ссылка `t.me/...` (если бот живой).
- Скриншоты сайта (мобильный и десктоп) в `media/`.
- Подчеркнуть, что это **продакшен-продукт реального клиента** — это самое сильное в портфолио.

### A3 — yandex-google-sync (серьёзный backend)
Источник: [ИзЯндексаВГугл](ИзЯндексаВГугл).
- Чистка секретов: убрать `.env`, `google_token.json`, `.sync_state/`. Оставить только `.env.example`.
- README — пошаговая инструкция получения OAuth-токенов (Яндекс и Google).
- Mermaid-схема: какие таблицы, какие сущности, как идёт sync.
- Dockerfile (если работает как сервис) или инструкция запуска через `run-sync.bat`.
- Раздел «Зачем это нужно» — конкретный бизнес-сценарий (миграция файлов между облаками).

### A4 — seo-mcp-bot (свежее направление: MCP)
Источник: [SEO-бот](SEO-бот). Два MCP-сервера для Yandex Wordstat.
- README — что такое MCP в одном абзаце, **зачем именно для SEO**.
- Инструкция подключения к Cursor/Claude Desktop (`mcp.json` сниппет).
- Скрин использования прямо в чате с ИИ — «как ассистент дёргает Wordstat».
- Объединить две вложенные папки (`yandex-wordstat-mcp/` и `mcp/`) — выбрать одну как основную, вторую либо удалить, либо положить как `legacy/`.

### A5 — wb-sales-commercial-analysis (реальные данные клиента)
Источник: [Задание](Задание). Анализ еженедельного отчёта Wildberries.
- **Обезличить данные**: проверить CSV на персональные данные / артикулы клиента, замаскировать если нужно.
- README — обозначить как «коммерческий кейс» (не учебный): какая задача стояла, какой ответ дали бизнесу.
- `WB_заключение_1страница.md` сделать главным артефактом, ссылка из README.
- Скрин ключевого графика/таблицы в `media/`.
- Это сильнее, чем `superstore-retail-analytics`, потому что данные реальные.

### A6 — superstore-retail-analytics (учебный, но визуально сильный)
Источник: [Бизнес_аналитика](Бизнес_аналитика).
- Превью-PNG дашборда и слайдов в `media/`, embed в README.
- Публикация `superstore-dashboard.html` через **GitHub Pages** — кнопка «Открыть демо».
- Отдельный `INSIGHTS.md` с тремя бизнес-выводами и цифрами.
- В README явно отметить «учебный датасет, демонстрация подхода» — честность дешевле обмана.

### A7 — team-ai-bot (Haystack + Pinecone)
Источник: [Уроки_VC/Диалоговый бот для команды](Уроки_VC/Диалоговый бот для команды).
- Dockerfile + `docker-compose.yml` с переменными из [.env.example](Уроки_VC/Диалоговый бот для команды/.env.example).
- Раздел «Деплой» — 1 команда запуска + чек-лист переменных Pinecone/OpenAI.
- Заменить блок «Что приложить к ДЗ» в README на «Демо-сценарий для оценщика/работодателя».
- Скриншоты диалога с ботом в `media/`.

### A8 — personal-rag-assistant (Haystack + Docling)
Источник: [Уроки_VC/Диалоговый бот - поиск_по_данным](Уроки_VC/Диалоговый бот - поиск_по_данным).
- Удалить `.venv` (Этап 1 — критично).
- Унифицировать точку входа: один из `bot.py`/`main.py`, второй удалить.
- Dockerfile + инструкция деплоя.
- Нейтральная бизнес-формулировка в README (без привязки к номеру урока платформы).

## Этап 2.5. Вторая волна флагманов (после первого пуша)

Делается отдельным заходом — не блокирует публикацию каркаса:
- **hotel-booking-tally-supabase** ([Итоговый проект_n8n](Итоговый проект_n8n)): свернуть 14 черновиков в `_docs-internal/`, чистый README, mermaid из `process-diagram.mermaid.md`, скрины executions.
- **barista-payroll-sheets** ([Скрипты для таблиц](Скрипты для таблиц)): скрины меню, ссылка на read-only Google Sheets.
- **audio-transcriber** ([Транскрибатор](Транскрибатор)): после очистки двойной venv — README с примером входа/выхода, демо-аудио и транскрипт.
- **fintech-ab-test-credit-offer** ([Fintech-ab-test-credit-offer](Fintech-ab-test-credit-offer)): чек-лист методологии (MDE, sample size, мощность), nbviewer.
- **ai-in-accounting-strategic-plan** ([ИИ в бухгалтерии](ИИ в бухгалтерии)): вложить `presentation.pdf` или ссылку на облако, превью обложки.

## Этап 3. Прочие проекты (минимальный косметический проход)

Для остальных ~15 подпроектов (в основном `02-automation` и `03-ai-products`):
- README из 4 блоков: что это / стек / запуск / статус (например, «учебный, ограниченная функциональность» или «коммерческий MVP»).
- Удалить `.env`, `.venv`, временные файлы, скриншоты-черновики.
- Если внутри направления несколько похожих ботов (`personal-rag-assistant`, `team-ai-bot`, `memory-bot`, `team-tg-bot-vc`) — в каждом README отметить уникальное отличие (в `03-ai-products/README.md` уже есть сводная таблица).

Для `99-archive/*` — README ровно из 3 строк: «учебные ноутбуки/скрипты, оставлены для истории».

## Этап 4. Корневой README (витрина)

Структура корневого `README.md`:
1. **Hero**: имя, позиционирование («аналитика данных · автоматизация процессов · ИИ-продукты · сайты · ИИ-консалтинг»), контакты ([t.me/kaluginvit](https://t.me/kaluginvit), email).
2. **Стек-бейджи**: Python, n8n, Apps Script, Next.js, TypeScript, Pinecone, Haystack, Supabase, Telegram Bot API, MCP, faster-whisper, Plotly, pandas.
3. **Карточки 5 направлений** — каждая ссылается на свою папку. Внутри карточки — буллет-список 1-3 флагманских кейсов с прямыми GitHub-ссылками вида `https://github.com/kaluginvit-svg/Portfolio/tree/main/02-automation/leadgen-n8n-system`.
4. **Featured-блок** наверху — отдельная плашка для кейса «Калькулятор выплат СВО» (web + бот) как самый продакшен-готовый кейс с реальным клиентом.
5. **Раздел «Архив» (учебные артефакты)** — свёрнутый `<details>` со ссылкой на `99-archive/`.
6. **Призыв к действию**: «обсудим задачу — Telegram/email».

## Этап 5. Опциональное переименование репозитория

Целевое имя репозитория на GitHub — **`Portfolio`** (`kaluginvit-svg/Portfolio`). Переименование на стороне GitHub не ломает историю; старые URL редиректятся. Остальные кандидаты (`kalugin-portfolio`, `it-portfolio`) — запасные.

## Этап 6. Пересборка архива (промоут достойных)

Из `99-archive/` поднимаются 7 проектов в основные направления — у каждого есть рабочий код или ценная документация:

**В `02-automation/`:**
- `mortgage-calculator/` — рабочий калькулятор ипотеки.
- `n8n-bpmn-notes/` — методические заметки по BPMN-моделированию в n8n.
- `github-actions-setup/` — шаблон CI с GitHub Actions.

**В `03-ai-products/`:**
- `mcp-lesson/` — урок-разбор MCP-протокола.
- `autonomous-agents/` — кейс автономных агентов.
- `pdf-checker/` — утилита проверки PDF через ИИ.

**В `04-web/`:**
- `postgres-work/` — учебный fullstack-кейс с PostgreSQL.

**Дедуп:**
- `99-archive/autonomous-agents-local/` — удаляется как дубликат `autonomous-agents/`.
- `99-archive/go-server-mini/` — вливается внутрь `99-archive/ai-coding-lessons/` как Go-аналог Python-сервера (демонстрация языкового паритета).

**Обновления README:**
- README у 7 поднятых проектов: проблема / решение / стек / демо; для `ci-cd-fastapi-deploy` (если он попадает в эту волну отдельно) — акцент на CI/CD.
- Категорийные README `02-automation/`, `03-ai-products/`, `04-web/` — добавить промоутнутые проекты в таблицы.
- Корневой `README.md` — добавить промоутнутые проекты в таблицы флагманов где уместно.
- `99-archive/README.md` — обновить список (минус 7 промоутнутых, минус 1 dedup, минус 1 merge).

## Этап 7. Чистка архива до 15 проектов

После промоута Этапа 6 в `99-archive/` остаётся 30 папок. Сжимаем до 15 «keep» с потенциалом доводки до самостоятельных проектов. Остальные 15 — учебные обрывки и дубли — удаляются из репо (локально остаются у пользователя).

### 15 «keep» — оставить в архиве

Категория «полузавершённые продукты»:
1. `mini-booking-system/` — Python + PostgreSQL-driver + Tkinter-GUI: каркас «БД + UI».
2. `password-generator/` — CLI + GUI, Fernet, хэш мастер-пароля; рабочая утилита.
3. `mcp-practice/` (`coin_flip_api/`) — Flask + Docker Compose + UI; самодостаточный мини-сервис.
4. `docker-vps-project/` — TG-бот + Docker Hub + Logtail; пример деплоя.
5. `rag-lessons/` — полный пример RAG: Pinecone + LangChain + TG-бот.
6. `ux-reviewer-agent/` — каркас FastAPI + Vite/React + Docker UX-агента.
7. `desktop-reminder/` — Tkinter + SQLite + win10toast + готовый `.exe`; завершённая Windows-утилита.
8. `recurring-payments-reminder/` — рабочий aiogram-бот напоминаний о платежах.
9. `api-lessons/` — Flask + Leaflet с UI и шаблонами; завершённый мини-сервис «карта + API».

Категория «методические артефакты с ценным кодом»:

10. `prompting-case/` — сравнение промптов GPT-4o с готовыми артефактами `.md/.json`.
11. `memory-lessons/` — три варианта памяти TG-ботов (`short`, `long`, `hybrid`).
12. `expert-project/` — Flask: URL → цепочка промптов → готовый пост.
13. `ai-bot-lessons/` — крупный TG-бот: Sora-видео, память, прайсинг.
14. `ai-automation-lessons/` — конвейер «транскрипт → ИИ → PDF-отчёт».
15. `ai-coding-lessons/` (+ влитая `go-server-mini/`) — демонстрация Python/Go API-паритета.

### 15 «remove» — удалить из репо (локально остаются)

`api-testing-bot/`, `auto-deploy-lesson/`, `autonomous-agents-local/` (если ещё не удалена в Этапе 6), `db-lessons/`, `docker-lessons/`, `langchain-lesson-1/`, `langchain-lesson-2/`, `llm-lessons/`, `local-ai-agent/`, `loki-grafana-stack/`, `python-modules-lessons/`, `python-oop-practice/`, `recipe-search-bot/`, `sql-lessons/`, `sqlite-lesson/`.

### Механика удаления (выбор пользователя — `soft_no_local_delete`)

```bash
# 1. Удалить из индекса и рабочего дерева репо
git rm -rf 99-archive/api-testing-bot \
          99-archive/auto-deploy-lesson \
          99-archive/autonomous-agents-local \
          99-archive/db-lessons \
          99-archive/docker-lessons \
          99-archive/langchain-lesson-1 \
          99-archive/langchain-lesson-2 \
          99-archive/llm-lessons \
          99-archive/local-ai-agent \
          99-archive/loki-grafana-stack \
          99-archive/python-modules-lessons \
          99-archive/python-oop-practice \
          99-archive/recipe-search-bot \
          99-archive/sql-lessons \
          99-archive/sqlite-lesson

# 2. Локально вернуть копии из последнего коммита (где они ещё есть) во временную папку вне репо,
#    чтобы не потерять (опционально, по желанию пользователя). Альтернативно — git checkout HEAD~1 -- ...
#    Простейший вариант: пользователь делает резервную копию папки 99-archive до коммита.

# 3. Дописать в .gitignore (чтобы пути не вернулись в индекс случайно)
99-archive/api-testing-bot/
99-archive/auto-deploy-lesson/
99-archive/autonomous-agents-local/
99-archive/db-lessons/
99-archive/docker-lessons/
99-archive/langchain-lesson-1/
99-archive/langchain-lesson-2/
99-archive/llm-lessons/
99-archive/local-ai-agent/
99-archive/loki-grafana-stack/
99-archive/python-modules-lessons/
99-archive/python-oop-practice/
99-archive/recipe-search-bot/
99-archive/sql-lessons/
99-archive/sqlite-lesson/

# 4. Один коммит и обычный push
git add -A
git commit -m "chore(archive): prune to 15 portfolio-worthy projects"
git push origin main
```

**Важно про режим `soft_no_local_delete`:**
- `git rm -rf` удаляет файлы и из индекса, и **из рабочего дерева**. Чтобы локально оставить копии, надо сделать резервную копию папки до коммита (например, `xcopy 99-archive _backup-archive\ /E /I`) или использовать `git rm -r --cached <path>` (тогда файлы остаются в рабочем дереве, но `.gitignore` обязателен, иначе они вернутся при следующем `git add`).
- **Рекомендованная команда** для требования «локально оставить» — это именно `git rm -r --cached <path>` + добавление пути в `.gitignore` тем же коммитом. Но Git не удаляет файлы из дерева, и они остаются у пользователя.

```bash
# Альтернатива, точно сохраняющая локальные копии:
git rm -r --cached 99-archive/api-testing-bot 99-archive/auto-deploy-lesson ... # все 15 путей
# + .gitignore добавление + commit + push
```

В реализации Этапа 7 будет использован именно вариант `git rm -r --cached` — он соответствует выбранному режиму без рисков для локальных файлов.

### Обновление `99-archive/README.md`

Краткая фраза в духе «Здесь оставлены 15 проектов с потенциалом довести до самостоятельных утилит/кейсов: 9 полузавершённых продуктов и 6 методических артефактов с рабочим кодом. Учебные обрывки и дубли удалены из репо (локально доступны автору)». Плюс таблица «оставленные 15» с одной строкой описания каждого.

## Что я НЕ делаю в рамках одного прохода (честно)

- Не «переписываю с нуля» каждый из 30+ подпроектов. Это работа на десятки часов и должна идти отдельным заходом. Здесь — каркас + 8 флагманов первой волны; 5 флагманов второй волны идут после первого пуша.
- Не записываю видео-демо (положу плейсхолдеры).
- Не публикую `presentation.pdf` для `ai-in-accounting-…`, если файла нет на диске — дам инструкцию, где разместить.
- Не деплою сайт на Vercel/хостинг — дам готовую инструкцию, нажмёте сами.
- Не настраиваю CI/CD (GitHub Actions) — это отдельная задача после публикации.

## Открытые вопросы (не блокирующие — решим по ходу)

- Какие 2-3 строчки положить в Hero корневого README (роль / для кого / что предлагаете)? Сейчас положу плейсхолдер, вы отредактируете.
- Имя репозитория на GitHub: целевое **`Portfolio`** (`kaluginvit-svg/Portfolio`); при необходимости старые URL редиректят после переименования.
- Нужно ли держать локальный `.venv` для `personal-rag-assistant` после удаления из git (через `.gitignore`) — или вы пересоздадите его сами?
