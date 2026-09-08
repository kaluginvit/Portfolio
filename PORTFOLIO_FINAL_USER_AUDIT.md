# Portfolio Final User Audit

**Дата:** 2026-09-08  
**Аудитор:** Claude Sonnet 4.6  
**Объект:** github.com/kaluginvit + kaluginvit.github.io/Portfolio/

---

## Executive Summary

Портфолио технически завершено и представлено профессионально. 7 Tier A систем охватывают заявленное позиционирование (Finance × Software × AI × Automation). Большинство README — чёткие, с живыми demo-ссылками. Production SVO кейс с реальным трафиком — сильный якорь. Два точечных гигиенических вопроса снижают первое впечатление, оба некритичны.

**Итоговые оценки:**
- Работодатель: **7.5/10**
- Клиент: **8.5/10**
- Технический интервьюер: **7/10**

---

## 1. Первые 15 секунд

### GitHub Profile

При открытии профиля видно:
- 6 pinned repos с понятными описаниями
- Языки: Python (×4), TypeScript (×2) — читается как backend + frontend разработчик
- Одна живая ссылка сразу: `svorazbor.ru` на svo-payouts-website
- Описания компактные и конкретные: "192 tests, 8-level filter", "64 business logic tests, 4 price scenarios", "11 n8n workflows"

**Что видно за 15 секунд:** разработчик, который строит рабочие продукты, тестирует их, деплоит. Finance-уклон читается из названий (finance-mcp-server, finance-data-screener, fedresurs).

**Слабое место:** первый pinned repo — `finance-mcp-server` — ведёт на саму себя (homepage = github.com/kaluginvit/finance-mcp-server). Нет ни live demo, ни страницы продукта. Второй pinned (`svo-payouts-website`) — с живым сайтом. Логичнее было бы поменять их местами.

### Portfolio Site

`kaluginvit.github.io/Portfolio/` — Astro-сайт с сервисным позиционированием (не резюме, а страница исполнителя). Структура: hero → услуги → кейсы → процесс. Понятно, что это не джуниор-портфолио, а страница практикующего специалиста.

**Что понятно сразу:** Финансы + автоматизация + ИИ. Кнопка «Каталог кейсов» ведёт на раздельный Core Showcase / More Projects.

**Оценка первых 15 секунд: 7/10** — информативно, но первый pinned без live demo создаёт лёгкую заминку.

---

## 2. Позиционирование

### Читаемость

Формула `Corporate Finance × Software Development × AI × Automation` присутствует:
- В description репозитория Portfolio
- В заголовке portfolio site
- В README (badges и stack)
- Подтверждается проектами (Finance MCP, Fedresurs, A/B-тест → финансы; SVO, mini-CRM → software; HR-Breaker, RF Macro, leadgen → AI/Automation)

### Конфликт ролей?

На поверхности — три роли одновременно (финансист + разработчик + AI-специалист). В реальности конфликта нет, потому что:
- Финансы — это **domain expertise**, не конкурирующая профессия
- AI/Automation — это **инструментарий**, а не отдельная специализация
- Все три оси сходятся в одном типе задач: построить рабочий инструмент для финансовых/бизнес-процессов

Риск: нестандартное позиционирование может вызвать у традиционного HR вопрос «а кто это вообще?». Для технического нанимателя или заказчика — наоборот, сильная дифференциация.

**Ясность позиционирования: 8/10**

---

## 3. Core Showcase

### Структура: 7 систем ✓

