"""
Download missing native Telegram videos for the finance project.

The script is DB-based:
  - reads video messages from finance_messages.db;
  - skips videos already present in finance_video_files or on disk;
  - saves files into category folders under finance/Финансы_видео;
  - preserves source/message linkage in the filename.

Run:
    uv run python finance/download_finance_videos.py --dry-run
    uv run python finance/download_finance_videos.py --limit 25
    uv run python finance/index_video_files.py
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import InputPeerChannel, InputPeerChat, InputPeerUser


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
PROJECT_ROOT = ROOT.parent
DB_PATH = ROOT / "finance_messages.db"
SESSION_NAME = "session2"
NATIVE_DIR = ROOT / "Финансы_видео"
PIPELINE_VERSION = "finance-practical-v1"


def safe_name(value: str, limit: int = 90) -> str:
    value = re.sub(r'[\\/:*?"<>|]', "_", value or "")
    value = re.sub(r"\s+", " ", value).strip().strip(".")
    return (value or "untitled")[:limit]


def category_dir_name(category_name: str) -> str:
    return safe_name(category_name).replace(" / ", " _ ")


def open_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    return con


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_video_download_policy (
            source_peer_id INTEGER NOT NULL,
            message_id     INTEGER NOT NULL,
            policy         TEXT NOT NULL,
            reason         TEXT,
            path           TEXT,
            attempt_count  INTEGER NOT NULL DEFAULT 0,
            last_error     TEXT,
            last_attempt_at TEXT,
            next_retry_at  TEXT,
            updated_at     TEXT NOT NULL,
            PRIMARY KEY (source_peer_id, message_id)
        )"""
    )
    cols = {row[1] for row in con.execute("PRAGMA table_info(finance_video_download_policy)")}
    if "attempt_count" not in cols:
        con.execute("ALTER TABLE finance_video_download_policy ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0")
    if "last_error" not in cols:
        con.execute("ALTER TABLE finance_video_download_policy ADD COLUMN last_error TEXT")
    if "last_attempt_at" not in cols:
        con.execute("ALTER TABLE finance_video_download_policy ADD COLUMN last_attempt_at TEXT")
    if "next_retry_at" not in cols:
        con.execute("ALTER TABLE finance_video_download_policy ADD COLUMN next_retry_at TEXT")
    con.commit()


def mark_deleted_skips(con: sqlite3.Connection) -> int:
    if not con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='finance_video_files'"
    ).fetchone():
        return 0

    now = datetime.now(timezone.utc).isoformat()
    rows = con.execute(
        """SELECT source_peer_id, message_id, relative_path
           FROM finance_video_files
           WHERE video_source = 'tg_native'
             AND source_peer_id IS NOT NULL
             AND message_id IS NOT NULL
             AND is_valid = 1
             AND COALESCE(is_stale, 0) = 0"""
    ).fetchall()
    deleted = []
    for row in rows:
        path = ROOT / row["relative_path"]
        if not path.exists():
            deleted.append(
                (
                    int(row["source_peer_id"]),
                    int(row["message_id"]),
                    "skip_deleted",
                    "File was present in the video index but is absent on disk; treating as intentional deletion.",
                    row["relative_path"],
                    now,
                )
            )
    if deleted:
        con.executemany(
            """INSERT INTO finance_video_download_policy (
                source_peer_id, message_id, policy, reason, path, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_peer_id, message_id) DO UPDATE SET
                policy=excluded.policy,
                reason=excluded.reason,
                path=excluded.path,
                updated_at=excluded.updated_at""",
            deleted,
        )
        con.commit()
    return len(deleted)


