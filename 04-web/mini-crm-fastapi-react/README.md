# Mini CRM

Мини-CRM система: FastAPI + SQLite + интеграция с Google Drive/Sheets (OAuth) + веб-интерфейс на React.

### Публичный репозиторий (портфолио)

Секреты не должны попадать в git: см. **`.gitignore`** и **[`SECURITY.md`](SECURITY.md)**. В репозитории только **шаблоны** с суффиксом `.example` (`google_integration/client_secret.example.json`, `config/google_settings.example.json`). После клона скопируйте их в рабочие файлы и заполните своими данными из Google Cloud; база и токены создаются локально в `data/`.

## Быстрый старт

1. Перейдите в корень этого проекта (где лежат `docker-compose.yml` и `requirements.txt`). В монорепозитории Portfolio путь: `04-web/mini-crm-fastapi-react/`.

2. **Бэкенд — из Docker:**

```powershell
docker compose up --build
```

API: **http://localhost:8000/docs** · Health: **http://localhost:8000/health**  
Код из `./backend` и `./google_integration` смонтирован в контейнер, SQLite — в `./data/crm.db` на хосте.

3. **Фронтенд** (отдельный терминал, на хосте):

```powershell
cd frontend
npm install
npm run dev
```

Откройте `http://localhost:5173` (в `frontend/.env.development` указан `VITE_API_URL=http://localhost:8000` — тот же порт, что у контейнера).

### Бэкенд без Docker (только для отладки)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "."
python start_backend.py
```

При необходимости скопируйте `.env.example` в `.env` (для `DATABASE_URL`, `CORS_ORIGINS` при локальном запуске).

## Google Cloud и OAuth

1. В GCP включите **Google Drive API** и **Google Sheets API**.
2. Создайте учётные данные **OAuth 2.0 Client ID** типа **Web application** (для localhost).
3. Добавьте **Authorized redirect URI**: `http://localhost:8000/auth/google/callback` (совпадает с `backend.config.Settings.google_redirect_uri`, при необходимости задайте через переменную окружения при расширении).
4. Скачанный JSON с client id/secret положите в проект (например `google_integration/client_secret.json`) — файл **не коммитьте**.
5. В OAuth consent screen добавьте свою почту как **Test users**, пока приложение в тестовом режиме.
6. В веб-приложении: **Настройки Google** — укажите путь к JSON и ID родительской папки на Drive (из URL после `folders/`), сохраните, затем «Войти через Google».

Токен OAuth сохраняется в подпапке корня: `data/google_token.pickle` (рядом с SQLite; в `.gitignore`). Путь можно переопределить переменной окружения `GOOGLE_TOKEN_PATH`.

Типичные проблемы: не добавлен redirect URI; аккаунт не в списке тестировчиков; не выбрана правильная папка или нет доступа Drive.

## Заполнение тестовыми данными

С поднятым API:

```powershell
$env:PYTHONPATH="."
python fill_test_data.py
```

Число строк на таблицу: переменная `CRM_SEED_ROWS` (по умолчанию 250). URL API: `CRM_API_URL` (по умолчанию `http://127.0.0.1:8000`).

## Тесты и smoke

```powershell
$env:PYTHONPATH="."
$env:CRM_SKIP_INIT_DB="1"
python -m pytest tests/ -q
```

Скрипт PowerShell для ручной проверки API: `scripts/smoke_curl.ps1`.

Проверка **доступа к Google Drive** (после сохранения настроек и авторизации):

```powershell
$env:PYTHONPATH="."
python scripts/check_google_drive.py
```

## Выгрузка отчётов

На страницах **Клиенты / Сделки / Задачи** кнопка «Выгрузить отчёт» создаёт новую Google Таблицу в указанной папке, заполняет данные и метаданные, возвращает ссылку (можно открыть или скопировать).

## Чек-лист сдачи на платформе (артефакты)

- Скриншоты: Docker или терминалы, интерфейс со списком/фильтром, Swagger или `/health`, настройки Google **без ключа**, успешная выгрузка со ссылкой, открытая таблица.
- Архив или GitHub **без** `client_secret*.json` (реальных), `data/google_token.*`, `config/google_settings.json`, `data/*.db`, `.env`.

Проект содержит `.env.example`, шаблоны `*.example.json` и `.gitignore` для секретов; подробности — в **`SECURITY.md`**.