| # | Система | Бизнес-задача | Архитектура | Инженерный уровень | Demo | Тесты | Дублирование |
|---|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | SVO System | ✅ Ясна | ✅ Описана | ✅ Production, CI/CD, VPS | ✅ Live svorazbor.ru | ✅ Playwright + Vitest | — |
| 2 | Finance MCP Server | ✅ Ясна | ✅ ASCII-диаграмма | ✅ Registry pattern, 19 tools | ⚠️ Нет live UI | ✅ pytest | — |
| 3 | HR-Breaker | ✅ Ясна | ✅ How It Works flow | ✅ Multi-filter, anti-hallucination | ✅ Pages demo | ✅ 192 теста | — |
| 4 | Leadgen n8n | ✅ Ясна | ✅ Workflow Map | ⚠️ JSON-конфиги, не традиционный код | ✅ Pages demo | ⚠️ Shadow validation (не юнит-тесты) | — |
| 5 | Finance Data Screener | ✅ Ясна | ✅ ASCII + стек-таблица | ✅ FastAPI + PG + React + LLM | ✅ Pages demo | ✅ 18 тестов | — |
| 6 | Fedresurs MVP | ✅ Очень конкретна | ✅ ASCII | ✅ Два движка, agentic loop | ✅ Pages demo | ✅ 47/64 тестов | — |
| 7 | A/B-тест в финтех | ✅ Ясна | ✅ Makefile pipeline + SQL | ✅ Методологически строго | ✅ Pages demo | ✅ reproducible | — |

**Дублирования нет.** Каждая система закрывает своё пространство: production web, MCP/AI-слой, документообработка, B2B automation, финансовый data-scraping, оценка активов, продуктовая аналитика.

**Слабые места:**
- Finance MCP Server: нет web-демо, потому что это CLI-tool. Это честно, но при беглом просмотре смотрится слабее соседей. Описание достаточно компенсирует.
- Leadgen n8n: JSON-воркфлоу — менее осязаемый артефакт, чем Python-код. Pages demo (architecture walkthrough) помогает, но не может показать работающую систему.
- Два аналитических кейса подряд (Fedresurs + A/B-тест) создают небольшой дисбаланс в конце списка.

---

## 4. Pinned Repos

### Текущий состав

| Позиция | Repo | Язык | Live | Сила |
|---------|------|------|------|------|
| 1 | finance-mcp-server | Python | Нет (self-link) | ★★★★ |
| 2 | svo-payouts-website | TypeScript | ✅ svorazbor.ru | ★★★★★ |
| 3 | hr-breaker | Python | ✅ Pages demo | ★★★★ |
| 4 | leadgen-n8n-system | Python | ✅ Pages demo | ★★★★ |
| 5 | finance-data-screener | TypeScript | ✅ Pages demo | ★★★★ |
| 6 | fedresurs-mvp | **HTML** | ✅ Pages demo | ★★★★ |

**Diversity оценка:**
- Finance × AI: ✅ (finance-mcp-server, finance-data-screener, fedresurs-mvp)
- Production Web: ✅ (svo-payouts-website)
- AI/ML: ✅ (hr-breaker)
- Automation: ✅ (leadgen-n8n-system)
- Backend depth: ✅ (все 4 Python-репо)
- Frontend depth: ✅ (2× TypeScript)

**Проблемы:**
1. `finance-mcp-server` стоит **первым** но ведёт на собственный репо вместо live demo — первое впечатление от кнопки "Website" разочаровывает
2. `fedresurs-mvp` показывает язык **HTML** — смотрится как "статичная страница", а не Python-инструмент

**Возможная замена (max 1):**
- Поменять первый и второй местами: `svo-payouts-website` на позицию 1 (реальный трафик, живой сайт), `finance-mcp-server` на позицию 2. Порядок 1-7 всё равно сильный — это лишь small UX fix.

---

## 5. Portfolio Site

| Критерий | Статус |
|----------|--------|
| Core Showcase = 7 карточек | ✅ |
| More Projects = 5 карточек | ✅ |
| Tier C не показывается | ✅ |
| SVO = одна карточка | ✅ |
| Live Demo кнопки (btn-primary) | ✅ |
| GitHub кнопки (btn-ghost) | ✅ |
| Finance MCP Server — GitHub кнопка (нет demo) | ✅ Честно |
| Порядок карточек | ✅ Логичен |
| Перегруза нет | ✅ |

