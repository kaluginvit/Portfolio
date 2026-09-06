"""
Index downloaded finance video files and report download completeness.

The script does not download or delete anything. It scans:
  - finance/Финансы_видео          for native Telegram videos
  - finance/Финансы_ссылки_видео   for videos downloaded from external links

Then it writes `finance_video_files` into finance_messages.db and exports
reports into finance/output/.

Run:
    uv run python finance/index_video_files.py
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DB_PATH = ROOT / "finance_messages.db"
OUT_DIR = ROOT / "output"
NATIVE_DIR = ROOT / "Финансы_видео"
EXTERNAL_DIR = ROOT / "Финансы_ссылки_видео"
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}
MIN_SIZE_BYTES = 100 * 1024

CATEGORIES = {
    1: "Управленческий учет / P&L / ДДС / баланс",
    2: "CFO / финдир / финслужба",
    3: "Налоги / бухучет / регуляторика",
    4: "Маркетплейсы",
    5: "Платежи / ВЭД / SWIFT / SEPA",
    6: "Автоматизация / Excel / BI / AI для финансов",
    7: "Продажи финуслуг / лидогенерация / воронки",
    8: "Инвестиции / рынки / макро",
    9: "Обучение / курсы / вебинары",
    10: "Шаблоны / документы / чек-листы",
    11: "Мусор / реклама / нерелевантное",
}

KEYWORDS = {
    1: ("ддс", "p&l", "pnl", "баланс", "бюджет", "отчет", "отчёт", "управлен", "финмодель", "прибыль"),
    2: ("cfo", "финдир", "финансовый директор", "финслуж"),
    3: ("налог", "ндс", "усн", "бухгалтер", "бухуч", "фнс", "регулятор"),
    4: ("wildberries", "wb", "ozon", "маркетплейс", "селлер"),
    5: ("swift", "sepa", "вэд", "платеж", "платёж", "перевод", "инвойс", "invoice"),
    6: ("excel", "bi", "дашборд", "ai", "ии", "chatgpt", "нейросет", "автоматиза", "claude", "gemini"),
    7: ("лид", "воронк", "продаж", "клиент", "консультац"),
    8: ("инвест", "рынок", "акци", "облигац", "макро", "ставк", "цб"),
    9: ("курс", "обуч", "вебинар", "мастер-класс", "урок", "школ", "эфир"),
    10: ("шаблон", "чек-лист", "чеклист", "инструкц", "гайд", "таблица"),
}


def safe_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]', "_", value or "")
    return value.strip().strip(".")[:80]


def compact_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def init_db(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_video_files (
            file_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            video_source     TEXT NOT NULL,
            source_folder    TEXT,
            relative_path    TEXT NOT NULL UNIQUE,
            filename         TEXT NOT NULL,
            extension        TEXT NOT NULL,
            size_bytes       INTEGER NOT NULL,
            mtime            TEXT NOT NULL,
            is_valid         INTEGER NOT NULL,
            detected_msg_id  INTEGER,
            detected_url     TEXT,
            source_peer_id   INTEGER,
            message_id       INTEGER,
            post_url         TEXT,
            match_method     TEXT NOT NULL,
            category_id      INTEGER NOT NULL DEFAULT 11,
            category_name    TEXT NOT NULL DEFAULT 'Мусор / реклама / нерелевантное',
            category_method  TEXT NOT NULL DEFAULT 'fallback',
            seen_at          TEXT,
            is_stale         INTEGER NOT NULL DEFAULT 0,
            indexed_at       TEXT NOT NULL
        )"""
    )
    cols = {row[1] for row in con.execute("PRAGMA table_info(finance_video_files)")}
    if "category_id" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN category_id INTEGER NOT NULL DEFAULT 11")
    if "category_name" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN category_name TEXT NOT NULL DEFAULT 'Мусор / реклама / нерелевантное'")
    if "category_method" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN category_method TEXT NOT NULL DEFAULT 'fallback'")
    if "duration_sec" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN duration_sec REAL")
    if "width" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN width INTEGER")
    if "height" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN height INTEGER")
    if "video_codec" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN video_codec TEXT")
    if "bitrate" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN bitrate INTEGER")
    if "seen_at" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN seen_at TEXT")
    if "is_stale" not in cols:
        con.execute("ALTER TABLE finance_video_files ADD COLUMN is_stale INTEGER NOT NULL DEFAULT 0")
    con.execute(
        """CREATE INDEX IF NOT EXISTS idx_finance_video_files_message
           ON finance_video_files(source_peer_id, message_id)"""
    )
    con.commit()


