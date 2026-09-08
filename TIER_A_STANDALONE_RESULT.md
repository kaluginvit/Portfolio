# Tier A Standalone Repos — Final Result

**Дата:** 2026-09-08  
**Monorepo commit:** `a789d0b`  
**Actions:** ✅ success (Deploy Portfolio site + Deploy svo-payments-bot)

---

## 1. Tier A Standalone Repos — итоговая таблица

| Project | Repo URL | Action | History | README | Live Demo |
|---------|----------|--------|---------|--------|-----------|
| SVO Payouts Website | https://github.com/kaluginvit/svo-payouts-website | SYNCED (force push) | subtree split (monorepo) | GOOD | https://svorazbor.ru |
| SVO Payments Bot | https://github.com/kaluginvit/svo-payments-bot | SYNCED (force push) | subtree split (monorepo) | FIXED | https://github.com/kaluginvit/Portfolio/pkgs/container/svo-payments-bot |
| Fintech A/B Test | https://github.com/kaluginvit/fintech-ab-test-credit-offer | SYNCED (force push) | subtree split (monorepo) | GOOD | https://kaluginvit.github.io/Portfolio/fintech-ab-test/ |
| Leadgen n8n System | https://github.com/kaluginvit/leadgen-n8n-system | CREATED | 6 commits (subtree) | FIXED | https://kaluginvit.github.io/Portfolio/leadgen-n8n-system/ |
| HR-Breaker | https://github.com/kaluginvit/hr-breaker | CREATED | 5 commits (subtree) | GOOD | https://kaluginvit.github.io/Portfolio/hr-breaker/ |
| Finance MCP Server | https://github.com/kaluginvit/finance-mcp-server | CREATED | 5 commits (subtree) | GOOD | https://github.com/kaluginvit/finance-mcp-server |
| Fedresurs MVP | https://github.com/kaluginvit/fedresurs-mvp | CREATED | 4 commits (subtree) | FIXED | https://kaluginvit.github.io/Portfolio/fedresurs-mvp/ |
| Finance Data Screener | https://github.com/kaluginvit/finance-data-screener | CREATED | 4 commits (subtree) | GOOD | https://kaluginvit.github.io/Portfolio/finance-data-screener/ |

*SVO System = 2 repos (web + bot) — показывается одной карточкой на сайте.*

---

## 2. Что создано (5 новых repos)

Использован `git subtree split` для сохранения истории из монорепо:

| Repo | Prefix в monorepo | Коммитов | SHA ветки |
|------|-------------------|----------|-----------|
| fedresurs-mvp | `01-data-analytics/fedresurs-mvp` | 4 | a7d10f9 |
| finance-data-screener | `04-web/finance-data-screener` | 4 | 0a287d9 |
| finance-mcp-server | `03-ai-products/finance-mcp-server` | 5 | 934d076 |
| hr-breaker | `03-ai-products/hr-breaker` | 5 | 0b3a4b9 |
| leadgen-n8n-system | `02-automation/leadgen-n8n-system` | 6 | fafe1eb |

---

## 3. Что синхронизировано (3 STALE repos)

Репозитории отставали от monorepo на 1 коммит. Синхронизированы через `git subtree split` + force push (единственный путь при несовместимых историях standalone ↔ monorepo):

| Repo | Старый HEAD | Новый HEAD | Изменения |
|------|-------------|------------|-----------|
| svo-payouts-website | `8f5d30f` | `c209cfe` | README rewrite, CI workflow update, SCREENSHOTS_TODO.md |
| svo-payments-bot | `e677027` | `62fe021` | README rewrite (+ problem statement + demo), CI workflow update, SCREENSHOTS_TODO.md |
| fintech-ab-test-credit-offer | `7ab408d` | `76d040a` | README: added live demo link |

**Force push обоснован:** независимые истории standalone repos несовместимы с subtree-extracted историей monorepo. Regular push невозможен.

---

## 4. Переведено в private (3 repos)

| Repo | Причина |
|------|---------|
| finsight | Tier C, компетенция закрыта finance-data-screener (Tier A) |
| autello-leads | Слабый, не классифицирован; аудит Stage 1 отметил как негативно влияющий |
| Create_CRM | Prototype, закрыт mini-crm-fastapi-react (Tier B) |

Уже были private (не трогали): `test_action`, `ai-finance-screener`, `finance-consulting-landing`

---

## 5. README — реальные изменения

Файлы изменены в monorepo, commit `a789d0b`:

| README | Что добавлено |
|--------|---------------|
| `03-ai-products/svo-payments-bot/README.md` | Business problem (1 paragraph) + Live link (svorazbor.ru + GHCR) |
| `02-automation/leadgen-n8n-system/README.md` | Live Demo URL + Testing note (shadow validation) |
| `01-data-analytics/fedresurs-mvp/README.md` | Live Demo URL |

Не изменялись (GOOD): SVO Website, Fintech A/B, HR-Breaker, Finance MCP Server, Finance Data Screener.

---

## 6. GitHub Metadata — все Tier A standalone repos

| Repo | Description | Topics | Homepage |
|------|-------------|--------|----------|
| svo-payouts-website | Production Next.js 14 site — SVO payment calculator... | nextjs, typescript, docker, playwright, production | https://svorazbor.ru |
| svo-payments-bot | Production Telegram bot — FSM-guided payout quiz... | python, aiogram, telegram, docker, fsm, production | https://github.com/kaluginvit/Portfolio/pkgs/container/svo-payments-bot |
| fintech-ab-test-credit-offer | Fintech A/B test — credit card placement impact... | python, finance, data-analysis, statistics, ab-testing, fintech | https://kaluginvit.github.io/Portfolio/fintech-ab-test/ |
| leadgen-n8n-system | B2B lead generation system — 11 n8n workflows... | n8n, automation, ai, python, b2b, llm, docker | https://kaluginvit.github.io/Portfolio/leadgen-n8n-system/ |
| hr-breaker | Resume optimizer with anti-hallucination pipeline... | python, ai, fastapi, pydantic, pdf, llm, resume | https://kaluginvit.github.io/Portfolio/hr-breaker/ |
| finance-mcp-server | Finance MCP Server — 19 MCP tools for Claude Desktop... | python, finance, mcp, ai, sqlite, claude, llm | https://github.com/kaluginvit/finance-mcp-server |
| fedresurs-mvp | Bankruptcy lot valuation tool — P25/P50/P75... | python, finance, ai, flask, sqlite, data-analysis, bankruptcy | https://kaluginvit.github.io/Portfolio/fedresurs-mvp/ |
| finance-data-screener | AI financial data screener — natural language... | python, finance, ai, fastapi, react, llm, moex, docker | https://kaluginvit.github.io/Portfolio/finance-data-screener/ |

---

## 7. Подтверждение сайта

Файл: `site/src/data/cases.ts`

- **Core Showcase (featured: true):** 7 карточек — `svo`, `finance-mcp-server`, `hr-breaker`, `leadgen-n8n`, `finance-data-screener`, `fedresurs`, `fintech-ab`
- **More Projects:** 5 карточек — `rf-macro-risk`, `mini-crm`, `superstore`, `team-bot`, `hotel-booking-n8n`
- **Итого: 12 карточек** ✅

SVO = одна карточка (`id: 'svo'`) → svorazbor.ru ✅

---

## 8. Live Check — все URLs 200 OK

| URL | Статус |
|-----|--------|
| https://kaluginvit.github.io/Portfolio/hr-breaker/ | ✅ 200 |
| https://kaluginvit.github.io/Portfolio/finance-data-screener/ | ✅ 200 |
| https://kaluginvit.github.io/Portfolio/fedresurs-mvp/ | ✅ 200 |
| https://kaluginvit.github.io/Portfolio/leadgen-n8n-system/ | ✅ 200 |
| https://kaluginvit.github.io/Portfolio/fintech-ab-test/ | ✅ 200 |
| https://svorazbor.ru | ✅ 200 |

---

## 9. Actions Status

| Workflow | SHA | Result |
|----------|-----|--------|
| Deploy Portfolio site (GitHub Pages) | `a789d0b` | ✅ success |
| Deploy svo-payments-bot | `a789d0b` | ✅ success |

---

## 10. Оставшиеся ручные действия

- [ ] Закрепить 6 pinned repos (GitHub → Profile → Customize):
  1. `kaluginvit/Portfolio`
  2. `kaluginvit/svo-payouts-website`
  3. `kaluginvit/svo-payments-bot`
  4. `kaluginvit/finance-mcp-server`
  5. `kaluginvit/hr-breaker`
  6. `kaluginvit/leadgen-n8n-system`
- [ ] Проверить CI на standalone repos (svo-payouts-website, svo-payments-bot — force push мог запустить их CI)
- [ ] Опционально: добавить mini-crm homepage в metadata (`https://kaluginvit.github.io/Portfolio/mini-crm-fastapi-react/`)
