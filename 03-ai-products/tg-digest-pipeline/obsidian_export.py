"""Экспорт тегов и сущностей из enrichments в Obsidian vault."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"
VAULT_DIR = HERE / "obsidian_vault"

MIN_TAG_COUNT = 5
MIN_ENTITY_COUNT = 3
TOP_LINKS = 20  # максимум связей на ноду


def _parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return [str(x).strip() for x in result if x and str(x).strip()]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _sanitize(name: str) -> str:
    """Имя файла: убираем символы, недопустимые в Windows."""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def _link(name: str) -> str:
    return f"[[{name}]]"


def load_data(db_path: Path) -> list[dict]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.execute(
        "SELECT tags, entities FROM enrichments WHERE tags IS NOT NULL"
    )
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def build_counts(rows: list[dict]):
    tag_count: dict[str, int] = defaultdict(int)
    entity_count: dict[str, int] = defaultdict(int)
    tag_entity: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tag_tag: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    entity_entity: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in rows:
        tags = [t.lower() for t in _parse_list(row["tags"])]
        entities = _parse_list(row["entities"])

        for t in tags:
            tag_count[t] += 1
        for e in entities:
            entity_count[e] += 1

        for t in tags:
            for e in entities:
                tag_entity[t][e] += 1

        for i, t1 in enumerate(tags):
            for t2 in tags[i + 1:]:
                tag_tag[t1][t2] += 1
                tag_tag[t2][t1] += 1

        for i, e1 in enumerate(entities):
            for e2 in entities[i + 1:]:
                entity_entity[e1][e2] += 1
                entity_entity[e2][e1] += 1

    return tag_count, entity_count, tag_entity, tag_tag, entity_entity


def top_sorted(d: dict[str, int], n: int) -> list[str]:
    return [k for k, _ in sorted(d.items(), key=lambda x: -x[1])[:n]]


def write_tag(
    name: str,
    count: int,
    related_entities: list[str],
    related_tags: list[str],
    out_dir: Path,
) -> None:
    lines = [f"# {name}", f"Постов: {count}", ""]
    if related_entities:
        lines += ["## Сущности", " · ".join(_link(e) for e in related_entities), ""]
    if related_tags:
        lines += ["## Связанные теги", " · ".join(_link(t) for t in related_tags), ""]
    path = out_dir / f"{_sanitize(name)}.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def write_entity(
    name: str,
    count: int,
    related_tags: list[str],
    related_entities: list[str],
    out_dir: Path,
) -> None:
    lines = [f"# {name}", f"Постов: {count}", ""]
    if related_tags:
        lines += ["## Теги", " · ".join(_link(t) for t in related_tags), ""]
    if related_entities:
        lines += ["## Связанные сущности", " · ".join(_link(e) for e in related_entities), ""]
    path = out_dir / f"{_sanitize(name)}.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def write_index(
    tags: list[tuple[str, int]],
    entities: list[tuple[str, int]],
    out_path: Path,
) -> None:
    lines = ["# ИнфоПовод — граф знаний", ""]
    lines += [f"Тегов: **{len(tags)}** · Сущностей: **{len(entities)}**", ""]
    lines += ["## Топ-30 тегов"]
    lines += [" · ".join(_link(t) for t, _ in tags[:30]), ""]
    lines += ["## Топ-30 сущностей"]
    lines += [" · ".join(_link(e) for e, _ in entities[:30]), ""]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print(f"Читаем {DB_PATH} ...")
    rows = load_data(DB_PATH)
    print(f"Строк enrichments: {len(rows)}")

    tag_count, entity_count, tag_entity, tag_tag, entity_entity = build_counts(rows)

    # Фильтрация
    valid_tags = {t for t, c in tag_count.items() if c >= MIN_TAG_COUNT}
    valid_entities = {e for e, c in entity_count.items() if c >= MIN_ENTITY_COUNT}
    print(f"Тегов (>= {MIN_TAG_COUNT} постов): {len(valid_tags)}")
    print(f"Сущностей (>= {MIN_ENTITY_COUNT} постов): {len(valid_entities)}")

    tags_dir = VAULT_DIR / "теги"
    entities_dir = VAULT_DIR / "сущности"
    tags_dir.mkdir(parents=True, exist_ok=True)
    entities_dir.mkdir(parents=True, exist_ok=True)

    # Записываем теги
    for tag in valid_tags:
        rel_entities = [
            e for e in top_sorted(tag_entity.get(tag, {}), TOP_LINKS)
            if e in valid_entities
        ]
        rel_tags = [
            t for t in top_sorted(tag_tag.get(tag, {}), TOP_LINKS)
            if t in valid_tags and t != tag
        ]
        write_tag(tag, tag_count[tag], rel_entities, rel_tags, tags_dir)

    # Записываем сущности
    for entity in valid_entities:
        rel_tags = top_sorted(
            {t: tag_entity[t].get(entity, 0) for t in valid_tags if tag_entity[t].get(entity, 0) > 0},
            TOP_LINKS,
        )
        rel_entities = [
            e for e in top_sorted(entity_entity.get(entity, {}), TOP_LINKS)
            if e in valid_entities and e != entity
        ]
        write_entity(entity, entity_count[entity], rel_tags, rel_entities, entities_dir)

    # Главная страница
    sorted_tags = sorted(valid_tags, key=lambda t: -tag_count[t])
    sorted_entities = sorted(valid_entities, key=lambda e: -entity_count[e])
    write_index(
        [(t, tag_count[t]) for t in sorted_tags],
        [(e, entity_count[e]) for e in sorted_entities],
        VAULT_DIR / "_Главная.md",
    )

    print(f"\nVault готов: {VAULT_DIR}")
    print("Откройте папку как Vault в Obsidian -> Graph View (Ctrl+G)")


if __name__ == "__main__":
    main()
