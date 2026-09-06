"""
Rebuild normalized link tables for coding_community/messages.db.

This script is safe to rerun. It keeps messages.links intact and recreates only
derived tables:
  - sources
  - message_links
  - links_catalog

Run:
    uv run python chat_summaries/coding_community/rebuild_links.py
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = Path(__file__).parent / "messages.db"
TRAILING_PUNCTUATION = """.,;:!?)\]}'" """

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "yclid",
    "ysclid",
    "s",
    "t",
    "ref",
    "referrer",
    "start",
}

DOMAIN_BLOCKLIST = {
    "249860.redirect.appmetrica.yandex.com",
    "313810.redirect.appmetrica.yandex.com",
    "redirect.appmetrica.yandex.com",
    "t.co",
    "clck.ru",
    "d.code-qr.ru",
    "qr.nspk.ru",
    "telemost.360.yandex.ru",
    "telemost.yandex.ru",
    "mailer.mail.ru",
    "film-api-check.emergent.host",
}

GITHUB_RE = re.compile(r"^/([^/\s]+)/([^/\s#?]+)")
ARXIV_RE = re.compile(r"^/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", re.I)
TG_POST_RE = re.compile(r"^/[^/]+/\d+")
URL_IN_TEXT_RE = re.compile(r"(https?://|www\.)[^\s<>\"]+", re.I)
BARE_URL_RE = re.compile(
    r"^(?:[a-z0-9-]+\.)+[a-z]{2,24}(?:/[^\s<>\"]*)?$",
    re.I,
)
FILE_EXTENSIONS = {
    "md",
    "txt",
    "json",
    "yaml",
    "yml",
    "toml",
    "py",
    "js",
    "ts",
    "tsx",
    "jsx",
    "css",
    "html",
}

CATEGORIES = {
    1: "AI-генерация",
    2: "AI-агенты / Skills",
    3: "Dev-инструменты",
    4: "Дизайн / UI",
    5: "Self-hosted",
    6: "Утилиты",
    7: "Работа с текстом",
    8: "Образование",
    9: "OSINT",
    10: "Хостинг / Деплой",
    11: "Разное",
}

