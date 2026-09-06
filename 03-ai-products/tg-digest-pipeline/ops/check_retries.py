import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT p.source_peer_id, p.message_id, p.policy, p.attempt_count,
           p.last_error, s.title, s.username
    FROM finance_video_download_policy p
    LEFT JOIN sources s ON s.source_peer_id = p.source_peer_id
    WHERE p.policy = 'retry_pending'
    ORDER BY p.attempt_count DESC, p.last_attempt_at DESC
""").fetchall()

print(f"retry_pending всего: {len(rows)}")
print()
for r in rows:
    url = f"https://t.me/{r['username']}/{r['message_id']}" if r['username'] else f"peer={r['source_peer_id']}/msg={r['message_id']}"
    print(f"  attempts={r['attempt_count']} | {r['title']} | msg={r['message_id']} | {url}")
    print(f"  last_error: {r['last_error']}")

conn.close()
