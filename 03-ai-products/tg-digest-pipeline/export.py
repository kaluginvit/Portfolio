"""Экспорт enrichments в CSV / JSON / Markdown."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from db import connect_rw, all_rows

HERE = Path(__file__).parent

_QUERY = """
SELECT
    m.message_id,
    m.date,
    m.text,
    m.forwarded_from,
    e.entities,
    e.tags,
    e.insight
FROM messages m
JOIN enrichments e ON e.message_id = m.message_id
ORDER BY m.date, m.message_id
"""


def _load_rows(db_path: Path) -> list[dict]:
    con = connect_rw(db_path)
    rows = all_rows(con, _QUERY)
    con.close()
    return rows


def _parse_json_field(value: str | None) -> list:
    """Парсит JSON-строку в список; при ошибке возвращает []."""
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else [result]
    except (json.JSONDecodeError, TypeError):
        return []


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def export_csv(db_path: Path, out_dir: Path) -> Path:
    """
    Экспортирует JOIN messages + enrichments в CSV.
    Колонки: message_id, date, text, forwarded_from, entities, tags, insight
    entities и tags — JSON-строки (массивы).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "enrichments.csv"

    rows = _load_rows(db_path)

    fieldnames = ["message_id", "date", "text", "forwarded_from", "entities", "tags", "insight"]

    with out_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "message_id": r["message_id"],
                "date": r["date"],
                "text": r.get("text") or "",
                "forwarded_from": r.get("forwarded_from") or "",
                "entities": r.get("entities") or "[]",
                "tags": r.get("tags") or "[]",
                "insight": r.get("insight") or "",
            })

    print(f"CSV: {out_path} ({len(rows)} строк)")
    return out_path


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def export_json(db_path: Path, out_dir: Path) -> Path:
    """
    Экспортирует JOIN messages + enrichments в JSON.
    entities и tags возвращаются как Python-списки.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "enrichments.json"

    rows = _load_rows(db_path)

    output = []
    for r in rows:
        output.append({
            "message_id": r["message_id"],
            "date": r["date"],
            "text": r.get("text") or "",
            "forwarded_from": r.get("forwarded_from") or "",
            "entities": _parse_json_field(r.get("entities")),
            "tags": _parse_json_field(r.get("tags")),
            "insight": r.get("insight") or "",
        })

    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"JSON: {out_path} ({len(output)} записей)")
    return out_path


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _month_key(date_str: str) -> str:
    """'2023-05-15 ...' → '2023-05'"""
    return (date_str or "")[:7]


def _day_label(date_str: str) -> str:
    """'2023-05-15T10:00:00' → '2023-05-15'"""
    return (date_str or "")[:10]


def export_markdown(db_path: Path, out_dir: Path) -> Path:
    """
    Экспортирует enrichments в Markdown, сгруппированный по месяцам.

    Формат:
    ## 2023-05 (N постов)

    **2023-05-15** · #санкции #нефть
    Роснефть, PDVSA, $10 млрд
    Инсайт: ...
    ---
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "enrichments.md"

    rows = _load_rows(db_path)

    # Группировка по месяцу
    by_month: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_month[_month_key(r["date"])].append(r)

    lines: list[str] = []
    lines.append("# ИнфоПовод — обогащённый архив\n")

    for month in sorted(by_month.keys()):
        month_rows = by_month[month]
        lines.append(f"## {month} ({len(month_rows)} постов)\n")

        for r in month_rows:
            day = _day_label(r["date"])
            tags = _parse_json_field(r.get("tags"))
            entities = _parse_json_field(r.get("entities"))
            insight = (r.get("insight") or "").strip()

            # Строка с датой и тегами
            tags_str = " ".join(f"#{t}" for t in tags) if tags else ""
            header = f"**{day}**"
            if tags_str:
                header += f" · {tags_str}"
            lines.append(header)

            # Сущности
            if entities:
                lines.append(", ".join(str(e) for e in entities))

            # Инсайт
            if insight:
                lines.append(f"Инсайт: {insight}")

            lines.append("---")
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Markdown: {out_path} ({len(rows)} записей, {len(by_month)} месяцев)")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    default_db = HERE / cfg.get("data_dir", "data") / "messages.db"

    parser = argparse.ArgumentParser(description="Экспорт enrichments в файлы")
    parser.add_argument(
        "--format",
        choices=["csv", "json", "md", "all"],
        default="all",
        help="Формат экспорта (default: all)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=HERE / "output",
        help="Директория для экспорта (default: output/)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db,
        help=f"Путь к БД (default: {default_db})",
    )
    args = parser.parse_args()

    fmt: str = args.format
    out_dir: Path = args.out
    db_path: Path = args.db

    if fmt in ("csv", "all"):
        export_csv(db_path, out_dir)
    if fmt in ("json", "all"):
        export_json(db_path, out_dir)
    if fmt in ("md", "all"):
        export_markdown(db_path, out_dir)


if __name__ == "__main__":
    main()
