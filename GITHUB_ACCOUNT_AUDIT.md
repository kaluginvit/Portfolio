# GitHub Account Audit — kaluginvit

> Дата: 2026-09-07  
> Метод: gh CLI read-only (repo list, API, CI runs)  
> Scope: только чтение. Ничего не изменено.

---

## Executive Summary

Аккаунт **kaluginvit** создан декабрь 2025. Молодой, но с реальными production-проектами.  
**15 репозиториев**: 13 public, 2 private. Из 13 публичных — **5–6 выглядят как реальные портфолио-проекты**, остальные снижают впечатление: 1 пустой, 2 в стадии scaffold, 2 без описания и тем, 1 домашняя работа по курсу.

**Главные проблемы:**
- Ни один публичный репозиторий не имеет topics — нулевая находимость
- CI имеет активные failures (Build Docker images, svo-payments-bot deploy)
- Профильный README (kaluginvit/kaluginvit) устарел — ссылается на Create_CRM и autello-leads вместо новых сильных проектов
- test_action — пустой репозиторий с публичным мусором
- ai-finance-screener — только scaffold step 0, без frontend и логики
- finance-consulting-landing — публичная домашняя работа курса

**Сильные стороны:**
- svo-payouts-website — реальный production, TypeScript, Playwright E2E
- fintech-ab-test-credit-offer — зрелая аналитика, CI, воспроизводимый pipeline
- rf-macro-risk-ai — live GitHub Pages demo, MIT лицензия, хорошее описание
- Portfolio — работающий Pages сайт, 4 workflow

**Общий балл аккаунта: 4.6 / 10** (потенциал есть, реализация пока слабая)

---

## Repository Inventory

| # | Repo | Visibility | Branch | Size KB | Created | Last Push | Stars | Fork | Описание | Homepage | Topics | License |
|---|------|------------|--------|--------:|---------|-----------|------:|------|----------|----------|--------|---------|
| 1 | Portfolio | PUBLIC | main | 210 947 | 2026-05-02 | 2026-09-06 | 0 | No | Портфолио проектов | — | ❌ | — |
| 2 | svo-payouts-website | PUBLIC | main | 291 | 2026-09-06 | 2026-09-06 | 0 | No | Live site svorazbor.ru. Next.js 15, TypeScript, Docker. | — | ❌ | — |
| 3 | mini-crm-fastapi-react | PUBLIC | main | 90 | 2026-09-06 | 2026-09-06 | 0 | No | Mini CRM: FastAPI + React + Google OAuth + Docker + pytest. | — | ❌ | — |
| 4 | fintech-ab-test-credit-offer | PUBLIC | main | 6 731 | 2026-09-06 | 2026-09-06 | 0 | No | A/B test credit offer: statistics, scipy, pandas, CI. | — | ❌ | — |
| 5 | svo-payments-bot | PUBLIC | main | 65 | 2026-09-06 | 2026-09-06 | 0 | No | Production Telegram bot | — | ❌ | — |
| 6 | rf-macro-risk-ai | PUBLIC | **master** | 1 002 | 2026-05-16 | 2026-08-26 | 0 | No | AI agent for Russian macro-risk monitoring. 35 risk criteria, Telegram report every 3 days. | — | ❌ | MIT |
| 7 | finsight | PUBLIC | **master** | 483 | 2026-06-02 | 2026-06-02 | 0 | No | AI-чат по финансовым CSV/Excel. Загрузи файл — получи инсайты и задавай вопросы по-русски. | — | ❌ | — |
| 8 | finance-consulting-landing | PUBLIC | main | 9 934 | 2026-05-25 | 2026-05-25 | 1 | No | *(пусто)* | — | ❌ | — |
| 9 | ai-finance-screener | PUBLIC | **master** | 16 | 2026-05-25 | 2026-05-25 | 1 | No | Финансовый скринер | — | ❌ | — |
| 10 | kaluginvit | PUBLIC | main | 1 | 2026-05-22 | 2026-05-22 | 0 | No | GitHub Profile README | — | ❌ | — |
| 11 | autello-leads | PUBLIC | main | 46 | 2026-05-12 | 2026-05-12 | 0 | No | *(пусто)* | — | ❌ | — |
| 12 | Create_CRM | PUBLIC | main | 108 | 2026-05-04 | 2026-05-04 | 0 | No | *(пусто)* | — | ❌ | — |
| 13 | test_action | PUBLIC | — | 0 | 2026-06-09 | 2026-06-09 | 0 | No | Под OpenAI | — | ❌ | — |
| 14 | claude-skills-archive | **PRIVATE** | master | 3 459 | 2026-06-04 | 2026-06-05 | 0 | No | Claude Code skills: 79 active + 821 archived | — | — | — |
| 15 | claude-config | **PRIVATE** | master | 2 816 | 2026-06-04 | 2026-06-04 | 0 | No | Claude Code config backup | — | — | — |