KIND_WEIGHT = {
    "github_repo": 50,
    "huggingface": 40,
    "arxiv": 35,
    "arxiv_other": 30,
    "github": 25,
    "video": 20,
    "telegram_channel": 15,
    "telegram_post": 10,
    "web": 5,
    "social": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to messages.db")
    return parser.parse_args()


def init_tables(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        DROP TABLE IF EXISTS sources;
        DROP TABLE IF EXISTS message_links;
        DROP TABLE IF EXISTS links_catalog;

        CREATE TABLE sources (
            source_peer_id  INTEGER PRIMARY KEY,
            title           TEXT NOT NULL,
            username        TEXT,
            first_seen      TEXT,
            last_seen       TEXT,
            messages_count  INTEGER NOT NULL DEFAULT 0,
            links_count     INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE message_links (
            link_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            source_peer_id  INTEGER NOT NULL,
            message_id      INTEGER NOT NULL,
            link_index      INTEGER NOT NULL,
            date            TEXT,
            is_filtered     INTEGER NOT NULL DEFAULT 0,
            url_original    TEXT NOT NULL,
            url_normalized  TEXT,
            domain          TEXT,
            kind            TEXT,
            is_valid        INTEGER NOT NULL,
            reject_reason   TEXT,
            UNIQUE(source_peer_id, message_id, link_index)
        );

        CREATE INDEX idx_message_links_message
            ON message_links(source_peer_id, message_id);
        CREATE INDEX idx_message_links_url
            ON message_links(url_normalized);
        CREATE INDEX idx_message_links_domain
            ON message_links(domain);
        CREATE INDEX idx_message_links_valid_kind
            ON message_links(is_valid, kind);

        CREATE TABLE links_catalog (
            url_normalized  TEXT PRIMARY KEY,
            domain          TEXT NOT NULL,
            kind            TEXT NOT NULL,
            title           TEXT,
            description     TEXT,
            section_id      INTEGER NOT NULL DEFAULT 11,
            section_name    TEXT NOT NULL DEFAULT 'Разное',
            score           INTEGER NOT NULL DEFAULT 0,
            first_seen      TEXT,
            last_seen       TEXT,
            mentions        INTEGER NOT NULL,
            messages_count  INTEGER NOT NULL,
            sources_count   INTEGER NOT NULL,
            filtered_mentions       INTEGER NOT NULL DEFAULT 0,
            filtered_messages_count INTEGER NOT NULL DEFAULT 0,
            filtered_sources_count  INTEGER NOT NULL DEFAULT 0,
            review_status   TEXT NOT NULL DEFAULT 'new',
            metadata_json   TEXT,
            enrich_status   TEXT NOT NULL DEFAULT 'pending',
            enriched_at     TEXT,
            context_text    TEXT,
            processed_at    TEXT,
            notes           TEXT
        );

        CREATE INDEX idx_links_catalog_domain
            ON links_catalog(domain);
        CREATE INDEX idx_links_catalog_kind
            ON links_catalog(kind);
        """
    )
    con.commit()


def load_existing_enrichment(con: sqlite3.Connection) -> dict[str, dict]:
    has_catalog = con.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'links_catalog'
        """
    ).fetchone()
    if not has_catalog:
        return {}

    cols = {r[1] for r in con.execute("PRAGMA table_info(links_catalog)").fetchall()}
    wanted = [
        "url_normalized",
        "title",
        "description",
        "metadata_json",
        "enrich_status",
        "enriched_at",
        "context_text",
        "review_status",
        "notes",
    ]
    available = [c for c in wanted if c in cols]
    if "url_normalized" not in available:
        return {}

    rows = con.execute(
        f"SELECT {', '.join(available)} FROM links_catalog"
    ).fetchall()
    result = {}
    for row in rows:
        data = dict(zip(available, row))
        result[data["url_normalized"]] = data
    return result


def normalize_url(raw: str) -> tuple[str | None, str | None, str | None]:
    url = (raw or "").strip().strip(TRAILING_PUNCTUATION)
    if not url:
        return None, None, "empty"
    if any(ch.isspace() for ch in url):
        match = URL_IN_TEXT_RE.search(url)
        if not match:
            return None, None, "contains whitespace"
        url = match.group(0).strip().strip(TRAILING_PUNCTUATION)
    if url.startswith("tps://"):
        url = f"h{url}"
    if url.startswith("ps://"):
        url = f"htt{url}"
    if url.startswith("www."):
        url = f"https://{url}"
    if url.startswith("t.me/"):
        url = f"https://{url}"
    if BARE_URL_RE.match(url):
        suffix = url.rsplit(".", 1)[-1].split("/", 1)[0].lower()
        if suffix in FILE_EXTENSIONS:
            return None, None, "unsupported scheme"
        url = f"https://{url}"

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None, None, "unsupported scheme"
    if not parsed.netloc or "." not in parsed.netloc:
        return None, None, "missing domain"

    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    if domain in DOMAIN_BLOCKLIST:
        return None, domain, "blocked domain"

    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    path = parsed.path.rstrip("/") if parsed.path != "/" else ""
    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            domain,
            path,
            "",
            urlencode(query, doseq=True),
            "",
        )
    )
    return normalized, domain, None


def classify_link(domain: str, normalized: str) -> str:
    parsed = urlparse(normalized)
    path = parsed.path

    if domain == "github.com":
        if path.startswith("/orgs/") or path.startswith("/login"):
            return "github"
        match = GITHUB_RE.match(path)
        if match:
            return "github_repo"
        return "github"
    if domain == "huggingface.co":
        return "huggingface"
    if domain == "arxiv.org":
        return "arxiv" if ARXIV_RE.match(path) else "arxiv_other"
    if domain == "t.me":
        return "telegram_post" if TG_POST_RE.match(path) else "telegram_channel"
    if domain in {"x.com", "twitter.com"}:
        return "social"
    if domain in {"youtube.com", "youtu.be", "rutube.ru", "vkvideo.ru"}:
        return "video"
    return "web"


def token_text(url: str, domain: str) -> str:
    parsed = urlparse(url)
    return f"{domain} {parsed.path} {parsed.query}".lower()


