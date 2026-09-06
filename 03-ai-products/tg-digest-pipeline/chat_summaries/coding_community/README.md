# coding_community

Digest pipeline for AI development and automation chats.

Configured sources are collected into the same database:

- `coding_community` from `vibecoding_community` (~130 800 raw messages)
- `n8n_community` (~34 000 raw messages)

Session: `session2`

**Current state (Aug 2026):** 164 861 raw messages, 17 790 filtered (10%),
2 228 URLs in catalog, 820 enriched resources across 11 sections.

## Pipeline

```text
collect.py
  -> refresh_ui_catalog.py (filter + rebuild_links + enrich offline)
       -> filter.py            messages_filtered
       -> rebuild_links.py     message_links, links_catalog
       -> enrich_links.py      URL titles/descriptions/context
  -> enrich_links.py --online  external metadata (GitHub, HF, arXiv, HTML)
  -> resources_catalog.py      output/resources_catalog.md
  -> analyze_insights.py       output/insights_8w.md

Diagnostics: status.py, link_quality_report.py
```

## Collection

```powershell
uv run python chat_summaries/collect.py coding_community
uv run python chat_summaries/collect.py n8n_community
```

## Filtering And Links

```powershell
uv run python chat_summaries/coding_community/refresh_ui_catalog.py
uv run python chat_summaries/coding_community/filter.py
uv run python chat_summaries/coding_community/rebuild_links.py
```

## Diagnostics

```powershell
uv run python chat_summaries/coding_community/status.py
uv run python chat_summaries/coding_community/link_quality_report.py
```

## Enrichment And Exports

```powershell
uv run python chat_summaries/coding_community/enrich_links.py --offline --limit 100
uv run python chat_summaries/coding_community/enrich_links.py --online --limit 0
uv run python chat_summaries/coding_community/export_link_sections.py
uv run python chat_summaries/coding_community/resources_catalog.py
```

`enrich_links.py --offline` uses only local message context. `--online` enables
network requests to linked services (GitHub, HuggingFace, arXiv, HTML pages).

## Insights Analysis

```powershell
uv run python chat_summaries/coding_community/analyze_insights.py
uv run python chat_summaries/coding_community/analyze_insights.py --since 2026-07-01 --until 2026-08-31
```

Analyzes filtered messages via MiniMax M3 (OpenRouter, free tier, 1M context).
Produces a structured Markdown report covering top topics, tools, pain points,
trends, and community insights. Output: `output/insights_8w.md`.

Before overwriting, the previous report is automatically archived as
`output/insights_YYYY-MM-DD.md` (date taken from the report header). Run every
7–10 days to maintain a rolling archive.

## Files

- `messages.db` stores raw collected messages and `messages_filtered`.
- `refresh_ui_catalog.py` is the canonical local refresh for the dashboard UI.
  It rebuilds `messages_filtered`, `message_links`, `links_catalog`, and fills
  pending URL titles/descriptions/context with offline local context by default.
- `filter.py` selects AI/dev/automation/business-relevant messages.
- `rebuild_links.py` rebuilds normalized link tables from `messages.links`.
- `link_quality_report.py` prints link quality, domain, reject, and resource stats.
- `enrich_links.py` enriches URL descriptions from local message context by default; `--online` enables external metadata fetches.
- `export_link_sections.py` exports normalized resource URLs grouped by 11 sections.
- `status.py` prints read-only database, source, link, enrichment, week, and output status.
- `resources_catalog.py` extracts GitHub, HuggingFace, arXiv, video, and Telegram-channel resources. Translates descriptions via Claude Haiku.
- `analyze_insights.py` analyzes filtered message texts via MiniMax M3 and produces a structured insights report.
- `output/` stores generated exports: `resources_catalog.md` (820 resources), `insights_8w.md` (8-week analysis).

`messages.db` is a local working database, not source code. It is ignored by the
root `.gitignore`.

## Resource Catalogs

`links_catalog` is the primary normalized resource catalog. It is built by
`rebuild_links.py`, enriched by `enrich_links.py`, inspected by
`link_quality_report.py`, exported by `export_link_sections.py`, and consumed by
the combined insights dashboard.

The catalog contains 2 228 URLs across 11 sections. Enrichment status (URLs with
`filtered_mentions > 0`): ~70% ok, ~14% offline_context, ~9% skipped (Telegram
posts and social links), ~6% fetch_failed, ~1% no_metadata.

`resources_catalog.py` is a separate export pipeline for GitHub, HuggingFace,
arXiv, video, and Telegram-channel resources. It reads from `links_catalog`,
translates descriptions via Claude Haiku, and generates `output/resources_catalog.md`.

## Link Tables

`messages.links` is kept as the raw Telegram extraction field. Run
`rebuild_links.py` to derive normalized tables:

- `sources` summarizes message/link counts by `source_peer_id`.
- `message_links` stores one row per extracted link with normalized URL, domain,
  kind, validity, reject reason, and `is_filtered`.
- `links_catalog` stores one row per unique normalized URL with mention counts,
  filtered-message counts, generated title/description, section, and score.
