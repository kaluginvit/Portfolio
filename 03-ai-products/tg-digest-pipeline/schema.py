"""DDL для всех таблиц проекта ИнфоПовод."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from db import connect_rw

MESSAGES_DDL = """
CREATE TABLE IF NOT EXISTS messages (
    message_id        INTEGER PRIMARY KEY,
    date              TEXT NOT NULL,
    text              TEXT,
    forwarded_from    TEXT,
    forwarded_from_id TEXT,
    photo             TEXT,
    has_photo         INTEGER DEFAULT 0,
    edited            TEXT,
    links             TEXT,
    raw_tags          TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);
CREATE INDEX IF NOT EXISTS idx_messages_fwd  ON messages(forwarded_from);
"""

ENRICHMENTS_DDL = """
CREATE TABLE IF NOT EXISTS enrichments (
    message_id  INTEGER PRIMARY KEY REFERENCES messages(message_id),
    entities    TEXT,
    tags        TEXT,
    insight     TEXT,
    llm_model   TEXT,
    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);
"""

USER_TAGS_DDL = """
CREATE TABLE IF NOT EXISTS user_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id  INTEGER NOT NULL REFERENCES messages(message_id),
    tag         TEXT,
    note        TEXT,
    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);
CREATE INDEX IF NOT EXISTS idx_user_tags_msg ON user_tags(message_id);
"""

FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    message_id UNINDEXED,
    text,
    tokenize='unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS enrichments_fts USING fts5(
    message_id UNINDEXED,
    insight,
    tags,
    entities,
    tokenize='unicode61'
);
"""


COLLECTOR_QUEUE_DDL = """
CREATE TABLE IF NOT EXISTS collector_queue (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id       TEXT    NOT NULL,
    channel_title    TEXT,
    channel_username TEXT,
    message_id       INTEGER NOT NULL,
    date             TEXT    NOT NULL,
    text             TEXT,
    has_photo        INTEGER DEFAULT 0,
    views            INTEGER DEFAULT 0,
    forwards         INTEGER DEFAULT 0,
    centroid_label   TEXT,
    centroid_score   REAL,
    keyword_match    TEXT,
    status           TEXT    DEFAULT 'pending',
    collected_at     TEXT    DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    reviewed_at      TEXT,
    UNIQUE(channel_id, message_id)
);
CREATE INDEX IF NOT EXISTS idx_cq_status  ON collector_queue(status);
CREATE INDEX IF NOT EXISTS idx_cq_date    ON collector_queue(date);
CREATE INDEX IF NOT EXISTS idx_cq_centroid ON collector_queue(centroid_label);

CREATE TABLE IF NOT EXISTS collector_state (
    channel_id       TEXT PRIMARY KEY,
    last_message_id  INTEGER DEFAULT 0,
    last_run         TEXT
);
"""


def init_db(db_path: Path) -> sqlite3.Connection:
    con = connect_rw(db_path)
    con.executescript(MESSAGES_DDL)
    con.executescript(ENRICHMENTS_DDL)
    con.executescript(USER_TAGS_DDL)
    con.executescript(FTS_DDL)
    con.executescript(COLLECTOR_QUEUE_DDL)
    con.commit()
    return con


if __name__ == "__main__":
    from pathlib import Path
    db_path = Path("data/messages.db")
    db_path.parent.mkdir(exist_ok=True)
    init_db(db_path)
    print(f"БД инициализирована: {db_path}")