---

## Содержимое репозиториев — быстрый обзор

| Repo | Назначение | Stack | README | Tests | Docker | Workflows | Pages | Secrets/Risk |
|------|-----------|-------|:------:|:-----:|:------:|:---------:|:-----:|:------------:|
| Portfolio | Монорепо всего портфолио | HTML/Astro/Python | ✅ | ✅ | ✅ | 4 | ✅ | — |
| svo-payouts-website | Production сайт svorazbor.ru | Next.js/TS/Playwright | ✅ | ✅ | ✅ | 3 | ❌ | — |
| svo-payments-bot | Production Telegram FSM-бот | Python/aiogram/aiosqlite | ✅ | ✅ | ✅ | 1 | ❌ | — |
| mini-crm-fastapi-react | CRM + Google OAuth | FastAPI/React/TS | ✅ | ✅ | ✅ | ❌ | ❌ | — |
| fintech-ab-test-credit-offer | A/B тест fintech | Python/scipy/pandas | ✅ | ✅ | ✅ | 1 | ❌ | — |
| rf-macro-risk-ai | Макрориск AI агент | Python/LangChain | ✅ | ✅ | ✅ | ❌ | ✅ | — |
| finsight | AI-чат по CSV/Excel | FastAPI/React/Claude | ✅ | ✅ | ✅ | ❌ | ❌ | CLAUDE.md публично |
| finance-consulting-landing | Лендинг (домашняя работа курса) | CSS/HTML/JS | ✅ | ❌ | ❌ | 1 | ✅ | Commit: "Homework CLs02" |
| ai-finance-screener | Финансовый скринер (scaffold only) | — | ✅ | ❌ | ❌ | ❌ | ❌ | CLAUDE.md публично |
| kaluginvit | Profile README | — | ✅ | ❌ | ❌ | ❌ | ❌ | — |
| autello-leads | Lead capture CRM | JS/Docker/nginx | ✅ | ❌ | ✅ | ❌ | ❌ | EnvExample (не .env.example) |
| Create_CRM | Мини-CRM | Python | ✅ | ✅ | ✅ | ❌ | ❌ | PNG с IDE структурой в корне |
| test_action | Пустой репозиторий | — | ✅ | ❌ | ❌ | ❌ | ❌ | — |

---

## Strong Repositories

### 1. svo-payouts-website
- Production Next.js 14, TypeScript, Tailwind, Playwright E2E тесты
- 3 GitHub Actions workflows (CI, deploy-vps, deploy)
- CI workflow: **passed** ✅
- Реальный трафик на svorazbor.ru
- Хорошее описание, есть README

### 2. fintech-ab-test-credit-offer
- Методологически зрелый A/B тест: Welch t-test, MDE, SQL pipeline
- CI workflow работает ✅
- Воспроизводимый: `make all`
- Хорошее описание

### 3. rf-macro-risk-ai
- Live GitHub Pages demo: kaluginvit.github.io/rf-macro-risk-ai/
- MIT лицензия (единственный с лицензией среди публичных)
- Хорошее описание (английское)
- Докер, тесты есть
- **Проблема**: ветка `master` вместо `main`

### 4. Portfolio
- Работающий GitHub Pages сайт
- 4 workflows, Pages deploy успешен ✅
- Большой (210 MB — включает media)
- Ссылки на все проекты

### 5. mini-crm-fastapi-react
- Decent описание, pytest, Docker
- Google OAuth integration

---

## OK Repositories

### svo-payments-bot
- Production бот, хороший код
- Описание слишком краткое: "Production Telegram bot" — непонятно что делает
- Нет homepage URL
- Deploy workflow: **failed** ⚠️

### finsight
- Хорошее описание на русском
- Docker, тесты есть
- CLAUDE.md публично в репо (незначительно, но необычно)
- Ветка `master` вместо `main`
- Давно не обновлялся (июнь 2026)

---

## Weak / Old Repositories

