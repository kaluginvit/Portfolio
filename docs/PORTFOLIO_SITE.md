# Сайт-визитка на GitHub Pages

После включения **GitHub Actions** как источника Pages:

- **Сайт-визитка (Astro):** корень проекта Pages, для репозитория `Portfolio` это `https://kaluginvit-svg.github.io/Portfolio/`
- **Superstore dashboard:** `https://kaluginvit-svg.github.io/Portfolio/superstore/`

Сборка и публикация — workflow [`.github/workflows/portfolio-github-pages.yml`](../.github/workflows/portfolio-github-pages.yml) (любой push в `main` или **Run workflow** вручную).

Файл **`.nojekyll`** в корне артефакта Pages (создаётся шагом workflow) отключает Jekyll, чтобы не отбрасывался каталог `_astro/` со стилями Astro.

### Если на главной виден длинный текст из «шапки README» (таблицы, ссылки на `/01-data-analytics/` и т.д.)

Значит **источник Pages** сейчас не Actions, а публикация **из ветки** (Jekyll отдаёт README как стартовую страницу). Визитка Astro при этом не показывается.

**Что сделать:**

1. Репозиторий → **Settings** → **Pages** → **Build and deployment** → **Source: GitHub Actions** (не «Deploy from a branch»).
2. **Actions** → **Deploy Portfolio site (GitHub Pages)** → **Run workflow** или дождаться push в `main` после исправления источника.

### Если в логе «YAML Exception» / «Invalid YAML front matter» в `.astro`

Это **не баг Astro**, а признак того, что Pages собирает сайт через **Jekyll из исходников репозитория**, а не публикует готовый артефакт из Actions. Jekyll воспринимает строки `---` в начале файлов Astro как YAML и падает на `interface Props`, `import` и т.д.

**Что сделать:**

1. Репозиторий → **Settings** → **Pages** → **Build and deployment** → **Source: GitHub Actions** (не «Deploy from a branch»).
2. **Actions** → откройте workflow **Deploy Portfolio site (GitHub Pages)** → **Run workflow** или сделайте push в `main`.
3. В корне репозитория лежит [`_config.yml`](../_config.yml) с `exclude: [site]` — подстраховка, чтобы при ошибочном деплое из ветки Jekyll не трогал папку `site/`. Саму витрину это не собирает: для неё всё равно нужен успешный прогон workflow.

## Яндекс.Метрика

Задайте в репозитории **Actions variable** `PUBLIC_YANDEX_METRIKA_ID` (числовой id счётчика). Без переменной счётчик в HTML не вставляется.

Цели `reachGoal` вешаются на элементы с атрибутом `data-ym-goal` (клик по ссылке).

## Локальная разработка

См. [`site/README.md`](../site/README.md).

## Кастомный домен

В `site/astro.config.mjs` обновите `site` и при необходимости `base` (для корня домена часто `base: '/'`).
