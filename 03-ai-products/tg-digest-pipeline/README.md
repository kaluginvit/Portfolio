# ИнфоПовод — RAG-пайплайн Telegram-канала

Система глубокого анализа Telegram-канала: от сбора постов до семантического поиска, граф знаний в Neo4j и подготовки данных для файнтюна LLM.

The repository root is an orchestration workspace, not a single package. Most
directories are independent pipelines that share Telegram sessions, `.env`, and
some topic/link configuration.

## Requirements

Install Python dependencies:

```powershell
uv pip install -r requirements.txt
```

Several scripts also call external command-line tools when needed:

- `claude` for summarization and catalog enrichment scripts.
- `yt-dlp` for external video downloads.
- `ffmpeg` for video re-encoding/compression.

Required environment variables live in `.env`:

- `TG_API_ID`
- `TG_API_HASH`
- `PROXYAPI_KEY` for OpenAI-compatible embedding calls
- `PINECONE_API_KEY`

## Directory Map

```text
tg_digest/
  chat_summaries/      Telegram chat collection, filtering, and summaries
  finance/             Finance Telegram folder link and video pipelines
  SavedPages/          Saved Messages collection and digest pipeline
  rag/                 Embedding upload and semantic search over filtered chats
  review_front/        Local review UIs for links
  google_tools_sync/   Google Docs/category sync exports and scripts

  digest_topics.json   Shared topic keyword configuration
  requirements.txt     Python dependencies
  session.session      Main Telethon session, ignored by git
  session2.session     Secondary Telethon session, ignored by git
```

## chat_summaries

`chat_summaries/collect.py` is the shared collector. Sources are configured in
`chat_summaries/chats.json`.

Current aggregate databases:

- `chat_summaries/invest_talks/messages.db`
  - sources: `invest_talks`, `c0ldtalk`
  - scripts: `filter.py`, `summarize_one.py`
- `chat_summaries/coding_community/messages.db`
  - sources: `coding_community`, `n8n_community`
  - scripts: `filter.py`, `rebuild_links.py`, `link_quality_report.py`, `summarize_one.py`, `resources_catalog.py`
- `chat_summaries/pesochnitsa/messages.db`
  - sources: `pesochnitsa`, `pesochnitsa_group`
  - scripts: `analyze.py`, `offers_pipeline.py`

Typical flow:

```powershell
uv run python chat_summaries/collect.py invest_talks
uv run python chat_summaries/collect.py c0ldtalk
uv run python chat_summaries/invest_talks/filter.py
uv run python chat_summaries/invest_talks/summarize_one.py

uv run python chat_summaries/collect.py coding_community
uv run python chat_summaries/collect.py n8n_community
uv run python chat_summaries/coding_community/filter.py
uv run python chat_summaries/coding_community/rebuild_links.py
uv run python chat_summaries/coding_community/link_quality_report.py
uv run python chat_summaries/coding_community/enrich_links.py --offline --limit 100
uv run python chat_summaries/coding_community/export_link_sections.py
uv run python chat_summaries/coding_community/summarize_one.py
```

Collect all configured chats:

```powershell
uv run python chat_summaries/collect.py --all
```

`pesochnitsa/analyze.py` is incremental. It stores per-message processing state
in `message_processing`, deduplicates channel/group copies by text hash, and
only sends messages without a status for the selected `--pipeline-version`.

```powershell
uv run python chat_summaries/pesochnitsa/analyze.py --start 2026-04-20 --end 2026-07-20 --status
uv run python chat_summaries/pesochnitsa/analyze.py --start 2026-04-20 --end 2026-07-20 --dry-run
uv run python chat_summaries/pesochnitsa/analyze.py --start 2026-04-20 --end 2026-07-20
uv run python chat_summaries/pesochnitsa/offers_pipeline.py --build-baseline --start 2026-04-20 --end 2026-07-20
uv run python chat_summaries/pesochnitsa/offers_pipeline.py --process-new --baseline-version 2026-04-20__2026-07-20
```

## finance

Finance pipelines work with the Telegram folder named `Финансы` through
`session2`.

Main scripts:

- `collect_finance_messages.py` collects raw messages into `finance_messages.db`.
- `practical_finance.py` builds normalized practical finance cards in SQLite and exports Markdown/CSV.
- `index_links.py` indexes all URLs, applies domain policy, and exports active/all link catalogs.
- `domain_policy.py` contains keep/suppress/review domain rules.
- `index_video_files.py` indexes downloaded video files and reports download coverage.
- `compress_finance_videos.ps1` compresses downloaded video files.

Important outputs:

- `finance_messages.db`
- `output/practical_finance.md`
- `output/practical_finance.csv`
- `output/practical_finance_stats.json`
- `output/finance_links.csv`
- `output/finance_links_all.csv`
- `output/finance_links_report.json`
- `output/video_files_report.json`
- `output/video_files.csv`
- `output/missing_native_videos.csv`
- `Финансы_видео/`
- `Финансы_ссылки_видео/`

## SavedPages

Collects and processes Telegram Saved Messages from configured sessions.

Typical commands:

```powershell
uv run python SavedPages/collect_saved_messages.py
uv run python SavedPages/categorize_messages.py
uv run python SavedPages/export_links_catalog.py
uv run python SavedPages/build_digest.py
```

Outputs include `saved_messages.db`, `saved_links_12cat.csv`,
`saved_links_12cat.json`, and digest Markdown exports.

## rag

RAG upload/search currently targets filtered aggregate chat databases:

- `chat_summaries/invest_talks/messages.db`
- `chat_summaries/coding_community/messages.db`

Run filters before embedding:

```powershell
uv run python chat_summaries/invest_talks/filter.py
uv run python chat_summaries/coding_community/filter.py
uv run python chat_summaries/coding_community/rebuild_links.py
uv run python rag/embed.py
uv run python rag/search.py "ИИ в финансах"
```

`rag/embedded.db` tracks uploaded message IDs locally.

## review_front

There are two local review tools:

- `review_server.py` reviews links from a Telegram `messages.db`. By default it
  uses `chat_summaries/coding_community/messages.db`. Override with
  `TG_DIGEST_REVIEW_DB`.
- `review_csv.py` reviews rows from `finance/financy_links.csv`.

Run:

```powershell
uv run python review_front/review_server.py
uv run python review_front/review_csv.py
```

## google_tools_sync

Contains Google Docs remapping scripts and exported tool catalog files. The first
Google API run requires local OAuth credentials in that directory and may create
`token.json`.

## Generated Data

The workspace intentionally contains large local artifacts: SQLite databases,
CSV/JSON exports, Telegram session files, and downloaded videos. `.gitignore`
excludes sessions, `.env`, and SQLite databases; downloaded media should be
treated as local data artifacts.
