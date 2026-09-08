# Portfolio — Claude Code Context

Рабочая папка: `C:\_Рабочая_папка\_Portfolio`  
GitHub: `https://github.com/kaluginvit/Portfolio`  
Pages: `https://kaluginvit.github.io/Portfolio/`  
gh CLI: `C:\Program Files\GitHub CLI\gh.exe`

---

## Владелец и позиционирование

**Виталий Калугин — Strong Middle / Middle+ Applied Developer**  
Специализация: `Corporate Finance × Software Development × AI × Automation`

Главный тезис: понимает бизнес и финансы → самостоятельно превращает бизнес-задачу в работающий инструмент.

---

## Tier-структура

### Tier A — Core Showcase (7 систем, featured на сайте)

| # | Система | M2 | Standalone Repo | Live Demo |
|---|---------|---:|-----------------|-----------|
| 1 | SVO System (web + bot) | 86% | svo-payouts-website + svo-payments-bot | https://svorazbor.ru |
| 2 | fintech-ab-test-credit-offer | 85% | fintech-ab-test-credit-offer | https://kaluginvit.github.io/Portfolio/fintech-ab-test/ |
| 3 | leadgen-n8n-system | 84% | leadgen-n8n-system | https://kaluginvit.github.io/Portfolio/leadgen-n8n-system/ |
| 4 | hr-breaker | 83% | hr-breaker | https://kaluginvit.github.io/Portfolio/hr-breaker/ |
| 5 | finance-mcp-server | 83% | finance-mcp-server | — (local MCP tool) |
| 6 | fedresurs-mvp | 82% | fedresurs-mvp | https://kaluginvit.github.io/Portfolio/fedresurs-mvp/ |
| 7 | finance-data-screener | 80% | finance-data-screener | https://kaluginvit.github.io/Portfolio/finance-data-screener/ |

### Tier B — More Projects (5, на сайте в блоке «More Projects»)

rf-macro-risk-ai (80%), mini-crm-fastapi-react (78%), team-ai-bot (67%), hotel-booking-n8n (64%), superstore-retail-analytics (63%)

### Tier C — GitHub-only (не показывать на сайте, не добавлять на Pages)

bankrot-trades-scraper, personal-rag-assistant, tg-digest-pipeline, finsight, bots-platform, dostaffkin

### Tier D → перемещены в _Portfolio_back (не трогать)

---

## Monorepo-структура

```
Portfolio/
├── 01-data-analytics/    fintech-ab-test-credit-offer, fedresurs-mvp, superstore
├── 02-automation/        leadgen-n8n-system, hotel-booking-n8n
├── 03-ai-products/       hr-breaker, finance-mcp-server, rf-macro-risk-ai, svo-payments-bot, team-ai-bot
├── 04-web/               finance-data-screener, mini-crm-fastapi-react, svo-payouts-website
├── 05-ai-consulting/
├── site/                 Astro portfolio site (каталог кейсов и публичная витрина)
└── Сертификаты/
```

---

## GitHub Pages — деплой

Единственный workflow: `.github/workflows/portfolio-github-pages.yml`  
Сборка: Astro (site/) + React demos + static HTML demos → `_site/`  
Триггер: любой push в `main`

**Не создавать отдельные Pages в standalone repos.** Все demos живут в Portfolio Pages.

---

## Ключевые файлы

| Файл | Назначение |
|------|-----------|
| `site/src/data/cases.ts` | Карточки сайта (7 Core + 5 More = 12) |
| `site/src/data/certs.ts` | Сертификаты на странице About |
| `Сертификаты/README.md` | Таблица сертификатов с описанием |
| `MANIFEST.md` | Текущее состояние всех repos и URLs |
| `PORTFOLIO_FINAL_CLASSIFICATION.md` | Tier A/B/C/D таблица |
| `PORTFOLIO_M2_AUDIT.md` | M2-баллы всех проектов |
| `PORTFOLIO_FINAL_USER_AUDIT.md` | Финальный аудит (работодатель/клиент/интервьюер) |

---

## Правила работы

**Никогда без явного подтверждения:**
- Git-операции: commit, push, force push, reset, checkout
- Менять Tier-классификацию проектов
- Трогать Tier C (не показывать, не удалять)
- Трогать Tier D (_Portfolio_back)
- Менять `.github/workflows/portfolio-github-pages.yml`
- Добавлять новые Pages-demos без запроса

**Можно самостоятельно:**
- Читать любые файлы репо
- Проверять HTTP-статус live URLs
- Читать gh API
- Анализировать и готовить рекомендации

**Subtree split** — для синхронизации standalone Tier A repos используется `git subtree split --prefix=<path>`. Force push допустим только при несовместимых историях (документировать причину).

---

## Сертификаты

Папка: `Сертификаты/`. Изображения в PNG.  
Новые сертификаты: добавить в `certs.ts`, `Сертификаты/README.md`, и `README.md` (cert wall).  
Файлы PNG должны быть закоммичены — иначе Actions не увидит их.
