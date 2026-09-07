# Stage 2B — finance-data-screener Pages Demo

> Date: 2026-09-07

## Status

| Project | Commit | Pages URL | Actions | Live Check |
|---------|--------|-----------|---------|------------|
| finance-data-screener | `ac94ebe` | https://kaluginvit.github.io/Portfolio/finance-data-screener/ | ✅ success | ✅ 200 OK |

## Changed Files

| File | Change |
|------|--------|
| `frontend/src/api/fixtures.ts` | NEW — fixture data: 10 CBR currencies + 10 MOEX stocks, audit log, 5 query responses |
| `frontend/src/api/client.ts` | Add `export const DEMO_MODE` (compile-time Vite env var) |
| `frontend/src/api/datasets.ts` | All API functions branch on DEMO_MODE: fixtures for reads, friendly error for writes |
| `frontend/src/components/DemoModeBanner.tsx` | NEW — green banner visible when DEMO_MODE=true |
| `frontend/src/components/Layout.tsx` | Render DemoModeBanner when DEMO_MODE |
| `frontend/src/pages/QueryPage.tsx` | Add 5 example query chips in demo mode |
| `frontend/src/App.tsx` | BrowserRouter → HashRouter (fixes GitHub Pages subpath navigation) |
| `frontend/vite.config.ts` | Add `base: process.env.VITE_BASE ?? "/"` |
| `.github/workflows/portfolio-github-pages.yml` | Add screener build step (VITE_DEMO_MODE=true, VITE_BASE=…) + copy dist/ |
| `04-web/finance-data-screener/README.md` | Add Live Demo URL line |

## Demo Mode

**Activation:** `VITE_DEMO_MODE=true` at build time (compile-time constant, dead code eliminated by Vite).

**Read operations** — return pre-loaded fixtures (no HTTP):
- `getDatasets()` → 2 demo datasets: "Курсы ЦБ РФ" (cbr, 10 records), "Акции MOEX — Топ-10" (moex, 10 records)
- `getRecords("demo-cbr")` → 10 CBR currency rates (USD, EUR, CNY, GBP, JPY, CHF, HKD, KZT, BYR, TRY)
- `getRecords("demo-moex")` → 10 MOEX stocks (SBER, GAZP, LKOH, YNDX, ROSN, NVTK, GMKN, POLY, MAGN, CHMF)
- `getAudit()` → 4 pre-loaded audit entries
- `queryDataset()` → keyword-matched precomputed answers; 5 known patterns; fallback to friendly review message

**Write operations** — return friendly error:
- `createDataset()` → `"Demo Mode — запись недоступна. Данные предзагружены."`
- `collectDataset()` → same message
- `planAndCollect()` → returns demo plan (non-destructive, shows architecture)

**UI indicators:**
- Green "Demo Mode" banner in header
- 5 example query chips in Query page

**Normal mode** (no VITE_DEMO_MODE): unchanged — all real API calls via axios to `/api`.

## Fixtures

Source: Public financial data (MOEX ISS API public fields, CBR public exchange rates). No private data, no API keys.

## Pages Build

Workflow step:
```yaml
- name: Build finance-data-screener demo
  working-directory: 04-web/finance-data-screener/frontend
  env:
    VITE_DEMO_MODE: "true"
    VITE_BASE: "/Portfolio/finance-data-screener/"
  run: |
    npm ci
    npx vite build
```

Then: `cp -r "04-web/finance-data-screener/frontend/dist/." _site/finance-data-screener/`

## Live Check

| URL | Status | Size |
|-----|--------|------|
| `/Portfolio/finance-data-screener/` | ✅ 200 | index.html |
| `/Portfolio/finance-data-screener/assets/index-JiNXrBBC.js` | ✅ 200 | 672 KB |
| `/Portfolio/finance-data-screener/assets/index-AJtsdVKF.css` | ✅ 200 | 17 KB |

## Limitations

- Bundle size: 672 KB (minified), 204 KB gzipped — recharts is heavy; acceptable for demo
- Navigation uses hash routing (`/#/datasets`) — cosmetic difference from production BrowserRouter
- Write flows (Create dataset, Collect) show error message instead of demo animation
- QueryPage precomputed answers cover 5 keyword patterns; other questions return review message

Stage 2B complete. finance-data-screener demo is live and verified.
