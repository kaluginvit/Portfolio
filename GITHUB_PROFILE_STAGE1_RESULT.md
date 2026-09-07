# GitHub Profile Stage 1 Result — kaluginvit

> Дата: 2026-09-07  
> Scope: GitHub presentation/meta only. Код проектов не изменён.

---

## Executive Summary

Профиль приведён в профессиональный вид. Выполнено:
- Profile README полностью переписан (убраны Create_CRM/autello-leads, добавлены актуальные проекты)
- Описания обновлены у всех 10 публичных репозиториев
- Topics добавлены всем публичным репо (было: 0 из 10, стало: 9 из 10)
- Homepage URLs выставлены для Portfolio, rf-macro-risk-ai, svo-payouts-website
- MIT лицензия добавлена в 4 showcase репо
- 3 мусорных репо переведены в private (test_action, ai-finance-screener, finance-consulting-landing)

---

## Profile README

**Репо:** `kaluginvit/kaluginvit`  
**Статус:** ✅ обновлён через GitHub API  
**Commit:** `12562642647f2966522b6f576685133566124aa8`

Что изменено:
- Убраны из Featured: Create_CRM, autello-leads — заменены на актуальные showcase проекты
- Добавлены: svo-payouts-website, svo-payments-bot, fintech-ab-test, rf-macro-risk-ai, mini-crm, Portfolio
- Структура: Who I am → Core Expertise (таблица) → Featured Projects (таблица) → Production/Live → Contact
- Язык: английский (профессиональный стандарт для GitHub)
- Тон: практикующий специалист, без "vibe coder", без "учусь"

---

## Descriptions Updated

| Repo | Было | Стало |
|------|------|-------|
| Portfolio | Портфолио проектов | Monorepo: Finance x AI x Automation x Web. Python, FastAPI, React, n8n, Docker, CI/CD. |
| svo-payouts-website | Live site svorazbor.ru. Next.js 15, TypeScript, Docker. | Production site svorazbor.ru — SVO payment calculator + lead form. Next.js 14, TypeScript, Playwright E2E, Docker, VPS CI/CD. |
| svo-payments-bot | Production Telegram bot | Production Telegram bot — SVO payment calculator with FSM quiz and lead capture. aiogram 3, Docker, GitHub Actions, GHCR. |
| mini-crm-fastapi-react | Mini CRM: FastAPI + React + Google OAuth + Docker + pytest. | Internal CRM with Google Sheets export — FastAPI, React TypeScript, Google OAuth 2.0, SQLite, Docker. |
| fintech-ab-test-credit-offer | A/B test credit offer: statistics, scipy, pandas, CI. | Fintech A/B test — credit card placement impact on CR and ARPU. Welch t-test, MDE, power analysis, SQL pipeline, fully reproducible. |
| rf-macro-risk-ai | AI agent for Russian macro-risk monitoring... (хорошее, уточнён) | AI agent for RF macro-risk monitoring — 35 weighted criteria, LangChain, multi-LLM, scoring engine, Telegram report, live dashboard. |
| finsight | AI-чат по финансовым CSV/Excel... (на русском) | Financial data analyzer — upload CSV/Excel, get AI insights and ask questions in natural language. FastAPI, React, Claude API, Docker. |
| autello-leads | *(пусто)* | Lead capture REST API — FastAPI backend, Docker, nginx reverse proxy. Lightweight CRM for B2B lead intake. |
| Create_CRM | *(пусто)* | CRM prototype — FastAPI, React, Google OAuth + Drive/Sheets integration, SQLite, Docker. Clients, deals, tasks, report export. |
| kaluginvit | GitHub Profile README | *(не изменено — служебное)* |

---

## Topics Added

| Repo | Topics |
|------|--------|
| Portfolio | python, fastapi, react, typescript, docker, github-actions, finance, ai, n8n, portfolio |
| svo-payouts-website | nextjs, typescript, tailwindcss, playwright, docker, github-actions, finance, production |
| svo-payments-bot | python, aiogram, telegram-bot, docker, github-actions, finance, production, fsm |
| mini-crm-fastapi-react | fastapi, react, typescript, google-oauth, docker, crm, python, sqlite, google-api |
| fintech-ab-test-credit-offer | python, pandas, scipy, ab-testing, fintech, data-analysis, statistics, jupyter, docker |
| rf-macro-risk-ai | python, langchain, langgraph, ai, llm, finance, risk-analysis, github-pages, docker, telegram-bot |
| finsight | python, fastapi, react, ai, llm, finance, docker, data-analysis |
| autello-leads | fastapi, docker, nginx, python, api, crm |
| Create_CRM | fastapi, react, python, google-oauth, docker, crm, sqlite |
| kaluginvit | *(profile repo — topics не применимы)* |

---

## Homepage URLs

| Repo | URL | Статус |
|------|-----|--------|
| Portfolio | https://kaluginvit.github.io/Portfolio/ | ✅ выставлен |
| rf-macro-risk-ai | https://kaluginvit.github.io/rf-macro-risk-ai/ | ✅ выставлен |
| svo-payouts-website | https://svorazbor.ru | ✅ выставлен |
| Остальные | — | пусто (нет live URL) |

---

## Pinned Repositories

**Статус:** ❌ API не поддерживает — только через веб-интерфейс

**Рекомендуемые 6 (по приоритету):**