**Нет нареканий.** Разделение Core / More Projects читается. Кнопки различаются визуально. Карточки не перегружены. Finance MCP без live-кнопки — правильное решение.

---

## 6. README Consistency

| README | Problem | Solution | Architecture | Demo | Tests | Итог |
|--------|:-------:|:--------:|:------------:|:----:|:-----:|------|
| SVO Website | ✅ | ✅ | ✅ ASCII + flow | ✅ svorazbor.ru | ✅ Playwright | **ОТЛИЧНО** |
| Finance MCP Server | ✅ | ✅ | ✅ Диаграмма + tools table | ✅ Claude Desktop | ✅ pytest | **ОТЛИЧНО** |
| HR-Breaker | ✅ | ✅ | ✅ How It Works | ✅ Pages link | ✅ упоминание | **ХОРОШО** |
| Leadgen n8n | ✅ | ✅ | ✅ Workflow Map | ✅ Pages link | ⚠️ Shadow validation | **ХОРОШО** |
| Finance Data Screener | ✅ | ✅ | ✅ ASCII + стек | ✅ Pages link | ✅ 18 тестов | **ХОРОШО** |
| Fedresurs MVP | ✅ Очень конкретно | ✅ | ✅ ASCII | ✅ Pages link | ✅ 47 тестов | **ОТЛИЧНО** |
| A/B-тест финтех | ✅ | ✅ | ✅ Pipeline + SQL | ✅ Pages link | ✅ reproducible | **ОТЛИЧНО** |

Все README читаются по нужной структуре. Реальных несоответствий нет.

---

## 7. Live Demos

| Demo | URL | HTTP | Тип | Ценность |
|------|-----|------|-----|----------|
| SVO | svorazbor.ru | 200 | Production | ★★★★★ Реальные пользователи |
| Finance Data Screener | .../finance-data-screener/ | 200 | React SPA (demo mode) | ★★★★ Интерактивный |
| Superstore | .../superstore/ | 200 | Plotly HTML | ★★★★ Интерактивные графики |
| Fintech A/B | .../fintech-ab-test/ | 200 | Reveal.js презентация | ★★★★ Профессионально |
| RF Macro Risk | rf-macro-risk-ai/ | 200 | GitHub Pages live report | ★★★★ Живой контент |
| Mini CRM | .../mini-crm-fastapi-react/ | 200 | React SPA (mock data) | ★★★ Работает |
| HR-Breaker | .../hr-breaker/ | 200 | Static walkthrough | ★★★ Объясняет |
| Leadgen n8n | .../leadgen-n8n-system/ | 200 | Static architecture | ★★★ Архитектурно |
| Fedresurs MVP | .../fedresurs-mvp/ | 200 | Static с данными | ★★★ Показывает вывод |
| Portfolio site | .../Portfolio/ | 200 | Astro сайт | ★★★★ |

Все URLs живые. Нет broken demos. Качество варьируется от production до static walkthrough — это нормально, архитектурные demos честнее, чем заглушки.

---

## 8. GitHub Hygiene

| Репо | Description | Topics | Homepage | Язык | Видимость |
|------|:-----------:|:------:|:--------:|:----:|:---------:|
| finance-mcp-server | ✅ | ✅ 7 тем | ⚠️ Self-link | Python | Public |
| svo-payouts-website | ✅ | ✅ 8 тем | ✅ svorazbor.ru | TypeScript | Public |
| hr-breaker | ✅ | ✅ 7 тем | ✅ Pages | Python | Public |
| leadgen-n8n-system | ✅ | ✅ 7 тем | ✅ Pages | Python | Public |
| finance-data-screener | ✅ | ✅ 8 тем | ✅ Pages | TypeScript | Public |
| fedresurs-mvp | ✅ | ✅ 7 тем | ✅ Pages | **HTML** ⚠️ | Public |
| fintech-ab-test-credit-offer | ✅ | ✅ 6 тем | ✅ Pages | Python | Public |
| Portfolio (monorepo) | ✅ | ✅ 8 тем | ✅ Pages | **HTML** ⚠️ | Public |
| mini-crm-fastapi-react | ✅ | — | ❌ Нет | Python | Public |
| rf-macro-risk-ai | ✅ | ✅ 10 тем | ✅ Pages | Python | Public |

