# Stage 2F — HR-Breaker Static Demo Result

## Summary

Static GitHub Pages pipeline demo for `hr-breaker` added.
No live LLM, no FastAPI runtime, no SSE backend.
Shows the full 8-layer filter pipeline on a precomputed sample case.

## Source of Sample Data

- **Resume:** `sample-data/resume.txt` — Alex Johnson (synthetic sample, no real personal data)
- **Job:** `sample-data/job-description.txt` — FinanceApp Senior Backend Engineer

## How Precomputed Result Was Obtained

LLM API keys not available in this environment. Precomputed result was derived by:
1. Manual application of the optimization logic to the sample data (restructure/reorder, no fabrication)
2. Running standalone TF-IDF keyword check to verify keyword score realism
3. Filter scores set to realistic values consistent with the scoring logic in each filter class

The optimized resume content is faithful to the anti-hallucination guarantee:
all experience and skills in the output exist verbatim in the original resume.txt.

## Changed Files

| File | Change |
|------|--------|
| `03-ai-products/hr-breaker/demo/index.html` | New — 4-tab static pipeline demo (31 KB, self-contained) |
| `.github/workflows/portfolio-github-pages.yml` | +2 lines: mkdir + cp for hr-breaker |
| `03-ai-products/hr-breaker/README.md` | +3 lines: Live Demo URL + note |

## Demo Structure

4-tab single-page HTML:

| Tab | Content |
|-----|---------|
| **Overview** | Stats (iter=1, 7/7 filters pass, 1 skipped, ~43s), optimizer changes log, filter score bars |
| **Input** | Original resume.txt + job-description.txt side by side |
| **Pipeline** | 3-phase timeline (Parse/Optimize/Validate) + 8 filter cards with scores and details |
| **Optimized Resume** | Browser-rendered HTML version of the optimized output (Times New Roman, 1-page style) |

## Pages URL

**https://kaluginvit.github.io/Portfolio/hr-breaker/**

## Actions Status

Checked after push — completed / success on commit SHA.

## Live Check

HTTP 200 · JS bundle contains demo content · no localhost/API calls.

## Demo Limitations

- All data is precomputed. No live LLM calls are made.
- Filter scores are representative estimates, not from an actual pipeline run.
- Optimized resume content was manually derived following the anti-hallucination rule (original content only).
- PDF output is not embedded in demo (would require live WeasyPrint render).
- No real personal data used — Alex Johnson is a synthetic sample persona from sample-data/.
