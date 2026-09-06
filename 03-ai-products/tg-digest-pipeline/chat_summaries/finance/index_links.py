"""
Index finance links as first-class categorized objects.

The script reads `messages.links_json`, joins message-level finance analysis,
and writes normalized unique URLs into `finance_links`.

Run:
    uv run python finance/index_links.py
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DB_PATH = ROOT / "finance_messages.db"
OUT_DIR = ROOT / "output"
PIPELINE_VERSION = "finance-practical-v1"


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("www."):
        url = f"https://{url}"
    if url.startswith("t.me/"):
        url = f"https://{url}"
    parsed = urlparse(url)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/") or parsed.path
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "yclid", "gclid"}
    ]
    query = urlencode(query_pairs, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def link_kind(url: str) -> str:
    domain = urlparse(url).netloc.lower().replace("www.", "")
    if domain == "t.me":
        return "telegram"
    if domain in {"vkvideo.ru", "vk.com", "rutube.ru", "youtube.com", "youtu.be"}:
        return "video"
    if domain.endswith("ru") or domain.endswith("com") or domain.endswith("pro"):
        return "web"
    return "other"


def init_db(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_link_domain_policy (
            domain      TEXT PRIMARY KEY,
            policy      TEXT NOT NULL CHECK(policy IN ('keep', 'suppress', 'review')),
            notes       TEXT,
            updated_at  TEXT NOT NULL
        )"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_links (
            url_normalized    TEXT PRIMARY KEY,
            domain            TEXT NOT NULL,
            kind              TEXT NOT NULL,
            category_id       INTEGER NOT NULL,
            category_name     TEXT NOT NULL,
            category_method   TEXT NOT NULL,
            domain_policy     TEXT NOT NULL DEFAULT 'review',
            use_in_outputs    INTEGER NOT NULL DEFAULT 0,
            mentions          INTEGER NOT NULL,
            messages_count    INTEGER NOT NULL,
            sources_count     INTEGER NOT NULL,
            first_date        TEXT,
            last_date         TEXT,
            source_titles_json TEXT NOT NULL,
            message_refs_json TEXT NOT NULL,
            sample_text       TEXT,
            seen_at           TEXT,
            is_stale          INTEGER NOT NULL DEFAULT 0,
            indexed_at        TEXT NOT NULL
        )"""
    )
    cols = {row[1] for row in con.execute("PRAGMA table_info(finance_links)")}
    if "domain_policy" not in cols:
        con.execute("ALTER TABLE finance_links ADD COLUMN domain_policy TEXT NOT NULL DEFAULT 'review'")
    if "use_in_outputs" not in cols:
        con.execute("ALTER TABLE finance_links ADD COLUMN use_in_outputs INTEGER NOT NULL DEFAULT 0")
    if "seen_at" not in cols:
        con.execute("ALTER TABLE finance_links ADD COLUMN seen_at TEXT")
    if "is_stale" not in cols:
        con.execute("ALTER TABLE finance_links ADD COLUMN is_stale INTEGER NOT NULL DEFAULT 0")
    con.commit()


def build_index(con: sqlite3.Connection) -> list[dict]:
    con.row_factory = sqlite3.Row
    policies = {
        row["domain"]: row["policy"]
        for row in con.execute("SELECT domain, policy FROM finance_link_domain_policy")
    }
    rows = con.execute(
        """SELECT
              m.source_peer_id, m.message_id, m.date, m.links_json, m.text,
              s.title AS source_title,
              a.category_id, a.category_name
           FROM messages m
           JOIN sources s ON s.source_peer_id = m.source_peer_id
           LEFT JOIN finance_item_analysis a
             ON a.source_peer_id = m.source_peer_id
            AND a.message_id = m.message_id
            AND a.pipeline_version = ?
            AND a.status = 'reviewed'
           WHERE m.links_json IS NOT NULL""",
        (PIPELINE_VERSION,),
    ).fetchall()
    links: dict[str, dict] = {}
    category_votes: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        for raw_url in json.loads(row["links_json"] or "[]"):
            url = normalize_url(raw_url)
            if not url:
                continue
            if url not in links:
                links[url] = {
                    "url_normalized": url,
                    "domain": urlparse(url).netloc.lower().replace("www.", ""),
                    "kind": link_kind(url),
                    "mentions": 0,
                    "message_refs": set(),
                    "source_titles": set(),
                    "dates": [],
                    "sample_text": row["text"] or "",
                }
            item = links[url]
            item["mentions"] += 1
            item["message_refs"].add((row["source_peer_id"], row["message_id"]))
            item["source_titles"].add(row["source_title"])
            item["dates"].append(row["date"])
            if row["category_id"]:
                category_votes[url][(int(row["category_id"]), row["category_name"])] += 1

    indexed = []
    now = datetime.now(timezone.utc).isoformat()
    for url, item in links.items():
        if category_votes[url]:
            (category_id, category_name), _ = category_votes[url].most_common(1)[0]
            category_method = "message_analysis"
        else:
            category_id, category_name, category_method = 11, "Мусор / реклама / нерелевантное", "fallback"
        dates = sorted(item["dates"])
        message_refs = [
            {"source_peer_id": source_peer_id, "message_id": message_id}
            for source_peer_id, message_id in sorted(item["message_refs"])
        ]
        indexed.append(
            {
                "url_normalized": url,
                "domain": item["domain"],
                "kind": item["kind"],
                "category_id": category_id,
                "category_name": category_name,
                "category_method": category_method,
                "domain_policy": policies.get(item["domain"], "review"),
                "use_in_outputs": 1 if policies.get(item["domain"]) == "keep" else 0,
                "mentions": item["mentions"],
                "messages_count": len(item["message_refs"]),
                "sources_count": len(item["source_titles"]),
                "first_date": dates[0] if dates else None,
                "last_date": dates[-1] if dates else None,
                "source_titles_json": json.dumps(sorted(item["source_titles"]), ensure_ascii=False),
                "message_refs_json": json.dumps(message_refs, ensure_ascii=False),
                "sample_text": (item["sample_text"] or "")[:600],
                "seen_at": now,
                "is_stale": 0,
                "indexed_at": now,
            }
        )
    return indexed


