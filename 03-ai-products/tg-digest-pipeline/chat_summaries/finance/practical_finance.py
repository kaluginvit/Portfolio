"""
Build practical finance insight cards from finance_messages.db.

This layer keeps raw Telegram messages intact and writes normalized analysis into
finance_item_analysis.

Run:
    uv run python finance/practical_finance.py --status
    uv run python finance/practical_finance.py --process --batch-size 8
    uv run python finance/practical_finance.py --export
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parents[1]))
from llm_client import call_llm

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
PROJECT_ROOT = ROOT.parent
DB_PATH = ROOT / "finance_messages.db"
OUT_DIR = ROOT / "output"
PIPELINE_VERSION = "finance-practical-v1"
_ENV_PATH = Path(__file__).parents[2] / ".env"

CATEGORIES = {
    1: "Управленческий учет / P&L / ДДС / баланс",
    2: "CFO / финдир / финслужба",
    3: "Налоги / бухучет / регуляторика",
    4: "Маркетплейсы",
    5: "Платежи / ВЭД / SWIFT / SEPA",
    6: "Автоматизация / Excel / BI / AI для финансов",
    7: "Продажи финуслуг / лидогенерация / воронки",
    8: "Инвестиции / рынки / макро",
    9: "Обучение / курсы / вебинары",
    10: "Шаблоны / документы / чек-листы",
    11: "Мусор / реклама / нерелевантное",
}

TARGET_USERS = {
    "owner",
    "cfo",
    "accountant",
    "marketplace_seller",
    "investor",
    "consultant",
    "ops",
    "other",
}


def open_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    return con


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS finance_item_analysis (
            source_peer_id   INTEGER NOT NULL,
            message_id       INTEGER NOT NULL,
            pipeline_version TEXT NOT NULL,
            date             TEXT NOT NULL,
            item_type        TEXT NOT NULL,
            source_title     TEXT,
            post_url         TEXT,
            category_id      INTEGER NOT NULL,
            category_name    TEXT NOT NULL,
            subcategory      TEXT,
            title            TEXT,
            summary          TEXT,
            practical_use    TEXT,
            action_plan_json TEXT,
            tools_json       TEXT,
            tags_json        TEXT,
            target_user      TEXT,
            business_value   TEXT,
            actionability    TEXT,
            priority         TEXT,
            links_json       TEXT,
            model            TEXT,
            status           TEXT NOT NULL,
            analyzed_at      TEXT NOT NULL,
            raw_json         TEXT,
            error            TEXT,
            PRIMARY KEY (source_peer_id, message_id, pipeline_version)
        )"""
    )
    con.execute(
        """CREATE INDEX IF NOT EXISTS idx_finance_item_analysis_category
           ON finance_item_analysis (pipeline_version, category_id, priority)"""
    )
    con.execute(
        """CREATE INDEX IF NOT EXISTS idx_fia_date_priority
           ON finance_item_analysis (pipeline_version, date DESC, priority)"""
    )
    cols = {row[1] for row in con.execute("PRAGMA table_info(finance_item_analysis)")}
    if "prompt_kind" not in cols:
        con.execute("ALTER TABLE finance_item_analysis ADD COLUMN prompt_kind TEXT")
    if "prompt_hash" not in cols:
        con.execute("ALTER TABLE finance_item_analysis ADD COLUMN prompt_hash TEXT")
    if "input_tokens" not in cols:
        con.execute("ALTER TABLE finance_item_analysis ADD COLUMN input_tokens INTEGER")
    if "output_tokens" not in cols:
        con.execute("ALTER TABLE finance_item_analysis ADD COLUMN output_tokens INTEGER")
    if "insight" not in cols:
        con.execute("ALTER TABLE finance_item_analysis ADD COLUMN insight TEXT")
    if "entities_json" not in cols:
        con.execute("ALTER TABLE finance_item_analysis ADD COLUMN entities_json TEXT")
    if "engagement_score" not in cols:
        con.execute("ALTER TABLE finance_item_analysis ADD COLUMN engagement_score REAL")
    # Standalone FTS5 (не external content) — populate вручную через rebuild_fts()
    con.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS finance_fts
           USING fts5(
               source_peer_id UNINDEXED,
               message_id UNINDEXED,
               pipeline_version UNINDEXED,
               title,
               summary,
               insight,
               tags,
               tokenize='unicode61'
           )"""
    )
    con.commit()


def rebuild_fts(con: sqlite3.Connection) -> None:
    con.execute("DELETE FROM finance_fts")
    con.execute(
        """INSERT INTO finance_fts(source_peer_id, message_id, pipeline_version, title, summary, insight, tags)
           SELECT source_peer_id, message_id, pipeline_version,
                  COALESCE(title, ''),
                  COALESCE(summary, ''),
                  COALESCE(insight, ''),
                  COALESCE(tags_json, '')
           FROM finance_item_analysis
           WHERE status = 'reviewed'"""
    )
    con.commit()
    print(f"  FTS rebuilt: {con.execute('SELECT COUNT(*) FROM finance_fts').fetchone()[0]} rows")


def item_type(row: sqlite3.Row) -> str:
    if row["media_type"] == "video":
        return "video"
    if row["links_json"]:
        return "link"
    return "message"


def core_where() -> str:
    return """(
        m.media_type = 'video'
        OR m.links_json IS NOT NULL
        OR m.text_len >= 300
    )"""


def load_targets(
    con: sqlite3.Connection,
    force: bool,
    limit: int | None,
    all_messages: bool,
    local_only: bool = False,
    high_only: bool = False,
    pipeline_version: str | None = None,
) -> list[sqlite3.Row]:
    pv = pipeline_version or PIPELINE_VERSION
    where = ["m.text IS NOT NULL", "m.text != ''"]
    if not all_messages:
        where.append(core_where())
    params: list[object] = []
    if not force:
        where.append(
            """NOT EXISTS (
                SELECT 1 FROM finance_item_analysis a
                WHERE a.source_peer_id = m.source_peer_id
                  AND a.message_id = m.message_id
                  AND a.pipeline_version = ?
                  AND a.status = 'reviewed'
            )"""
        )
        params.append(pv)
    if local_only:
        where.append(
            """EXISTS (
                SELECT 1 FROM finance_item_analysis a2
                WHERE a2.source_peer_id = m.source_peer_id
                  AND a2.message_id = m.message_id
                  AND a2.model = 'local-heuristic-v1'
            )"""
        )
    if high_only:
        where.append(
            """EXISTS (
                SELECT 1 FROM finance_item_analysis a3
                WHERE a3.source_peer_id = m.source_peer_id
                  AND a3.message_id = m.message_id
                  AND a3.pipeline_version = 'finance-practical-v1'
                  AND a3.priority = 'high'
            )"""
        )
    sql_limit = ""
    if limit:
        sql_limit = "LIMIT ?"
        params.append(limit)
    return con.execute(
        f"""SELECT
                m.source_peer_id, m.message_id, m.date, m.text, m.text_len,
                m.links_json, m.media_type, m.video_duration_sec, m.post_url,
                m.views, m.forwards, m.reactions,
                s.title AS source_title
            FROM messages m
            JOIN sources s ON s.source_peer_id = m.source_peer_id
            WHERE {' AND '.join(where)}
            ORDER BY m.date, m.source_peer_id, m.message_id
            {sql_limit}""",
        params,
    ).fetchall()


def load_video_targets(con: sqlite3.Connection, force: bool, limit: int | None) -> list[sqlite3.Row]:
    where = ["m.media_type = 'video'"]
    params: list[object] = []
    if not force:
        where.append(
            """NOT EXISTS (
                SELECT 1 FROM finance_item_analysis a
                WHERE a.source_peer_id = m.source_peer_id
                  AND a.message_id = m.message_id
                  AND a.pipeline_version = ?
                  AND a.status = 'reviewed'
            )"""
        )
        params.append(PIPELINE_VERSION)
    sql_limit = ""
    if limit:
        sql_limit = "LIMIT ?"
        params.append(limit)
    return con.execute(
        f"""SELECT
                m.source_peer_id, m.message_id, m.date, m.text, m.text_len,
                m.links_json, m.media_type, m.video_duration_sec, m.post_url,
                s.title AS source_title
            FROM messages m
            JOIN sources s ON s.source_peer_id = m.source_peer_id
            WHERE {' AND '.join(where)}
            ORDER BY m.date, m.source_peer_id, m.message_id
            {sql_limit}""",
        params,
    ).fetchall()


def compact_text(text: str, max_chars: int = 2200) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + " ..."


def domains(links: list[str]) -> list[str]:
    result = []
    seen = set()
    for link in links:
        domain = urlparse(link).netloc.replace("www.", "")
        if domain and domain not in seen:
            seen.add(domain)
            result.append(domain)
    return result


def build_prompt(rows: list[sqlite3.Row]) -> str:
    payload = []
    for row in rows:
        links = json.loads(row["links_json"] or "[]")
        payload.append(
            {
                "source_peer_id": row["source_peer_id"],
                "message_id": row["message_id"],
                "date": row["date"][:10],
                "source": row["source_title"],
                "item_type": item_type(row),
                "media_type": row["media_type"],
                "video_duration_sec": row["video_duration_sec"],
                "post_url": row["post_url"],
                "links": links,
                "domains": domains(links),
                "text": compact_text(row["text"]),
            }
        )
    categories_text = "\n".join(f"{k}. {v}" for k, v in CATEGORIES.items())
    return f"""Ты анализируешь финансовые Telegram-источники и делаешь практическую базу для бизнеса.

