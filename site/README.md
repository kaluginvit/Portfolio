# Сайт-визитка (GitHub Pages)

Статический маркетинговый сайт на [Astro](https://astro.build/). Публикуется в корень `https://kaluginvit.github.io/Portfolio/`; дашборд Superstore — по пути `/Portfolio/superstore/`.

## Локально

```bash
cd site
npm install
npm run dev
```

Сборка: `npm run build` → каталог `dist/`.

## Яндекс.Метрика

Создайте `site/.env` (не коммитится):

```bash
PUBLIC_YANDEX_METRIKA_ID=12345678
```

В CI задайте репозиторий **Variable** `PUBLIC_YANDEX_METRIKA_ID` с тем же именем (GitHub Actions передаёт env в `npm run build`).

## Базовый URL

Для кастомного домена измените `site` и `base` в `astro.config.mjs`.
