"""
Refresh the `links_catalog` data used by the insights dashboard UI.

This is the canonical local pipeline for the coding resources UI:
    1. rebuild `messages_filtered` from raw `messages`
    2. rebuild normalized link tables and `links_catalog`
    3. enrich pending links from local message context by default

Run from the project root:
    uv run python chat_summaries/coding_community/refresh_ui_catalog.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "messages.db"
UI_RESOURCE_KINDS = (
    "github_repo",
    "github",
    "huggingface",
    "arxiv",
    "arxiv_other",
    "video",
    "telegram_channel",
)

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import enrich_links  # noqa: E402
import filter as filter_messages  # noqa: E402
import rebuild_links  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh coding_community links_catalog for the UI.")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to messages.db")
    parser.add_argument("--skip-filter", action="store_true", help="Do not rebuild messages_filtered.")
    parser.add_argument("--skip-rebuild-links", action="store_true", help="Do not rebuild message_links/links_catalog.")
    parser.add_argument("--skip-enrich", action="store_true", help="Do not enrich pending catalog rows.")
    parser.add_argument(
        "--enrich-limit",
        type=int,
        default=0,
        help="Max URLs to enrich; 0 means all pending URLs.",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help="Allow network calls during enrichment. Default is offline local-context enrichment.",
    )
    parser.add_argument("--include-web", action="store_true", help="Also enrich generic web URLs not shown in the UI.")
    parser.add_argument("--force-enrich", action="store_true", help="Refresh already enriched URLs too.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.db != DB_PATH:
        rebuild_links.DB_PATH = args.db
        enrich_links.DB_PATH = args.db

    if not args.skip_filter:
        print("== filter.py: rebuild messages_filtered ==")
        filter_stats = filter_messages.rebuild_filtered(args.db)
        filter_messages.print_stats(filter_stats)

    if not args.skip_rebuild_links:
        print("\n== rebuild_links.py: rebuild links_catalog ==")
        stats = rebuild_links.rebuild(args.db)
        print(json.dumps(stats, ensure_ascii=False, indent=2))

    if not args.skip_enrich:
        print("\n== enrich_links.py: fill UI descriptions/context ==")
        limit = None if args.enrich_limit <= 0 else args.enrich_limit
        kinds = None if args.include_web else list(UI_RESOURCE_KINDS)
        count = enrich_links.enrich_links(
            db_path=args.db,
            kinds=kinds,
            limit=limit,
            force=args.force_enrich,
            offline=not args.online,
            online=args.online,
            sleep=0.0 if not args.online else 0.2,
        )
        print(f"enriched: {count}")

    print("\nDone. The insights dashboard reads coding_community/messages.db -> links_catalog.")


if __name__ == "__main__":
    main()
