# Stage 2C — Fedresurs MVP Static Demo Result

## Summary

Static GitHub Pages demo for `fedresurs-mvp` added.
No Flask, no live API, no LLM, no backend. Fully self-contained HTML.

## Changed Files

| File | Change |
|------|--------|
| `01-data-analytics/fedresurs-mvp/demo/index.html` | New — static demo page (31 KB, self-contained) |
| `.github/workflows/portfolio-github-pages.yml` | +2 lines: mkdir + cp for fedresurs-mvp |
| `01-data-analytics/fedresurs-mvp/README.md` | +5 lines: Live Demo URL + note |

## Demo Source Data

- **Origin:** `demo_seed.py` → 5 synthetic lots (DEMO-001 … DEMO-005)
- **Valuations:** Precomputed and embedded in HTML `<script>` block as JSON
- **Engines simulated:**
  - Statistical (DEMO-001, DEMO-004): P25/P50/P75 per sq.m → market_min/mid/max → target_price = market_min × 0.90
  - LLM-agent (DEMO-002, DEMO-003, DEMO-005): analogue price range + 4 price scenarios

## Precomputed Valuation Summary

| Lot | Asset | Start Price | Decision |
|-----|-------|------------|----------|
| DEMO-001 | Квартира 54м², Екатеринбург | 3 500 000 ₽ | ✅ auction_interesting |
| DEMO-002 | МАЗ-6430, 2015г | 1 200 000 ₽ | ⚡ public_offer_price_reached |
| DEMO-003 | Станок ГФ2171, 1989г | 450 000 ₽ | ❌ overpriced_skip |
| DEMO-004 | Нежилое 120м², Москва | 8 900 000 ₽ | ✅ auction_interesting |
| DEMO-005 | Дебиторка 3.2М | 320 000 ₽ | ⚡ public_offer_price_reached |

## Pages URL

**https://kaluginvit.github.io/Portfolio/fedresurs-mvp/**

## Tests

`python -m pytest tests/test_lot_source.py -v` — 17 passed, 0 failed

## Demo Limitations

- All lots are synthetic (demo_seed.py). No real Fedresurs data.
- Valuations are precomputed static estimates, not live LLM/search results.
- No search, no live market data, no API calls of any kind.
- `demo/index.html` is a standalone file — no build step, no npm, no dependencies.