def save_index(con: sqlite3.Connection, rows: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    con.execute("UPDATE finance_links SET is_stale=1, indexed_at=?", (now,))
    con.executemany(
        """INSERT INTO finance_links (
            url_normalized, domain, kind, category_id, category_name,
            category_method, domain_policy, use_in_outputs,
            mentions, messages_count, sources_count,
            first_date, last_date, source_titles_json, message_refs_json,
            sample_text, seen_at, is_stale, indexed_at
        ) VALUES (
            :url_normalized, :domain, :kind, :category_id, :category_name,
            :category_method, :domain_policy, :use_in_outputs,
            :mentions, :messages_count, :sources_count,
            :first_date, :last_date, :source_titles_json, :message_refs_json,
            :sample_text, :seen_at, :is_stale, :indexed_at
        )
        ON CONFLICT(url_normalized) DO UPDATE SET
            domain=excluded.domain,
            kind=excluded.kind,
            category_id=excluded.category_id,
            category_name=excluded.category_name,
            category_method=excluded.category_method,
            domain_policy=excluded.domain_policy,
            use_in_outputs=excluded.use_in_outputs,
            mentions=excluded.mentions,
            messages_count=excluded.messages_count,
            sources_count=excluded.sources_count,
            first_date=excluded.first_date,
            last_date=excluded.last_date,
            source_titles_json=excluded.source_titles_json,
            message_refs_json=excluded.message_refs_json,
            sample_text=excluded.sample_text,
            seen_at=excluded.seen_at,
            is_stale=0,
            indexed_at=excluded.indexed_at""",
        rows,
    )
    con.commit()


def export(con: sqlite3.Connection) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    rows = con.execute(
        """SELECT *
           FROM finance_links
           WHERE is_stale=0
           ORDER BY mentions DESC, messages_count DESC, category_id, url_normalized"""
    ).fetchall()
    with (OUT_DIR / "finance_links_all.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "url_normalized", "domain", "kind", "category_id", "category_name",
            "category_method", "domain_policy", "use_in_outputs",
            "mentions", "messages_count", "sources_count",
            "first_date", "last_date", "source_titles", "sample_text",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "url_normalized": row["url_normalized"],
                    "domain": row["domain"],
                    "kind": row["kind"],
                    "category_id": row["category_id"],
                    "category_name": row["category_name"],
                    "category_method": row["category_method"],
                    "domain_policy": row["domain_policy"],
                    "use_in_outputs": row["use_in_outputs"],
                    "mentions": row["mentions"],
                    "messages_count": row["messages_count"],
                    "sources_count": row["sources_count"],
                    "first_date": row["first_date"],
                    "last_date": row["last_date"],
                    "source_titles": "; ".join(json.loads(row["source_titles_json"] or "[]")),
                    "sample_text": row["sample_text"],
                }
            )

    active_rows = [row for row in rows if row["use_in_outputs"]]
    with (OUT_DIR / "finance_links.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "url_normalized", "domain", "kind", "category_id", "category_name",
            "mentions", "messages_count", "sources_count", "first_date",
            "last_date", "source_titles", "sample_text",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in active_rows:
            writer.writerow(
                {
                    "url_normalized": row["url_normalized"],
                    "domain": row["domain"],
                    "kind": row["kind"],
                    "category_id": row["category_id"],
                    "category_name": row["category_name"],
                    "mentions": row["mentions"],
                    "messages_count": row["messages_count"],
                    "sources_count": row["sources_count"],
                    "first_date": row["first_date"],
                    "last_date": row["last_date"],
                    "source_titles": "; ".join(json.loads(row["source_titles_json"] or "[]")),
                    "sample_text": row["sample_text"],
                }
            )

    stats = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "links": len(rows),
        "active_links": len(active_rows),
        "categories": {},
        "kinds": {},
        "domain_policy": {},
        "domains_top": {},
    }
    for row in rows:
        stats["categories"][row["category_name"]] = stats["categories"].get(row["category_name"], 0) + 1
        stats["kinds"][row["kind"]] = stats["kinds"].get(row["kind"], 0) + 1
        stats["domain_policy"][row["domain_policy"]] = stats["domain_policy"].get(row["domain_policy"], 0) + 1
        stats["domains_top"][row["domain"]] = stats["domains_top"].get(row["domain"], 0) + 1
    stats["domains_top"] = dict(sorted(stats["domains_top"].items(), key=lambda item: -item[1])[:30])
    (OUT_DIR / "finance_links_report.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    init_db(con)
    rows = build_index(con)
    save_index(con, rows)
    export(con)
    print(f"Indexed links: {len(rows)}")
    print(f"Reports: {OUT_DIR / 'finance_links.csv'}, {OUT_DIR / 'finance_links_all.csv'}, {OUT_DIR / 'finance_links_report.json'}")
    con.close()


if __name__ == "__main__":
    main()