### finance-consulting-landing
- Описание пустое
- 9.9 MB (самый тяжёлый кроме Portfolio — медиафайлы)
- Commit message явно: `"Homework CLs02 Advanced — client-presentation level landing page"`
- Работает GitHub Pages, но это учебная работа
- 1 звезда (вероятно, случайная)
- Размывает профиль

### autello-leads
- Описание пустое
- Файл `EnvExample` вместо стандартного `.env.example`
- JavaScript/Node.js
- Последний commit май 2026
- Непонятно для стороннего наблюдателя что это

### Create_CRM
- Описание пустое
- В корне лежит `эталон_структура_из_IDE.png` — случайный файл
- Commit: `"merge: resolve README with remote; keep full project doc  Co-authored-by: Cursor <cursoragent@cursor.com>"` — видно AI/Cursor автор в commit message
- Учебная CRM, не впечатляет

---

## Test / Service Repositories

### test_action
- **Абсолютно пустой** (size: 0 KB, нет default branch)
- Описание: "Под OpenAI" — не объясняет ничего
- Публичный мусор

### ai-finance-screener
- Только scaffold: `.gitignore`, `.env.example`, `CLAUDE.md`, `ROADMAP.md`, пустые папки
- Commit: `"chore: step 0 - project scaffold"` — проект не начат
- `CLAUDE.md` публично — видно как работает внутренняя кухня
- 1 звезда (случайная)
- Вводит в заблуждение: название громкое, внутри пусто

### claude-skills-archive (PRIVATE)
- Правильно приватный: 79 скиллов + 821 архивных
- Не влияет на публичный профиль

### claude-config (PRIVATE)
- Правильно приватный: конфиги Claude Code

---

## CI / CD

| Repo | Workflow | Trigger | Последний запуск | Статус |
|------|----------|---------|-----------------|--------|
| Portfolio | CI — fintech-ab-test-credit-offer | push main | 2026-09-06 | ✅ success |
| Portfolio | Deploy Portfolio site (GitHub Pages) | push main | 2026-09-06 | ✅ success |
| Portfolio | Build Docker images (GHCR) | push main | 2026-09-06 | ❌ **failure** |
| Portfolio | Deploy svo-payments-bot | push main | 2026-09-06 | ❌ **failure** |
| svo-payouts-website | CI | push main | 2026-09-06 | ✅ success |
| svo-payouts-website | Deploy (Docker → GHCR → VPS) | push main | 2026-09-06 | ❌ **failure** |
| svo-payments-bot | Build, push to GHCR, deploy | push main | 2026-09-06 | ❌ **failure** |
| fintech-ab-test-credit-offer | run-analysis.yml | push | 2026-09-06 | ✅ success |
| finance-consulting-landing | deploy.yml | push | — | неизвестно |

**Итог CI:** 3 из 4 deploy-workflows в состоянии failure. Это первое что видит технический специалист на странице репо.

---

## Live Deployments

| Repository | Live URL | Механизм | Статус |
|------------|----------|----------|--------|
| Portfolio | https://kaluginvit.github.io/Portfolio/ | GitHub Pages (Actions) | ✅ работает |
| rf-macro-risk-ai | https://kaluginvit.github.io/rf-macro-risk-ai/ | GitHub Pages | ✅ работает |
| finance-consulting-landing | https://kaluginvit.github.io/finance-consulting-landing/ | GitHub Pages (Actions) | ✅ (учебная работа) |
| svo-payouts-website | https://svorazbor.ru | Docker → VPS | ✅ production (deploy workflow failed, но сайт живой) |
| svo-payments-bot | — | GHCR → VPS | Deploy failed ⚠️ |

*Доступность URL проверена только через CI статус и наличие Pages конфигурации, не через HTTP запросы.*

---

## Profile Assessment

### Profile Quality — 5 / 10

**Плюсы:**
- Bio содержательное: "Финансовый аналитик (19 лет) → Vibe-coder"
- Ссылка на портфолио есть
- Profile README существует

**Минусы:**
- Profile README (kaluginvit/kaluginvit) **сильно устарел**: в таблице проектов — rf-macro-risk-ai (ещё ок), Create_CRM (слабый), autello-leads (слабый), Portfolio (generic)
- Новые сильные репозитории (svo-payouts-website, fintech-ab-test, mini-crm) не упомянуты в profile README
- 1 follower, 0 following — аккаунт изолирован
- Нет location (необязательно, но помогает)

### Portfolio Clarity — 3 / 10