def load_native_candidates(con: sqlite3.Connection) -> dict[tuple[str, int], sqlite3.Row]:
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """SELECT m.source_peer_id, m.message_id, m.post_url, m.text, s.title
           FROM messages m
           JOIN sources s ON s.source_peer_id = m.source_peer_id
           WHERE m.media_type = 'video'"""
    ).fetchall()
    result = {}
    for row in rows:
        result[(safe_name(row["title"]).lower(), int(row["message_id"]))] = row
        result[(compact_spaces(row["title"]).lower(), int(row["message_id"]))] = row
    return result


def load_native_candidate_rows(con: sqlite3.Connection) -> list[sqlite3.Row]:
    con.row_factory = sqlite3.Row
    return con.execute(
        """SELECT m.source_peer_id, m.message_id, m.post_url, m.text, s.title
           FROM messages m
           JOIN sources s ON s.source_peer_id = m.source_peer_id
           WHERE m.media_type = 'video'"""
    ).fetchall()


def load_external_candidates(con: sqlite3.Connection) -> list[sqlite3.Row]:
    con.row_factory = sqlite3.Row
    return con.execute(
        """SELECT m.source_peer_id, m.message_id, m.post_url, m.links_json, m.text, s.title
           FROM messages m
           JOIN sources s ON s.source_peer_id = m.source_peer_id
           WHERE m.links_json IS NOT NULL"""
    ).fetchall()


def ffprobe_metadata(path: Path) -> dict:
    empty = {
        "duration_sec": None,
        "width": None,
        "height": None,
        "video_codec": None,
        "bitrate": None,
    }
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "format=duration,bit_rate:stream=width,height,codec_name",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return empty
    if result.returncode != 0:
        return empty
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return empty

    stream = (payload.get("streams") or [{}])[0]
    fmt = payload.get("format") or {}

    def as_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def as_int(value):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    return {
        "duration_sec": as_float(fmt.get("duration")),
        "width": as_int(stream.get("width")),
        "height": as_int(stream.get("height")),
        "video_codec": stream.get("codec_name"),
        "bitrate": as_int(fmt.get("bit_rate")),
    }


def detect_message_id(filename: str) -> int | None:
    stem = Path(filename).stem
    match = re.search(r"(?:^|__)msg_(\d+)(?:__|$)", stem)
    if match:
        return int(match.group(1))
    patterns = [
        r"^_(\d+)$",
        r"^(\d{3,})_",
        r"_(\d{3,})(?:_|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, stem)
        if match:
            return int(match.group(1))
    return None


def detect_source_message_ids(filename: str) -> tuple[int | None, int | None]:
    stem = Path(filename).stem
    match = re.search(r"(?:^|__)sp_(\d+)__msg_(\d+)(?:__|$)", stem)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def url_to_filename_fragment(url: str) -> str:
    return safe_name(url).lower()


def token_set(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zа-яё0-9]{4,}", (value or "").lower())
        if token not in {"https", "video", "финансы", "финансист", "финансовый"}
    }


def detect_external_from_filename(
    filename: str,
    source_folder: str,
    candidates: list[sqlite3.Row],
) -> tuple[str | None, sqlite3.Row | None, str]:
    stem = Path(filename).stem.lower()
    folder_key = safe_name(source_folder).lower()
    best: tuple[int, str, sqlite3.Row] | None = None
    for row in candidates:
        if folder_key and safe_name(row["title"]).lower() != folder_key:
            continue
        for link in json.loads(row["links_json"] or "[]"):
            domain = urlparse(link).netloc.lower().replace("www.", "")
            if domain not in {"vkvideo.ru", "vk.com", "rutube.ru", "youtube.com", "youtu.be"}:
                continue
            fragment = url_to_filename_fragment(link)
            score = 0
            if fragment and fragment[:70] in stem:
                score = len(fragment[:70])
            elif fragment and fragment[:42] in stem:
                score = len(fragment[:42])
            elif domain in stem or domain.replace(".", "_") in stem:
                tail = re.sub(r"\D+", "", link)[-8:]
                if tail and tail in stem:
                    score = len(tail)
            if score and (best is None or score > best[0]):
                best = (score, link, row)
    if best:
        return best[1], best[2], "external_url_filename"

    file_tokens = token_set(Path(filename).stem)
    if len(file_tokens) >= 2:
        title_best: tuple[int, sqlite3.Row] | None = None
        for row in candidates:
            if folder_key and safe_name(row["title"]).lower() != folder_key:
                continue
            text_tokens = token_set(row["post_url"] + " " + (row["links_json"] or ""))
            # Pull the message text lazily into candidate rows by selecting it in load_external_candidates.
            text_tokens |= token_set(row["text"] or "")
            overlap = len(file_tokens & text_tokens)
            if overlap >= 3 and (title_best is None or overlap > title_best[0]):
                title_best = (overlap, row)
        if title_best:
            links = json.loads(title_best[1]["links_json"] or "[]")
            video_link = next(
                (
                    link
                    for link in links
                    if urlparse(link).netloc.lower().replace("www.", "")
                    in {"vkvideo.ru", "vk.com", "rutube.ru", "youtube.com", "youtu.be"}
                ),
                None,
            )
            return video_link, title_best[1], "external_title_text"
    return None, None, "unmatched"


