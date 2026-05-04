# Сайт-визитка на GitHub Pages

После включения **GitHub Actions** как источника Pages:

- **Сайт-визитка (Astro):** корень проекта Pages, для репозитория `Portfolio` это `https://kaluginvit-svg.github.io/Portfolio/`
- **Superstore dashboard:** `https://kaluginvit-svg.github.io/Portfolio/superstore/`

Сборка и публикация — workflow [`.github/workflows/portfolio-github-pages.yml`](../.github/workflows/portfolio-github-pages.yml) (триггеры: изменения в `site/`, в `superstore-dashboard.html` или в самом workflow).

Файл **`.nojekyll`** в корне артефакта Pages (создаётся шагом workflow) отключает Jekyll, чтобы не отбрасывался каталог `_astro/` со стилями Astro.

## Яндекс.Метрика

Задайте в репозитории **Actions variable** `PUBLIC_YANDEX_METRIKA_ID` (числовой id счётчика). Без переменной счётчик в HTML не вставляется.

Цели `reachGoal` вешаются на элементы с атрибутом `data-ym-goal` (клик по ссылке).

## Локальная разработка

См. [`site/README.md`](../site/README.md).

## Кастомный домен

В `site/astro.config.mjs` обновите `site` и при необходимости `base` (для корня домена часто `base: '/'`).
