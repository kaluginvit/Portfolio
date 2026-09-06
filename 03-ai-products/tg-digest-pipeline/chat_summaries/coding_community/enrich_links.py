"""
Enrich links_catalog with title, description, metadata, and message context.

No LLM is used. Network calls are made only to the linked services.

Run:
    uv run python chat_summaries/coding_community/enrich_links.py --offline --limit 100
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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
    "web",
)
USER_AGENT = "tg-digest-link-enricher/1.0"
MAX_HTML_BYTES = 512_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to messages.db")
    parser.add_argument("--limit", type=int, default=100, help="Max URLs to enrich")
    parser.add_argument("--kind", action="append", choices=RESOURCE_KINDS, help="Limit to kind; can repeat")
    parser.add_argument("--force", action="store_true", help="Refresh already enriched URLs")
    parser.add_argument("--offline", action="store_true", help="Use only local message context; no network calls")
    parser.add_argument("--online", action="store_true", help="Allow network calls to linked services")
    parser.add_argument("--sleep", type=float, default=0.2, help="Pause between network requests")
    return parser.parse_args()


def request_json(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def request_html(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(MAX_HTML_BYTES)
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
    except Exception:
        return None


def clean_text(value: str | None, limit: int = 500) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def extract_html_metadata(url: str) -> dict:
    page = request_html(url)
    if not page:
        return {"status": "fetch_failed"}

    title = ""
    match = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    if match:
        title = clean_text(re.sub(r"<[^>]+>", " ", match.group(1)), 200)

    description = ""
    patterns = [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, page, re.I | re.S)
        if match:
            description = clean_text(match.group(1), 500)
            break

    return {
        "status": "ok" if title or description else "no_metadata",
        "title": title,
        "description": description,
    }


def github_repo_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        return None
    return f"{parts[0]}/{parts[1].removesuffix('.git')}"


def enrich_github_repo(url: str) -> dict:
    repo = github_repo_id(url)
    if not repo:
        return extract_html_metadata(url)
    data = request_json(f"https://api.github.com/repos/{repo}")
    if not data:
        return extract_html_metadata(url)
    return {
        "status": "ok",
        "title": data.get("full_name") or repo,
        "description": data.get("description") or "",
        "metadata": {
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "language": data.get("language"),
            "archived": data.get("archived"),
            "homepage": data.get("homepage"),
            "topics": data.get("topics") or [],
        },
    }


def hf_resource_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        return None
    if parts[0] in {"models", "spaces", "datasets", "docs", "settings", "login"}:
        return None
    return f"{parts[0]}/{parts[1]}"


def enrich_huggingface(url: str) -> dict:
    resource_id = hf_resource_id(url)
    if not resource_id:
        return extract_html_metadata(url)
    data = request_json(f"https://huggingface.co/api/models/{resource_id}")
    if not data:
        return extract_html_metadata(url)
    card = data.get("cardData") or {}
    description = card.get("description") or data.get("description") or ""
    return {
        "status": "ok",
        "title": data.get("modelId") or resource_id,
        "description": clean_text(description, 500),
        "metadata": {
            "pipeline_tag": data.get("pipeline_tag"),
            "likes": data.get("likes"),
            "downloads": data.get("downloads"),
            "tags": data.get("tags") or [],
        },
    }


ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", re.I)


def enrich_arxiv(url: str) -> dict:
    match = ARXIV_RE.search(url)
    if not match:
        return extract_html_metadata(url)
    arxiv_id = match.group(1)
    api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8", errors="replace")
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml)
        entry = root.find("atom:entry", ns)
        if entry is None:
            return {"status": "not_found"}
        title = clean_text(entry.findtext("atom:title", "", ns), 300)
        summary = clean_text(entry.findtext("atom:summary", "", ns), 700)
        published = (entry.findtext("atom:published", "", ns) or "")[:10]
        return {
            "status": "ok",
            "title": title or f"arXiv:{arxiv_id}",
            "description": summary,
            "metadata": {"arxiv_id": arxiv_id, "published": published},
        }
    except Exception:
        return extract_html_metadata(url)


def enrich_url(url: str, kind: str) -> dict:
    if kind == "github_repo":
        return enrich_github_repo(url)
    if kind == "huggingface":
        return enrich_huggingface(url)
    if kind in {"arxiv", "arxiv_other"}:
        return enrich_arxiv(url)
    return extract_html_metadata(url)


def offline_description(context_text: str, kind: str) -> str:
    if not context_text:
        return f"Local {kind} link; no filtered message context available."
    text = re.sub(r"https?://\S+", "", context_text)
    text = re.sub(r"\s+", " ", text).strip()
    return clean_text(text, 900)


def enrich_offline(url: str, kind: str, fallback_title: str, context_text: str) -> dict:
    return {
        "status": "offline_context",
        "title": fallback_title or urllib.parse.urlparse(url).netloc,
        "description": offline_description(context_text, kind),
        "metadata": {"source": "local_message_context"},
    }


def context_for_url(con: sqlite3.Connection, url: str, limit: int = 5) -> str:
    rows = con.execute(
        """
        SELECT m.date, m.sender_name, m.text
        FROM message_links ml
        JOIN messages m
          ON m.source_peer_id = ml.source_peer_id
         AND m.message_id = ml.message_id
        WHERE ml.url_normalized = ?
          AND ml.is_valid = 1
          AND ml.is_filtered = 1
        ORDER BY m.date DESC
        LIMIT ?
        """,
        (url, limit),
    ).fetchall()
    parts = []
    for date, sender, text in rows:
        snippet = clean_text(text, 700)
        parts.append(f"[{(date or '')[:10]}] {sender or 'anon'}: {snippet}")
    return "\n---\n".join(parts)


def select_targets(con: sqlite3.Connection, kinds: list[str] | None, limit: int | None, force: bool) -> list[sqlite3.Row]:
    params: list[object] = []
    where = ["filtered_mentions > 0"]
    if kinds:
        where.append(f"kind IN ({','.join('?' for _ in kinds)})")
        params.extend(kinds)
    else:
        where.append(f"kind IN ({','.join('?' for _ in RESOURCE_KINDS)})")
        params.extend(RESOURCE_KINDS)
    if not force:
        where.append("(enrich_status IS NULL OR enrich_status IN ('pending', 'fetch_failed', 'no_metadata'))")
    sql_limit = ""
    if limit and limit > 0:
        sql_limit = "LIMIT ?"
        params.append(limit)
    return con.execute(
        f"""
        SELECT url_normalized, kind, title, description
        FROM links_catalog
        WHERE {' AND '.join(where)}
        ORDER BY score DESC, filtered_mentions DESC, url_normalized
        {sql_limit}
        """,
        params,
    ).fetchall()


def update_link(con: sqlite3.Connection, url: str, result: dict, context_text: str) -> None:
    status = result.get("status") or "unknown"
    title = clean_text(result.get("title"), 300)
    description = clean_text(result.get("description"), 1000)
    metadata = result.get("metadata") or {}
    con.execute(
        """
        UPDATE links_catalog
        SET
            title = COALESCE(NULLIF(?, ''), title),
            description = COALESCE(NULLIF(?, ''), description),
            metadata_json = ?,
            enrich_status = ?,
            enriched_at = ?,
            context_text = ?
        WHERE url_normalized = ?
        """,
        (
            title,
            description,
            json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else None,
            status,
            datetime.now(timezone.utc).isoformat(),
            context_text,
            url,
        ),
    )


def enrich_links(
    db_path: Path = DB_PATH,
    kinds: list[str] | None = None,
    limit: int | None = 100,
    force: bool = False,
    offline: bool = True,
    online: bool = False,
    sleep: float = 0.2,
) -> int:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        skipped = con.execute(
            """UPDATE links_catalog SET enrich_status = 'skipped'
               WHERE enrich_status = 'pending'
                 AND kind IN ('telegram_post', 'social')
                 AND filtered_mentions > 0"""
        ).rowcount
        if skipped:
            con.commit()
            print(f"auto-skipped: {skipped} (telegram_post/social)")

        targets = select_targets(con, kinds, limit, force)
        print(f"targets: {len(targets)}")
        for index, row in enumerate(targets, 1):
            url = row["url_normalized"]
            kind = row["kind"]
            print(f"[{index}/{len(targets)}] {kind} {url}")
            context_text = context_for_url(con, url)
            use_offline = offline or not online
            if use_offline:
                result = enrich_offline(url, kind, row["title"], context_text)
            else:
                result = enrich_url(url, kind)
            update_link(con, url, result, context_text)
            con.commit()
            if sleep:
                time.sleep(sleep)
        return len(targets)
    finally:
        con.close()


def main() -> None:
    args = parse_args()
    enrich_links(
        db_path=args.db,
        kinds=args.kind,
        limit=args.limit,
        force=args.force,
        offline=args.offline or not args.online,
        online=args.online,
        sleep=args.sleep,
    )


if __name__ == "__main__":
    main()
