"""
Export normalized resource URLs grouped by the 11 local sections.

This is a deterministic, no-network export from links_catalog. It does not call
GitHub, HuggingFace, arXiv, or any LLM.

Run:
    uv run python chat_summaries/coding_community/export_link_sections.py
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = Path(__file__).parent / "messages.db"
OUT_PATH = Path(__file__).parent / "output" / "link_sections.md"
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
    parser.add_argument("--out", type=Path, default=OUT_PATH, help="Output Markdown file")
    parser.add_argument("--limit-per-section", type=int, default=0, help="0 means no limit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    try:
        sections = con.execute(
            """
            SELECT section_id, section_name, COUNT(*) AS unique_urls, SUM(filtered_mentions) AS mentions
            FROM links_catalog
            WHERE kind IN ({})
              AND filtered_mentions > 0
              AND enrich_status IN ('ok', 'offline_context')
            GROUP BY section_id, section_name
            ORDER BY section_id
            """.format(",".join("?" for _ in RESOURCE_KINDS)),
            RESOURCE_KINDS,
        ).fetchall()

        parts = [
            "# Link Sections - coding_community",
            "",
            "_Deterministic export from links_catalog. Sorted by score, filtered mentions, URL._",
            "",
        ]

        for section in sections:
            parts.append(
                f"## {section['section_id']}. {section['section_name']} "
                f"({section['unique_urls']} URLs, {section['mentions']} mentions)"
            )
            rows = con.execute(
                """
                SELECT title, description, url_normalized, kind, domain, filtered_mentions, mentions, score
                FROM links_catalog
                WHERE kind IN ({})
                  AND filtered_mentions > 0
                  AND enrich_status IN ('ok', 'offline_context')
                  AND section_id = ?
                ORDER BY score DESC, filtered_mentions DESC, url_normalized
                {}
                """.format(
                    ",".join("?" for _ in RESOURCE_KINDS),
                    "LIMIT ?" if args.limit_per_section > 0 else "",
                ),
                (
                    *RESOURCE_KINDS,
                    section["section_id"],
                    *([args.limit_per_section] if args.limit_per_section > 0 else []),
                ),
            ).fetchall()
            for row in rows:
                parts.append(
                    f"- [{row['title']}]({row['url_normalized']})"
                    f" | {row['kind']} | score={row['score']}"
                    f" | mentions={row['filtered_mentions']}"
                    f" | {row['description']}"
                )
            parts.append("")

        args.out.write_text("\n".join(parts), encoding="utf-8")
        print(f"exported: {args.out}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
