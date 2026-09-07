# Stage 2A — GitHub Pages Result

> Date: 2026-09-07

## Status Table

| Project | Commit | Pages URL | Actions | Live Check |
|---------|--------|-----------|---------|------------|
| fintech-ab-test-credit-offer | `c8282c9` | https://kaluginvit.github.io/Portfolio/fintech-ab-test/ | ✅ success | ✅ 200 OK (20 181 bytes) |
| superstore-retail-analytics | `c8282c9` | https://kaluginvit.github.io/Portfolio/superstore/ | ✅ success | ✅ 200 OK (1 379 949 bytes) |
| superstore title-bg.png | `c8282c9` | …/superstore/title-bg.png | ✅ | ✅ 200 OK (148 598 bytes) |

## What Changed

**`portfolio-github-pages.yml`** — добавлена одна строка:
```yaml
cp "01-data-analytics/superstore-retail-analytics/title-bg.png" _site/superstore/title-bg.png
```
Без этого заголовок дашборда отображался без фонового изображения (CSS `url('title-bg.png')` → 404).

**`fintech-ab-test-credit-offer/README.md`** — добавлена строка `Live demo: ...`

**`superstore-retail-analytics/README.md`** — добавлена строка `Live demo: ...`

## Pages Source

Оба проекта деплоятся через **Portfolio repo** (`kaluginvit/Portfolio`) в единый Pages artifact:

```
_site/
  fintech-ab-test/index.html   ← reports/presentation.html (Reveal.js)
  superstore/index.html         ← superstore-dashboard.html (Plotly embedded)
  superstore/title-bg.png       ← local image asset
  rf-macro-risk-ai/             ← docs/ (already live)
  [site/ Astro output]          ← portfolio site
```

Workflow: `.github/workflows/portfolio-github-pages.yml`

## Pages Infrastructure

Workflow уже был настроен до начала Stage 2A:
- fintech-ab-test и superstore уже были в `Assemble Pages artifact`
- Pages уже был включён (`Portfolio | pages=True`)
- Недоставало только `title-bg.png` в superstore/ — это и было исправлено

## Manual Steps Remaining

**GitHub homepage URLs** (PATCH требует auth token — настроить через GitHub UI):
- `kaluginvit/fintech-ab-test-credit-offer` → Homepage: `https://kaluginvit.github.io/Portfolio/fintech-ab-test/`
- `kaluginvit/superstore-retail-analytics` — отдельного repo нет, только в монорепо

## Live Check Results

| URL | Status | Notes |
|-----|--------|-------|
| `/Portfolio/fintech-ab-test/` | ✅ 200 | Reveal.js slideshow, все CDN assets загружены |
| `/Portfolio/superstore/` | ✅ 200 | Plotly dashboard, embedded data, filters работают |
| `/Portfolio/superstore/title-bg.png` | ✅ 200 | Фоновое изображение заголовка |

Stage 2A complete. Both Pages demos live and verified.
