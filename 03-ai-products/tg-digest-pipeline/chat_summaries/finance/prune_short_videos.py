"""
Delete already downloaded finance videos shorter than a threshold.

The script uses duration_sec from finance_video_files, records skip policy in
SQLite, deletes matching files from disk, and exports a deletion manifest.

Run:
    uv run python finance/prune_short_videos.py --dry-run
    uv run python finance/prune_short_videos.py --min-duration-sec 20
    uv run python finance/index_video_files.py
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DB_PATH = ROOT / "finance_messages.db"
OUT_DIR = ROOT / "output"


def open_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ensure_policy_tables(con)
    return con


def ensure_policy_tables(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_video_download_policy (
            source_peer_id INTEGER NOT NULL,
            message_id     INTEGER NOT NULL,
            policy         TEXT NOT NULL,
            reason         TEXT,
            path           TEXT,
            updated_at     TEXT NOT NULL,
            PRIMARY KEY (source_peer_id, message_id)
        )"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_external_video_download_policy (
            url_normalized TEXT PRIMARY KEY,
            policy         TEXT NOT NULL,
            reason         TEXT,
            source_peer_id INTEGER,
            message_id     INTEGER,
            path           TEXT,
            updated_at     TEXT NOT NULL
        )"""
    )
    con.commit()


def load_targets(con: sqlite3.Connection, min_duration_sec: float) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT file_id, video_source, relative_path, filename, size_bytes,
                  duration_sec, source_peer_id, message_id, detected_url,
                  category_id, category_name
           FROM finance_video_files
           WHERE duration_sec IS NOT NULL
             AND duration_sec < ?
           ORDER BY duration_sec, size_bytes""",
        (min_duration_sec,),
    ).fetchall()


def record_policy(con: sqlite3.Connection, row: sqlite3.Row, min_duration_sec: float) -> None:
    now = datetime.now(timezone.utc).isoformat()
    reason = f"Deleted because duration {row['duration_sec']:.2f}s is below {min_duration_sec:.2f}s."
    if row["video_source"] == "tg_native" and row["source_peer_id"] and row["message_id"]:
        con.execute(
            """INSERT INTO finance_video_download_policy (
                source_peer_id, message_id, policy, reason, path, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_peer_id, message_id) DO UPDATE SET
                policy=excluded.policy,
                reason=excluded.reason,
                path=excluded.path,
                updated_at=excluded.updated_at""",
            (
                int(row["source_peer_id"]),
                int(row["message_id"]),
                "skip_short_duration",
                reason,
                row["relative_path"],
                now,
            ),
        )
    elif row["video_source"] == "external_link":
        key = row["detected_url"] or f"file:{row['relative_path']}"
        con.execute(
            """INSERT INTO finance_external_video_download_policy (
                url_normalized, policy, reason, source_peer_id, message_id, path, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url_normalized) DO UPDATE SET
                policy=excluded.policy,
                reason=excluded.reason,
                source_peer_id=excluded.source_peer_id,
                message_id=excluded.message_id,
                path=excluded.path,
                updated_at=excluded.updated_at""",
            (
                key,
                "skip_short_duration",
                reason,
                row["source_peer_id"],
                row["message_id"],
                row["relative_path"],
                now,
            ),
        )


def export_manifest(rows: list[sqlite3.Row], min_duration_sec: float) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / "deleted_short_videos.csv"
    fields = [
        "video_source",
        "relative_path",
        "filename",
        "size_bytes",
        "duration_sec",
        "source_peer_id",
        "message_id",
        "detected_url",
        "category_id",
        "category_name",
        "threshold_sec",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            item = {field: row[field] for field in fields if field != "threshold_sec"}
            item["threshold_sec"] = min_duration_sec
            writer.writerow(item)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-duration-sec", type=float, default=20.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    con = open_db()
    rows = load_targets(con, args.min_duration_sec)
    bytes_total = sum(int(row["size_bytes"] or 0) for row in rows)
    print(
        f"Short videos: {len(rows)} files, "
        f"{bytes_total / 1024 / 1024 / 1024:.2f} GB, threshold={args.min_duration_sec}s"
    )
    manifest = export_manifest(rows, args.min_duration_sec)
    print(f"Manifest: {manifest}")
    if args.dry_run:
        return

    deleted = 0
    missing = 0
    for row in rows:
        path = ROOT / row["relative_path"]
        record_policy(con, row, args.min_duration_sec)
        if path.exists():
            path.unlink()
            deleted += 1
        else:
            missing += 1
    con.commit()
    print(f"Deleted: {deleted}, already missing: {missing}")
    print("Run indexer next: uv run python finance/index_video_files.py")


if __name__ == "__main__":
    main()