Нужно классифицировать каждую запись и извлечь применимую пользу.

Категории:
{categories_text}

Правила:
- Пиши по-русски, конкретно, без пересказа ради пересказа.
- category_id выбирай строго 1-11.
- Если это реклама без самостоятельной ценности, category_id=11, priority=low, actionability=archive.
- Не называй запись полезной, если из текста непонятно, что делать.
- summary = коротко, что это (1-2 предложения).
- practical_use = как применить в реальной жизни/бизнесе.
- action_plan = 2-5 коротких шагов.
- tools = сервисы, документы, отчеты, методы, системы, если явно есть или разумно вытекают из задачи.
- target_user: owner | cfo | accountant | marketplace_seller | investor | consultant | ops | other.
- business_value = финансовый/операционный эффект.
- actionability: use_now | test | read | watch | contact | save_template | monitor | archive.
- priority: high = конкретный инструмент/метод/кейс с понятным действием прямо сейчас; medium = полезный контекст без немедленного применения; low = общие рассуждения, реклама с ценностью, обучение.
- insight = одно предложение до 200 символов: начни с конкретного факта из текста, добавь неочевидный вывод и практическое следствие. Если нетривиального вывода нет — оставь пустой строкой.
- entities = массив упомянутых в тексте объектов (только реально присутствующие, не придумывать). Тип: company | person | tool | regulation | market.
- Верни только валидный JSON без markdown.

