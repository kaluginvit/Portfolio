import sqlite3
conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row
row = conn.execute('SELECT * FROM finance_video_download_policy WHERE source_peer_id=2458485366 AND message_id=955').fetchone()
if row:
    print(dict(row))
else:
    print('NOT FOUND')
total = conn.execute("SELECT COUNT(*) FROM messages WHERE media_type IN ('video','video_note')").fetchone()[0]
done = conn.execute("SELECT COUNT(*) FROM finance_video_download_policy").fetchone()[0]
print(f'Total={total} Done={done} Queue={total-done}')
conn.close()
