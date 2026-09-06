# SEO Crew — мультиагентный анализ страниц

CrewAI-система для SEO-анализа веб-страниц: парсинг → анализ → рекомендации.

## Быстрый старт

1. **Создать venv:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Настроить `.env`:**
   ```env
   OPENAI_API_KEY=ваш_ключ_proxyapi
   OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
   OPENAI_MODEL_NAME=gpt-4o
   ```

3. **Запустить (CLI):**
   ```bash
   python seo_crew.py https://example.com
   ```

   **Или запустить веб-API с фронтендом:**
   ```bash
   python api.py
   ```
   Затем откройте:
   - **Веб-интерфейс:** http://localhost:8001 (введите URL и получите результат)
   - **API документация:** http://localhost:8001/docs

   **Или запустить в Docker:**
   ```bash
   docker-compose up --build
   ```
   Затем откройте: http://localhost:8001/docs

## Где смотреть результаты

После выполнения результаты сохраняются в:

- **`results/seo_<url>_<timestamp>.txt`** — итоговый отчёт (текст)
- **`logs/seo_crew_output.log`** — логи выполнения Crew (детали шагов)

Папки создаются автоматически. Файлы можно открыть в любом текстовом редакторе.

## Веб-интерфейс

После запуска `python api.py` откройте в браузере:

**http://localhost:8001**

На странице вы сможете:
1. Ввести URL страницы для анализа
2. Выбрать, сохранять ли результат в файл
3. Нажать "Запустить анализ"
4. Получить результат прямо на странице

## Веб-API

После запуска `python api.py` доступны endpoints:

- **GET /** — веб-интерфейс (HTML форма)
- **GET /health** — проверка статуса
- **POST /analyze** — запустить SEO-анализ (JSON ответ)
- **POST /analyze/text** — запустить SEO-анализ (текстовый ответ)

Интерактивная документация: http://localhost:8001/docs

Пример запроса через curl:
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Docker

Проект можно запустить в Docker-контейнере:

```bash
# Собрать и запустить
docker-compose up --build

# Или только собрать образ
docker build -t seo-crew-api .

# Запустить контейнер вручную
docker run -p 8001:8001 --env-file .env seo-crew-api
```

**Важно:** Убедитесь, что файл `.env` существует и содержит все необходимые переменные окружения.

Результаты и логи будут сохраняться в папках `results/` и `logs/` на хосте (благодаря volume mounts).

## Структура проекта

- `agents.py` — агенты (Reader, Analyst, Core Engineer)
- `tasks/` — задачи (task_parse, task_analyze, task_recommend)
- `seo_crew.py` — сборка Crew и запуск (CLI)
- `api.py` — FastAPI веб-сервер
- `static/index.html` — веб-интерфейс для ввода URL и отображения результатов
- `Dockerfile` — конфигурация Docker-образа
- `docker-compose.yml` — конфигурация для docker-compose
- `.env` — ключи ProxyAPI (не коммитится)