Формат:
{{
  "items": [
    {{
      "source_peer_id": 123,
      "message_id": 456,
      "category_id": 1,
      "subcategory": "ДДС / кассовые разрывы",
      "title": "короткое название",
      "summary": "что это",
      "practical_use": "как применить",
      "action_plan": ["шаг 1", "шаг 2"],
      "tools": ["ДДС", "Excel"],
      "tags": ["cashflow", "planning"],
      "target_user": "cfo",
      "business_value": "снижает риск кассового разрыва",
      "actionability": "use_now",
      "priority": "high",
      "insight": "рост просрочки по кредитам МСБ в Q2 означает ужесточение условий рефинансирования — стоит зафиксировать текущие ставки до конца квартала",
      "entities": [{{"name": "ЦБ РФ", "type": "company"}}, {{"name": "ДДС", "type": "tool"}}]
    }}
  ]
}}

Записи:
{json.dumps(payload, ensure_ascii=False)}
"""


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()




def build_classification_prompt(rows: list[sqlite3.Row]) -> str:
    payload = []
    for row in rows:
        links = json.loads(row["links_json"] or "[]")
        payload.append(
            {
                "source_peer_id": row["source_peer_id"],
                "message_id": row["message_id"],
                "date": row["date"][:10],
                "source": row["source_title"],
                "item_type": item_type(row),
                "media_type": row["media_type"],
                "domains": domains(links),
                "text": compact_text(row["text"], 900),
            }
        )
    categories_text = "\n".join(f"{k}. {v}" for k, v in CATEGORIES.items())
    return f"""Ты классифицируешь финансовые Telegram-записи по смыслу.

Категории:
{categories_text}

Верни только валидный JSON без markdown.
Формат:
{{
  "items": [
    {{
      "source_peer_id": 123,
      "message_id": 456,
      "category_id": 1,
      "confidence": 0.0,
      "reason": "коротко почему"
    }}
  ]
}}

Правила:
- category_id выбирай строго 1-11.
- Если это реклама, розыгрыш, чистый анонс без самостоятельной пользы или непонятный короткий пост, category_id=11.
- confidence от 0 до 1.
- reason до 120 символов.

