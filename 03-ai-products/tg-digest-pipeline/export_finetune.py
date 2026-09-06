"""
export_finetune.py — экспорт датасета для fine-tuning Qwen2.5-7B.

Формат: JSONL (ChatML), инсайт -> пост.
Источник: авторские посты (#имеюссообщить) с заполненным insight.

Использование:
    python export_finetune.py
    python export_finetune.py --out finetune_data/dataset.jsonl --min-len 80
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"
OUT_DIR = HERE / "finetune_data"

SYSTEM_PROMPT = (
    "Ты — Виталий Калугин, финансовый аналитик и автор Telegram-канала @kaluginprofit. "
    "Пиши от первого лица: провокационно, прямо, с личной позицией и агрессией к официальным нарративам. "
    "Конкретные цифры, резкие оценки, короткие абзацы, разговорный тон. 150-400 слов. "
    "Без ИИ-маркеров: не использовать 'следует отметить', 'таким образом', 'безусловно', "
    "'с одной стороны', списков и заголовков внутри поста."
)


def export(db_path: Path, out_path: Path, min_len: int = 100) -> int:
    con = sqlite3.connect(db_path)
    rows = con.execute(
        """
        SELECT m.text, e.insight
        FROM messages m
        JOIN enrichments e ON e.message_id = m.message_id
        JOIN user_tags u   ON u.message_id = m.message_id
        WHERE u.tag = '#имеюссообщить'
          AND e.insight IS NOT NULL
          AND e.insight != ''
          AND m.text IS NOT NULL
          AND length(m.text) >= ?
        ORDER BY m.date
        """,
        (min_len,),
    ).fetchall()
    con.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for text, insight in rows:
            text = (text or "").strip()
            insight = (insight or "").strip()
            if not text or not insight:
                continue
            record = {
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": f"Напиши пост по аналитике: {insight}"},
                    {"role": "assistant", "content": text},
                ]
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    return count


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Экспорт датасета для fine-tuning")
    parser.add_argument("--db",      type=Path, default=DB_PATH)
    parser.add_argument("--out",     type=Path, default=OUT_DIR / "dataset.jsonl")
    parser.add_argument("--min-len", type=int,  default=100, help="Минимальная длина текста поста")
    args = parser.parse_args()

    count = export(args.db, args.out, args.min_len)
    print(f"Экспортировано: {count} записей -> {args.out}")

    # Превью первых 2 записей
    with args.out.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 2:
                break
            rec = json.loads(line)
            user_msg = rec["messages"][1]["content"][:120]
            asst_msg = rec["messages"][2]["content"][:120]
            print(f"\n[{i+1}] user: {user_msg}...")
            print(f"     asst: {asst_msg}...")


if __name__ == "__main__":
    main()
