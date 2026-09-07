# GitHub-Only Deployment Plan

> Created: 2026-09-07
> Infrastructure: GitHub Pages + GitHub Actions only. No VPS, no Vercel, no external hosting.

---

## Main Table

| Project | Tier | GitHub Format | Pages | Demo Type | Changes Needed | Effort | Portfolio Value | Priority |
|---------|------|--------------|-------|-----------|---------------|--------|-----------------|----------|
| SVO System | A | LIVE | ✅ already live | production site | none | — | HIGH | already done |
| fintech-ab-test-credit-offer | A | LIVE GITHUB PAGES | ✅ ready | Reveal.js presentation | enable Pages + index redirect | XS | HIGH | **P0** |
| superstore-retail-analytics | B | LIVE GITHUB PAGES | ✅ ready | interactive Plotly dashboard | enable Pages + check `title-bg.png` path | XS | HIGH | **P0** |
| finance-data-screener | A | INTERACTIVE FRONTEND DEMO | 🔧 build needed | React + preloaded JSON fixtures | mock API interceptor + fixture JSON | M | HIGH | **P1** |
| hr-breaker | A | STATIC DEMO | 🔧 create needed | pipeline walkthrough page | create static HTML with precomputed result | M | HIGH | **P1** |
| fedresurs-mvp | A | GENERATED REPORT | 🔧 regenerate | static dashboard (no live calls) | modify generation script to embed data | M | MEDIUM | **P2** |
| mini-crm-fastapi-react | B | INTERACTIVE FRONTEND DEMO | 🔧 build needed | React + seeded mock data | mock API + seed data | M | MEDIUM | **P2** |
| leadgen-n8n-system | A | STATIC DEMO | 🔧 create needed | architecture + workflow diagrams | create static architecture HTML | S | MEDIUM | **P2** |
| rf-macro-risk-ai | B | LIVE GITHUB PAGES | ✅ already live | scoring dashboard + data.json | none | — | HIGH | already done |
| finance-mcp-server | A | GITHUB ONLY | ❌ no | example prompts + screenshots | static showcase page | S | LOW | **P3** |
| hotel-booking-n8n | B | GITHUB ONLY | ❌ no | HTML files call live Supabase/n8n | screenshots only | — | LOW | **P3** |
| team-ai-bot | B | GITHUB ONLY | ❌ no | Telegram bot, no frontend | README + architecture.png | — | LOW | **P3** |

---

## Already Live

### SVO System (Tier A)
- **Status:** production at svorazbor.ru
- **What:** svo-payouts-website + svo-payments-bot — full e2e deployment
- **Action:** none

### rf-macro-risk-ai (Tier B)
- **Status:** GitHub Pages via `docs/index.html` + `tools/data.json`
- **What:** scoring dashboard reading from data.json (fetched externally)
- **Action:** none

---

## Deploy to GitHub Pages — Ready Now

### fintech-ab-test-credit-offer (Tier A) · P0 · XS

**What exists:** `reports/presentation.html` — self-contained Reveal.js 5.1 slideshow  
**CDN deps only:** fonts.googleapis.com, cdn.jsdelivr.net (Reveal.js, highlight.js)  
**No external data fetches.**

**Pages setup:**
- Enable GitHub Pages on repo
- Source: `docs/` folder OR `reports/` folder
- Optionally add `reports/index.html` redirect

**Also available:** `reports/Credit_of_Day_Optimization.pdf` (linked from presentation)

**Effort:** ~30 min (enable Pages + one redirect file)

---

### superstore-retail-analytics (Tier B) · P0 · XS

**What exists:** `superstore-dashboard.html` — self-contained interactive Plotly dashboard  
**Data:** fully embedded in HTML (no external fetches)  
**CDN deps only:** `https://cdn.plot.ly/plotly-2.27.0.min.js`  
**Local asset:** `title-bg.png` used as CSS background — must be in same directory

**Pages setup:**
- Enable GitHub Pages on repo
- Source: root `/`
- Rename/symlink `superstore-dashboard.html` → `index.html` OR add minimal `index.html` redirect
- Ensure `title-bg.png` is at repo root (already is)

**Also available:** `superstore_presentation.html` (secondary page, 593 lines, also self-contained)

