import sqlite3
conn = sqlite3.connect('finance/finance_messages.db')
total = conn.execute("SELECT COUNT(*) FROM messages WHERE media_type IN ('video','video_note')").fetchone()[0]
try:
    done = conn.execute("SELECT COUNT(*) FROM finance_video_download_policy").fetchone()[0]
except Exception as e:
    done = 0
    print(f"Warning: {e}")
print(f"Total: {total}")
print(f"Done: {done}")
print(f"Queue: {total - done}")
conn.close()