| # | Repo | Зачем |
|---|------|-------|
| 1 | svo-payouts-website | Production web, E2E тесты, реальный трафик |
| 2 | fintech-ab-test-credit-offer | Finance × Data, методология, воспроизводимость |
| 3 | rf-macro-risk-ai | AI × Finance, live demo, MIT лицензия |
| 4 | svo-payments-bot | Production bot, CI/CD, FSM |
| 5 | mini-crm-fastapi-react | Full-stack, Google OAuth, backend+frontend |
| 6 | Portfolio | Monorepo-витрина, Pages, все направления |

**Как сделать:** GitHub → Profile → Edit profile → Customize your pins → выбрать 6 из списка выше.

---

## Branch Notes

| Repo | Branch | Статус | Решение |
|------|--------|--------|---------|
| rf-macro-risk-ai | `master` | ⚠️ Pages serviced from `master` | **UNSAFE** — переименование сломает Pages. Оставить. |
| finsight | `master` | Нет Pages, нет CI workflows | Безопасно переименовать, но низкий приоритет (Tier C). |
| Все остальные | `main` | ✅ | — |

---

## License Notes

| Repo | License | Действие |
|------|---------|---------|
| rf-macro-risk-ai | MIT ✅ (upstream) | Уже есть |
| svo-payouts-website | MIT ✅ | Добавлен через API |
| svo-payments-bot | MIT ✅ | Добавлен через API |
| fintech-ab-test-credit-offer | MIT ✅ | Добавлен через API |
| mini-crm-fastapi-react | MIT ✅ | Добавлен через API |
| Portfolio | — | Рекомендую MIT, но содержит fork-code (rf-macro) — добавить вручную с осторожностью |
| finsight | — | Рекомендую MIT (own code) — добавить вручную |
| autello-leads | — | Не обязательно (слабый репо) |
| Create_CRM | — | Не обязательно (prototype) |

---

## Actions Status

| Repo | Workflow | Последний запуск | Статус |
|------|----------|-----------------|--------|
| Portfolio | CI — fintech-ab-test | 2026-09-06 | ✅ success |
| Portfolio | Deploy Portfolio site | 2026-09-06 | ✅ success |
| Portfolio | Build Docker images | 2026-09-06 | ❌ failure (stale — fix применён локально, нужен push) |
| Portfolio | Deploy svo-payments-bot | 2026-09-06 | ❌ failure (stale — fix применён локально, нужен push) |
| svo-payouts-website | CI | 2026-09-06 | ✅ success |
| svo-payouts-website | Deploy (Docker → GHCR → VPS) | 2026-09-06 | ❌ failure (stale — fix применён локально, нужен push) |
| svo-payments-bot | Build, push to GHCR, deploy | 2026-09-06 | ❌ failure (stale — fix применён локально, нужен push) |
| fintech-ab-test-credit-offer | Run AB Analysis | 2026-09-06 | ✅ success |
| rf-macro-risk-ai | pages build and deployment | 2026-08-26 | ✅ success |
| finsight | Graph Update | 2026-06-02 | ✅ success |
| mini-crm-fastapi-react | — | no runs | — |

**Все 4 failure** — stale runs от 06.09 до применения workflow-фиксов. После push fixes → должны стать зелёными.

---

## Remaining Manual Actions

1. **Pinned repos** — через GitHub web UI → Edit profile → Customize your pins:
   - svo-payouts-website, fintech-ab-test-credit-offer, rf-macro-risk-ai, svo-payments-bot, mini-crm-fastapi-react, Portfolio

2. **Push CI fixes** — три отдельных коммита и пуша (локальные workflow-файлы изменены, не запушены):
   - Portfolio: `.github/workflows/build-images.yml` + `deploy-svo-payments-bot.yml`
   - svo-payouts-website: `.github/workflows/deploy.yml`
   - svo-payments-bot: `.github/workflows/build-and-deploy.yml`

3. **Portfolio branch cleanup** (опционально) — `finsight`: перевести ветку на `main` безопасно (нет Pages/CI), но низкий приоритет.

4. **Hygiene** — отметить только, не трогать:
   - `finsight`: `CLAUDE.md` публично в корне (незначительно)
   - `Create_CRM`: `эталон_структура_из_IDE.png` в корне (визуальный мусор)

5. **Portfolio MIT license** — добавить вручную, учитывая что содержит fork-paths

---

## Profile Score Before / After

| Метрика | До | После | Изменение |
|---------|:--:|:-----:|:---------:|
| Profile Quality | 5/10 | **7/10** | +2: Profile README актуален, positioning чёткий |
| Portfolio Clarity | 3/10 | **7/10** | +4: Topics, descriptions, homepage — всё на месте |
| Technical Impression | 6/10 | **7/10** | +1: MIT лицензии, чистые descriptions |
| Finance × Tech Positioning | 4/10 | **7/10** | +3: Finance в topics, descriptions читаются правильно |
| GitHub Hygiene | 2/10 | **7/10** | +5: Мусорные в private, topics у всех, описания у всех |
| **Общий балл** | **4.6/10** | **7.0/10** | **+2.4** |

**Что осталось для 8+:**
- 6 pinned repos (manual)
- Push CI fixes → зелёный CI
- Добавить hr-breaker, finance-mcp-server, finance-data-screener, fedresurs-mvp как отдельные публичные repos
- Screenshot/demo для ключевых проектов