**Что в порядке:** finsight, autello-leads, Create_CRM убраны в private. Нет "test_", "temp_", "final2" репозиториев. Все описания конкретные, не шаблонные.

**Замечания:**
- `finance-mcp-server` homepage = `github.com/kaluginvit/finance-mcp-server` (ссылка на сам репозиторий — бессмысленно для посетителя)
- `fedresurs-mvp` primaryLanguage = **HTML** (после отката .gitattributes — пользователь принял это сознательно)
- `Portfolio` monorepo = **HTML** (из-за Astro dist-файлов и HTML статики)
- `mini-crm-fastapi-react` — нет homepage URL (есть Pages demo, не прописан)

---

## 9. M2 / Middle+ Assessment

| Компетенция | Доказательства | Уверенность |
|-------------|---------------|-------------|
| Backend (Python/FastAPI) | finance-data-screener, hr-breaker, fedresurs, mini-crm | **★★★★** |
| Frontend (React/Next.js/TS) | finance-data-screener, mini-crm, svo-website | **★★★** |
| Data/SQL | fintech-ab (4 SQL + window functions + CTEs), finance-mcp (SQLite schema) | **★★★★** |
| AI/LLM integration | HR-Breaker (Pydantic-AI, LiteLLM), MCP server, rf-macro (LangChain), leadgen (multi-LLM consensus) | **★★★★★** |
| Automation | leadgen-n8n (11 workflows), GitHub Actions во всех репо | **★★★★** |
| Testing | 192 + 64 + 47 + 43 + 30 тестов; pytest, Playwright | **★★★★** |
| Docker/CI | Dockerfile в большинстве проектов, GHCR, VPS deploy, Actions | **★★★★** |
| Business/Domain depth | Finance MCP (управленческий учёт), Fedresurs (оценка банкротств), A/B-тест (продуктовая аналитика) | **★★★★★** |
| End-to-end delivery | SVO (web+bot+VPS+trафик), Finance Screener (full-stack+Docker) | **★★★★** |

**M2 confidence: 82%**  
**Middle+ signal: 78%**

*Ограничивающие факторы: отсутствие высоконагруженных систем, distributed architecture, сложных SQL оптимизаций. Всё это — уровень Senior, а не Middle+.*

---

## 10. Три аудитории

### Работодатель — 7.5/10

**Нанимает на:** Middle/Middle+ applied developer (Python backend, AI integration, full-stack)

**Плюсы:**
- Несколько production систем с реальным трафиком (SVO) — не учебные проекты
- Культура тестирования видна: 192 теста — это не formality
- CI/CD, Docker, GHCR — стандарт производства
- Финансовая экспертиза как domain knowledge — ускоряет онбординг на релевантных задачах
- Понятные README и живые демо — уважение к читателю

**Минусы:**
- Нет сигналов алгоритмической сложности (leetcode/CS fundamentals)
- ML engineering (обучение моделей) отсутствует — только LLM integration
- Database depth — преимущественно SQLite/простой PostgreSQL
- Frontend-скиллы присутствуют, но не на уровне Frontend specialist

### Клиент — 8.5/10

**Ищет:** самостоятельного исполнителя, который понимает бизнес-задачу и доводит до результата

**Плюсы:**
- SVO — доказательство: реальный сайт, реальный трафик, реальная чувствительная тема
- Finance MCP и Fedresurs — видно, что автор понимает финансы как профессионал, а не имитирует
- Leadgen и hotel-booking — показывают автоматизацию бизнес-процессов под ключ
- Живые демо позволяют проверить качество до разговора
- End-to-end: идея → архитектура → код → тесты → deploy → живёт

