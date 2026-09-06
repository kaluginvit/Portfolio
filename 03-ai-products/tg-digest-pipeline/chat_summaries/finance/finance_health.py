"""
Build a single health report for the finance pipeline.

Run:
    uv run python finance/finance_health.py
    uv run python finance/finance_health.py --write-progress
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DB_PATH = ROOT / "finance_messages.db"
OUT_DIR = ROOT / "output"
PROGRESS_PATH = ROOT / "PROGRESS.md"
PIPELINE_VERSION = "finance-practical-v1"
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    return bool(
        con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
    ).fetchone()
    )


def column_exists(con: sqlite3.Connection, table: str, column: str) -> bool:
    return column in {row[1] for row in con.execute(f"PRAGMA table_info({table})")}


def scalar(con: sqlite3.Connection, sql: str, params: tuple = ()) -> int | float:
    return con.execute(sql, params).fetchone()[0] or 0


def folder_file_stats(path: Path) -> dict:
    files = [item for item in path.rglob("*") if item.is_file()] if path.exists() else []
    total_bytes = sum(item.stat().st_size for item in files)
    video_files = [item for item in files if item.suffix.lower() in VIDEO_EXTS]
    part_files = [item for item in files if item.suffix.lower() == ".part"]
    return {
        "files": len(files),
        "video_files": len(video_files),
        "part_files": len(part_files),
        "bytes": total_bytes,
        "gb": round(total_bytes / 1024 / 1024 / 1024, 2),
    }


def part_stats() -> dict:
    parts = [item for item in ROOT.rglob("*.part") if item.is_file()]
    by_root = Counter()
    bytes_by_root = Counter()
    rows = []
    for item in parts:
        rel = item.relative_to(ROOT).as_posix()
        top = rel.split("/", 1)[0]
        size = item.stat().st_size
        by_root[top] += 1
        bytes_by_root[top] += size
        rows.append(
            {
                "path": rel,
                "mb": round(size / 1024 / 1024, 2),
                "mtime": datetime.fromtimestamp(item.stat().st_mtime, timezone.utc).isoformat(),
            }
        )
    return {
        "count": len(parts),
        "mb": round(sum(bytes_by_root.values()) / 1024 / 1024, 2),
        "by_folder": {
            key: {
                "count": by_root[key],
                "mb": round(bytes_by_root[key] / 1024 / 1024, 2),
            }
            for key in sorted(by_root)
        },
        "largest": sorted(rows, key=lambda row: row["mb"], reverse=True)[:20],
    }


def analysis_stats(con: sqlite3.Connection) -> dict:
    if not table_exists(con, "finance_item_analysis"):
        return {"reviewed": 0, "failed": 0, "missing_core": None, "categories": {}}

    reviewed = scalar(
        con,
        "SELECT COUNT(*) FROM finance_item_analysis WHERE pipeline_version=? AND status='reviewed'",
        (PIPELINE_VERSION,),
    )
    failed = scalar(
        con,
        "SELECT COUNT(*) FROM finance_item_analysis WHERE pipeline_version=? AND status='failed'",
        (PIPELINE_VERSION,),
    )
    missing_core = scalar(
        con,
        """SELECT COUNT(*)
           FROM messages m
           WHERE m.text IS NOT NULL
             AND m.text != ''
             AND (m.media_type='video' OR m.links_json IS NOT NULL OR m.text_len >= 300)
             AND NOT EXISTS (
               SELECT 1 FROM finance_item_analysis a
               WHERE a.source_peer_id=m.source_peer_id
                 AND a.message_id=m.message_id
                 AND a.pipeline_version=?
                 AND a.status='reviewed'
             )""",
        (PIPELINE_VERSION,),
    )
    categories = {
        row["category_name"]: row["count"]
        for row in con.execute(
            """SELECT category_name, COUNT(*) AS count
               FROM finance_item_analysis
               WHERE pipeline_version=? AND status='reviewed'
               GROUP BY category_name
               ORDER BY count DESC""",
            (PIPELINE_VERSION,),
        )
    }
    models = {
        row["model"] or "unknown": row["count"]
        for row in con.execute(
            """SELECT model, COUNT(*) AS count
               FROM finance_item_analysis
               WHERE pipeline_version=? AND status='reviewed'
               GROUP BY model
               ORDER BY count DESC""",
            (PIPELINE_VERSION,),
        )
    }
    return {
        "reviewed": reviewed,
        "failed": failed,
        "missing_core": missing_core,
        "categories": categories,
        "models": models,
    }


def link_stats(con: sqlite3.Connection) -> dict:
    if not table_exists(con, "finance_links"):
        return {"links": 0, "active_links": 0, "review_domains": None}
    active_filter = "COALESCE(is_stale, 0)=0" if column_exists(con, "finance_links", "is_stale") else "1=1"
    policies = {
        row["domain_policy"]: row["count"]
        for row in con.execute(
            f"SELECT domain_policy, COUNT(*) AS count FROM finance_links WHERE {active_filter} GROUP BY domain_policy"
        )
    }
    return {
        "links": scalar(con, f"SELECT COUNT(*) FROM finance_links WHERE {active_filter}"),
        "active_links": scalar(con, f"SELECT COUNT(*) FROM finance_links WHERE use_in_outputs=1 AND {active_filter}"),
        "review_domains": scalar(
            con,
            f"""SELECT COUNT(DISTINCT domain)
               FROM finance_links
               WHERE domain_policy='review' AND {active_filter}""",
        ),
        "policies": policies,
    }


def video_stats(con: sqlite3.Connection) -> dict:
    if not table_exists(con, "finance_video_files"):
        return {"indexed_files": 0}
    active_filter = "COALESCE(is_stale, 0)=0" if column_exists(con, "finance_video_files", "is_stale") else "1=1"
    expected_native = scalar(con, "SELECT COUNT(*) FROM messages WHERE media_type='video'")
    indexed_native = scalar(
        con,
        f"SELECT COUNT(*) FROM finance_video_files WHERE video_source='tg_native' AND {active_filter}",
    )
    indexed_external = scalar(
        con,
        f"SELECT COUNT(*) FROM finance_video_files WHERE video_source='external_link' AND {active_filter}",
    )
    valid_files = scalar(con, f"SELECT COUNT(*) FROM finance_video_files WHERE is_valid=1 AND {active_filter}")
    total_bytes = scalar(
        con,
        f"SELECT COALESCE(SUM(size_bytes), 0) FROM finance_video_files WHERE {active_filter}",
    )
    return {
        "expected_native": expected_native,
        "indexed_native": indexed_native,
        "indexed_external": indexed_external,
        "valid_files": valid_files,
        "gb": round(total_bytes / 1024 / 1024 / 1024, 2),
        "native_coverage": round(indexed_native / expected_native, 4) if expected_native else None,
    }


def source_stats(con: sqlite3.Connection) -> dict:
    return {
        "sources": scalar(con, "SELECT COUNT(*) FROM sources") if table_exists(con, "sources") else 0,
        "messages": scalar(con, "SELECT COUNT(*) FROM messages") if table_exists(con, "messages") else 0,
        "video_messages": scalar(con, "SELECT COUNT(*) FROM messages WHERE media_type='video'")
        if table_exists(con, "messages")
        else 0,
        "link_messages": scalar(con, "SELECT COUNT(*) FROM messages WHERE links_json IS NOT NULL")
        if table_exists(con, "messages")
        else 0,
    }


def build_report() -> dict:
    con = connect()
    try:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "database": {
                "path": DB_PATH.as_posix(),
                "mb": round(DB_PATH.stat().st_size / 1024 / 1024, 2) if DB_PATH.exists() else 0,
            },
            "sources": source_stats(con),
            "analysis": analysis_stats(con),
            "links": link_stats(con),
            "videos": video_stats(con),
            "folders": {
                "native": folder_file_stats(ROOT / "Финансы_видео"),
                "external": folder_file_stats(ROOT / "Финансы_ссылки_видео"),
                "output": folder_file_stats(OUT_DIR),
            },
            "partial_downloads": part_stats(),
        }
    finally:
        con.close()
    return report


def next_actions(report: dict) -> list[str]:
    actions = []
    if report["analysis"].get("missing_core"):
        actions.append("Run practical_finance.py --process-local or --classify-only for missing core items.")
    if report["links"].get("review_domains"):
        actions.append("Review unresolved link domains with domain_policy.py --review.")
    if report["partial_downloads"]["count"]:
        actions.append("Inspect stale partial downloads before the next native video batch.")
    native_coverage = report["videos"].get("native_coverage")
    if native_coverage is not None and native_coverage < 0.9:
        actions.append("Run download_finance_videos.py --dry-run before the next native batch.")
    return actions or ["Pipeline is up to date enough for the current local reports."]


def markdown(report: dict) -> str:
    lines = [
        "# Finance Project Progress",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Current State",
        "",
        f"- Sources: {report['sources']['sources']}",
        f"- Messages: {report['sources']['messages']}",
        f"- Video messages: {report['sources']['video_messages']}",
        f"- Link messages: {report['sources']['link_messages']}",
        f"- Database: {report['database']['mb']} MB",
        "",
        "## Analysis",
        "",
        f"- Reviewed items: {report['analysis']['reviewed']}",
        f"- Failed items: {report['analysis']['failed']}",
        f"- Missing core items: {report['analysis']['missing_core']}",
        "",
        "## Links",
        "",
        f"- Indexed links: {report['links']['links']}",
        f"- Active links: {report['links']['active_links']}",
        f"- Domains still in review: {report['links']['review_domains']}",
        "",
        "## Videos",
        "",
        f"- Expected native video messages: {report['videos'].get('expected_native', 0)}",
        f"- Indexed native files: {report['videos'].get('indexed_native', 0)}",
        f"- Indexed external files: {report['videos'].get('indexed_external', 0)}",
        f"- Valid indexed files: {report['videos'].get('valid_files', 0)}",
        f"- Indexed video size: {report['videos'].get('gb', 0)} GB",
        f"- Native coverage: {report['videos'].get('native_coverage')}",
        "",
        "## Folders",
        "",
    ]
    for name, stats in report["folders"].items():
        lines.append(
            f"- {name}: {stats['files']} files, {stats['video_files']} videos, {stats['part_files']} .part, {stats['gb']} GB"
        )
    lines += [
        "",
        "## Partial Downloads",
        "",
        f"- .part files: {report['partial_downloads']['count']}",
        f"- .part size: {report['partial_downloads']['mb']} MB",
        "",
        "## Next Actions",
        "",
    ]
    lines += [f"- {action}" for action in next_actions(report)]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-progress", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    report = build_report()
    (OUT_DIR / "finance_health.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md = markdown(report)
    (OUT_DIR / "finance_health.md").write_text(md, encoding="utf-8")
    if args.write_progress:
        PROGRESS_PATH.write_text(md, encoding="utf-8")
    print(md)
    print(f"Reports: {OUT_DIR / 'finance_health.json'}, {OUT_DIR / 'finance_health.md'}")
    if args.write_progress:
        print(f"Updated: {PROGRESS_PATH}")


if __name__ == "__main__":
    main()