def link_title(url: str, domain: str, kind: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if kind == "github_repo":
        parts = path.split("/")
        return "/".join(parts[:2])
    if kind == "telegram_channel":
        return path or domain
    if kind == "telegram_post":
        return path or domain
    if kind == "huggingface":
        return path or domain
    if kind in {"arxiv", "arxiv_other"}:
        match = ARXIV_RE.match(parsed.path)
        return f"arXiv:{match.group(1)}" if match else path or domain
    if kind == "video":
        return path or domain
    return path or domain


def link_description(url: str, domain: str, kind: str) -> str:
    title = link_title(url, domain, kind)
    if kind == "github_repo":
        return f"GitHub repository: {title}"
    if kind == "github":
        return f"GitHub page: {title}"
    if kind == "huggingface":
        return f"HuggingFace resource: {title}"
    if kind in {"arxiv", "arxiv_other"}:
        return f"arXiv paper/resource: {title}"
    if kind == "video":
        return f"Video resource on {domain}: {title}"
    if kind == "telegram_channel":
        return f"Telegram channel or bot: {title}"
    if kind == "telegram_post":
        return f"Telegram post: {title}"
    return f"Web resource on {domain}: {title}"


def classify_section(url: str, domain: str, kind: str, title: str = "", description: str = "") -> tuple[int, str]:
    text = token_text(url, domain) + " " + (title or "").lower() + " " + (description or "").lower()

    if kind in {"arxiv", "arxiv_other"}:
        return 8, CATEGORIES[8]
    if kind == "video":
        return 8, CATEGORIES[8]

    if any(x in text for x in ("agent", "agents", "mcp", "skill", "skills", "claude-code", "autogpt", "crew", "browser-use", "gpt", "chatgpt", "claude", "gemini", "assistant", "bot")):
        return 2, CATEGORIES[2]
    if any(x in text for x in ("image", "video", "voice", "tts", "stt", "diffusion", "gen", "generate", "nano-banana", "sora", "veo", "flux")):
        return 1, CATEGORIES[1]
    if any(x in text for x in ("ui", "ux", "design", "figma", "component", "shadcn", "tailwind", "css", "frontend")):
        return 4, CATEGORIES[4]
    if any(x in text for x in ("self-host", "selfhost", "local", "ollama", "llama.cpp", "docker", "kubernetes", "compose")):
        return 5, CATEGORIES[5]
    if any(x in text for x in ("deploy", "vercel", "netlify", "cloud", "hosting", "vps", "server", "supabase", "firebase", "railway", "render")):
        return 10, CATEGORIES[10]
    if any(x in text for x in ("osint", "security", "pentest", "scan", "vuln", "exploit", "forensic", "privacy")):
        return 9, CATEGORIES[9]
    if any(x in text for x in ("prompt", "rag", "text", "markdown", "docs", "note", "obsidian", "pdf", "writer", "editor", "memory")):
        return 7, CATEGORIES[7]
    if any(x in text for x in ("course", "learn", "tutorial", "guide", "book", "paper", "awesome", "example", "demo")):
        return 8, CATEGORIES[8]
    if kind in {"github_repo", "github"} or any(x in text for x in ("api", "sdk", "cli", "ide", "cursor", "vscode", "python", "typescript", "react", "n8n", "vibe", "coding")):
        return 3, CATEGORIES[3]
    if any(x in text for x in ("tool", "tools", "parser", "scraper", "automation", "workflow", "extension", "chrome")):
        return 6, CATEGORIES[6]
    return 11, CATEGORIES[11]


def link_score(kind: str, mentions: int, filtered_mentions: int) -> int:
    return filtered_mentions * 10 + mentions * 2 + KIND_WEIGHT.get(kind, 0)


def load_links(raw_json: str | None) -> list[str]:
    if not raw_json:
        return []
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, str) and x.strip()]


