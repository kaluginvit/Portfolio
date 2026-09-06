"""
Локальный пре-фильтр для ИнфоПовод.

Создаёт таблицу messages_filtered в data/messages.db.
3 этапа:
  1. Длина текста >= min_len
  2. Ключевые слова (если список не пуст)
  3. Шум — очень короткие сообщения без валидных ссылок

Использование:
    python local_gate.py
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent


# ---------------------------------------------------------------------------
# Вспомогательные функции (идентично shared/local_gate.py)
# ---------------------------------------------------------------------------

def _clean_links(links_json: str | None) -> list[str]:
    """Вернуть валидные http/https URL из JSON-закодированного списка."""
    if not links_json:
        return []
    try:
        links = json.loads(links_json)
    except (json.JSONDecodeError, TypeError):
        return []
    return [u for u in links if isinstance(u, str) and u.startswith(("http://", "https://"))]


def _is_relevant(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    t = text.lower()
    return any(kw in t for kw in keywords)


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

def rebuild_filtered(
    db_path: Path,
    keywords: list[str],
    min_len: int = 150,
    filter_on_analyzed_at: bool = False,
) -> dict:
    """
    Пересобрать таблицу messages_filtered в db_path по 3-этапной фильтрации.

    filter_on_analyzed_at=True — исключить message_id, уже имеющиеся в enrichments.

    Возвращает stats dict: total, after_len, after_kw, after_domain, filtered_out, filtered_pct.
    """
    con = sqlite3.connect(db_path)
    try:
        total = con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

        # Этап 1: фильтр по длине (+ опциональный guard на enrichments)
        analyzed_clause = (
            " AND message_id NOT IN (SELECT message_id FROM enrichments)"
            if filter_on_analyzed_at
            else ""
        )
        con.execute("DROP TABLE IF EXISTS messages_filtered")
        con.execute(
            f"CREATE TABLE messages_filtered AS "
            f"SELECT * FROM messages WHERE "
            f"(COALESCE(source, 'channel') = 'channel' OR length(text) >= ?)"
            f"{analyzed_clause}",
            (min_len,),
        )
        after_len = con.execute("SELECT COUNT(*) FROM messages_filtered").fetchone()[0]

        # Этап 2: релевантность по ключевым словам (пропускаем если список пуст)
        after_kw = con.execute("SELECT COUNT(*) FROM messages_filtered").fetchone()[0]
        if keywords:
            rows = con.execute("SELECT rowid, text FROM messages_filtered").fetchall()
            irrelevant_rowids = [r[0] for r in rows if not _is_relevant(r[1] or "", keywords)]
            chunk = 500
            for i in range(0, len(irrelevant_rowids), chunk):
                batch = irrelevant_rowids[i:i + chunk]
                con.execute(
                    "DELETE FROM messages_filtered WHERE rowid IN ({})".format(
                        ",".join("?" * len(batch))
                    ),
                    batch,
                )
            con.commit()
            after_kw = con.execute("SELECT COUNT(*) FROM messages_filtered").fetchone()[0]

        # Этап 3: шум — очень короткий текст без валидных ссылок (только не-channel)
        rows = con.execute("SELECT rowid, text, links, COALESCE(source,'channel') FROM messages_filtered").fetchall()
        noise_rowids = [
            rid
            for rid, text, links_json, src in rows
            if src != 'channel' and len(text or "") < 30 and not _clean_links(links_json)
        ]
        if noise_rowids:
            con.execute(
                "DELETE FROM messages_filtered WHERE rowid IN ({})".format(
                    ",".join("?" * len(noise_rowids))
                ),
                noise_rowids,
            )
            con.commit()
        after_domain = con.execute("SELECT COUNT(*) FROM messages_filtered").fetchone()[0]

    finally:
        con.close()

    return {
        "total": total,
        "after_len": after_len,
        "after_kw": after_kw,
        "after_domain": after_domain,
        "filtered_out": total - after_domain,
        "filtered_pct": (total - after_domain) / total * 100 if total else 0,
    }


def print_stats(stats: dict, min_len: int = 150) -> None:
    print(f"Всего сообщений:           {stats['total']:>6}")
    print(f"После фильтра длины >={min_len}: {stats['after_len']:>6}")
    print(f"После фильтра по теме:     {stats['after_kw']:>6}")
    print(f"После фильтра шума:        {stats['after_domain']:>6}")
    print(f"Отфильтровано итого:       {stats['filtered_out']:>6} ({stats['filtered_pct']:.0f}%)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    config_path = HERE / "config.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    gate_cfg = config.get("local_gate", {})
    min_len: int = gate_cfg.get("min_len", 150)
    keywords: list[str] = [kw.lower() for kw in gate_cfg.get("keywords", [])]

    data_dir = HERE / config.get("data_dir", "data")
    db_path = data_dir / "messages.db"

    print(f"БД:          {db_path}")
    print(f"min_len:     {min_len}")
    print(f"Ключевые слова: {keywords or '(нет — пропускаем всё)'}")
    print()

    stats = rebuild_filtered(db_path, keywords=keywords, min_len=min_len)
    print_stats(stats, min_len=min_len)
