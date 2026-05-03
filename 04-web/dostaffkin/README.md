# Dostaffkin — доставка: заказ и трек статусов

SPA на **Angular 21** с лёгким backend на **Node.js + Express** и хранением в **PostgreSQL**. Пользователь оформляет доставку, получает номер заказа и может смотреть цепочку статусов на экране трекинга.

## Ценность в портфолио

- Полноценный **full-stack минимализм**: фронт (маршруты Home / Order / Track), REST API, схема БД через миграцию на старте сервера.
- **Русскоязычный UX**: статусы и даты подписаны понятными фразами, а не техническими кодами.
- Готовность к **демо локально**: две команды — фронт и бэкенд (см. ниже).

## Стек

| Слой | Технологии |
|------|-------------|
| Frontend | Angular 21, TypeScript, Vitest |
| Backend | Express 5, `pg`, CORS |
| Хранилище | PostgreSQL (таблица `deliveries`) |

Подробнее по API см. [`backend/README.md`](./backend/README.md).

## Быстрый старт (Windows)

**1. База**

```sql
CREATE DATABASE dostaffkin;
```

**2. Переменные окружения бэкенда**

Скопируйте [`.env.example`](./.env.example) → `backend/` не используется — `.env.example` лежит в корне проекта; для backend ожидается `.env` в **корне** `dostaffkin` при запуске `npm run backend` (см. `server.js`: `dotenv` в корне проекта).

```powershell
cd 04-web\dostaffkin
copy .env.example .env
# Отредактируйте DATABASE_URL при необходимости
```

**3. Backend**

```powershell
npm install
npm run backend
```

API по умолчанию: `http://localhost:3000` (`/health`, `POST /delivery/create`, `GET /delivery/info?id=…`).

**4. Frontend**

В другом терминале:

```powershell
cd 04-web\dostaffkin
npm start
```

Откройте URL из вывода `ng serve` (обычно `http://localhost:4200`). База URL API задана в [`src/app/services/delivery-api.ts`](./src/app/services/delivery-api.ts) как `http://localhost:3000` — перед выкладкой на другой домен её нужно изменить или вынести в конфиг.

## Деплой

- Статическая сборка: `npm run build` → артефакты по настройке `angular.json` (папка `docs/` в репозитории может использоваться как GitHub Pages — проверьте `outputPath`).
- Backend: любой VPS/контейнер с Node + PostgreSQL, переменные как в `.env.example`.

## Парное расположение в портфолио

Часть «веб-витрины» этого репозитория живёт рядом: [`svo-payouts-website`](../svo-payouts-website/) (Next.js, другой домен задачи).

## Статус

Рабочий учебный/продуктовый образец под портфолио; ключи и `.env` в git не коммитятся (см. корневой `.gitignore` репозитория портфолио).
