"""
Download missing external video links for the finance project.

This script uses yt-dlp and works from finance_messages.db:
  - collects concrete video URLs from messages.links_json;
  - skips URLs already downloaded or explicitly skipped;
  - saves files into category folders under finance/Финансы_ссылки_видео;
  - includes source/message/link identity in the filename for later indexing.

Run:
    uv run python finance/download_external_videos.py --dry-run
    uv run python finance/download_external_videos.py --limit 50
    uv run python finance/index_video_files.py
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DB_PATH = ROOT / "finance_messages.db"
EXTERNAL_DIR = ROOT / "Финансы_ссылки_видео"
PIPELINE_VERSION = "finance-practical-v1"
VIDEO_DOMAINS = {"vkvideo.ru", "vk.com", "rutube.ru", "youtube.com", "youtu.be"}


def safe_name(value: str, limit: int = 80) -> str:
    value = re.sub(r'[\\/:*?"<>|]', "_", value or "")
    value = re.sub(r"\s+", " ", value).strip().strip(".")
    return (value or "untitled")[:limit]


def category_dir_name(category_name: str) -> str:
    return safe_name(category_name).replace(" / ", " _ ")


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    parsed = urlparse(url)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/") or parsed.path
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() in {"v", "z"} or not key.lower().startswith(("utm_", "fbclid", "yclid", "gclid"))
    ]
    return urlunparse((scheme, netloc, path, "", urlencode(query_pairs, doseq=True), ""))


def domain(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def is_concrete_video_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.lower()
    query = parsed.query.lower()
    if host == "rutube.ru":
        return "/video/" in path
    if host in {"vkvideo.ru", "vk.com"}:
        return "video" in path or "z=video" in query
    if host == "youtu.be":
        return len(path.strip("/")) >= 6
    if host == "youtube.com":
        return path == "/watch" and "v=" in query or path.startswith("/shorts/")
    return False


def open_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    return con


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_external_video_download_policy (
            url_normalized TEXT PRIMARY KEY,
            policy         TEXT NOT NULL,
            reason         TEXT,
            source_peer_id INTEGER,
            message_id     INTEGER,
            path           TEXT,
            attempt_count  INTEGER NOT NULL DEFAULT 0,
            last_error     TEXT,
            last_attempt_at TEXT,
            next_retry_at  TEXT,
            updated_at     TEXT NOT NULL
        )"""
    )
    cols = {row[1] for row in con.execute("PRAGMA table_info(finance_external_video_download_policy)")}
    if "attempt_count" not in cols:
        con.execute("ALTER TABLE finance_external_video_download_policy ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0")
    if "last_error" not in cols:
        con.execute("ALTER TABLE finance_external_video_download_policy ADD COLUMN last_error TEXT")
    if "last_attempt_at" not in cols:
        con.execute("ALTER TABLE finance_external_video_download_policy ADD COLUMN last_attempt_at TEXT")
    if "next_retry_at" not in cols:
        con.execute("ALTER TABLE finance_external_video_download_policy ADD COLUMN next_retry_at TEXT")
    con.commit()


def existing_urls(con: sqlite3.Connection, retry_failed: bool) -> set[str]:
    urls: set[str] = set()
    policies = ("downloaded", "failed", "skip_manual", "skip_non_concrete")
    if retry_failed:
        policies = ("downloaded", "skip_manual", "skip_non_concrete")
    placeholders = ",".join("?" for _ in policies)
    for row in con.execute(
        f"SELECT url_normalized FROM finance_external_video_download_policy WHERE policy IN ({placeholders})",
        policies,
    ):
        urls.add(row["url_normalized"])
    if con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='finance_video_files'"
    ).fetchone():
        for row in con.execute(
            "SELECT detected_url FROM finance_video_files WHERE video_source='external_link' AND detected_url IS NOT NULL AND is_valid=1 AND COALESCE(is_stale, 0)=0"
        ):
            urls.add(normalize_url(row["detected_url"]))
    return urls


def mark_non_concrete(con: sqlite3.Connection, rows: list[dict]) -> int:
    now = datetime.now(timezone.utc).isoformat()
    skipped = [
        (
            row["url_normalized"],
            "skip_non_concrete",
            "URL is a channel, playlist, profile, or collection page rather than a concrete video.",
            row["source_peer_id"],
            row["message_id"],
            None,
            now,
        )
        for row in rows
        if not is_concrete_video_url(row["url_original"])
    ]
    if skipped:
        con.executemany(
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
            skipped,
        )
        con.commit()
    return len(skipped)


