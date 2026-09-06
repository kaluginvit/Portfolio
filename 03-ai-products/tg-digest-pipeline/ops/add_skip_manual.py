import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row

now = datetime.now(timezone.utc).isoformat()

# msg=955, source_peer_id=2458485366 (AI с Софьей и Натали) — стабильно падает ValueError
conn.execute("""
INSERT INTO finance_video_download_policy
    (source_peer_id, message_id, policy, reason, path, attempt_count, last_error, last_attempt_at, updated_at)
VALUES (?, ?, 'skip_manual', ?, '', 2, ?, ?, ?)
ON CONFLICT(source_peer_id, message_id) DO UPDATE SET
    policy='skip_manual',
    reason=excluded.reason,
    last_error=excluded.last_error,
    last_attempt_at=excluded.last_attempt_at,
    updated_at=excluded.updated_at
""", (
    2458485366, 955,
    'Повторный ValueError: Request was unsuccessful 6 time(s) — пропускаем',
    'ValueError: Request was unsuccessful 6 time(s)',
    now, now
))
conn.commit()
print("Added msg=955 (source_peer_id=2458485366) to skip_manual")

# Проверим очередь
total = conn.execute("SELECT COUNT(*) FROM messages WHERE media_type IN ('video','video_note')").fetchone()[0]
done = conn.execute("SELECT COUNT(*) FROM finance_video_download_policy").fetchone()[0]
print(f"Queue after skip: {total - done}")
conn.close()
