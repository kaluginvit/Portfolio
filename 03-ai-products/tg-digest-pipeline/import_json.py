"""
Импорт result.json (экспорт Telegram Desktop) в data/messages.db.

Использование:
    python import_json.py [--result result.json] [--db data/messages.db]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent

from db import connect_rw
from schema import init_db


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def extract_text(text_field) -> str:
    """Извлечь plain-текст из поля text сообщения."""
    if isinstance(text_field, str):
        return text_field
    if isinstance(text_field, list):
        parts: list[str] = []
        for item in text_field:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""


def extract_hashtags(text: str) -> list[str]:
    """Найти все #хэштеги в тексте."""
    return re.findall(r"#\w+", text)


def extract_links(text_field) -> list[str]:
    """Извлечь href из dict-элементов типа text_link."""
    if not isinstance(text_field, list):
        return []
    links: list[str] = []
    for item in text_field:
        if isinstance(item, dict) and item.get("type") == "text_link":
            href = item.get("href", "")
            if href:
                links.append(href)
    return links


# ---------------------------------------------------------------------------
# Основная логика импорта
# ---------------------------------------------------------------------------

def import_messages(result_path: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = init_db(db_path)

    print(f"Загружаем {result_path} ...")
    with open(result_path, encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])
    total = len(messages)
    print(f"Всего записей в файле: {total}")

    imported = 0
    skipped = 0

    for i, msg in enumerate(messages, 1):
        if i % 1000 == 0:
            print(f"Обработано: {i} / {total}")

        # Пропускаем сервисные сообщения
        if msg.get("type") != "message":
            skipped += 1
            continue

        message_id: int = msg.get("id")
        date: str = msg.get("date", "")
        edited: str | None = msg.get("edited")

        text_field = msg.get("text", "")
        text = extract_text(text_field)
        links = extract_links(text_field)
        raw_tags = extract_hashtags(text)

        # Источник пересылки
        fwd_from: str | None = msg.get("forwarded_from")
        fwd_from_id: str | None = None
        if isinstance(msg.get("forwarded_from_id"), (int, str)):
            fwd_from_id = str(msg["forwarded_from_id"])

        # Фото
        photo: str | None = msg.get("photo")
        has_photo: int = 1 if photo else 0

        try:
            con.execute(
                """
                INSERT OR IGNORE INTO messages
                    (message_id, date, text, forwarded_from, forwarded_from_id,
                     photo, has_photo, edited, links, raw_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    date,
                    text,
                    fwd_from,
                    fwd_from_id,
                    photo,
                    has_photo,
                    edited,
                    json.dumps(links, ensure_ascii=False),
                    json.dumps(raw_tags, ensure_ascii=False),
                ),
            )
            if con.execute("SELECT changes()").fetchone()[0] > 0:
                # Новая запись — добавляем в FTS
                con.execute(
                    "INSERT INTO messages_fts(message_id, text) VALUES (?, ?)",
                    (message_id, text),
                )
                imported += 1
            else:
                skipped += 1
        except sqlite3.Error as exc:
            print(f"  [WARN] message_id={message_id}: {exc}")
            skipped += 1

    con.commit()
    con.close()

    print(f"\nИмпортировано новых: {imported}, пропущено (дубли): {skipped}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Импорт result.json в SQLite БД")
    parser.add_argument(
        "--result",
        type=Path,
        default=HERE / "result.json",
        help="Путь к result.json (по умолчанию: result.json)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=HERE / "data" / "messages.db",
        help="Путь к БД (по умолчанию: data/messages.db)",
    )
    args = parser.parse_args()
    import_messages(args.result, args.db)


if __name__ == "__main__":
    main()
