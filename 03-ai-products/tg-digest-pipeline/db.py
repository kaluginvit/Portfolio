from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def connect_rw(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def has_table(con: sqlite3.Connection, table_name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone() is not None


def one(con: sqlite3.Connection, sql: str, params: tuple = ()) -> dict:
    row = con.execute(sql, params).fetchone()
    return dict(row) if row else {}


def all_rows(con: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in con.execute(sql, params).fetchall()]


def safe_one(con: sqlite3.Connection, table: str, sql: str, params: tuple = ()) -> dict:
    if not has_table(con, table):
        return {"missing_table": table}
    return one(con, sql, params)


def safe_all(con: sqlite3.Connection, table: str, sql: str, params: tuple = ()) -> list[dict]:
    if not has_table(con, table):
        return []
    return all_rows(con, sql, params)