def existing_message_keys(con: sqlite3.Connection) -> set[tuple[int, int]]:
    keys: set[tuple[int, int]] = set()
    if con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='finance_video_download_policy'"
    ).fetchone():
        for row in con.execute(
            """SELECT source_peer_id, message_id
               FROM finance_video_download_policy
               WHERE policy IN ('downloaded', 'skip_deleted', 'skip_manual', 'skip_short_duration', 'skip_large')"""
        ):
            keys.add((int(row["source_peer_id"]), int(row["message_id"])))

    if con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='finance_video_files'"
    ).fetchone():
        for row in con.execute(
            """SELECT source_peer_id, message_id
               FROM finance_video_files
               WHERE video_source = 'tg_native'
                 AND source_peer_id IS NOT NULL
                 AND message_id IS NOT NULL
                 AND is_valid = 1
                 AND COALESCE(is_stale, 0) = 0"""
        ):
            keys.add((int(row["source_peer_id"]), int(row["message_id"])))

    prefix_re = re.compile(r"^sp_(\d+)__msg_(\d+)__", re.IGNORECASE)
    if NATIVE_DIR.exists():
        for path in NATIVE_DIR.rglob("*"):
            if not path.is_file():
                continue
            match = prefix_re.match(path.name)
            if match and path.stat().st_size >= 100 * 1024:
                keys.add((int(match.group(1)), int(match.group(2))))
    return keys


def load_targets(
    con: sqlite3.Connection,
    limit: int | None,
    source_peer_id: int | None,
    category_id: int | None,
) -> list[sqlite3.Row]:
    seen = existing_message_keys(con)
    params: list[object] = [PIPELINE_VERSION]
    where = ["m.media_type = 'video'"]
    if source_peer_id is not None:
        where.append("m.source_peer_id = ?")
        params.append(source_peer_id)
    if category_id is not None:
        where.append("a.category_id = ?")
        params.append(category_id)

    sql = f"""
        SELECT
            m.source_peer_id,
            m.message_id,
            m.date,
            m.text,
            m.video_duration_sec,
            m.post_url,
            s.title AS source_title,
            s.username,
            s.entity_id,
            s.access_hash,
            s.type AS source_type,
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
        WHERE {' AND '.join(where)}
        ORDER BY m.date, m.source_peer_id, m.message_id
    """
    rows = [
        row
        for row in con.execute(sql, params).fetchall()
        if (int(row["source_peer_id"]), int(row["message_id"])) not in seen
    ]
    return rows[:limit] if limit else rows


def input_peer(row: sqlite3.Row):
    entity_id = int(row["entity_id"])
    access_hash = row["access_hash"]
    source_type = (row["source_type"] or "").lower()
    if access_hash is not None and "channel" in source_type:
        return InputPeerChannel(entity_id, int(access_hash))
    if access_hash is not None and "user" in source_type:
        return InputPeerUser(entity_id, int(access_hash))
    if "chat" in source_type:
        return InputPeerChat(entity_id)
    if access_hash is not None:
        return InputPeerChannel(entity_id, int(access_hash))
    return row["username"] or entity_id


def target_path(row: sqlite3.Row) -> Path:
    category = category_dir_name(row["category_name"])
    source = safe_name(row["source_title"], limit=50)
    title = safe_name(row["item_title"] or (row["text"] or "")[:80], limit=70)
    filename = f"sp_{row['source_peer_id']}__msg_{row['message_id']}__{source}__{title}.mp4"
    return NATIVE_DIR / category / filename


SEGMENT_CHUNK = 512 * 1024   # 512 KB per request — must be multiple of 4096
MIN_SEGMENTED_BYTES = 50 * 1024 * 1024  # use segmented only for files >= 50 MB
_max_size_bytes: int = 0  # 0 = no limit


async def _download_segment(
    client: TelegramClient,
    doc,
    fh,
    seg_start: int,
    seg_end: int,
    worker_id: int,
) -> int:
    """Download bytes [seg_start, seg_end) into fh at the correct offset."""
    written = 0
    seg_len = seg_end - seg_start
    async for chunk in client.iter_download(
        doc,
        offset=seg_start,
        request_size=SEGMENT_CHUNK,
        limit=math.ceil(seg_len / SEGMENT_CHUNK),
    ):
        remaining = seg_len - written
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
        # seek+write are synchronous — no await between them, safe in asyncio
        fh.seek(seg_start + written)
        fh.write(chunk)
        written += len(chunk)
        if written >= seg_len:
            break
    return written


