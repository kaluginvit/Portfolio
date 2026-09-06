#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_mvp(path: Path):
    spec = importlib.util.spec_from_file_location("fedresurs_mvp_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def find_folder(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    if node.get("type") == "folder" and node.get("name") == name:
        return node
    for child in node.get("children") or []:
        if isinstance(child, dict):
            found = find_folder(child, name)
            if found:
                return found
    return None


def old_to_new(url: str) -> str:
    if "old.bankrot.fedresurs.ru/MessageWindow.aspx" not in url:
        return url
    marker = "ID="
    if marker not in url:
        return url
    message_id = url.split(marker, 1)[1].split("&", 1)[0].upper().replace("-", "")
    return f"https://fedresurs.ru/bankruptmessages/{message_id}"


def collect_links(node: dict[str, Any], trail: list[str], links: list[dict[str, str]]) -> None:
    if node.get("type") == "folder":
        trail = trail + [node.get("name") or ""]
    if node.get("type") == "url":
        url = old_to_new(node.get("url") or "")
        if "fedresurs.ru/bankruptmessages/" in url:
            links.append(
                {
                    "name": node.get("name") or url,
                    "url": url,
                    "folder": " / ".join(trail),
                }
            )
        return
    for child in node.get("children") or []:
        if isinstance(child, dict):
            collect_links(child, trail, links)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bookmarks", type=Path, required=True)
    parser.add_argument("--mvp", type=Path, required=True)
    parser.add_argument("--folder", default="Объявления о торгах")
    parser.add_argument("--use-cache", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    bookmarks = json.loads(args.bookmarks.read_text(encoding="utf-8"))
    target = None
    for root in (bookmarks.get("roots") or {}).values():
        if isinstance(root, dict):
            target = find_folder(root, args.folder)
            if target:
                break
    if not target:
        raise RuntimeError(f"Folder not found: {args.folder}")

    links: list[dict[str, str]] = []
    collect_links(target, [], links)
    if args.limit:
        links = links[: args.limit]

    module = load_mvp(args.mvp)
    module.init_db()

    ok = 0
    failed: list[tuple[str, str]] = []
    for index, link in enumerate(links, start=1):
        print(f"[{index}/{len(links)}] {link['folder']} | {link['url']}")
        try:
            module.fetch_links([link], args.use_cache)
            ok += 1
        except Exception as exc:
            failed.append((link["url"], str(exc)))
            print(f"  FAILED: {exc}")

    module.value_command(argparse.Namespace(margin_of_safety=0.9))
    module.render_command(argparse.Namespace())

    tools_dir = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(tools_dir / "export_fedresurs_cards_tsv.py")], check=True)
    subprocess.run([sys.executable, str(tools_dir / "render_fedresurs_cards_dashboard.py")], check=True)

    print(f"links={len(links)} ok={ok} failed={len(failed)}")
    for url, error in failed[:50]:
        print(f"FAILED_URL={url} | {error}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