Записи:
{json.dumps(payload, ensure_ascii=False)}
"""


def parse_json(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def normalize_choice(value: str, allowed: set[str], default: str) -> str:
    value = (value or "").strip()
    return value if value in allowed else default


KEYWORDS = {
    1: (
        "p&l", "pnl", "ддс", "cash flow", "cashflow", "баланс", "отчет", "отчёт",
        "управленчес", "финмодель", "финансовая модель", "маржиналь", "ebitda",
        "прибыль", "рентабель", "кассов", "деньги", "бюджет", "план-факт",
        "юнит-эконом", "du pont", "дюпон",
    ),
    2: (
        "cfo", "финдир", "финансовый директор", "финслуж", "финансовая служба",
        "главный бухгалтер", "регламент", "финансовая функция", "команда финансов",
    ),
    3: (
        "налог", "ндс", "усн", "осн", "патент", "бухуч", "бухгалтер", "фнс",
        "деклара", "счет-фактур", "счёт-фактур", "акт", "первич", "закон",
        "штраф", "камерал", "провер", "регулятор", "152-фз", "персональн",
    ),
    4: (
        "wildberries", "wb", "ozon", "маркетплейс", "селлер", "seller",
        "комисси", "кабинет продавца", "фбо", "фбс", "склад",
    ),
    5: (
        "swift", "sepa", "вэд", "валют", "платеж", "платёж", "перевод",
        "moneyport", "банк", "санкци", "юань", "доллар", "евро", "крипт",
        "инвойс", "invoice", "экспорт", "импорт",
    ),
    6: (
        "excel", "power bi", "bi", "дашборд", "dashboard", "автоматиза",
        "chatgpt", "gpt", "deepseek", "qwen", "ai", "ии", "бот", "скрипт",
        "api", "таблиц", "google sheets", "1с", "1c", "интеграц",
    ),
    7: (
        "лид", "воронк", "продаж", "клиент", "заявк", "консультац",
        "crm", "вебинар", "лендинг", "офер", "трафик", "записаться",
    ),
    8: (
        "акци", "облигац", "рынок", "инвест", "инфляц", "ставк", "цб",
        "мосбирж", "sp500", "s&p", "индекс", "нефть", "золото", "портфель",
        "дивиденд", "макро", "экономик",
    ),
    9: (
        "курс", "урок", "обуч", "школ", "мастер-класс", "мастеркласс",
        "вебинар", "эфир", "запись", "семинар", "интенсив", "лекци",
    ),
    10: (
        "шаблон", "чек-лист", "чеклист", "таблица", "гайд", "инструкц",
        "регламент", "образец", "форма", "калькулятор", "файл",
    ),
}


def local_category(text: str, links: list[str], media_type: str | None) -> int:
    haystack = " ".join([text.lower(), " ".join(links).lower(), media_type or ""])
    scores: dict[int, int] = {}
    for category_id, words in KEYWORDS.items():
        scores[category_id] = sum(1 for word in words if word in haystack)
    best_id, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        if links and len(text.strip()) < 220:
            return 11
        return 1
    return best_id


def local_title(text: str, category_id: int) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    clean = re.sub(r"^[^\wА-Яа-яЁё]+", "", clean)
    if not clean:
        return CATEGORIES[category_id]
    title = clean[:90].rstrip(" .,:;")
    return title or CATEGORIES[category_id]


def local_target_user(category_id: int) -> str:
    return {
        1: "cfo",
        2: "cfo",
        3: "accountant",
        4: "marketplace_seller",
        5: "cfo",
        6: "cfo",
        7: "consultant",
        8: "investor",
        9: "other",
        10: "cfo",
        11: "other",
    }.get(category_id, "other")


def local_actionability(category_id: int, row_type: str) -> str:
    if category_id == 11:
        return "archive"
    if category_id == 10:
        return "save_template"
    if row_type == "video":
        return "watch"
    if category_id in {1, 3, 5, 6}:
        return "use_now"
    if category_id in {8, 9}:
        return "read"
    return "test"


def local_priority(category_id: int, row: sqlite3.Row, text: str) -> str:
    if category_id == 11:
        return "low"
    if category_id in {9, 10}:
        return "medium"
    if category_id == 7:
        return "low" if not row["links_json"] else "medium"
    if category_id in {1, 3, 5, 6} and (row["media_type"] == "video" or len(text) >= 600):
        return "high"
    if category_id == 6 and row["links_json"] and len(text) >= 300:
        return "high"
    if category_id in {2, 4, 8}:
        return "medium"
    return "medium"


def local_item(row: sqlite3.Row) -> dict:
    text = row["text"] or ""
    links = json.loads(row["links_json"] or "[]")
    row_type = item_type(row)
    category_id = local_category(text, links, row["media_type"])
    title = local_title(text, category_id)
    actionability = local_actionability(category_id, row_type)
    priority = local_priority(category_id, row, text)
    target_user = local_target_user(category_id)

    if category_id == 11:
        practical_use = "Оставить в архиве или использовать только как контекст источника."
        action_plan = ["Не тратить время на внедрение", "Вернуться только при наличии явной задачи или запроса"]
        business_value = "снижает информационный шум"
    else:
        practical_use = f"Использовать как материал по теме: {CATEGORIES[category_id]}."
        action_plan = [
            "Сверить тезис с текущей задачей бизнеса",
            "Сохранить ссылку или post_url в рабочую подборку",
            "Проверить применимость на одном кейсе или отчете",
        ]
        business_value = "помогает быстрее найти применимый финансовый материал"

    return {
        "category_id": category_id,
        "subcategory": CATEGORIES[category_id].split(" / ")[0],
        "title": title,
        "summary": compact_text(text, 320) or f"Материал типа {row_type}",
        "practical_use": practical_use,
        "action_plan": action_plan,
        "tools": domains(links),
        "tags": [CATEGORIES[category_id].split(" / ")[0].lower(), row_type],
        "target_user": target_user,
        "business_value": business_value,
        "actionability": actionability,
        "priority": priority,
    }


def compute_engagement_score(views: int | None, forwards: int | None, reactions: int | None) -> float | None:
    import math
    v = views or 0
    f = forwards or 0
    r = reactions or 0
    if v == 0 and f == 0 and r == 0:
        return None
    score = (
        0.5 * min(math.log1p(v) / math.log1p(5845), 1.0)
        + 0.3 * min(math.log1p(f) / math.log1p(23), 1.0)
        + 0.2 * min(math.log1p(r) / math.log1p(50), 1.0)
    )
    return round(score, 4)


def upsert_item(
    con: sqlite3.Connection,
    row: sqlite3.Row,
    item: dict,
    model: str,
    prompt_kind: str = "full",
    prompt_hash_value: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    pipeline_version: str | None = None,
) -> None:
    pv = pipeline_version or PIPELINE_VERSION
    category_id = int(item.get("category_id") or 11)
    if category_id not in CATEGORIES:
        category_id = 11
    now = datetime.now(timezone.utc).isoformat()
    target_user = normalize_choice(item.get("target_user") or "", TARGET_USERS, "other")
    priority = normalize_choice(item.get("priority") or "", {"high", "medium", "low"}, "medium")
    actionability = normalize_choice(
        item.get("actionability") or "",
        {"use_now", "test", "read", "watch", "contact", "save_template", "monitor", "archive"},
        "read",
    )
    views = row["views"] if "views" in row.keys() else None
    forwards = row["forwards"] if "forwards" in row.keys() else None
    reactions = row["reactions"] if "reactions" in row.keys() else None
    engagement = compute_engagement_score(views, forwards, reactions)
    con.execute(
        """INSERT OR REPLACE INTO finance_item_analysis (
            source_peer_id, message_id, pipeline_version, date, item_type,
            source_title, post_url, category_id, category_name, subcategory,
            title, summary, practical_use, action_plan_json, tools_json,
            tags_json, target_user, business_value, actionability, priority,
            links_json, model, status, analyzed_at, raw_json, error,
            prompt_kind, prompt_hash, input_tokens, output_tokens,
            insight, entities_json, engagement_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'reviewed', ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)""",
        (
            row["source_peer_id"],
            row["message_id"],
            pv,
            row["date"],
            item_type(row),
            row["source_title"],
            row["post_url"],
            category_id,
            CATEGORIES[category_id],
            item.get("subcategory") or "",
            item.get("title") or "",
            item.get("summary") or "",
            item.get("practical_use") or "",
            json.dumps(item.get("action_plan") or [], ensure_ascii=False),
            json.dumps(item.get("tools") or [], ensure_ascii=False),
            json.dumps(item.get("tags") or [], ensure_ascii=False),
            target_user,
            item.get("business_value") or "",
            actionability,
            priority,
            row["links_json"] or "[]",
            model,
            now,
            json.dumps(item, ensure_ascii=False, sort_keys=True),
            prompt_kind,
            prompt_hash_value,
            input_tokens,
            output_tokens,
            item.get("insight") or "",
            json.dumps(item.get("entities") or [], ensure_ascii=False),
            engagement,
        ),
    )


def mark_failed(con: sqlite3.Connection, rows: list[sqlite3.Row], model: str, error: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    con.executemany(
        """INSERT OR REPLACE INTO finance_item_analysis (
            source_peer_id, message_id, pipeline_version, date, item_type,
            source_title, post_url, category_id, category_name,
            status, model, analyzed_at, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 11, ?, 'failed', ?, ?, ?)""",
        [
            (
                row["source_peer_id"],
                row["message_id"],
                PIPELINE_VERSION,
                row["date"],
                item_type(row),
                row["source_title"],
                row["post_url"],
                CATEGORIES[11],
                model,
                now,
                error,
            )
            for row in rows
        ],
    )
    con.commit()


def process(
    force: bool,
    limit: int | None,
    batch_size: int,
    sleep_seconds: float,
    all_messages: bool,
    high_only: bool = False,
    pipeline_version: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.25,
) -> None:
    pv = pipeline_version or PIPELINE_VERSION
    con = open_db()
    rows = load_targets(con, force=force, limit=limit, all_messages=all_messages, high_only=high_only, pipeline_version=pv)
    print(f"Targets: {len(rows)}")
    by_id = {(row["source_peer_id"], row["message_id"]): row for row in rows}
    done = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        print(f"  batch {start // batch_size + 1}: {len(batch)}")
        try:
            prompt = build_prompt(batch)
            prompt_hash_value = prompt_hash(prompt)
            content, model_used, usage = call_llm(
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                env_path=_ENV_PATH,
            )
            input_tokens = usage.get("tokens_input")
            output_tokens = usage.get("tokens_output")
            data = parse_json(content or "{}")
            batch_done = 0
            for item in data.get("items") or []:
                key = (int(item["source_peer_id"]), int(item["message_id"]))
                if key in by_id:
                    upsert_item(
                        con,
                        by_id[key],
                        item,
                        model_used,
                        prompt_kind="full",
                        prompt_hash_value=prompt_hash_value,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        pipeline_version=pv,
                    )
                    done += 1
                    batch_done += 1
            con.commit()
            print(f"    reviewed: +{batch_done}, total {done}/{len(rows)}")
        except Exception as exc:
            mark_failed(con, batch, "openrouter", str(exc))
            print(f"    failed: {exc}")
        if sleep_seconds:
            time.sleep(sleep_seconds)
    rebuild_fts(con)
    con.close()


def classification_item(row: sqlite3.Row, item: dict) -> dict:
    category_id = int(item.get("category_id") or 11)
    if category_id not in CATEGORIES:
        category_id = 11
    confidence = item.get("confidence")
    reason = str(item.get("reason") or "").strip()
    row_type = item_type(row)
    text = row["text"] or ""
    title = local_title(text, category_id)
    return {
        "category_id": category_id,
        "subcategory": CATEGORIES[category_id].split(" / ")[0],
        "title": title,
        "summary": reason or compact_text(text, 260) or f"Материал типа {row_type}",
        "practical_use": (
            "Требует второго слоя анализа перед практическим применением."
            if category_id != 11
            else "Оставить в архиве или использовать только как контекст источника."
        ),
        "action_plan": (
            ["Отправить во второй слой анализа", "Проверить практическую ценность"]
            if category_id != 11
            else ["Не тратить время на внедрение"]
        ),
        "tools": domains(json.loads(row["links_json"] or "[]")),
        "tags": [CATEGORIES[category_id].split(" / ")[0].lower(), row_type, "classified"],
        "target_user": local_target_user(category_id),
        "business_value": "быстрая тематическая раскладка без полной карточки",
        "actionability": local_actionability(category_id, row_type),
        "priority": local_priority(category_id, row, text),
        "confidence": confidence,
        "reason": reason,
    }


def process_classify_only(
    force: bool,
    limit: int | None,
    batch_size: int,
    sleep_seconds: float,
    all_messages: bool,
    local_only: bool = False,
    max_tokens: int = 4096,
    temperature: float = 0.1,
) -> None:
    con = open_db()
    rows = load_targets(con, force=force, limit=limit, all_messages=all_messages, local_only=local_only)
    print(f"Classification targets: {len(rows)}")
    by_id = {(row["source_peer_id"], row["message_id"]): row for row in rows}
    done = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        print(f"  classify batch {start // batch_size + 1}: {len(batch)}")
        try:
            prompt = build_classification_prompt(batch)
            prompt_hash_value = prompt_hash(prompt)
            content, model_used, usage = call_llm(
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                env_path=_ENV_PATH,
            )
            input_tokens = usage.get("tokens_input")
            output_tokens = usage.get("tokens_output")
            data = parse_json(content or "{}")
            batch_done = 0
            for item in data.get("items") or []:
                key = (int(item["source_peer_id"]), int(item["message_id"]))
                if key in by_id:
                    upsert_item(
                        con,
                        by_id[key],
                        classification_item(by_id[key], item),
                        model_used,
                        prompt_kind="classify_only",
                        prompt_hash_value=prompt_hash_value,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                    done += 1
                    batch_done += 1
            con.commit()
            print(f"    classified: +{batch_done}, total {done}/{len(rows)}")
        except Exception as exc:
            mark_failed(con, batch, "openrouter", str(exc))
            print(f"    failed: {exc}")
        if sleep_seconds:
            time.sleep(sleep_seconds)
    con.close()


def process_local(force: bool, limit: int | None, all_messages: bool, local_only: bool = False) -> None:
    con = open_db()
    rows = load_targets(con, force=force, limit=limit, all_messages=all_messages, local_only=local_only)
    print(f"Local targets: {len(rows)}")
    for index, row in enumerate(rows, 1):
        upsert_item(con, row, local_item(row), "local-heuristic-v1", prompt_kind="local")
        if index % 1000 == 0:
            con.commit()
            print(f"  reviewed local: {index}/{len(rows)}")
    con.commit()
    rebuild_fts(con)
    con.close()
    print(f"Local reviewed: {len(rows)}")


def process_local_videos(force: bool, limit: int | None) -> None:
    con = open_db()
    rows = load_video_targets(con, force=force, limit=limit)
    print(f"Local video targets: {len(rows)}")
    for index, row in enumerate(rows, 1):
        upsert_item(con, row, local_item(row), "local-heuristic-v1", prompt_kind="local_video")
        if index % 500 == 0:
            con.commit()
            print(f"  reviewed local videos: {index}/{len(rows)}")
    con.commit()
    con.close()
    print(f"Local videos reviewed: {len(rows)}")


def status(all_messages: bool) -> None:
    con = open_db()
    target_filter = "1=1" if all_messages else core_where()
    print("Finance analysis status:")
    print(
        "  target scope:",
        "all messages" if all_messages else "core: videos OR links OR text_len >= 300",
    )
    for row in con.execute(
        f"""SELECT coalesce(a.status, 'missing') AS status, COUNT(*) AS count
            FROM messages m
            LEFT JOIN finance_item_analysis a
              ON a.source_peer_id = m.source_peer_id
             AND a.message_id = m.message_id
             AND a.pipeline_version = ?
            WHERE m.text IS NOT NULL AND m.text != '' AND {target_filter}
            GROUP BY coalesce(a.status, 'missing')
            ORDER BY status""",
        (PIPELINE_VERSION,),
    ):
        print(f"  {row['status']}: {row['count']}")
    print("Item types in target:")
    for row in con.execute(
        f"""SELECT
              CASE WHEN media_type = 'video' THEN 'video'
                   WHEN links_json IS NOT NULL THEN 'link'
                   ELSE 'message' END AS item_type,
              COUNT(*) AS count
            FROM messages m
            WHERE m.text IS NOT NULL AND m.text != '' AND {target_filter}
            GROUP BY item_type
            ORDER BY count DESC"""
    ):
        print(f"  {row['item_type']}: {row['count']}")
    print("Categories reviewed:")
    for row in con.execute(
        """SELECT category_id, category_name, priority, COUNT(*) AS count
           FROM finance_item_analysis
           WHERE pipeline_version = ? AND status = 'reviewed'
           GROUP BY category_id, category_name, priority
           ORDER BY category_id, priority""",
        (PIPELINE_VERSION,),
    ):
        print(f"  {row['category_id']}. {row['category_name']} / {row['priority']}: {row['count']}")
    con.close()


def _fetch_rows(con: sqlite3.Connection, pipeline_version: str | None = None, date_from: str | None = None) -> list[sqlite3.Row]:
    pv = pipeline_version or PIPELINE_VERSION
    where = ["a.pipeline_version = ?", "a.status = 'reviewed'", "a.category_id != 11"]
    params: list[object] = [pv]
    if date_from:
        where.append("a.date >= ?")
        params.append(date_from)
    return con.execute(
        f"""SELECT a.*, m.text AS original_text, m.text_len
               FROM finance_item_analysis a
               JOIN messages m
                 ON m.source_peer_id = a.source_peer_id
                AND m.message_id = a.message_id
               WHERE {' AND '.join(where)}
               ORDER BY
                 CASE a.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                 a.category_id,
                 COALESCE(a.engagement_score, 0) DESC,
                 a.date DESC""",
        params,
    ).fetchall()


def _write_md(rows: list, path, title: str = "Практические финансовые инсайты") -> None:
    lines = [f"# {title}", "", f"_Всего: {len(rows)}_", ""]
    for priority in ("high", "medium", "low"):
        subset = [row for row in rows if row["priority"] == priority]
        if not subset:
            continue
        lines += [f"## Priority: {priority}", ""]
        current_category = None
        for row in subset:
            category = f"{row['category_id']}. {row['category_name']}"
            if category != current_category:
                lines += [f"### {category}", ""]
                current_category = category
            action_plan = json.loads(row["action_plan_json"] or "[]")
            tools = json.loads(row["tools_json"] or "[]")
            links = json.loads(row["links_json"] or "[]")
            insight = row["insight"] if "insight" in row.keys() else ""
            lines += [
                f"#### {row['title'] or 'Без названия'}",
                "",
                f"**Источник:** {row['source_title']} / {row['date'][:10]} / {row['item_type']}",
                "",
                f"**Подтема:** {row['subcategory'] or '-'}",
                "",
                f"**Суть:** {row['summary']}",
            ]
            if insight:
                lines += ["", f"**Инсайт:** {insight}"]
            lines += [
                "",
                f"**Практическое применение:** {row['practical_use']}",
                "",
                "**Что сделать:**",
            ]
            lines += [f"- {step}" for step in action_plan] or ["- -"]
            lines += [
                "",
                f"**Для кого:** {row['target_user']}",
                "",
                f"**Инструменты:** {', '.join(tools) if tools else '-'}",
                "",
                f"**Ценность:** {row['business_value'] or '-'}",
                "",
                f"**Действие:** {row['actionability']}",
                "",
                f"**Post:** {row['post_url'] or '-'}",
            ]
            if links:
                lines += ["", "**Ссылки:**"]
                lines += [f"- {link}" for link in links]
            lines += ["", "---", ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def export(split: bool = False) -> None:
    con = open_db()
    rows = _fetch_rows(con)
    # include category 11 (мусор) only in monolith CSV, not in MD
    rows_all = con.execute(
        """SELECT a.*, m.text AS original_text, m.text_len
           FROM finance_item_analysis a
           JOIN messages m ON m.source_peer_id = a.source_peer_id AND m.message_id = a.message_id
           WHERE a.pipeline_version = ? AND a.status = 'reviewed'
           ORDER BY
             CASE a.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
             a.category_id,
             COALESCE(a.engagement_score, 0) DESC,
             a.date DESC""",
        (PIPELINE_VERSION,),
    ).fetchall()
    OUT_DIR.mkdir(exist_ok=True)

    csv_path = OUT_DIR / "practical_finance.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "source_peer_id", "message_id", "date", "item_type", "source_title",
            "category_id", "category_name", "subcategory", "title", "summary",
            "insight", "practical_use", "action_plan", "tools", "tags", "target_user",
            "business_value", "actionability", "priority", "engagement_score",
            "post_url", "links", "text_len",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_all:
            writer.writerow(
                {
                    "source_peer_id": row["source_peer_id"],
                    "message_id": row["message_id"],
                    "date": row["date"][:10],
                    "item_type": row["item_type"],
                    "source_title": row["source_title"],
                    "category_id": row["category_id"],
                    "category_name": row["category_name"],
                    "subcategory": row["subcategory"],
                    "title": row["title"],
                    "summary": row["summary"],
                    "insight": row["insight"] if "insight" in row.keys() else "",
                    "practical_use": row["practical_use"],
                    "action_plan": "; ".join(json.loads(row["action_plan_json"] or "[]")),
                    "tools": ", ".join(json.loads(row["tools_json"] or "[]")),
                    "tags": ", ".join(json.loads(row["tags_json"] or "[]")),
                    "target_user": row["target_user"],
                    "business_value": row["business_value"],
                    "actionability": row["actionability"],
                    "priority": row["priority"],
                    "engagement_score": row["engagement_score"] if "engagement_score" in row.keys() else "",
                    "post_url": row["post_url"],
                    "links": " ".join(json.loads(row["links_json"] or "[]")),
                    "text_len": row["text_len"],
                }
            )

    md_path = OUT_DIR / "practical_finance.md"
    _write_md(rows, md_path)

    if split:
        for cat_id, cat_name in CATEGORIES.items():
            if cat_id == 11:
                continue
            subset = [r for r in rows if r["category_id"] == cat_id]
            if not subset:
                continue
            safe = re.sub(r"[^\w\-]", "_", cat_name.split("/")[0].strip())[:30]
            _write_md(subset, OUT_DIR / f"cat_{cat_id:02d}_{safe}.md", title=cat_name)
        for user in sorted(TARGET_USERS - {"other"}):
            subset = [r for r in rows if r["target_user"] == user]
            if not subset:
                continue
            _write_md(subset, OUT_DIR / f"for_{user}.md", title=f"Для: {user}")
        print(f"Split export done → {OUT_DIR}")

    stats = {
        "pipeline_version": PIPELINE_VERSION,
        "items": len(rows_all),
        "categories": {},
        "priorities": {},
        "target_users": {},
        "actionability": {},
        "item_types": {},
    }
    for row in rows_all:
        stats["categories"][row["category_name"]] = stats["categories"].get(row["category_name"], 0) + 1
        stats["priorities"][row["priority"]] = stats["priorities"].get(row["priority"], 0) + 1
        stats["target_users"][row["target_user"]] = stats["target_users"].get(row["target_user"], 0) + 1
        stats["actionability"][row["actionability"]] = stats["actionability"].get(row["actionability"], 0) + 1
        stats["item_types"][row["item_type"]] = stats["item_types"].get(row["item_type"], 0) + 1
    (OUT_DIR / "practical_finance_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    con.close()
    print(f"Exported: {md_path}, {csv_path}, practical_finance_stats.json")


def export_weekly(days: int = 7) -> None:
    from datetime import timedelta
    con = open_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = _fetch_rows(con, date_from=cutoff)
    OUT_DIR.mkdir(exist_ok=True)
    week_label = datetime.now().strftime("%Y-W%V")
    path = OUT_DIR / f"weekly_{week_label}.md"
    _write_md(rows, path, title=f"Дайджест: {week_label} (последние {days} дней)")
    con.close()
    print(f"Weekly digest: {path} ({len(rows)} items)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--process", action="store_true")
    parser.add_argument("--classify-only", action="store_true", help="Run cheap LLM categorization without full practical cards.")
    parser.add_argument("--process-local", action="store_true", help="Process missing items with local deterministic rules, without LLM/API.")
    parser.add_argument("--process-local-videos", action="store_true", help="Process every missing video message with local deterministic rules.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--all-messages", action="store_true", help="Process every non-empty message, not only the dense core.")
    parser.add_argument("--local-only", action="store_true", help="Reprocess only records already processed by local-heuristic-v1.")
    parser.add_argument("--high-only", action="store_true", help="Target only messages with priority=high in v1 (for v2 insight/entities pass).")
    parser.add_argument("--pipeline-version", type=str, default=None, help="Override pipeline version (default: finance-practical-v1).")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max output tokens for LLM (default: 4096).")
    parser.add_argument("--temperature", type=float, default=0.25, help="LLM temperature (default: 0.25).")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--export-split", action="store_true", help="Also write per-category and per-target_user MD files.")
    parser.add_argument("--export-weekly", action="store_true", help="Export a weekly digest (last 7 days).")
    parser.add_argument("--weekly-days", type=int, default=7)
    args = parser.parse_args()

    if args.process:
        process(args.force, args.limit, args.batch_size or 8, args.sleep, args.all_messages,
                high_only=args.high_only, pipeline_version=args.pipeline_version,
                max_tokens=args.max_tokens, temperature=args.temperature)
    if args.classify_only:
        process_classify_only(args.force, args.limit, args.batch_size or 50, args.sleep, args.all_messages,
                              local_only=args.local_only, max_tokens=args.max_tokens, temperature=args.temperature)
    if args.process_local:
        process_local(args.force, args.limit, args.all_messages, local_only=args.local_only)
    if args.process_local_videos:
        process_local_videos(args.force, args.limit)
    if args.status:
        status(args.all_messages)
    if args.export or args.export_split:
        export(split=args.export_split)
    if args.export_weekly:
        export_weekly(days=args.weekly_days)
    if not any([
        args.process, args.classify_only, args.process_local, args.process_local_videos,
        args.status, args.export, args.export_split, args.export_weekly,
    ]):
        parser.print_help()


if __name__ == "__main__":
    main()
