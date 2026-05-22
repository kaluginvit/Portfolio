# Запустить любой кейс локально за 5 минут

Этот файл — **единая инструкция для внешнего пользователя**. Здесь общий шаблон; нюансы конкретного проекта — в его README.

## Что нужно один раз

- **Docker Desktop** (Windows / macOS) или Docker Engine (Linux) — для большинства запусков.
- **Python 3.10+** — если запускаете Python-проекты без Docker (аналитика, часть ботов).
- **Node.js 20+** — если запускаете веб-проекты без Docker.
- **git** — для клонирования.

Если планируете только смотреть готовые образы из GHCR — достаточно Docker.

---

## Шаблон A: Docker-проект (рекомендуется)

```bash
git clone https://github.com/kaluginvit/Portfolio.git
cd Portfolio/<путь_до_проекта>
cp .env.example .env       # заполните плейсхолдеры (токены, ключи API)
docker compose up -d       # или: docker run --env-file .env -p ... ghcr.io/kaluginvit/<image>:latest
```

Smoke-проверка — в README конкретного проекта (раздел «Smoke-чеклист»).

### Готовые образы

Список всех опубликованных Docker-образов и пути сборки → [`GHCR_IMAGES.md`](./GHCR_IMAGES.md).

```bash
docker pull ghcr.io/kaluginvit/<image>:latest
docker run --rm -it --env-file .env ghcr.io/kaluginvit/<image>:latest
```

---

## Шаблон B: Python без Docker

```bash
git clone https://github.com/kaluginvit/Portfolio.git
cd Portfolio/<путь_до_проекта>
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # если файл есть
python <main_script>.py    # точное имя — в README проекта
```

---

## Шаблон C: Node / Web без Docker

```bash
git clone https://github.com/kaluginvit/Portfolio.git
cd Portfolio/<путь_до_проекта>
npm ci
cp .env.example .env       # если файл есть
npm start                  # или npm run dev / npm run build — см. package.json
```

---

## Карта запусков по флагманам (минимальный smoke)

| Путь | Что запустить |
|------|---------------|
| [`01-data-analytics/fintech-ab-test-credit-offer`](../01-data-analytics/fintech-ab-test-credit-offer/) | `make all` или Quick start из README |
| [`01-data-analytics/superstore-retail-analytics`](../01-data-analytics/superstore-retail-analytics/) | `pip install -r requirements.txt`, открыть HTML-дашборд |
| [`02-automation/leadgen-n8n-system`](../02-automation/leadgen-n8n-system/) | `docker compose up`, UI на `5678`, импорт workflow 01–11 |
| [`02-automation/yandex-google-sync`](../02-automation/yandex-google-sync/) | OAuth по README, потом `python main.py sync` |
| [`02-automation/mortgage-calculator`](../02-automation/mortgage-calculator/) | `python app.py` или `docker run -p 5000:5000 ghcr.io/kaluginvit/mortgage-calculator:latest` |
| [`02-automation/google-sheets-report`](../02-automation/google-sheets-report/) | `pip install -r requirements.txt`, сервисный аккаунт по README, `python report_generator.py` |
| [`03-ai-products/mcp-lesson`](../03-ai-products/mcp-lesson/) | `.env` → `docker compose up` |
| [`03-ai-products/svo-payments-bot`](../03-ai-products/svo-payments-bot/) | `.env` → `docker run` (готовый образ в GHCR) |
| [`04-web/dostaffkin`](../04-web/dostaffkin/) | `docker compose up`, `/health` на `:3000`, статика на `:8080` (или **онлайн-демо**: [kaluginvit72.github.io/dostaffkin](https://kaluginvit72.github.io/dostaffkin/)) |
| [`04-web/postgres-work`](../04-web/postgres-work/) | `docker compose up`, `.env`, `python bot.py` |
| [`04-web/mini-crm-fastapi-react`](../04-web/mini-crm-fastapi-react/) | `docker compose up --build`, в другом терминале `cd frontend && npm install && npm run dev` (см. README) |

Полный список образов и контекстов сборки → [`GHCR_IMAGES.md`](./GHCR_IMAGES.md).

---

## Где живут секреты

В репозитории — **только плейсхолдеры** в `.env.example`. Реальные токены/ключи задаёте сами в `.env` (он в `.gitignore`).

Подробности по каждому проекту — в его `README.md`, раздел «Запуск» / «Setup».

---

## Если что-то не запустилось

1. Проверьте версию Docker / Python / Node (см. требования выше).
2. Убедитесь, что заполнили **все** ключи в `.env` (часть проектов падает с понятной ошибкой при пустых переменных).
3. Откройте `Issues` репозитория или напишите в [Telegram @kaluginvit](https://t.me/kaluginvit) — приложите скрин ошибки и путь проекта.
