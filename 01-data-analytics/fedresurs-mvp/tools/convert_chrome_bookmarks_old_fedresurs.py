#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


OLD_HOST = "old.bankrot.fedresurs.ru"
NEW_PREFIX = "https://fedresurs.ru/bankruptmessages/"


def convert_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc.lower() != OLD_HOST:
        return None
    if not parsed.path.lower().endswith("/messagewindow.aspx"):
        return None
    message_id = parse_qs(parsed.query).get("ID", [""])[0].strip()
    compact = message_id.upper().replace("-", "")
    if len(compact) != 32 or any(ch not in "0123456789ABCDEF" for ch in compact):
        return None
    return NEW_PREFIX + compact


def walk(node: dict[str, Any], converted: list[tuple[str, str, str]]) -> None:
    if node.get("type") == "url":
        old_url = node.get("url") or ""
        new_url = convert_url(old_url)
        if new_url:
            node["url"] = new_url
            converted.append((node.get("name") or "", old_url, new_url))
    for child in node.get("children") or []:
        if isinstance(child, dict):
            walk(child, converted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bookmarks", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.bookmarks.read_text(encoding="utf-8"))
    converted: list[tuple[str, str, str]] = []
    for root in (data.get("roots") or {}).values():
        if isinstance(root, dict):
            walk(root, converted)

    print(f"old_links_found={len(converted)}")
    for name, old_url, new_url in converted[:10]:
        print(f"- {name} | {old_url} -> {new_url}")

    if args.dry_run:
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = args.bookmarks.with_name(f"{args.bookmarks.name}.codex-backup-{stamp}")
    shutil.copy2(args.bookmarks, backup)
    args.bookmarks.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"backup={backup}")
    print(f"converted={len(converted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
