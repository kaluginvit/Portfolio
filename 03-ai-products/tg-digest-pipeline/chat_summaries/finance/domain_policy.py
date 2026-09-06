"""
Manage finance link domain policy.

Policies:
  keep     - use links from this domain in exports/UI
  suppress - keep links in DB, but exclude from working exports/UI
  review   - undecided; kept in DB, excluded from working exports/UI

Run:
    uv run python finance/domain_policy.py --review --limit 50
    uv run python finance/domain_policy.py --set rbc.ru keep
    uv run python finance/domain_policy.py --set t.me suppress --notes "internal TG links"
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


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_link_domain_policy (
            domain      TEXT PRIMARY KEY,
            policy      TEXT NOT NULL CHECK(policy IN ('keep', 'suppress', 'review')),
            notes       TEXT,
            updated_at  TEXT NOT NULL
        )"""
    )
    con.commit()


def set_policy(domain: str, policy: str, notes: str | None) -> None:
    con = sqlite3.connect(DB_PATH)
    ensure_schema(con)
    con.execute(
        """INSERT INTO finance_link_domain_policy(domain, policy, notes, updated_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(domain) DO UPDATE SET
             policy=excluded.policy,
             notes=excluded.notes,
             updated_at=excluded.updated_at""",
        (domain.lower().replace("www.", ""), policy, notes or "", datetime.now(timezone.utc).isoformat()),
    )
    con.commit()
    con.close()
    print(f"{domain}: {policy}")


def review(limit: int) -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    rows = con.execute(
        """SELECT
              l.domain,
              COALESCE(p.policy, 'review') AS policy,
              COUNT(*) AS urls,
              SUM(l.mentions) AS mentions,
              GROUP_CONCAT(DISTINCT l.kind) AS kinds
           FROM finance_links l
           LEFT JOIN finance_link_domain_policy p ON p.domain = l.domain
           GROUP BY l.domain, COALESCE(p.policy, 'review')
           ORDER BY
             CASE COALESCE(p.policy, 'review')
               WHEN 'review' THEN 1
               WHEN 'keep' THEN 2
               ELSE 3
             END,
             urls DESC,
             mentions DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / "finance_domains_review.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domain", "policy", "urls", "mentions", "kinds"])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    for row in rows:
        print(f"{row['domain']:<36} {row['policy']:<8} urls={row['urls']:<4} mentions={row['mentions']:<5} kinds={row['kinds']}")
    print(f"Exported: {path}")
    con.close()


_SUPPRESS_PATTERNS = [
    "t.me", "telegram.me", "telegram.org",
    "youtube.com", "youtu.be", "rutube.ru", "vkvideo.ru", "vk.com",
    "instagram.com", "facebook.com", "twitter.com", "x.com",
    "tiktok.com", "ok.ru",
    "appmetrica.yandex.com", "redirect.appmetrica.yandex.com",
]

_KEEP_PATTERNS = [
    "fd.ru", "1fd.ru", "fin-academy.pro", "fin-ctrl.ru", "finaverix.ru",
    "noboring-finance.ru", "mpnl.ru", "finmarket.ru", "rbc.ru",
    "tbank.ru", "tinkoff.ru", "ozon.ru", "wildberries.ru",
    "vc.ru", "habr.com", "forbes.ru", "kommersant.ru",
    "ft.com", "wsj.com", "economist.com", "bloomberg.com",
    "minfin.ru", "nalog.gov.ru", "cbr.ru", "consultant.ru", "garant.ru",
    "kad.arbitr.ru", "arbitr.ru",
]


def _heuristic_suggest(domain: str) -> str | None:
    d = domain.lower()
    for pat in _SUPPRESS_PATTERNS:
        if d == pat or d.endswith("." + pat):
            return "suppress"
    for pat in _KEEP_PATTERNS:
        if d == pat or d.endswith("." + pat):
            return "keep"
    return None


def ensure_suggestions_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_domain_suggestions (
            domain TEXT PRIMARY KEY,
            suggestion TEXT NOT NULL,
            reason TEXT,
            model TEXT,
            suggested_at TEXT NOT NULL,
            applied INTEGER NOT NULL DEFAULT 0
        )"""
    )
    con.commit()


