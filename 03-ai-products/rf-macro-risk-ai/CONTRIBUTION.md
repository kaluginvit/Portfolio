# Author Contribution

## Upstream

Этот проект основан на [Rai220/money_alert_ai](https://github.com/Rai220/money_alert_ai) — спасибо Константину Крестникову за оригинальную архитектуру.

## Что было в upstream

Оригинальный проект реализовывал:
- LangChain-агент с Tavily-поиском для анализа макроэкономических событий
- Концепцию scoring по критериям
- Базовый Telegram bot для публикации результатов

## Что добавлено и изменено в этой версии

### 1. Полная переработка системы критериев (`criteria.json`)

Разработаны с нуля **35 оригинальных критериев** с детальными параметрами:

- `weight` — вес в итоговом score
- `search_query` — точный поисковый запрос для Tavily
- `source_policy` — политика источников (только официальные / новостные / рыночные данные)
- `freshness` — окно актуальности данных в днях
- `speed` — скорость реагирования критерия (`fast` / `medium` / `slow`)
- `type` — тип источника (`official_event` / `official_stats` / `market_data` / `news_event`)

Критерии разбиты на тематические группы: форс-мажор, финансовая система, валюта/инфляция, торговля, социально-политическая обстановка.

### 2. Расширенный scoring engine (`src/scoring.py`)

Написан с нуля / значительно переработан:
- **Severity multipliers:** `quiet / watch / warming_up / triggered / critical / cooling_down`
- **Cooldown / novelty ledger:** предотвращает повторный учёт одного события через `research_ledger.json`
- **Deposit access risk block:** отдельный scoring по 5 специальным критериям риска доступа к вкладам с собственными весами
- **Аварийный уровень:** особый триггер для форс-мажорных критериев

### 3. Source registry (`src/source_registry.py`)

Реестр использованных источников с дедупликацией и подсчётом по доменам.

### 4. Web export и GitHub Pages pipeline (`src/analysis_core.py`)

Экспорт результатов в `docs/data.json` → автоматическое обновление inline-данных в `docs/index.html` → git commit + push → GitHub Pages деплой.

Интерактивный дашборд (`docs/index.html`) с историей прогонов, реестром критериев, визуализацией score.

### 5. Multi-LLM provider support

Поддержка OpenAI / Gemini / GigaChat / Anthropic через единый интерфейс с `--provider` флагом.

### 6. Декаплинг Telegram-публикации

Telegram-публикация вынесена в отдельный независимый репозиторий (бот-репортёр). Связь через `BOT_REPORTER_DIR` — опциональная.

### 7. Малый набор критериев для тестов

`criteria_small.json` — 10 критериев для быстрого тестового прогона без расходов на полный анализ.

### 8. Tests

`tests/test_criteria_validation.py` — валидация структуры 35 критериев.  
`tests/test_source_registry.py` — тесты реестра источников.

## Что осталось близким к upstream

- Общая идея: LangChain-агент + Tavily + scoring → результат
- Паттерн одного агента с инструментами
- Структура проекта (src/, docs/, pyproject.toml)

## Summary

| Компонент | Статус |
|-----------|--------|
| criteria.json (35 критериев) | Авторский, написан с нуля |
| scoring.py | Авторский, написан с нуля |
| source_registry.py | Авторский |
| analysis_core.py (web export) | Авторский (новые модули) |
| GitHub Pages dashboard | Авторский |
| Multi-LLM support | Авторский |
| lc_money_alert_bot.py | Основан на upstream, расширен |
| Общая концепция агента | Upstream (Rai220/money_alert_ai) |