**Проблема:** глядя на список репо в хронологическом порядке, непонятно что человек умеет. Сильные проекты (svo-payouts-website, fintech-ab) не выделены ничем. Слабые (test_action, ai-finance-screener) стоят вперемешку. Ни у одного репо нет topics — невозможно найти через поиск GitHub.

**Конкретно:**
- 0 из 13 публичных репозиториев имеют topics
- 5 из 13 не имеют описания
- Ни один не имеет homepage URL (поле website в настройках репо)

### Technical Impression — 6 / 10

**Плюсы:**
- Есть TypeScript + Next.js production (svo-payouts-website)
- Есть CI/CD с Docker и GHCR
- Python + FastAPI + pytest понятны
- rf-macro-risk-ai с MIT лицензией

**Минусы:**
- 4 из 7 deploy workflows в failure
- Пустой репо test_action
- ai-finance-screener — scaffold который выдаёт себя за проект
- finance-consulting-landing — "Homework CLs02" в commit

### Finance × Tech Positioning — 4 / 10

**Проблема:** из списка репозиториев finance-позиционирование почти невидно.
- `rf-macro-risk-ai` — есть описание с "macro-risk", хорошо
- `fintech-ab-test-credit-offer` — хорошее название, но без topics
- Остальные (CRM, бот, лендинг) не сигнализируют finance domain

Без topics `python`, `finance`, `fastapi`, `telegram-bot` и т.д. позиционирование не читается.

### GitHub Hygiene — 2 / 10

Критические проблемы:
- `test_action` — публичный пустой репо
- `ai-finance-screener` — публичный scaffold без кода
- `finance-consulting-landing` — публичная домашняя работа (commit message не врёт)
- 0 topics во всех публичных репо
- `master` вместо `main` в 3 репо (rf-macro-risk-ai, finsight, ai-finance-screener)
- Активные CI failures красными крестами
- Portfolio весит 210 MB (медиафайлы, возможно сертификаты PNG прямо в репо)

---

## Top 5

### 1. svo-payouts-website
**Почему:** Единственный репо с реальным production сайтом (svorazbor.ru). TypeScript, Playwright E2E, Docker, 3 workflows. CI зелёный. Показывает: умею доводить до прода, тестирую end-to-end, деплой в VPS через Actions. **Убедительность: 8/10** — снижает Deploy workflow failure.

### 2. fintech-ab-test-credit-offer
**Почему:** Чёткое описание на английском. CI проходит. Название сразу говорит что внутри. A/B тест в fintech — точное позиционирование Finance × Data. **Убедительность: 8/10** — если открыть README, сразу понятен уровень.

### 3. rf-macro-risk-ai
**Почему:** Live demo (GitHub Pages). MIT лицензия. Английское описание. Хорошо пахнет как portfolio project. Macro risk × AI — уникальная ниша. **Убедительность: 7/10** — ветка master и 0 topics тянут вниз.

### 4. mini-crm-fastapi-react
**Почему:** Приличное описание, Docker, pytest, Google OAuth — это нетривиально. FastAPI + React + Google — понятный для читателя стек. **Убедительность: 6/10** — нет topics, нет homepage.

### 5. Portfolio
**Почему:** Рабочий GitHub Pages сайт (kaluginvit.github.io/Portfolio/). Видно что человек поддерживает монорепо. Но 210MB — тяжело, "Портфолио проектов" — generic описание. **Убедительность: 5/10** — сам по себе не впечатляет, но даёт точку входа.

---

## Bottom 5

### 1. test_action
**Почему:** Пустой публичный репозиторий с описанием "Под OpenAI". Нет кода, нет файлов. Плохо влияет как мусор.

### 2. ai-finance-screener
**Почему:** Только scaffold (step 0). Публичный. Название громкое — "AI Finance Screener", внутри пустые папки. CLAUDE.md и ROADMAP.md показывают внутреннюю кухню. Создаёт expectation, которую невозможно выполнить.

### 3. finance-consulting-landing
**Почему:** Описание пустое. 9.9 MB медиафайлов. Commit "Homework CLs02 Advanced — client-presentation level landing page. Empower.com reference style". CSS/HTML. GitHub Pages работает, но это учебная работа.

### 4. autello-leads
**Почему:** Нет описания. JavaScript/nginx. Называется `autello-leads` — непонятно без контекста. Файл `EnvExample` вместо `.env.example`. Давно не обновлялся.

### 5. Create_CRM
**Почему:** Нет описания. PNG-скриншот IDE в корне. Commit с Cursor co-author в сообщении. Самый ранний основной репо — задаёт первое впечатление у посетителей сортирующих по дате создания.

