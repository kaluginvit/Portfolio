import sqlite3
from pathlib import Path

conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row

print("=" * 60)
print("ЧЕКАП ВИДЕО-ПАЙПЛАЙНА")
print("=" * 60)

# 1. Общая статистика
total_video = conn.execute("SELECT COUNT(*) FROM messages WHERE media_type = 'video'").fetchone()[0]
total_note = conn.execute("SELECT COUNT(*) FROM messages WHERE media_type = 'video_note'").fetchone()[0]
print(f"\n[1] Сообщений в базе:")
print(f"    media_type='video':       {total_video}")
print(f"    media_type='video_note':  {total_note}")
print(f"    Итого:                    {total_video + total_note}")

# 2. Разбивка по policy
policies = {r['policy']: r['cnt'] for r in conn.execute(
    "SELECT policy, COUNT(*) as cnt FROM finance_video_download_policy GROUP BY policy"
)}
processed = sum(policies.values())
print(f"\n[2] Статусы в finance_video_download_policy ({processed} записей):")
for p, cnt in sorted(policies.items(), key=lambda x: -x[1]):
    print(f"    {p:<25} {cnt}")

# 3. video без policy (только media_type='video', т.к. загрузчик их не трогает)
no_policy_video = conn.execute("""
    SELECT COUNT(*) FROM messages m
    WHERE m.media_type = 'video'
    AND NOT EXISTS (
        SELECT 1 FROM finance_video_download_policy p
        WHERE p.source_peer_id = m.source_peer_id AND p.message_id = m.message_id
    )
""").fetchone()[0]

no_policy_note = conn.execute("""
    SELECT COUNT(*) FROM messages m
    WHERE m.media_type = 'video_note'
    AND NOT EXISTS (
        SELECT 1 FROM finance_video_download_policy p
        WHERE p.source_peer_id = m.source_peer_id AND p.message_id = m.message_id
    )
""").fetchone()[0]

print(f"\n[3] Без записи в policy:")
print(f"    video (должно быть 0):    {no_policy_video}")
print(f"    video_note (норма):       {no_policy_note}")

# 4. Файлы на диске vs policy=downloaded
downloaded_policy = policies.get('downloaded', 0)
try:
    files_indexed = conn.execute(
        "SELECT COUNT(*) FROM finance_video_files WHERE is_valid=1 AND COALESCE(is_stale,0)=0"
    ).fetchone()[0]
except:
    files_indexed = None

NATIVE_DIR = Path("finance/Финансы_видео")
files_on_disk = sum(1 for f in NATIVE_DIR.rglob("*.mp4") if f.is_file()) if NATIVE_DIR.exists() else 0

print(f"\n[4] Файлы:")
print(f"    policy=downloaded:        {downloaded_policy}")
print(f"    .mp4 на диске:            {files_on_disk}")
if files_indexed is not None:
    print(f"    в индексе (valid):        {files_indexed}")

# 5. Проблемные: retry_pending
if policies.get('retry_pending', 0) > 0:
    rows = conn.execute("""
        SELECT p.source_peer_id, p.message_id, p.attempt_count, p.last_error, s.title
        FROM finance_video_download_policy p
        LEFT JOIN sources s ON s.source_peer_id = p.source_peer_id
        WHERE p.policy = 'retry_pending'
        ORDER BY p.attempt_count DESC
    """).fetchall()
    print(f"\n[5] retry_pending ({len(rows)}):")
    for r in rows:
        print(f"    attempts={r['attempt_count']} | {r['title']} | msg={r['message_id']}")
        print(f"    {r['last_error']}")
else:
    print(f"\n[5] retry_pending: 0 — чисто")

# 6. skip_large список
skip_large_rows = conn.execute("""
    SELECT p.source_peer_id, p.message_id, p.reason, m.post_url, s.title
    FROM finance_video_download_policy p
    LEFT JOIN messages m ON m.source_peer_id=p.source_peer_id AND m.message_id=p.message_id
    LEFT JOIN sources s ON s.source_peer_id=p.source_peer_id
    WHERE p.policy='skip_large'
    ORDER BY m.date
""").fetchall()
print(f"\n[6] skip_large ({len(skip_large_rows)}) — скачать вручную:")
for r in skip_large_rows:
    url = r['post_url'] or ''
    reason = (r['reason'] or '')[:60]
    print(f"    {r['title']} | msg={r['message_id']} | {reason}")
    if url:
        print(f"    {url}")

# 7. Итоговый вердикт
print(f"\n{'='*60}")
print("ИТОГ:")
if no_policy_video == 0 and policies.get('retry_pending', 0) == 0:
    print("  OK — все video обработаны (retry_pending=0, no_policy_video=0)")
else:
    if no_policy_video > 0:
        print(f"  ВНИМАНИЕ: {no_policy_video} video без policy")
    if policies.get('retry_pending', 0) > 0:
        print(f"  ВНИМАНИЕ: {policies['retry_pending']} retry_pending")
print(f"  skip_large (вручную): {len(skip_large_rows)}")
print(f"  skip_manual (недоступны): {policies.get('skip_manual', 0)}")

conn.close()