def rebuild(db_path: Path) -> dict:
    con = sqlite3.connect(db_path)
    try:
        existing_enrichment = load_existing_enrichment(con)
        init_tables(con)

        filtered_pairs = {
            (int(source_peer_id), int(message_id))
            for source_peer_id, message_id in con.execute(
                """
                SELECT source_peer_id, message_id
                FROM messages_filtered
                """
            ).fetchall()
        }

        rows = con.execute(
            """
            SELECT source_peer_id, message_id, date, links
            FROM messages
            ORDER BY date, source_peer_id, message_id
            """
        ).fetchall()

        source_stats: dict[int, dict] = defaultdict(
            lambda: {
                "first_seen": None,
                "last_seen": None,
                "messages": 0,
                "links": 0,
            }
        )
        catalog: dict[str, dict] = {}
        rejects = Counter()
        inserted_links = 0

        for source_peer_id, message_id, date, links_json in rows:
            source_peer_id = int(source_peer_id)
            message_id = int(message_id)
            is_filtered = int((source_peer_id, message_id) in filtered_pairs)
            stats = source_stats[int(source_peer_id)]
            stats["messages"] += 1
            stats["first_seen"] = min(stats["first_seen"] or date, date or "")
            stats["last_seen"] = max(stats["last_seen"] or date, date or "")

            for index, raw in enumerate(load_links(links_json)):
                normalized, domain, reject_reason = normalize_url(raw)
                is_valid = int(reject_reason is None and normalized is not None and domain is not None)
                kind = classify_link(domain, normalized) if is_valid else None
                if not is_valid:
                    rejects[reject_reason or "invalid"] += 1
                else:
                    stats["links"] += 1
                    item = catalog.setdefault(
                        normalized,
                        {
                            "domain": domain,
                            "kind": kind,
                            "first_seen": date,
                            "last_seen": date,
                            "mentions": 0,
                            "messages": set(),
                            "sources": set(),
                            "filtered_mentions": 0,
                            "filtered_messages": set(),
                            "filtered_sources": set(),
                        },
                    )
                    item["first_seen"] = min(item["first_seen"] or date, date or "")
                    item["last_seen"] = max(item["last_seen"] or date, date or "")
                    item["mentions"] += 1
                    item["messages"].add((source_peer_id, message_id))
                    item["sources"].add(source_peer_id)
                    if is_filtered:
                        item["filtered_mentions"] += 1
                        item["filtered_messages"].add((source_peer_id, message_id))
                        item["filtered_sources"].add(source_peer_id)

                con.execute(
                    """
                    INSERT INTO message_links(
                        source_peer_id, message_id, link_index, date, is_filtered,
                        url_original, url_normalized, domain, kind,
                        is_valid, reject_reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_peer_id,
                        message_id,
                        index,
                        date,
                        is_filtered,
                        raw,
                        normalized,
                        domain,
                        kind,
                        is_valid,
                        reject_reason,
                    ),
                )
                inserted_links += 1

        for source_peer_id, stats in source_stats.items():
            con.execute(
                """
                INSERT INTO sources(
                    source_peer_id, title, username, first_seen, last_seen,
                    messages_count, links_count
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?)
                """,
                (
                    source_peer_id,
                    f"source {source_peer_id}",
                    stats["first_seen"],
                    stats["last_seen"],
                    stats["messages"],
                    stats["links"],
                ),
            )

        now = datetime.now(timezone.utc).isoformat()
        for url, item in catalog.items():
            if item["filtered_mentions"] == 0:
                continue
            previous = existing_enrichment.get(url, {})
            title = previous.get("title") or link_title(url, item["domain"], item["kind"])
            description = previous.get("description") or link_description(url, item["domain"], item["kind"])
            review_status = previous.get("review_status") or "new"
            metadata_json = previous.get("metadata_json")
            enrich_status = previous.get("enrich_status") or "pending"
            enriched_at = previous.get("enriched_at")
            context_text = previous.get("context_text")
            notes = previous.get("notes")
            con.execute(
                """
                INSERT INTO links_catalog(
                    url_normalized, domain, kind, title, description,
                    section_id, section_name, score, first_seen, last_seen,
                    mentions, messages_count, sources_count,
                    filtered_mentions, filtered_messages_count, filtered_sources_count,
                    review_status, metadata_json, enrich_status, enriched_at,
                    context_text, processed_at, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url,
                    item["domain"],
                    item["kind"],
                    title,
                    description,
                    *classify_section(url, item["domain"], item["kind"], title, description),
                    link_score(item["kind"], item["mentions"], item["filtered_mentions"]),
                    item["first_seen"],
                    item["last_seen"],
                    item["mentions"],
                    len(item["messages"]),
                    len(item["sources"]),
                    item["filtered_mentions"],
                    len(item["filtered_messages"]),
                    len(item["filtered_sources"]),
                    review_status,
                    metadata_json,
                    enrich_status,
                    enriched_at,
                    context_text,
                    now,
                    notes,
                ),
            )

        con.commit()
        valid_links = con.execute(
            "SELECT COUNT(*) FROM message_links WHERE is_valid = 1"
        ).fetchone()[0]
        return {
            "messages": len(rows),
            "raw_links": inserted_links,
            "valid_links": valid_links,
            "unique_links": len(catalog),
            "rejects": dict(rejects),
        }
    finally:
        con.close()


def main() -> None:
    args = parse_args()
    stats = rebuild(args.db)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
