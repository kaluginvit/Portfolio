# Stage 2D — Leadgen n8n System Static Demo Result

## Summary

Static GitHub Pages architecture demo for `leadgen-n8n-system` added.
No live n8n, no credentials, no outreach, no external API calls.

## Changed Files

| File | Change |
|------|--------|
| `02-automation/leadgen-n8n-system/demo/index.html` | New — static demo page (46 KB, self-contained) |
| `.github/workflows/portfolio-github-pages.yml` | +2 lines: mkdir + cp for leadgen-n8n-system |
| `02-automation/leadgen-n8n-system/README.md` | +5 lines: Live Demo URL + note |

## Demo Structure

4-tab single-page HTML:

| Tab | Content |
|-----|---------|
| **Pipeline** | CSS flowchart of 4 groups (Intake/Decide/Engage/Ops), lead state machine |
| **11 Workflows** | Cards for each workflow: trigger, purpose, output, key nodes |
| **E2E Trace** | Step-by-step mock trace from mock_lead_payload.json through all stages |
| **Engineering Logic** | 6 code-snippet cards: idempotency, warmth decay, consensus, error classification, HITL, shadow mode |

## Demo Source

- **Lead payload:** `tests/mock_lead_payload.json` (Alex Johnson @ Acme Technologies)
- **Precomputed values** (from workflow_utils.py, no live calls):
  - Idempotency key: `e308cb1b5e34d52b`
  - Consensus score: 0.788, divergence 0.07, agreement=True
  - Warmth after day 1: 54 → bucket "warm"
  - Error classifications: CRITICAL/WARNING/INFO examples

## Pages URL

**https://kaluginvit.github.io/Portfolio/leadgen-n8n-system/**

## Tests

No Python logic changed → tests not re-run (per task spec).
Existing tests: `pytest tests/test_workflow_utils.py` — 43 passed (from Stage 1).

## Actions Status

Checked after push — completed / success on commit SHA.

## Demo Limitations

- No real n8n instance connected — all workflow logic is shown for architecture purposes.
- No Slack messages, LinkedIn DMs, emails, or webhooks are triggered.
- No real credentials, API keys, or CRM data.
- `demo/index.html` is a standalone file — no build step, no npm, no external dependencies.
