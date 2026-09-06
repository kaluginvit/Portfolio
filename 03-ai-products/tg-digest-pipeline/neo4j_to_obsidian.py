"""Экспорт Neo4j (VPS) -> Obsidian vault локально, затем очистка Neo4j.

Использование:
    Установи переменную окружения NEO4J_PASS перед запуском:
    $env:NEO4J_PASS = "пароль"
    python neo4j_to_obsidian.py           # только экспорт
    python neo4j_to_obsidian.py --delete  # экспорт + очистка Neo4j
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

NEO4J_URL = "http://83.220.174.1:7474"
NEO4J_USER = "neo4j"
NEO4J_PASS = os.environ.get("NEO4J_PASS", "")
VAULT_DIR = Path(__file__).parent / "obsidian_vault_neo4j"

if not NEO4J_PASS:
    print("Ошибка: задай $env:NEO4J_PASS = 'пароль'")
    sys.exit(1)

AUTH = HTTPBasicAuth(NEO4J_USER, NEO4J_PASS)
TX_URL = f"{NEO4J_URL}/db/neo4j/tx/commit"


def cypher(query: str, params: dict | None = None) -> list[dict]:
    body = {"statements": [{"statement": query, "parameters": params or {}}]}
    r = requests.post(TX_URL, json=body, auth=AUTH, timeout=120)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    results = data["results"][0]
    cols = results["columns"]
    return [dict(zip(cols, row["row"])) for row in results["data"]]


def _sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", (name or "без_названия").strip()) or "без_названия"


def _link(name: str) -> str:
    return f"[[{name}]]"


def export_sections(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = cypher("MATCH (s:Section) RETURN s.section_id as id, s.name as name ORDER BY s.name")
    for row in rows:
        name = row.get("name") or f"Раздел {row['id']}"
        path = out_dir / f"{_sanitize(name)}.md"
        path.write_text(f"# {name}\n\nРаздел ID: {row['id']}\n", encoding="utf-8")
    print(f"Разделов: {len(rows)}")


def export_sources(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = cypher("MATCH (s:Source) RETURN s ORDER BY s.title")
    for row in rows:
        s = row["s"]
        title = s.get("title") or s.get("username") or str(s.get("peer_id", "unknown"))
        lines = [f"# {title}", ""]
        if s.get("username"):
            lines.append(f"Username: @{s['username']}")
        if s.get("peer_id"):
            lines.append(f"ID: {s['peer_id']}")
        path = out_dir / f"{_sanitize(title)}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Источников: {len(rows)}")


def export_posts(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    total = cypher("MATCH (p:Post) RETURN count(p) as cnt")[0]["cnt"]
    print(f"Постов: {total}")

    batch = 100
    for skip in range(0, total, batch):
        rows = cypher(f"MATCH (p:Post) RETURN p SKIP {skip} LIMIT {batch}")
        for row in rows:
            p = row["p"]
            post_id = p.get("post_id") or p.get("message_id") or "unknown"
            text = p.get("text_snippet") or ""
            date = p.get("date") or ""
            section = p.get("section_name") or ""
            professions_raw = p.get("for_professions") or "[]"
            try:
                professions = json.loads(professions_raw) if isinstance(professions_raw, str) else professions_raw
            except Exception:
                professions = []
            subcat = p.get("subcategory") or ""
            src_title = ""

            title_text = text[:60].replace("\n", " ").strip() or str(post_id)
            lines = [f"# {title_text}", ""]
            if date:
                lines.append(f"Дата: {date}")
            if section:
                lines.append(f"Раздел: {_link(section)}")
            if src_title:
                lines.append(f"Источник: {_link(src_title)}")
            if professions:
                lines.append(f"Профессии: {', '.join(professions)}")
            if subcat:
                lines.append(f"Категория: {subcat}")
            lines += ["", text]

            slug = _sanitize(str(post_id))
            (out_dir / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")

        print(f"  {min(skip + batch, total)}/{total}")


def delete_all() -> None:
    print("Удаляем все ноды из Neo4j...")
    cypher("MATCH (n) DETACH DELETE n")
    remaining = cypher("MATCH (n) RETURN count(n) as cnt")[0]["cnt"]
    print(f"Осталось нод: {remaining}")


def main() -> None:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Экспорт Neo4j -> Obsidian ===")
    export_sections(VAULT_DIR / "разделы")
    export_sources(VAULT_DIR / "источники")
    export_posts(VAULT_DIR / "посты")
    (VAULT_DIR / "_Главная.md").write_text(
        "# Neo4j архив\n\nЭкспортировано с VPS 83.220.174.1\n\n"
        "- [[разделы]]\n- [[источники]]\n- [[посты]]\n",
        encoding="utf-8",
    )
    print(f"\nVault готов: {VAULT_DIR}")
    if "--delete" in sys.argv:
        delete_all()
        print("Neo4j очищен.")
    else:
        print("\nДля удаления: python neo4j_to_obsidian.py --delete")


if __name__ == "__main__":
    main()
