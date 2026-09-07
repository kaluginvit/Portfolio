# Stage 1 Git Finalized

> Date: 2026-09-07

## Repo Status

| Repo | Commit | Push | Working Tree | Actions |
| ---- | ------ | ---- | ------------ | ------- |
| Portfolio (root) | `128832e` | ✅ | clean | ✅ all green |

All changes are in the root monorepo. No nested git repositories found.

## Commits Made

| SHA | Message |
|-----|---------|
| `ca6fdd0` | chore(portfolio): finalize stage 1 curation and GitHub presentation |
| `2f42a2d` | ci: fix Docker build failures in build-images matrix |
| `868ec77` | ci: fix mini-crm-backend build context — root + explicit Dockerfile path |
| `128832e` | fix(hr-breaker): repair Docker build — uv editable install requires README.md |

## Actions Status (sha: 128832e)

| Workflow | Status |
|---------|--------|
| Deploy svo-payments-bot | ✅ success |
| CI — fintech-ab-test-credit-offer | ✅ success |
| Deploy Portfolio site (GitHub Pages) | ✅ success |
| Build Docker images (GHCR) — all jobs | ✅ success |

## hr-breaker Root Cause

**Root cause:** `uv sync --frozen --no-dev` в Dockerfile запускался до `COPY src/`, что
заставляло hatchling читать `README.md` (из `pyproject.toml: readme = "README.md"`)
ещё до его копирования в контейнер → `OSError: Readme file does not exist: README.md`.

**Fix:** разбит на два вызова:
1. `uv sync --frozen --no-dev --no-install-project` — устанавливает только зависимости
2. После `COPY src/ README.md` — `uv sync --frozen --no-dev` — устанавливает сам проект

**Changed files:** `03-ai-products/hr-breaker/Dockerfile` (+3 lines)

## Preserved

- M2 upgrades: mini-crm (78%), rf-macro (80%), fedresurs (82%), leadgen (84%)
- Portfolio tiers: Tier A/B/C/D classification committed
- `_Portfolio_back`: not tracked (10 Tier D + 99-archive moved there, deletions committed)
- GitHub cleanup, metadata, licenses: preserved
- Existing SVO production: unchanged

hr-breaker Docker build fixed. Stage 1 fully green.