def fallback_category(filename: str, source_folder: str) -> tuple[int, str]:
    haystack = f"{filename} {source_folder}".lower()
    scores = {
        category_id: sum(1 for word in words if word in haystack)
        for category_id, words in KEYWORDS.items()
    }
    best_id, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return 11, CATEGORIES[11]
    return best_id, CATEGORIES[best_id]


def analysis_category(con: sqlite3.Connection, source_peer_id: int | None, message_id: int | None) -> tuple[int, str] | None:
    if source_peer_id is None or message_id is None:
        return None
    row = con.execute(
        """SELECT category_id, category_name
           FROM finance_item_analysis
           WHERE source_peer_id = ?
             AND message_id = ?
             AND pipeline_version = 'finance-practical-v1'
             AND status = 'reviewed'""",
        (source_peer_id, message_id),
    ).fetchone()
    if not row:
        return None
    return int(row["category_id"]), row["category_name"]


def detect_native_by_title(
    filename: str,
    source_folder: str,
    candidates: list[sqlite3.Row],
) -> sqlite3.Row | None:
    file_tokens = token_set(Path(filename).stem)
    if len(file_tokens) < 2:
        return None
    folder_key = safe_name(source_folder).lower()
    best: tuple[int, sqlite3.Row] | None = None
    for row in candidates:
        if folder_key and safe_name(row["title"]).lower() != folder_key:
            continue
        text_tokens = token_set(row["text"] or "")
        overlap = len(file_tokens & text_tokens)
        if overlap >= 3 and (best is None or overlap > best[0]):
            best = (overlap, row)
    return best[1] if best else None


def scan_files() -> list[dict]:
    files = []
    roots = [(NATIVE_DIR, "tg_native"), (EXTERNAL_DIR, "external_link")]
    for root, video_source in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in VIDEO_EXTS:
                continue
            stat = path.stat()
            parent = path.parent.name if path.parent != root else ""
            metadata = ffprobe_metadata(path)
            files.append(
                {
                    "video_source": video_source,
                    "source_folder": parent,
                    "relative_path": path.relative_to(ROOT).as_posix(),
                    "filename": path.name,
                    "extension": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "is_valid": int(stat.st_size >= MIN_SIZE_BYTES),
                    **metadata,
                }
            )
    return files


