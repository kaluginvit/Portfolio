# SVO Payouts Website

Production Next.js сайт: квиз → ориентировочный расчёт выплат → лид-форма → webhook в CRM. Часть end-to-end системы вместе с [Telegram-ботом](../../03-ai-products/svo-payments-bot/).

**Live:** [svorazbor.ru](https://svorazbor.ru)

> Расчёты — ориентиры, не юридическое заключение.

## Business Problem

Семьи погибших участников СВО часто не понимают: какие выплаты существуют, чем разовые отличаются от ежемесячных, куда обращаться. Высокий стресс + сложный регуляторный ландшафт = люди теряются ещё на первом шаге.

Сайт решает одну задачу: дать понятный вход. Без канцелярита, по шагам, с ориентировочными цифрами — и с возможностью оставить заявку на консультацию.

## Solution

Next.js 14 App Router сайт с интерактивным квизом в двух ветках:

- **Fresh flow:** ответил на вопросы → получил ориентировочный расчёт федеральных мер
- **Clarify flow:** документы уже поданы, нужно разобраться в ситуации → фокус на шагах, не на суммах

Заявка сохраняется в файловое хранилище, дублируется в Telegram и опционально отправляется в CRM через webhook.

## Key Features

- Два сценария квиза (fresh / clarify) с независимой логикой
- Расчёт с учётом состава семьи и региона
- localStorage persistence — незавершённый квиз восстанавливается при возврате
- Lead форма: имя, телефон, согласие на ПДн → Telegram + webhook
- Vitest (unit + integration) + Playwright E2E тесты
- Full CI/CD: GitHub Actions → Docker → GHCR → SSH deploy → VPS

## Architecture

```
User
  │
  ▼
Next.js App Router (svorazbor.ru)
  ├── / (quiz-context, calculator, localStorage)
  ├── /api/lead (Zod validation → storage → Telegram → webhook)
  ├── /thanks
  └── /privacy, /consent

Storage (file or memory)
  └── data/leads.json (Docker volume on VPS)

Telegram Bot API ──► Admin chat
Webhook (optional) ──► CRM / n8n

CI/CD Pipeline:
  push main → GitHub Actions → Docker build
    → GHCR (ghcr.io/.../svo-site:latest)
      → SSH to VPS → docker compose pull && up -d
        → nginx (HTTPS) → app :3001
```

## Tech Stack

| Компонент | Технология |
|-----------|-----------|
| Framework | Next.js 14 App Router |
| Language | TypeScript |
| Styling | Tailwind CSS v4 |
| UI | Radix primitives + CVA (shadcn-style) |
| Animation | Framer Motion |
| Forms | React Hook Form + Zod |
| Unit tests | Vitest |
| E2E tests | Playwright |
| Container | Docker (multi-stage, standalone Next.js) |
| Proxy | nginx |
| CI/CD | GitHub Actions → GHCR → SSH deploy |

## Business / Domain Logic

**Калькулятор** (`src/lib/calculator.ts`): федеральные единовременные и ежемесячные выплаты с учётом состава семьи и региональных надбавок.

**Квиз-контекст** (`src/contexts/quiz-context.tsx`): глобальное состояние с синхронизацией в localStorage под ключом `svo_quiz_v2`. Сценарий (A/B) определяется на первом шаге и не меняется до сброса.

**Lead валидация** (`src/lib/validation/lead.ts`): Zod схема — имя, телефон (≥10 цифр), регион, согласие, сценарий квиза. Телефон нормализуется (+7).

**Analytics events** (`src/lib/analytics/events.ts`): события в GA4 + Яндекс.Метрика по ключевым шагам воронки (`quiz_start`, `result_view`, `lead_form_success`, ...).

## Project Structure

```
svo-payouts-website/
├── web/                  # Next.js приложение
│   ├── src/
│   │   ├── app/          # Роуты, API handlers
│   │   ├── components/   # quiz/, sections/, ui/
│   │   ├── lib/          # calculator, validation, telegram, analytics
│   │   └── data/         # texts, seo metadata
│   ├── e2e/              # Playwright тесты
│   ├── Dockerfile
│   └── .env.example
├── deploy/
│   ├── nginx/            # nginx конфиги для VPS
│   ├── scripts/          # VPS setup script
│   └── env.production.example
├── docker-compose.yml
├── Makefile
└── RELATED.md            # Связь с Telegram-ботом
```

## Quick Start

```bash
cd web
cp .env.example .env
npm install
npm run dev
# http://localhost:3000
```

Минимальные переменные: без них сайт запустится, Telegram и webhook не будут работать (лиды пишутся только в файл).

## Configuration

`.env.example` в `web/`:

| Переменная | Обязательно | Описание |
|-----------|:-----------:|---------|
| `NEXT_PUBLIC_SITE_URL` | prod | `https://svorazbor.ru` |
| `TELEGRAM_BOT_TOKEN` | нет | Token бота для уведомлений |
| `TELEGRAM_CHAT_ID` | нет | Chat ID админа |
| `LEAD_WEBHOOK_URL` | нет | POST endpoint для CRM/n8n |
| `LEAD_WEBHOOK_SECRET` | нет | Bearer token для webhook |
| `LEADS_STORAGE_MODE` | нет | `file` (default) или `memory` |
| `LEADS_FILE_PATH` | нет | Путь к JSON-файлу лидов |
| `NEXT_PUBLIC_GA_ID` | нет | Google Analytics 4 |
| `NEXT_PUBLIC_YM_ID` | нет | Яндекс.Метрика |

## Tests

```bash
cd web

# Unit + integration
npm run test

# E2E (нужен установленный Chromium)
npx playwright install chromium
npm run test:e2e

# Smoke (lint + test + build)
npm run smoke
```

**E2E сценарии:** `fresh-flow.spec.ts`, `lead-form.spec.ts`, `quiz-navigation.spec.ts`, `stuck-flow.spec.ts`

**Unit/integration:** calculator, region normalization, phone normalization, payout breakdown builder, Zod schemas, quiz navigation.

## Screenshots

→ `docs/SCREENSHOTS_TODO.md`

## Engineering Decisions

**Next.js App Router (не Pages Router):** поддержка Server Components, удобная структура route handlers для `/api/lead`. Standalone output для компактного Docker-образа.

**localStorage для квиза:** пользователь может уйти и вернуться — квиз восстанавливается с того же шага. Простое решение без backend state.

**Два сценария (A/B), не один:** пользователи разные — один приходит разбираться с нуля, другой уже в процессе получения и хочет понять "почему тормозит". Одинаковый квиз для обоих плохо работает.

**Docker + GHCR + SSH deploy:** VPS без managed platform. Простая, предсказуемая цепочка. PM2 рассматривался, Docker выбран для изоляции и воспроизводимости.

## Security / Privacy

- Персональные данные (имя, телефон) только в `data/leads.json` на VPS (Docker volume)
- Telegram токен и webhook URL только через `.env` на VPS, не в образе
- `.gitignore` исключает `.env` и `data/`
- HTTPS через nginx + Certbot

## Reuse / Customization

Тип: **Production case → Reusable architecture**

Квиз-архитектура переиспользуема для похожих сценариев: мед. льготы, налоговые вычеты, социальные выплаты.

**Для адаптации под другую тему:**
1. Заменить тексты в `src/data/texts/`
2. Заменить логику расчёта в `src/lib/calculator.ts`
3. Обновить шаги квиза в `src/components/quiz/`
4. Заменить SEO-данные в `src/data/seo/`

**Технический стек остаётся тем же** — webhook, Telegram, хранилище, CI/CD.

## Limitations

- Расчёты — ориентиры на основе публичной информации, не юридически значимые суммы
- Региональные меры не полностью актуализированы (указано в интерфейсе)
- Файловое хранилище лидов (`data/leads.json`): при высоком трафике стоит заменить на БД
- Zero-downtime deploy требует дополнительной настройки (blue/green)

## CI/CD и Deployment

Полная документация по деплою: [`web/README.md`](./web/README.md)

Краткая схема:
```
git push main
  → GitHub Actions (CI: lint + test + build)
  → Docker build → push to GHCR
  → SSH to VPS → docker compose pull && up -d
  → nginx proxy → HTTPS via Certbot
```

## Парный продукт

Telegram-бот с той же логикой квиза: [`03-ai-products/svo-payments-bot`](../../03-ai-products/svo-payments-bot/)  
Связь и архитектура системы: [`RELATED.md`](./RELATED.md)

## Roadmap

- База данных для лидов (PostgreSQL) вместо JSON-файла
- Автоматическое обновление региональных надбавок
- A/B тест разных формулировок расчёта
- Кабинет для просмотра заявок (без внешней CRM)