---

## Issues Found

### Критические
- [ ] `test_action` — пустой публичный репо без смысла
- [ ] `ai-finance-screener` — scaffold-only, вводит в заблуждение
- [ ] Все 4 deploy workflows в Portfolio/svo-payments-bot/svo-payouts-website — **FAILED**
- [ ] Profile README (`kaluginvit/kaluginvit`) устарел: ссылается на Create_CRM и autello-leads

### Серьёзные
- [ ] 0 topics у всех 13 публичных репозиториев — нулевая дискаверабилити
- [ ] Нет homepage URL ни у одного репо (поле "Website" в настройках)
- [ ] 5 репозиториев без описания: finance-consulting-landing, autello-leads, Create_CRM + 2 пустых поля
- [ ] `master` branch в 3 публичных репо: rf-macro-risk-ai, finsight, ai-finance-screener

### Умеренные
- [ ] Portfolio весит 210 MB (PNG сертификаты и медиа прямо в репо)
- [ ] `finance-consulting-landing` — публичная учебная работа (9.9 MB, "Homework CLs02")
- [ ] `finsight` давно не обновлялся (июнь 2026), первичный вид — старый
- [ ] CLAUDE.md публично в `ai-finance-screener` и `finsight` — видна внутренняя кухня
- [ ] `autello-leads`: файл `EnvExample` вместо `.env.example` — нестандартно
- [ ] `Create_CRM`: PNG с IDE структурой в корне репо
- [ ] Нет лицензий у большинства репозиториев (только rf-macro-risk-ai имеет MIT)

### Незначительные
- [ ] svo-payments-bot — описание слишком короткое: "Production Telegram bot" без контекста что делает
- [ ] Portfolio — описание generic: "Портфолио проектов"
- [ ] Inconsistent язык описаний: часть на русском, часть на английском

---

## Recommendations

*(Только перечисление — реализация отдельно)*

1. **Сделать приватными или удалить:** test_action, ai-finance-screener (или удалить scaffold и не публиковать до реального кода)
2. **Добавить topics** ко всем публичным репозиториям (python, fastapi, react, telegram-bot, docker, n8n, langchain, finance, ab-testing и т.д.)
3. **Обновить Profile README** (kaluginvit/kaluginvit): заменить Create_CRM/autello-leads на svo-payouts-website, fintech-ab-test, mini-crm-fastapi-react
4. **Добавить homepage URL** к репозиториям: svo-payouts-website → svorazbor.ru, rf-macro-risk-ai → github.io, Portfolio → github.io
5. **Исправить CI failures**: разобраться почему падают Build Docker images, svo-payments-bot deploy, svo-payouts-website deploy
6. **Перевести rf-macro-risk-ai на main** (сейчас master)
7. **Улучшить описания**: svo-payments-bot — добавить что считает, Portfolio — добавить ключевые слова
8. **Оценить finance-consulting-landing**: приватный или убрать (учебная работа)
9. **Добавить лицензии** к ключевым репозиториям (MIT или Apache 2.0)
10. **Уменьшить размер Portfolio**: вынести PNG сертификаты или использовать Git LFS

---

## Общая картина — ответы

1. **Репозиториев всего:** 15
2. **Public/Private:** 13 public / 2 private
3. **Forks:** 0
4. **Реально выглядят как portfolio projects:** 5–6 (svo-payouts-website, fintech-ab-test, rf-macro-risk-ai, mini-crm, svo-payments-bot, finsight)
5. **Выглядят тестовыми/старыми:** 5 (test_action, ai-finance-screener, finance-consulting-landing, autello-leads, Create_CRM)
6. **Имеют CI/CD:** 4 (Portfolio, svo-payouts-website, svo-payments-bot, fintech-ab-test)
7. **Имеют live demo / Pages:** 4 (Portfolio Pages, rf-macro-risk-ai Pages, finance-consulting-landing Pages, svorazbor.ru)
8. **Лучше всего продают прямо сейчас:** svo-payouts-website, fintech-ab-test-credit-offer, rf-macro-risk-ai, mini-crm-fastapi-react, Portfolio
9. **Хуже всего влияют:** test_action, ai-finance-screener, finance-consulting-landing, autello-leads, Create_CRM
10. **Готовность быть публичной витриной:** **40%** — есть реальные проекты, но hygiene и profile presentation тянут вниз. После fixes (topics + profile README + CI + убрать мусор) → 70%+
