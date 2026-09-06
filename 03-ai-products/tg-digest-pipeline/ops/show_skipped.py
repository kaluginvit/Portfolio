import sqlite3

conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT
        p.policy,
        p.source_peer_id,
        p.message_id,
        p.reason,
        p.last_error,
        p.attempt_count,
        m.date,
        m.post_url,
        m.text,
        s.title as source_title,
        s.username as source_username
    FROM finance_video_download_policy p
    LEFT JOIN messages m ON m.source_peer_id = p.source_peer_id AND m.message_id = p.message_id
    LEFT JOIN sources s ON s.source_peer_id = p.source_peer_id
    WHERE p.policy IN ('skip_manual', 'skip_large', 'skip_deleted', 'retry_pending')
    ORDER BY p.policy, m.date
""").fetchall()

by_policy = {}
for r in rows:
    by_policy.setdefault(r['policy'], []).append(r)

for policy, items in by_policy.items():
    print(f"\n=== {policy.upper()} ({len(items)} шт.) ===")
    for r in items:
        url = r['post_url'] or f"https://t.me/{r['source_username']}/{r['message_id']}" if r['source_username'] else ''
        date = (r['date'] or '')[:10]
        text_preview = (r['text'] or '').replace('\n', ' ')[:80]
        print(f"  {date} | {r['source_title']} | msg={r['message_id']} | attempts={r['attempt_count']}")
        if url:
            print(f"         URL: {url}")
        print(f"         Причина: {r['reason'] or r['last_error'] or '—'}")
        print()

conn.close()
