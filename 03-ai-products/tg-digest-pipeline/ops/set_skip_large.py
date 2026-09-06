import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row

now = datetime.now(timezone.utc).isoformat()

conn.execute("""
UPDATE finance_video_download_policy
SET policy='skip_large',
    reason='Скачать вручную — скрипт падает с ValueError (Telegram не отдаёт файл автоматически)',
    updated_at=?
WHERE source_peer_id=2458485366 AND message_id=955
""", (now,))
conn.commit()

# Покажем инфу о видео для ручного скачивания
row = conn.execute("""
    SELECT m.message_id, m.source_peer_id, m.date, m.post_url, m.text,
           s.title as source_title, s.username as source_username
    FROM messages m
    LEFT JOIN sources s ON s.source_peer_id = m.source_peer_id
    WHERE m.source_peer_id=2458485366 AND m.message_id=955
""").fetchone()

if row:
    print("=== Видео для ручного скачивания ===")
    print(f"Канал:    {row['source_title']} (@{row['source_username']})")
    print(f"Дата:     {row['date']}")
    print(f"msg_id:   {row['message_id']}")
    print(f"URL:      {row['post_url']}")
    print(f"Текст:    {(row['text'] or '')[:200]}")

print("\nPolicy обновлён: skip_manual → skip_large")
conn.close()
