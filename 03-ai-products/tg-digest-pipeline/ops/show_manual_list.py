import sqlite3

conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT p.source_peer_id, p.message_id, p.reason,
           m.post_url, m.date, s.title, s.username
    FROM finance_video_download_policy p
    LEFT JOIN messages m ON m.source_peer_id=p.source_peer_id AND m.message_id=p.message_id
    LEFT JOIN sources s ON s.source_peer_id=p.source_peer_id
    WHERE p.policy = 'skip_large'
    ORDER BY m.date
""").fetchall()

for r in rows:
    url = r['post_url'] or (f"https://t.me/{r['username']}/{r['message_id']}" if r['username'] else f"peer={r['source_peer_id']}/msg={r['message_id']}")
    reason = (r['reason'] or '').replace('[manual] ', '')
    print(f"{(r['date'] or '')[:10]}\t{r['title']}\tmsg={r['message_id']}\t{reason[:60]}\t{url}")

conn.close()