**Effort:** ~20 min (enable Pages + add index redirect)

---

## Static Demo Candidates

### finance-data-screener (Tier A) · P1 · M

**What exists:** React + Vite SPA (`frontend/src/`)  
**Pages:** `DatasetsPage`, `CollectPage`, `ShowcasePage`, `AuditPage`, `SourcesPage`, `QueryPage`  
**API pattern:** `axios.create({ baseURL: "/api" })` — all calls to FastAPI backend

**Why Pages isn't trivial:**  
All pages call real backend endpoints (`/api/datasets`, `/api/ai/plan_and_collect`, etc.).  
`ShowcasePage` also calls `getDatasets()` + `getRecords()` — no built-in mock mode.

**Demo approach:**
1. Add `VITE_DEMO_MODE=true` env var
2. In `api/client.ts` — add axios interceptor that returns preloaded JSON when demo mode active
3. Fixture JSON files: CBR currency rates, MOEX stock data, 1-2 pre-collected datasets
4. Disable write operations in demo mode (show toast "Demo mode — write disabled")
5. `vite.config.ts`: add `base: "/<repo-name>/"` for GitHub Pages path
6. GitHub Actions: `npm run build` → deploy `dist/` to Pages

**Data for fixtures:** `tests_data/` already has sample data — check content

**Effort:** M (2–4h for mock interceptor + fixtures + vite base config + workflow)

---

### hr-breaker (Tier A) · P1 · M

**What exists:**
- `src/hr_breaker/static/index.html` — 746-line FastAPI-served web UI (calls `/api/*` endpoints)
- `sample-data/resume.txt` + `job-description.txt` — real sample inputs  
- `templates/resume.html` + `resume_wrapper.html` — Jinja2 PDF templates  
- Pipeline: upload vacancy → analyze resume → score → generate PDF

**Why Pages isn't trivial:**  
The static/index.html is a frontend that calls live FastAPI endpoints for all operations.

**Demo approach — static pipeline walkthrough:**  
Create a standalone `docs/index.html` that shows the full pipeline as a story:
1. Section: "The Problem" — job description (show sample text)
2. Section: "Resume Input" — show resume.txt content
3. Section: "AI Analysis Stages" — illustrated step-by-step pipeline diagram
4. Section: "Scoring Result" — precomputed score cards, match % per criterion
5. Section: "Output" — static version of the PDF result (rendered HTML from template)

**All content is static — no LLM calls at demo time.**  
Run the pipeline once locally with the sample data → capture output → bake into static HTML.

**Effort:** M (3–5h: run pipeline locally, capture output, build walkthrough page)

---

### fedresurs-mvp (Tier A) · P2 · M

**What exists:**  
- `reports/dashboard.html` — 67K-line HTML, but fetches `http://localhost:5000/valuate` — NOT self-contained
- `demo_seed.py` — 5 synthetic lots with pre-defined parameters
- `lot_source.py` — `DemoSource` with synthetic data + precomputed P25/P50/P75
- `valuate.py` — valuation engine

**Demo approach — regenerate static version:**
1. Run `python demo_seed.py` + `valuate_batch.py` locally → generate results JSON
2. Modify dashboard generation to embed results directly (no live fetch calls)
3. Export static HTML with all data baked in
4. Deploy to GitHub Pages via `docs/`

**Effort:** M (2–3h to modify generation to output self-contained HTML)

---

### leadgen-n8n-system (Tier A) · P2 · S

**What exists:**
- `n8n-workflows/*.json` — 11 workflow JSON files with full node definitions
- `media/README.md` — likely has screenshots
- `docs/screenshots/` — screenshots directory
- `workflow_utils.py` — Python business logic
- `tests/mock_lead_payload.json` — sample lead data

**Why Pages is possible:**  
No frontend app, but a hand-crafted static page is feasible.

**Demo approach — static architecture page:**
1. Create `docs/index.html`: visual workflow pipeline (SVG or CSS)
2. Show all 11 workflows as cards with descriptions
3. Embed `mock_lead_payload.json` as an example E2E trace
4. Show warmth decay curve (static chart)
5. Link to GitHub repo for full JSON source

**Effort:** S (2–3h to create the static HTML page)

---

## GitHub Only