def load_targets(con: sqlite3.Connection, limit: int | None, retry_failed: bool) -> list[dict]:
    seen = existing_urls(con, retry_failed=retry_failed)
    rows = con.execute(
        """SELECT
              m.source_peer_id, m.message_id, m.date, m.links_json, m.text,
              s.title AS source_title,
              COALESCE(a.category_id, 11) AS category_id,
              COALESCE(a.category_name, 'Мусор / реклама / нерелевантное') AS category_name,
              COALESCE(a.title, '') AS item_title
           FROM messages m
           JOIN sources s ON s.source_peer_id = m.source_peer_id
           LEFT JOIN finance_item_analysis a
             ON a.source_peer_id = m.source_peer_id
            AND a.message_id = m.message_id
            AND a.pipeline_version = ?
            AND a.status = 'reviewed'
           WHERE m.links_json IS NOT NULL
           ORDER BY m.date, m.source_peer_id, m.message_id""",
        (PIPELINE_VERSION,),
    ).fetchall()

    by_url: dict[str, dict] = {}
    for row in rows:
        for link in json.loads(row["links_json"] or "[]"):
            if domain(link) not in VIDEO_DOMAINS:
                continue
            normalized = normalize_url(link)
            if normalized in seen or normalized in by_url:
                continue
            by_url[normalized] = {
                "url_original": link,
                "url_normalized": normalized,
                "source_peer_id": int(row["source_peer_id"]),
                "message_id": int(row["message_id"]),
                "date": row["date"],
                "source_title": row["source_title"],
                "category_id": int(row["category_id"]),
                "category_name": row["category_name"],
                "item_title": row["item_title"] or (row["text"] or "")[:80],
            }

    targets = list(by_url.values())
    mark_non_concrete(con, targets)
    targets = [row for row in targets if is_concrete_video_url(row["url_original"])]
    return targets[:limit] if limit else targets


def output_template(row: dict) -> Path:
    category = category_dir_name(row["category_name"])
    source = safe_name(row["source_title"], limit=45)
    title = safe_name(row["item_title"], limit=60)
    digest = hashlib.sha1(row["url_normalized"].encode("utf-8")).hexdigest()[:10]
    stem = f"sp_{row['source_peer_id']}__msg_{row['message_id']}__url_{digest}__{source}__{title}"
    return EXTERNAL_DIR / category / f"{stem}.%(ext)s"


def yt_dlp_command() -> list[str]:
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    return [sys.executable, "-m", "yt_dlp"]


async def download_one(row: dict, per_url_timeout: int) -> tuple[str, str]:
    outtmpl = output_template(row)
    outtmpl.parent.mkdir(parents=True, exist_ok=True)
    command = [
        *yt_dlp_command(),
        "--no-playlist",
        "--restrict-filenames",
        "--windows-filenames",
        "--merge-output-format",
        "mp4",
        "-f",
        "bv*+ba/b",
        "-o",
        str(outtmpl),
        row["url_original"],
    ]
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=per_url_timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "failed", f"Timed out after {per_url_timeout} seconds."
    output = stdout.decode("utf-8", errors="replace")[-1200:]
    if proc.returncode == 0:
        return "downloaded", str(outtmpl.parent)
    return "failed", output.strip()


def record_policy(con: sqlite3.Connection, row: dict, policy: str, reason: str, path: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    is_failure = 1 if policy == "failed" else 0
    con.execute(
        """INSERT INTO finance_external_video_download_policy (
            url_normalized, policy, reason, source_peer_id, message_id, path,
            attempt_count, last_error, last_attempt_at, next_retry_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        ON CONFLICT(url_normalized) DO UPDATE SET
            policy=excluded.policy,
            reason=excluded.reason,
            source_peer_id=excluded.source_peer_id,
            message_id=excluded.message_id,
            path=excluded.path,
            attempt_count=finance_external_video_download_policy.attempt_count + excluded.attempt_count,
            last_error=excluded.last_error,
            last_attempt_at=excluded.last_attempt_at,
            next_retry_at=excluded.next_retry_at,
            updated_at=excluded.updated_at""",
        (
            row["url_normalized"],
            policy,
            reason,
            row["source_peer_id"],
            row["message_id"],
            path,
            is_failure,
            reason if policy == "failed" else None,
            now if policy == "failed" else None,
            now,
        ),
    )
    con.commit()


async def run(args: argparse.Namespace) -> None:
    con = open_db()
    rows = load_targets(con, args.limit, retry_failed=args.retry_failed)
    print(f"External video targets: {len(rows)}")
    if args.dry_run:
        for row in rows[:100]:
            print(f"{row['date']} | msg={row['message_id']} | cat={row['category_id']} | {row['url_original']}")
        return

    downloaded = 0
    failed = 0
    for index, row in enumerate(rows, start=1):
        print(f"{index}/{len(rows)} {row['url_original']}")
        try:
            status, detail = await download_one(row, args.per_url_timeout)
        except Exception as exc:
            status, detail = "failed", f"{type(exc).__name__}: {exc}"
        if status == "downloaded":
            downloaded += 1
            record_policy(con, row, "downloaded", "Downloaded by finance external video downloader.", detail)
        else:
            failed += 1
            record_policy(con, row, "failed", detail)
            print(detail)
    print(f"Done. downloaded={downloaded}, failed={failed}")
    print("Run indexer next: uv run python finance/index_video_files.py")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--per-url-timeout", type=int, default=600)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
