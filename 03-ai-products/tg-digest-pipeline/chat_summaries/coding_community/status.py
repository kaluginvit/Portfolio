"""
Print read-only status for the coding_community digest pipeline.

Run from the project root:
    uv run python chat_summaries/coding_community/status.py
    uv run python chat_summaries/coding_community/status.py --json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.db import connect_readonly as _connect_ro, has_table, one, all_rows, safe_one, safe_all

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "messages.db"
OUT_DIR = ROOT / "output"


def connect_readonly() -> sqlite3.Connection:
    return _connect_ro(DB_PATH)


KNOWN_SOURCES = {
    1481574785: "n8n_community",
    3061072345: "coding_community / vibecoding_community",
}

STALE_AFTER_HOURS = 24


def collect_status() -> dict:
    if not DB_PATH.exists():
        return {"ok": False, "error": f"missing database: {DB_PATH}"}

    con = connect_readonly()
    try:
        raw = one(con, "SELECT COUNT(*) AS count, MIN(date) AS min_date, MAX(date) AS max_date FROM messages")
        filtered = safe_one(
            con,
            "messages_filtered",
            "SELECT COUNT(*) AS count, MIN(date) AS min_date, MAX(date) AS max_date FROM messages_filtered",
        )
        sources = safe_all(
            con,
            "messages_filtered",
            """
            SELECT
                m.source_peer_id,
                COUNT(*) AS raw_count,
                MIN(m.date) AS raw_min_date,
                MAX(m.date) AS raw_max_date,
                COALESCE(f.filtered_count, 0) AS filtered_count,
                f.filtered_min_date,
                f.filtered_max_date
            FROM messages m
            LEFT JOIN (
                SELECT
                    source_peer_id,
                    COUNT(*) AS filtered_count,
                    MIN(date) AS filtered_min_date,
                    MAX(date) AS filtered_max_date
                FROM messages_filtered
                GROUP BY source_peer_id
            ) f ON f.source_peer_id = m.source_peer_id
            GROUP BY m.source_peer_id
            ORDER BY raw_count DESC
            """,
        )
        if not sources:
            sources = all_rows(
                con,
                """
                SELECT
                    source_peer_id,
                    COUNT(*) AS raw_count,
                    MIN(date) AS raw_min_date,
                    MAX(date) AS raw_max_date
                FROM messages
                GROUP BY source_peer_id
                ORDER BY raw_count DESC
                """,
            )
        for source in sources:
            peer_id = int(source["source_peer_id"])
            source["name"] = KNOWN_SOURCES.get(peer_id, f"source {peer_id}")

        links = safe_one(
            con,
            "message_links",
            """
            SELECT
                COUNT(*) AS raw_links,
                SUM(is_valid) AS valid_links,
                SUM(CASE WHEN is_valid = 1 AND is_filtered = 1 THEN 1 ELSE 0 END) AS filtered_valid_links
            FROM message_links
            """,
        )
        catalog = safe_one(
            con,
            "links_catalog",
            """
            SELECT
                COUNT(*) AS unique_urls,
                SUM(CASE WHEN filtered_mentions > 0 THEN 1 ELSE 0 END) AS filtered_unique_urls
            FROM links_catalog
            """,
        )
        enrichment = safe_all(
            con,
            "links_catalog",
            """
            SELECT enrich_status, COUNT(*) AS unique_urls
            FROM links_catalog
            GROUP BY enrich_status
            ORDER BY unique_urls DESC
            """,
        )
        link_kinds = safe_all(
            con,
            "links_catalog",
            """
            SELECT kind, COUNT(*) AS unique_urls, SUM(filtered_mentions) AS filtered_mentions
            FROM links_catalog
            WHERE filtered_mentions > 0
            GROUP BY kind
            ORDER BY unique_urls DESC
            """,
        )
    finally:
        con.close()

    output = {
        "dir": str(OUT_DIR),
        "exists": OUT_DIR.exists(),
        "catalog_files": len(list(OUT_DIR.glob("*catalog*.md"))) if OUT_DIR.exists() else 0,
        "markdown_files": len(list(OUT_DIR.glob("*.md"))) if OUT_DIR.exists() else 0,
        "json_files": len(list(OUT_DIR.glob("*.json"))) if OUT_DIR.exists() else 0,
    }
    warnings = []
    if "missing_table" in filtered:
        warnings.append("messages_filtered is missing; run filter.py")
    elif raw.get("max_date") and filtered.get("max_date"):
        try:
            raw_max = datetime.fromisoformat(raw["max_date"])
            filtered_max = datetime.fromisoformat(filtered["max_date"])
            lag_hours = (raw_max - filtered_max).total_seconds() / 3600
            if lag_hours > STALE_AFTER_HOURS:
                warnings.append(
                    f"messages_filtered is stale by about {lag_hours:.1f} hours; run filter.py"
                )
        except ValueError:
            warnings.append("could not compare raw and filtered max dates")

    return {
        "ok": True,
        "database": str(DB_PATH),
        "warnings": warnings,
        "raw": raw,
        "filtered": filtered,
        "sources": sources,
        "links": links,
        "catalog": catalog,
        "enrichment": enrichment,
        "link_kinds": link_kinds,
        "output": output,
    }


def print_text(data: dict) -> None:
    if not data.get("ok"):
        print(data["error"])
        return

    raw = data["raw"]
    filtered = data["filtered"]
    print("coding_community status")
    print(f"DB: {data['database']}")
    if data["warnings"]:
        print("\nWarnings:")
        for warning in data["warnings"]:
            print(f"  {warning}")
        print("")
    print(f"Raw messages:      {raw['count']} | {raw['min_date']} -> {raw['max_date']}")
    if "missing_table" in filtered:
        print("Filtered messages: missing messages_filtered; run filter.py")
    else:
        print(f"Filtered messages: {filtered['count']} | {filtered['min_date']} -> {filtered['max_date']}")

    print("\nSources:")
    for source in data["sources"]:
        print(
            f"  {source['name']}: raw={source['raw_count']}, "
            f"filtered={source.get('filtered_count', '-')}, "
            f"raw_max={source['raw_max_date']}, filtered_max={source.get('filtered_max_date', '-')}"
        )

    print("\nLinks:")
    links = data["links"]
    if "missing_table" in links:
        print("  missing message_links; run rebuild_links.py")
    else:
        print(
            f"  raw={links['raw_links']}, valid={links['valid_links']}, "
            f"filtered_valid={links['filtered_valid_links']}"
        )
    catalog = data["catalog"]
    if "missing_table" in catalog:
        print("  missing links_catalog; run rebuild_links.py")
    else:
        print(f"  catalog_urls={catalog['unique_urls']}, filtered_urls={catalog['filtered_unique_urls']}")

    if data["enrichment"]:
        print("\nEnrichment:")
        for row in data["enrichment"]:
            print(f"  {row['enrich_status']}: {row['unique_urls']}")

    if data["link_kinds"]:
        print("\nFiltered URL kinds:")
        for row in data["link_kinds"]:
            print(f"  {row['kind']}: urls={row['unique_urls']}, mentions={row['filtered_mentions']}")

    print("\nOutput:")
    output = data["output"]
    print(
        f"  markdown={output['markdown_files']}, json={output['json_files']}, "
        f"catalogs={output['catalog_files']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Show read-only coding_community pipeline status.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    data = collect_status()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_text(data)


if __name__ == "__main__":
    main()