def auto_suggest(limit: int, llm_batch: int = 30) -> None:
    import sys
    sys.path.insert(0, str(DB_PATH.parent.parent))
    try:
        from llm_client import call_llm
        has_llm = True
    except ImportError:
        has_llm = False

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    ensure_suggestions_schema(con)

    pending = con.execute(
        """SELECT l.domain, COUNT(*) as urls, SUM(l.mentions) as mentions, l.sample_text, l.category_name
           FROM finance_links l
           LEFT JOIN finance_link_domain_policy p ON l.domain = p.domain
           LEFT JOIN finance_domain_suggestions s ON l.domain = s.domain
           WHERE (p.policy IS NULL OR p.policy = 'review') AND s.domain IS NULL
           GROUP BY l.domain ORDER BY urls DESC LIMIT ?""",
        (limit,),
    ).fetchall()

    heuristic_count = 0
    llm_queue = []
    now = datetime.now(timezone.utc).isoformat()

    for row in pending:
        domain = row["domain"]
        suggestion = _heuristic_suggest(domain)
        if suggestion:
            con.execute(
                """INSERT OR REPLACE INTO finance_domain_suggestions
                   (domain, suggestion, reason, model, suggested_at, applied)
                   VALUES (?, ?, ?, 'heuristic', ?, 0)""",
                (domain, suggestion, f"pattern match → {suggestion}", now),
            )
            heuristic_count += 1
        else:
            llm_queue.append(row)

    con.commit()
    print(f"Heuristic: {heuristic_count} domains suggested")

    if not has_llm or not llm_queue:
        print(f"LLM queue: {len(llm_queue)} domains (skipped — no llm_client or empty queue)")
        con.close()
        return

    llm_count = 0
    for start in range(0, len(llm_queue), llm_batch):
        batch = llm_queue[start:start + llm_batch]
        lines = []
        for r in batch:
            sample = (r["sample_text"] or "")[:80].replace("\n", " ")
            lines.append(f"- {r['domain']} (cat: {r['category_name'] or '?'}, urls: {r['urls']}, sample: {sample})")
        prompt = (
            "Ты оцениваешь домены для финансового агрегатора (финансы, бухучёт, налоги, автоматизация).\n"
            "Для каждого домена ответь: keep (полезный финансовый ресурс) или suppress (реклама, спам, нерелевантное).\n"
            "Верни JSON: [{\"domain\": \"...\", \"suggestion\": \"keep|suppress\", \"reason\": \"до 80 символов\"}]\n\n"
            "Домены:\n" + "\n".join(lines)
        )
        try:
            content, model_used, _ = call_llm(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                env_path=DB_PATH.parents[2] / ".env",
            )
            import json as _json
            items = _json.loads(content.strip().lstrip("```json").rstrip("```"))
            if isinstance(items, list):
                for item in items:
                    if "domain" in item and "suggestion" in item and item["suggestion"] in ("keep", "suppress"):
                        con.execute(
                            """INSERT OR REPLACE INTO finance_domain_suggestions
                               (domain, suggestion, reason, model, suggested_at, applied)
                               VALUES (?, ?, ?, ?, ?, 0)""",
                            (item["domain"], item["suggestion"], item.get("reason", ""), model_used, now),
                        )
                        llm_count += 1
            con.commit()
        except Exception as exc:
            print(f"LLM batch failed: {exc}")

    print(f"LLM: {llm_count} domains suggested")
    con.close()


def apply_suggestions(dry_run: bool = False) -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    ensure_suggestions_schema(con)

    rows = con.execute(
        "SELECT domain, suggestion, reason FROM finance_domain_suggestions WHERE applied=0"
    ).fetchall()

    print(f"Applying {len(rows)} suggestions {'(dry-run)' if dry_run else ''}:")
    now = datetime.now(timezone.utc).isoformat()
    applied = 0
    for row in rows:
        print(f"  {row['domain']}: {row['suggestion']} ({row['reason']})")
        if not dry_run:
            domain = row["domain"].lower().replace("www.", "")
            con.execute(
                """INSERT INTO finance_link_domain_policy(domain, policy, notes, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(domain) DO UPDATE SET
                     policy=excluded.policy,
                     notes=excluded.notes,
                     updated_at=excluded.updated_at""",
                (domain, row["suggestion"], row["reason"] or "", now),
            )
            con.execute("UPDATE finance_domain_suggestions SET applied=1 WHERE domain=?", (row["domain"],))
            applied += 1
    if not dry_run:
        con.commit()
        print(f"Applied: {applied} domains")
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--set", nargs=2, metavar=("DOMAIN", "POLICY"))
    parser.add_argument("--notes", default="")
    parser.add_argument("--auto-suggest", action="store_true", help="Auto-suggest keep/suppress for review domains.")
    parser.add_argument("--llm-batch", type=int, default=30, help="Batch size for LLM domain classification.")
    parser.add_argument("--apply-suggestions", action="store_true", help="Apply auto-suggested policies.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.set:
        domain, policy = args.set
        if policy not in {"keep", "suppress", "review"}:
            parser.error("POLICY must be keep, suppress, or review")
        set_policy(domain, policy, args.notes)
    if args.review:
        review(args.limit)
    if args.auto_suggest:
        auto_suggest(args.limit, llm_batch=args.llm_batch)
    if args.apply_suggestions:
        apply_suggestions(dry_run=args.dry_run)
    if not any([args.set, args.review, args.auto_suggest, args.apply_suggestions]):
        parser.print_help()


if __name__ == "__main__":
    main()