### finance-mcp-server (Tier A) · P3

**Why Pages won't work:**
- MCP server communicates via stdio, not HTTP
- `product-mcp-ui` is Next.js with `serverActions` — no `output: 'export'` configured
- Adding static export would require significant Next.js config changes + mocking the MCP invocation layer

**Recommendation:** GitHub Only for now. README with screenshots of Claude Desktop integration covers the portfolio need adequately.

**If screenshots are added:** HIGH portfolio value without any deployment work.

---

### hotel-booking-n8n (Tier B) · P3

**Why Pages won't work:**
- `admin-panel.html` — fetches live Supabase (`supabase.kalugin-consulting.ru`) with API keys
- `booking-form.html` — POSTs to live n8n webhook (`n8n.kalugin-consulting.ru`)
- Both depend on live external services that are credentials-controlled

**Recommendation:** GitHub Only. Screenshots of the admin panel and booking flow in README.

---

### team-ai-bot (Tier B) · P3

**Why Pages won't work:** Telegram bot, no web frontend whatsoever.

**Recommendation:** GitHub Only. `architecture.png` + README covers portfolio presentation.

---

## Recommended Implementation Order

### Phase 1 — Zero risk, immediate impact (P0)

```
1. fintech-ab-test-credit-offer   → enable Pages, add index.html redirect
2. superstore-retail-analytics    → enable Pages, add index.html redirect
```

**Result:** 2 live Pages demos. Effort: ~1h total. Zero code changes.

### Phase 2 — Tier A visual demos (P1)

```
3. finance-data-screener          → mock API layer + fixture JSON + GH Pages workflow
4. hr-breaker                     → run pipeline once, build static walkthrough page
```

**Result:** 4 live Pages demos. Effort: ~1–2 days total.

### Phase 3 — Remaining Tier A (P2, if needed)

```
5. fedresurs-mvp                  → regenerate dashboard without live fetch calls
6. leadgen-n8n-system             → create static architecture page
```

**Result:** 6 live Pages demos. Effort: ~1 more day.

---

## Final Recommendations

### 1. Leave as-is
- **SVO System** — production live, don't touch
- **rf-macro-risk-ai** — already on GitHub Pages ✅
- **team-ai-bot** — GitHub Only is correct
- **hotel-booking-n8n** — GitHub Only (depends on live external services)
- **finance-mcp-server** — GitHub Only; screenshots in README cover portfolio need

### 2. Deploy to Pages — existing artifacts
- **fintech-ab-test** — XS, highest ROI, Reveal.js presentation is production-ready
- **superstore-retail-analytics** — XS, interactive dashboard is production-ready

### 3. Static demo
- **hr-breaker** — create a pipeline walkthrough page from one real local run
- **fedresurs-mvp** — regenerate dashboard without live server calls (embed demo_seed results)
- **leadgen-n8n-system** — create architecture page (if screenshots are added first)

### 4. GitHub Only (confirmed)
- **team-ai-bot**, **hotel-booking-n8n**, **finance-mcp-server**

### 5. Top 3 projects for maximum portfolio effect
| # | Project | Why |
|---|---------|-----|
| 1 | **fintech-ab-test-credit-offer** | XS effort, Tier A, Reveal.js presentation is already polished and recruiter-friendly |
| 2 | **finance-data-screener** | M effort, but Tier A full interactive React app — the most visually impressive demo possible |
| 3 | **superstore-retail-analytics** | XS effort, self-contained Plotly dashboard with filters — immediately readable data analytics |

### 6. Minimum changes
- fintech-ab-test: enable Pages + 3-line `index.html` redirect → no code change
- superstore: enable Pages + add `index.html` → no code change
- These two require ZERO modification to existing project code

### 7. Implementation order
1. fintech-ab-test (P0, XS) — 20 min
2. superstore (P0, XS) — 20 min
3. finance-data-screener (P1, M) — full sprint, highest Tier A visual value
4. hr-breaker (P1, M) — full sprint, Tier A, requires one local pipeline run
5. fedresurs-mvp (P2, M) — only if Phases 1–2 done
6. leadgen-n8n-system (P2, S) — architecture page after screenshots

---

*Stage 2 has not started. This is a planning document only — no code changes, no workflows created, no Pages enabled.*