def match_file(
    file_row: dict,
    native_candidates: dict,
    native_candidate_rows: list[sqlite3.Row],
    external_candidates: list[sqlite3.Row],
) -> dict:
    detected_msg_id = detect_message_id(file_row["filename"])
    detected_source_id, embedded_message_id = detect_source_message_ids(file_row["filename"])
    if embedded_message_id:
        detected_msg_id = embedded_message_id
    detected_url = None
    matched = None
    match_method = "unmatched"
    if detected_source_id and detected_msg_id:
        matched = next(
            (
                row
                for row in native_candidate_rows + external_candidates
                if int(row["source_peer_id"]) == detected_source_id
                and int(row["message_id"]) == detected_msg_id
            ),
            None,
        )
        if matched is not None:
            match_method = "embedded_source_message_id"
    if matched is None and file_row["video_source"] == "tg_native" and detected_msg_id:
        source_keys = [
            (file_row["source_folder"].lower(), detected_msg_id),
            (safe_name(file_row["source_folder"]).lower(), detected_msg_id),
        ]
        for key in source_keys:
            matched = native_candidates.get(key)
            if matched is not None:
                match_method = "source_folder_message_id"
                break
        if matched is None:
            for (folder, msg_id), row in native_candidates.items():
                if msg_id == detected_msg_id:
                    matched = row
                    match_method = "message_id_only"
                    break
        if matched is None:
            matched = detect_native_by_title(file_row["filename"], file_row["source_folder"], native_candidate_rows)
            if matched is not None:
                match_method = "native_title_text"
    elif matched is None and file_row["video_source"] == "tg_native":
        matched = detect_native_by_title(file_row["filename"], file_row["source_folder"], native_candidate_rows)
        if matched is not None:
            match_method = "native_title_text"
    elif matched is None and file_row["video_source"] == "external_link":
        detected_url, matched, match_method = detect_external_from_filename(
            file_row["filename"], file_row["source_folder"], external_candidates
        )
        if matched is not None:
            pass

    file_row.update(
        {
            "detected_msg_id": detected_msg_id,
            "detected_url": detected_url,
            "source_peer_id": matched["source_peer_id"] if matched is not None else None,
            "message_id": matched["message_id"] if matched is not None else None,
            "post_url": matched["post_url"] if matched is not None else None,
            "match_method": match_method,
            "seen_at": datetime.now(timezone.utc).isoformat(),
            "is_stale": 0,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return file_row


def upsert_files(con: sqlite3.Connection, files: list[dict]) -> None:
    for file_row in files:
        category = analysis_category(con, file_row["source_peer_id"], file_row["message_id"])
        if category:
            file_row["category_id"], file_row["category_name"] = category
            file_row["category_method"] = "analysis"
        else:
            file_row["category_id"], file_row["category_name"] = fallback_category(
                file_row["filename"], file_row["source_folder"] or ""
            )
            file_row["category_method"] = "filename_fallback"
        file_row["seen_at"] = datetime.now(timezone.utc).isoformat()
        file_row["is_stale"] = 0
    con.execute("UPDATE finance_video_files SET is_stale=1, indexed_at=?", (datetime.now(timezone.utc).isoformat(),))
    con.executemany(
        """INSERT INTO finance_video_files (
            video_source, source_folder, relative_path, filename, extension,
            size_bytes, mtime, is_valid, detected_msg_id, detected_url,
            source_peer_id, message_id, post_url, match_method,
            category_id, category_name, category_method,
            duration_sec, width, height, video_codec, bitrate, seen_at, is_stale, indexed_at
        ) VALUES (
            :video_source, :source_folder, :relative_path, :filename, :extension,
            :size_bytes, :mtime, :is_valid, :detected_msg_id, :detected_url,
            :source_peer_id, :message_id, :post_url, :match_method,
            :category_id, :category_name, :category_method,
            :duration_sec, :width, :height, :video_codec, :bitrate, :seen_at, :is_stale, :indexed_at
        )
        ON CONFLICT(relative_path) DO UPDATE SET
            video_source=excluded.video_source,
            source_folder=excluded.source_folder,
            filename=excluded.filename,
            extension=excluded.extension,
            size_bytes=excluded.size_bytes,
            mtime=excluded.mtime,
            is_valid=excluded.is_valid,
            detected_msg_id=excluded.detected_msg_id,
            detected_url=excluded.detected_url,
            source_peer_id=excluded.source_peer_id,
            message_id=excluded.message_id,
            post_url=excluded.post_url,
            match_method=excluded.match_method,
            category_id=excluded.category_id,
            category_name=excluded.category_name,
            category_method=excluded.category_method,
            duration_sec=excluded.duration_sec,
            width=excluded.width,
            height=excluded.height,
            video_codec=excluded.video_codec,
            bitrate=excluded.bitrate,
            seen_at=excluded.seen_at,
            is_stale=0,
            indexed_at=excluded.indexed_at""",
        files,
    )
    con.commit()


def completeness_report(con: sqlite3.Connection) -> dict:
    expected_native = con.execute("SELECT COUNT(*) FROM messages WHERE media_type = 'video'").fetchone()[0]
    downloaded_native = con.execute("SELECT COUNT(*) FROM finance_video_files WHERE video_source='tg_native' AND is_stale=0").fetchone()[0]
    matched_native = con.execute(
        "SELECT COUNT(*) FROM finance_video_files WHERE video_source='tg_native' AND message_id IS NOT NULL AND is_stale=0"
    ).fetchone()[0]
    valid_native = con.execute(
        "SELECT COUNT(*) FROM finance_video_files WHERE video_source='tg_native' AND is_valid=1 AND is_stale=0"
    ).fetchone()[0]

    video_link_patterns = ("%vkvideo%", "%rutube%", "%youtube%", "%youtu.be%", "%vk.com/video%")
    external_conditions = " OR ".join("links_json LIKE ?" for _ in video_link_patterns)
    expected_external_messages = con.execute(
        f"SELECT COUNT(*) FROM messages WHERE links_json IS NOT NULL AND ({external_conditions})",
        video_link_patterns,
    ).fetchone()[0]
    downloaded_external = con.execute(
        "SELECT COUNT(*) FROM finance_video_files WHERE video_source='external_link' AND is_stale=0"
    ).fetchone()[0]
    matched_external = con.execute(
        "SELECT COUNT(*) FROM finance_video_files WHERE video_source='external_link' AND message_id IS NOT NULL AND is_stale=0"
    ).fetchone()[0]
    valid_external = con.execute(
        "SELECT COUNT(*) FROM finance_video_files WHERE video_source='external_link' AND is_valid=1 AND is_stale=0"
    ).fetchone()[0]

    total_bytes = con.execute("SELECT COALESCE(SUM(size_bytes), 0) FROM finance_video_files WHERE is_stale=0").fetchone()[0]
    total_duration = con.execute("SELECT COALESCE(SUM(duration_sec), 0) FROM finance_video_files WHERE is_stale=0").fetchone()[0]
    return {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "native": {
            "expected_video_messages": expected_native,
            "downloaded_files": downloaded_native,
            "valid_files": valid_native,
            "matched_files": matched_native,
            "coverage_by_files": round(downloaded_native / expected_native, 4) if expected_native else None,
            "coverage_by_matched_files": round(matched_native / expected_native, 4) if expected_native else None,
        },
        "external": {
            "expected_video_link_messages": expected_external_messages,
            "downloaded_files": downloaded_external,
            "valid_files": valid_external,
            "matched_files": matched_external,
            "coverage_by_files": round(downloaded_external / expected_external_messages, 4) if expected_external_messages else None,
            "coverage_by_matched_files": round(matched_external / expected_external_messages, 4) if expected_external_messages else None,
        },
        "total": {
            "files": downloaded_native + downloaded_external,
            "valid_files": valid_native + valid_external,
            "bytes": total_bytes,
            "gb": round(total_bytes / 1024 / 1024 / 1024, 2),
            "duration_sec": round(total_duration, 1),
            "hours": round(total_duration / 3600, 2),
        },
    }


def export_reports(con: sqlite3.Connection, report: dict) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "video_files_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with (OUT_DIR / "video_files.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "video_source", "source_folder", "relative_path", "filename",
            "size_bytes", "duration_sec", "width", "height", "video_codec", "bitrate",
            "is_valid", "source_peer_id", "message_id",
            "post_url", "detected_msg_id", "detected_url", "match_method",
            "category_id", "category_name", "category_method",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in con.execute(
            """SELECT video_source, source_folder, relative_path, filename,
                      size_bytes, duration_sec, width, height, video_codec, bitrate,
                      is_valid, source_peer_id, message_id,
                      post_url, detected_msg_id, detected_url, match_method,
                      category_id, category_name, category_method
               FROM finance_video_files
               WHERE is_stale=0
               ORDER BY video_source, source_folder, filename"""
        ):
            writer.writerow(dict(row))

    with (OUT_DIR / "missing_native_videos.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["source_title", "date", "message_id", "post_url", "video_duration_sec", "text"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in con.execute(
            """SELECT s.title AS source_title, m.date, m.message_id, m.post_url,
                      m.video_duration_sec, substr(m.text, 1, 300) AS text
               FROM messages m
               JOIN sources s ON s.source_peer_id = m.source_peer_id
               LEFT JOIN finance_video_files f
                ON f.source_peer_id = m.source_peer_id
                AND f.message_id = m.message_id
                AND f.video_source = 'tg_native'
                AND f.is_stale = 0
               WHERE m.media_type = 'video'
                 AND f.file_id IS NULL
               ORDER BY m.date"""
        ):
            writer.writerow(dict(row))


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    init_db(con)
    native_candidates = load_native_candidates(con)
    native_candidate_rows = load_native_candidate_rows(con)
    external_candidates = load_external_candidates(con)
    files = [
        match_file(row, native_candidates, native_candidate_rows, external_candidates)
        for row in scan_files()
    ]
    upsert_files(con, files)
    report = completeness_report(con)
    export_reports(con, report)
    con.close()
    print(f"Indexed files: {report['total']['files']} ({report['total']['gb']} GB)")
    print("Native:", report["native"])
    print("External:", report["external"])
    print(f"Reports: {OUT_DIR / 'video_files_report.json'}, {OUT_DIR / 'video_files.csv'}, {OUT_DIR / 'missing_native_videos.csv'}")


if __name__ == "__main__":
    main()
