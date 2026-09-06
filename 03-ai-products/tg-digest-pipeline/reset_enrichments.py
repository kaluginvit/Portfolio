import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "data" / "messages.db"
con = sqlite3.connect(DB)

con.execute("DELETE FROM enrichments")
con.execute("DELETE FROM enrichments_fts")
con.execute("""
CREATE TABLE IF NOT EXISTS photo_enrichments (
    message_id    INTEGER PRIMARY KEY REFERENCES messages(message_id),
    description   TEXT,
    objects       TEXT,
    text_on_image TEXT,
    llm_model     TEXT,
    created_at    TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
)
""")
con.commit()

n = con.execute("SELECT COUNT(*) FROM enrichments").fetchone()[0]
print(f"enrichments очищены: {n}")
print("photo_enrichments создана")
con.close()