async def _download_segmented(
    client: TelegramClient,
    doc,
    tmp_path: Path,
    total_size: int,
    num_workers: int,
) -> None:
    """Parallel segmented download: splits file into num_workers chunks."""
    raw = math.ceil(total_size / num_workers)
    # Align segment boundaries to SEGMENT_CHUNK so iter_download offsets are clean
    seg_size = math.ceil(raw / SEGMENT_CHUNK) * SEGMENT_CHUNK

    segments = []
    for i in range(num_workers):
        start = i * seg_size
        if start >= total_size:
            break
        end = min(start + seg_size, total_size)
        segments.append((i, start, end))

    # Pre-allocate the file
    with open(tmp_path, "wb") as f:
        f.seek(total_size - 1)
        f.write(b"\x00")

    with open(tmp_path, "r+b") as fh:
        tasks = [
            _download_segment(client, doc, fh, start, end, i)
            for i, start, end in segments
        ]
        results = await asyncio.gather(*tasks)

    total_written = sum(results)
    if total_written < total_size:
        raise RuntimeError(f"Segmented download incomplete: {total_written}/{total_size} bytes")


async def download_one(
    client: TelegramClient,
    row: sqlite3.Row,
    num_workers: int = 1,
) -> tuple[str, str]:
    path = target_path(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size >= 100 * 1024:
        return "skip_exists", str(path)

    entity = input_peer(row)
    msg = await client.get_messages(entity, ids=int(row["message_id"]))
    if not msg or not getattr(msg, "media", None):
        return "missing_media", str(path)

    tmp_path = path.with_suffix(path.suffix + ".part")
    if tmp_path.exists():
        tmp_path.unlink()

    doc = getattr(msg.media, "document", None)
    file_size = getattr(doc, "size", 0) if doc else 0

    if _max_size_bytes and file_size > _max_size_bytes:
        return "skip_large", f"{file_size/1024/1024:.1f}MB"

    use_segmented = num_workers > 1 and doc and file_size >= MIN_SEGMENTED_BYTES

    if use_segmented:
        print(f"    segmented ({num_workers} workers, {file_size/1024/1024:.1f} MB)", flush=True)
        await _download_segmented(client, doc, tmp_path, file_size, num_workers)
    else:
        downloaded = await client.download_media(msg, file=str(tmp_path))
        if not downloaded:
            return "download_failed", str(path)
        downloaded_path = Path(downloaded)
        if downloaded_path != tmp_path:
            if path.exists():
                path.unlink()
            downloaded_path.replace(path)
            return "downloaded", str(path)

    if path.exists():
        path.unlink()
    tmp_path.replace(path)
    return "downloaded", str(path)


def video_duration_sec(path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return float((result.stdout or "").strip())
    except ValueError:
        return None


def remove_if_too_short(path: str, min_duration_sec: float) -> tuple[bool, float | None]:
    file_path = Path(path)
    duration = video_duration_sec(file_path)
    if duration is not None and duration < min_duration_sec:
        file_path.unlink(missing_ok=True)
        return True, duration
    return False, duration


async def download_with_reconnect(
    client: TelegramClient,
    row: sqlite3.Row,
    attempts: int,
    file_timeout: float,
    num_workers: int = 1,
    max_size_bytes: int = 0,
) -> tuple[str, str]:
    global _max_size_bytes
    _max_size_bytes = max_size_bytes
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            if not client.is_connected():
                await client.connect()
            return await asyncio.wait_for(download_one(client, row, num_workers=num_workers), timeout=file_timeout)
        except asyncio.TimeoutError:
            # Clean up any partial download before giving up.
            tmp_path = target_path(row).with_suffix(".mp4.part")
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise TimeoutError(f"Download exceeded {file_timeout:.0f}s per-file timeout")
        except FloodWaitError:
            raise
        except (ConnectionError, TimeoutError, OSError, RPCError) as exc:
            last_error = exc
            if attempt >= attempts:
                break
            await asyncio.sleep(min(10 * attempt, 60))
            try:
                await client.disconnect()
            except Exception:
                pass
            await client.connect()
    assert last_error is not None
    raise last_error


def record_attempt(
    con: sqlite3.Connection,
    row: sqlite3.Row,
    error: str | None = None,
    retry_delay_seconds: int | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    next_retry_at = (now + timedelta(seconds=retry_delay_seconds)).isoformat() if retry_delay_seconds else None
    con.execute(
        """INSERT INTO finance_video_download_policy (
            source_peer_id, message_id, policy, reason, path,
            attempt_count, last_error, last_attempt_at, next_retry_at, updated_at
        ) VALUES (?, ?, 'retry_pending', ?, ?, 1, ?, ?, ?, ?)
        ON CONFLICT(source_peer_id, message_id) DO UPDATE SET
            attempt_count=COALESCE(finance_video_download_policy.attempt_count, 0) + 1,
            last_error=excluded.last_error,
            last_attempt_at=excluded.last_attempt_at,
            next_retry_at=excluded.next_retry_at,
            updated_at=excluded.updated_at""",
        (
            int(row["source_peer_id"]),
            int(row["message_id"]),
            "Download attempt failed; retry metadata recorded.",
            str(target_path(row).relative_to(ROOT).as_posix()),
            error,
            now.isoformat(),
            next_retry_at,
            now.isoformat(),
        ),
    )
    con.commit()


def record_download_policy(con: sqlite3.Connection, row: sqlite3.Row, policy: str, path: str, reason: str) -> None:
    con.execute(
        """INSERT INTO finance_video_download_policy (
            source_peer_id, message_id, policy, reason, path,
            last_error, next_retry_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, NULL, NULL, ?)
        ON CONFLICT(source_peer_id, message_id) DO UPDATE SET
            policy=excluded.policy,
            reason=excluded.reason,
            path=excluded.path,
            last_error=NULL,
            next_retry_at=NULL,
            updated_at=excluded.updated_at""",
        (
            int(row["source_peer_id"]),
            int(row["message_id"]),
            policy,
            reason,
            str(Path(path).relative_to(ROOT).as_posix()) if Path(path).is_absolute() else path,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    con.commit()


def cleanup_stale_parts(older_than_hours: float, dry_run: bool) -> None:
    root = ROOT.resolve()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
    targets = []
    for path in ROOT.rglob("*.part"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if root not in [resolved, *resolved.parents]:
            raise RuntimeError(f"Refusing to touch outside finance root: {resolved}")
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if mtime < cutoff:
            targets.append(path)
    total = sum(path.stat().st_size for path in targets)
    print(f"Stale .part targets: {len(targets)}, {total / 1024 / 1024:.2f} MB")
    for path in sorted(targets):
        print(f"  {path.relative_to(ROOT)}")
        if not dry_run:
            path.unlink()


async def run(args: argparse.Namespace) -> None:
    if args.cleanup_stale_parts:
        cleanup_stale_parts(args.older_than_hours, dry_run=args.dry_run)
        return

    load_dotenv(PROJECT_ROOT / ".env")
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

    con = open_db()
    deleted_skips = mark_deleted_skips(con)
    if deleted_skips:
        print(f"Marked intentionally deleted videos as skipped: {deleted_skips}")
    rows = load_targets(con, args.limit, args.source_peer_id, args.category_id)
    print(f"Missing native video targets: {len(rows)}")
    if args.dry_run:
        for row in rows[:50]:
            print(
                f"{row['date']} | {row['source_title']} | msg={row['message_id']} | "
                f"cat={row['category_id']} | {target_path(row)}"
            )
        if len(rows) > 50:
            print(f"... {len(rows) - 50} more")
        return

    max_size_bytes = int(args.max_size_mb * 1024 * 1024) if args.max_size_mb else 0
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"Started at {started_at}")
    if max_size_bytes:
        print(f"Max file size: {args.max_size_mb:.0f} MB")
    downloaded = 0
    skipped = 0
    failed = 0
    large_files: list[dict] = []

    async with TelegramClient(str(PROJECT_ROOT / args.session_name), api_id, api_hash) as client:
        for index, row in enumerate(rows, start=1):
            label = f"{index}/{len(rows)} source={row['source_title']} msg={row['message_id']}"
            try:
                status, path = await download_with_reconnect(client, row, attempts=args.reconnect_attempts, file_timeout=args.file_timeout, num_workers=args.workers, max_size_bytes=max_size_bytes)
            except FloodWaitError as exc:
                wait_seconds = int(getattr(exc, "seconds", 0) or 0)
                print(f"{label} flood_wait={wait_seconds}s")
                await asyncio.sleep(wait_seconds + 3)
                status, path = await download_with_reconnect(client, row, attempts=args.reconnect_attempts, file_timeout=args.file_timeout, num_workers=args.workers, max_size_bytes=max_size_bytes)
            except TimeoutError as exc:
                failed += 1
                record_attempt(con, row, str(exc), retry_delay_seconds=3600)
                print(f"{label} timeout: {exc}")
                continue
            except (RPCError, OSError) as exc:
                failed += 1
                record_attempt(con, row, f"{type(exc).__name__}: {exc}", retry_delay_seconds=3600)
                print(f"{label} failed: {type(exc).__name__}: {exc}")
                continue

            if status == "downloaded":
                removed, duration = remove_if_too_short(path, args.min_duration_sec)
                if removed:
                    skipped += 1
                    status = "skip_short_duration"
                    record_download_policy(
                        con,
                        row,
                        "skip_short_duration",
                        path,
                        f"Downloaded and removed because duration {duration:.2f}s is below {args.min_duration_sec:.2f}s.",
                    )
                else:
                    downloaded += 1
                    reason = "Downloaded by finance native video downloader."
                    if duration is not None:
                        reason = f"{reason} duration={duration:.2f}s."
                    record_download_policy(con, row, "downloaded", path, reason)
            elif status == "skip_exists":
                skipped += 1
                record_download_policy(con, row, "downloaded", path, "Already exists on disk.")
            elif status == "skip_large":
                skipped += 1
                large_files.append({
                    "date": row["date"][:10],
                    "source": row["source_title"],
                    "msg_id": row["message_id"],
                    "size_mb": path,  # path contains "X.XMB" string for skip_large
                    "url": row["post_url"] or "",
                })
                record_download_policy(con, row, "skip_large", str(target_path(row)), f"File size {path} exceeds limit {args.max_size_mb:.0f} MB.")
            else:
                failed += 1
            print(f"{label} {status}: {path}")

    print(f"Done. downloaded={downloaded}, skipped={skipped}, failed={failed}")
    if large_files:
        print(f"\n=== Реестр крупных файлов (>{args.max_size_mb:.0f} МБ) — скачать вручную ===")
        for f in large_files:
            print(f"  {f['date']} | {f['source']} | msg={f['msg_id']} | {f['size_mb']} | {f['url']}")
    print("Run indexer next: uv run python finance/index_video_files.py")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source-peer-id", type=int, default=None)
    parser.add_argument("--category-id", type=int, default=None)
    parser.add_argument("--reconnect-attempts", type=int, default=3)
    parser.add_argument("--min-duration-sec", type=float, default=20.0)
    parser.add_argument("--file-timeout", type=float, default=300.0, help="Per-file download timeout in seconds (default: 300)")
    parser.add_argument("--workers", type=int, default=1, help="Parallel segments per file for large files >=50 MB (default: 1 = disabled)")
    parser.add_argument("--max-size-mb", type=float, default=0, help="Skip files larger than this (MB). 0 = no limit.")
    parser.add_argument("--cleanup-stale-parts", action="store_true", help="Delete .part files older than --older-than-hours inside finance/.")
    parser.add_argument("--older-than-hours", type=float, default=12.0)
    parser.add_argument("--session-name", default=SESSION_NAME)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
