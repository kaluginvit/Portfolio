# Stage 2E — Mini CRM Static Demo Result

## Summary

Frontend-only GitHub Pages demo for `mini-crm-fastapi-react` added.
No FastAPI runtime, no Google OAuth, no external API calls.
Synthetic data lives in browser memory; resets on page reload.

## Changed Files

| File | Change |
|------|--------|
| `frontend/src/api/demoAdapter.ts` | New — in-memory CRUD mock (10 clients, 10 deals, 10 tasks) |
| `frontend/src/api/client.ts` | +IS_DEMO guard: exports real axios OR mockApi based on VITE_DEMO_MODE |
| `frontend/src/App.tsx` | createHashRouter when IS_DEMO (GitHub Pages subpath routing) |
| `frontend/src/layout/AppLayout.tsx` | Demo Mode banner + title suffix when IS_DEMO |
| `frontend/vite.config.ts` | +base: process.env.VITE_BASE ?? '/' |
| `frontend/package-lock.json` | Updated (npm install to sync lock file) |
| `.github/workflows/portfolio-github-pages.yml` | +build step + cache path + assemble copy |
| `README.md` | +Live Demo URL + one-liner about synthetic demo |

## Mock API / Data Approach

Single adapter file `demoAdapter.ts` — all demo logic in one place, zero `if demo` in components.

- `client.ts` exports `api: AxiosInstance` — real axios in prod, `mockApi as unknown as AxiosInstance` in demo
- Pages unchanged: import `api` from `'../api/client'` as before
- `demoGet/demoPost/demoPatch/demoPut/demoDelete` parse URL and dispatch to in-memory arrays
- Google OAuth (`/auth/google/url`) and report exports throw `Error('Demo Mode — Google integration disabled.')`
- Settings page (`/settings/google`) returns safe defaults; save is silently accepted
- All mutations (create/update/delete) stored in module-level arrays — survive navigation, reset on reload

## Synthetic Seed Data

| Entity | Count | Coverage |
|--------|-------|----------|
| Clients | 10 | 8 active, 2 archived; full fields with email/phone/company |
| Deals | 10 | all 5 stages (lead/qualified/proposal/won/lost) |
| Tasks | 10 | all 3 priorities; 2 done, 8 pending; linked to clients & deals |

## Pages URL

**https://kaluginvit.github.io/Portfolio/mini-crm-fastapi-react/**

## Actions Status

Checked after push — completed / success on commit SHA.

## Demo Limitations

- No backend: FastAPI not running; all data is synthetic in-memory JavaScript arrays.
- No persistence: changes (create/edit/delete) reset on page reload.
- No Google integration: OAuth flow and report export show "Demo Mode — Google integration disabled."
- No real credentials, API keys, or client data used.
- VITE_DEMO_MODE=true is baked at build time — no runtime toggle.
