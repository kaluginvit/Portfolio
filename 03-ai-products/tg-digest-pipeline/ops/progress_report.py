import sqlite3

conn = sqlite3.connect('finance/finance_messages.db')
conn.row_factory = sqlite3.Row

total_video = conn.execute("SELECT COUNT(*) FROM messages WHERE media_type IN ('video','video_note')").fetchone()[0]
total_all = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

policies = conn.execute("""
    SELECT policy, COUNT(*) as cnt
    FROM finance_video_download_policy
    GROUP BY policy ORDER BY cnt DESC
""").fetchall()

downloaded = next((r['cnt'] for r in policies if r['policy'] == 'downloaded'), 0)
skip_short = next((r['cnt'] for r in policies if r['policy'] == 'skip_short_duration'), 0)
skip_large = next((r['cnt'] for r in policies if r['policy'] == 'skip_large'), 0)
skip_manual = next((r['cnt'] for r in policies if r['policy'] == 'skip_manual'), 0)
skip_deleted = next((r['cnt'] for r in policies if r['policy'] == 'skip_deleted'), 0)
retry_pending = next((r['cnt'] for r in policies if r['policy'] == 'retry_pending'), 0)

done_total = sum(r['cnt'] for r in policies)

# Файлы на диске
try:
    files_on_disk = conn.execute("SELECT COUNT(*) FROM finance_video_files WHERE is_valid=1 AND COALESCE(is_stale,0)=0").fetchone()[0]
except:
    files_on_disk = None

# Размер по категориям
try:
    cats = conn.execute("""
        SELECT category_name, COUNT(*) as cnt
        FROM finance_video_files
        WHERE is_valid=1 AND COALESCE(is_stale,0)=0
        GROUP BY category_name ORDER BY cnt DESC
    """).fetchall()
except:
    cats = []

print(f"=== Прогресс загрузки видео ===")
print(f"Всего сообщений в базе:    {total_all}")
print(f"Из них video/video_note:   {total_video}")
print()
print(f"--- Статусы загрузки ---")
print(f"  downloaded:              {downloaded}")
print(f"  skip_short_duration:     {skip_short}  (короткие, <20 сек)")
print(f"  skip_large:              {skip_large}  (>200 МБ, вручную)")
print(f"  skip_manual:             {skip_manual}  (недоступны)")
print(f"  skip_deleted:            {skip_deleted}")
print(f"  retry_pending:           {retry_pending}")
print(f"  Итого обработано:        {done_total} / {total_video}")
print(f"  Не обработано:           {total_video - done_total}")
print()
if files_on_disk is not None:
    print(f"Файлов на диске (индекс): {files_on_disk}")
if cats:
    print(f"\n--- По категориям (индекс) ---")
    for c in cats:
        print(f"  {c['cnt']:3d}  {c['category_name']}")

conn.close()
