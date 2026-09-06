"""
Print a console quality report for normalized coding_community links.

Run:
    uv run python chat_summaries/coding_community/link_quality_report.py
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = Path(__file__).parent / "messages.db"
RESOURCE_KINDS = (
    "github_repo",
    "github",
    "huggingface",
    "arxiv",
    "arxiv_other",
    "video",
    "telegram_channel",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to messages.db")
    parser.add_argument("--limit", type=int, default=20, help="Rows per sample section")
    return parser.parse_args()


def print_rows(title: str, rows) -> None:
    print(f"\n{title}")
    for row in rows:
        print(dict(row))


def main() -> None:
    args = parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    try:
        print_rows(
            "Summary",
            con.execute(
                """
                SELECT
                    COUNT(*) AS raw_links,
                    SUM(is_valid) AS valid_links,
                    SUM(CASE WHEN is_valid = 1 AND is_filtered = 1 THEN 1 ELSE 0 END)
                        AS filtered_valid_links,
                    COUNT(DISTINCT CASE WHEN is_valid = 1 THEN url_normalized END)
                        AS unique_valid_urls
                FROM message_links
                """
            ).fetchall(),
        )
        print_rows(
            "Reject reasons",
            con.execute(
                """
                SELECT reject_reason, COUNT(*) AS count, SUM(is_filtered) AS filtered_count
                FROM message_links
                WHERE is_valid = 0
                GROUP BY reject_reason
                ORDER BY count DESC
                """
            ).fetchall(),
        )
        print_rows(
            "Top filtered domains",
            con.execute(
                """
                SELECT domain, kind, COUNT(*) AS mentions
                FROM message_links
                WHERE is_valid = 1 AND is_filtered = 1
                GROUP BY domain, kind
                ORDER BY mentions DESC
                LIMIT ?
                """,
                (args.limit,),
            ).fetchall(),
        )
        print_rows(
            "Top resource URLs",
            con.execute(
                f"""
                SELECT url_normalized, kind, mentions, filtered_mentions
                FROM links_catalog
                WHERE kind IN ({",".join("?" for _ in RESOURCE_KINDS)})
                  AND filtered_mentions > 0
                ORDER BY filtered_mentions DESC, mentions DESC, url_normalized
                LIMIT ?
                """,
                (*RESOURCE_KINDS, args.limit),
            ).fetchall(),
        )
        print_rows(
            "Resource URLs by kind",
            con.execute(
                f"""
                SELECT kind, COUNT(*) AS unique_urls, SUM(filtered_mentions) AS mentions
                FROM links_catalog
                WHERE kind IN ({",".join("?" for _ in RESOURCE_KINDS)})
                  AND filtered_mentions > 0
                GROUP BY kind
                ORDER BY mentions DESC
                """,
                RESOURCE_KINDS,
            ).fetchall(),
        )
        print_rows(
            "Resource URLs by section",
            con.execute(
                f"""
                SELECT
                    section_id,
                    section_name,
                    COUNT(*) AS unique_urls,
                    SUM(filtered_mentions) AS mentions,
                    MAX(score) AS top_score
                FROM links_catalog
                WHERE kind IN ({",".join("?" for _ in RESOURCE_KINDS)})
                  AND filtered_mentions > 0
                GROUP BY section_id, section_name
                ORDER BY section_id
                """,
                RESOURCE_KINDS,
            ).fetchall(),
        )
        print_rows(
            "Enrichment status",
            con.execute(
                """
                SELECT enrich_status, COUNT(*) AS unique_urls
                FROM links_catalog
                WHERE filtered_mentions > 0
                GROUP BY enrich_status
                ORDER BY unique_urls DESC
                """
            ).fetchall(),
        )
        print_rows(
            "Rejected samples",
            con.execute(
                """
                SELECT reject_reason, url_original
                FROM message_links
                WHERE is_valid = 0
                ORDER BY reject_reason, link_id
                LIMIT ?
                """,
                (args.limit,),
            ).fetchall(),
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