**Минусы:**
- Нет кейсов "что было до / что стало после" с измеримым эффектом (метрики экономии, ROI)
- Масштаб проектов — Solo-разработчик. Нет сигнала управления командой или крупными проектами

### Технический интервьюер — 7/10

**Проверяет:** инженерную глубину, не поверхностность

**Плюсы:**
- HR-Breaker anti-hallucination pipeline — нетривиальная проблема, нетривиальное решение
- Registry pattern в Finance MCP — осознанная архитектурная декомпозиция
- Fintech A/B: объяснено ПОЧЕМУ Welch, не Mann-Whitney — показывает понимание, не копирование
- Multi-LLM consensus в leadgen — системное мышление об ненадёжности одного LLM
- Тесты не только есть, но и разнообразны: pytest, Playwright, shadow validation

**Минусы:**
- Leadgen: JSON-конфиги n8n — менее верифицируемые, чем код
- Fintech A/B — датасет был bootstrapped (расширен искусственно). Интервьюер заметит
- Нет примеров работы с реальными production-инцидентами, мониторингом, observability
- Глубина тестов не верифицируется без открытия кода — наличие 192 тестов ≠ качественный test design

---

## Critical Fixes

Всего 2 реальных проблемы:

**1. `finance-mcp-server` homepage = self-link (github.com/kaluginvit/finance-mcp-server)**  
Посетитель видит кнопку "Website" на GitHub-карточке, кликает — попадает снова на GitHub. Бессмысленно. Лучше убрать homepage вообще, или поставить Portfolio monorepo URL для этого проекта.  
*Воздействие: первое впечатление от пинового репо.*

**2. Порядок pinned: finance-mcp-server (нет live demo) стоит первым**  
`svo-payouts-website` с живым production-сайтом сильнее как первый pinned. Обмен мест.  
*Воздействие: первые 5 секунд при открытии профиля.*

---

## Nice-to-Have

**1. `mini-crm-fastapi-react` — прописать homepage**  
Есть Pages demo, но поле пустое. Одна строка в repo settings.

**2. Fedresurs README: явно указать язык проекта в начале**  
GitHub показывает HTML. Первая строка README: "Python + Flask + SQLite" — компенсирует визуальное впечатление.

**3. Portfolio monorepo — язык HTML**  
Monorepo отображается как HTML. .gitattributes для `site/dist/` или `**/*.html linguist-vendored` покажет Python/TypeScript как основные языки.

**4. A/B-тест: пояснение к bootstrapped-датасету**  
Короткая ремарка, что базовый датасет синтетически расширен для целей showcase — снижает потенциальный вопрос интервьюера.

**5. Добавить 1 кейс с реальным ROI/результатом**  
Даже короткий: "запуск SVO → X заявок за Y месяцев". Не для всех проектов, но для SVO это возможно.

---

## Final Verdict

Портфолио находится на уровне **крепкого Middle+**, ближе к верхней границе этого диапазона.

Основные сильные стороны:
- Реальные production системы (не только учебные проекты)
- Уникальное сочетание финансового домена + разработки + AI
- Живые демо для большинства проектов
- Культура тестирования видна
- Позиционирование ясное и дифференцированное

Основные ограничения:
- Нет сигналов Senior-уровня (scale, distributed systems, performance)
- Два из шести pinned репо создают первое впечатление слабее, чем могли бы
- Измеримые бизнес-результаты не представлены

**Для работодателя** портфолио убедительно обоснует собеседование на Middle/Middle+ позицию в финтех, продукт с AI-фокусом или автоматизацию.

**Для клиента** — достаточно, чтобы начать разговор без дополнительных доказательств компетентности.

**Для технического интервьюера** — даст повод для содержательной дискуссии об архитектурных решениях, не будет отклонён как "vibe-only".
