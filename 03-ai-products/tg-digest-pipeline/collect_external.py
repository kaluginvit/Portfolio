"""
collect_external.py — сбор постов из внешних каналов в collector_queue.

Двухфазный подход:
  Фаза 1 (быстро): обходим все каналы, собираем посты прошедшие keyword-фильтр — без эмбеддингов
  Фаза 2 (батч):  все собранные тексты эмбеддим одним батчем → centroid-фильтр → в БД

Использование:
    python collect_external.py                    # посты за последние 24 часа
    python collect_external.py --since 2026-09-04 # конкретная дата
    python collect_external.py --limit 50         # лимит постов с канала
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import pickle
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, FloodWaitError
from telethon.tl.types import MessageMediaPhoto

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"
CHANNELS_FILE = HERE / "tmp_final_channels.json"
CENTROIDS_FILE = HERE / "vectors" / "centroids.pkl"

load_dotenv(HERE / ".env")

API_ID   = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION  = str(HERE.parent / "session2")

CENTROID_THRESHOLD = 0.70
VIRAL_MAX_SCORE    = 0.15
VIRAL_MIN_VIEWS    = 10_000
DELAY_BETWEEN_CHANNELS = 1.5


KEYWORDS = [
    "санкц", "геополит", "нато", "украин", "запад", "войн",
    "эконом", "инфляц", "бюджет", "рубл", "ввп", "цб", "ставк",
    "нефт", "газ", "энергет", "экспорт", "трубопров",
    "инвестиц", "фондов", "акци", "облигац",
    "промышлен", "импортозамещ", "производств",
    "технолог", "искусственн", "нейросет", "цифров",
    "китай", "китайск", "пекин",
    "макроэконом", "статистик", "демограф",
    "минфин", "минэконом", "минпромторг",
    "курс доллар", "курс евро", "ключевая ставка",
    "истори", "наук", "образован", "социолог",
    "юмор", "иронич", "сатир", "мем",
]


def _migrate(db_path: Path) -> None:
    from schema import COLLECTOR_QUEUE_DDL
    con = sqlite3.connect(db_path)
    con.executescript(COLLECTOR_QUEUE_DDL)
    con.commit()
    con.close()


def _keyword_match(text: str) -> str | None:
    if not text:
        return None
    t = text.lower()
    for kw in KEYWORDS:
        if kw in t:
            return kw
    return None


def _load_centroids() -> list[dict]:
    with open(CENTROIDS_FILE, "rb") as f:
        return pickle.load(f)


def _centroid_match(vec: np.ndarray, centroids: list[dict]) -> tuple[str, float]:
    best_label, best_score = "", 0.0
    for c in centroids:
        score = float(np.dot(vec, c["centroid"]))
        if score > best_score:
            best_score = score
            best_label = c["label"]
    return best_label, best_score


# ---------------------------------------------------------------------------
# Фаза 1: быстрый сбор без эмбеддингов
# ---------------------------------------------------------------------------

async def _fetch_channel(
    client: TelegramClient,
    channel: dict,
    since: datetime,
    until: datetime | None,
    limit: int,
) -> tuple[list[dict], int, str | None]:
    """Возвращает (посты прошедшие keyword, кол-во просмотрено, ошибка)."""
    channel_id = str(channel["id"])
    collected = []
    fetched = 0

    try:
        entity = await client.get_entity(int(channel_id))
    except Exception as e:
        return [], 0, str(e)

    try:
        async for msg in client.iter_messages(entity, limit=limit):
            if msg.date < since:
                break
            if until and msg.date >= until:
                continue
            if not msg.message:
                continue

            fetched += 1
            text     = msg.message
            views    = getattr(msg, "views",    0) or 0
            forwards = getattr(msg, "forwards", 0) or 0
            has_photo = 1 if isinstance(msg.media, MessageMediaPhoto) else 0

            kw = _keyword_match(text)
            is_viral = (not kw) and (views >= VIRAL_MIN_VIEWS)

            if not kw and not is_viral:
                continue

            collected.append({
                "channel_id":       channel_id,
                "channel_title":    channel.get("title", ""),
                "channel_username": channel.get("username", ""),
                "message_id":       msg.id,
                "date":             msg.date.strftime("%Y-%m-%dT%H:%M:%S"),
                "text":             text,
                "has_photo":        has_photo,
                "views":            views,
                "forwards":         forwards,
                "keyword_match":    kw or f"viral:{views}",
                "is_viral":         is_viral,
            })

    except ChannelPrivateError:
        return [], fetched, "private"
    except FloodWaitError as e:
        print(f"  FloodWait {e.seconds}s …", flush=True)
        await asyncio.sleep(e.seconds + 5)
    except Exception as e:
        return [], fetched, str(e)

    return collected, fetched, None


# ---------------------------------------------------------------------------
# Фаза 2: батч-эмбеддинг и фильтрация
# ---------------------------------------------------------------------------

def _embed_and_filter(candidates: list[dict], centroids: list[dict]) -> list[dict]:
    if not candidates:
        return []

    from embed_client import encode
    texts = [c["text"] for c in candidates]

    print(f"\nФаза 2: эмбеддинг {len(texts)} постов батчем…", flush=True)
    vecs = encode(texts)
    print("Эмбеддинг готов. Применяем centroid-фильтр…", flush=True)

    result = []
    for post, vec in zip(candidates, vecs):
        label, score = _centroid_match(vec, centroids)

        if post["is_viral"] and score <= VIRAL_MAX_SCORE:
            result.append({**post, "centroid_label": "Другое/Вирусное", "centroid_score": round(score, 4)})
        elif not post["is_viral"] and score >= CENTROID_THRESHOLD:
            result.append({**post, "centroid_label": label, "centroid_score": round(score, 4)})

    return result


# ---------------------------------------------------------------------------
# Запись в БД
# ---------------------------------------------------------------------------

def _insert(con: sqlite3.Connection, posts: list[dict]) -> int:
    inserted = 0
    for p in posts:
        try:
            con.execute(
                """INSERT OR IGNORE INTO collector_queue
                   (channel_id, channel_title, channel_username,
                    message_id, date, text, has_photo, views, forwards,
                    centroid_label, centroid_score, keyword_match)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (p["channel_id"], p["channel_title"], p["channel_username"],
                 p["message_id"], p["date"], p["text"], p["has_photo"],
                 p["views"], p["forwards"],
                 p["centroid_label"], p["centroid_score"], p["keyword_match"]),
            )
            if con.execute("SELECT changes()").fetchone()[0] > 0:
                inserted += 1
        except sqlite3.Error:
            pass
    con.commit()
    return inserted


# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------

async def collect(since_date: str | None = None, limit: int = 200) -> None:
    _migrate(DB_PATH)

    if since_date:
        since = datetime.fromisoformat(since_date).replace(tzinfo=timezone.utc)
        until = since + timedelta(days=1) if "T" not in since_date and " " not in since_date else None
    else:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        until = None

    until_str = until.strftime("%Y-%m-%d") if until else "сейчас"
    print(f"Сбор постов с {since.strftime('%Y-%m-%d')} по {until_str} UTC")

    channels  = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
    centroids = _load_centroids()
    print(f"Каналов: {len(channels)} | Центроидов: {len(centroids)}\n")

    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("Сессия не авторизована!")
        await client.disconnect()
        return

    n_total    = len(channels)
    candidates = []   # все посты прошедшие keyword
    total_fetched = 0
    total_errors  = 0
    progress_path = HERE / "data" / "collect_progress.json"

    def _write_progress(i: int, title: str, done: bool = False) -> None:
        json.dump({
            "running": not done, "done": done,
            "current": i, "total": n_total,
            "pct": round(i / n_total * 100, 1),
            "current_title": title,
            "fetched": total_fetched,
            "inserted": len(candidates),
            "since": since.strftime("%Y-%m-%d"),
        }, open(progress_path, "w", encoding="utf-8"), ensure_ascii=False)

    # --- Фаза 1 ---
    print("=== Фаза 1: сбор из каналов (без эмбеддингов) ===")
    for i, channel in enumerate(channels, 1):
        title = channel.get("title") or channel.get("username") or str(channel.get("id", "?"))
        print(f"[{i:3}/{n_total}] {title[:45]:<45}", end=" ", flush=True)
        _write_progress(i, title)

        posts, fetched, error = await _fetch_channel(client, channel, since, until, limit)
        total_fetched += fetched

        if error and fetched == 0:
            print(f"skip ({error[:30]})")
            total_errors += 1
        else:
            candidates.extend(posts)
            print(f"fetch={fetched} kw={len(posts)}")

        await asyncio.sleep(DELAY_BETWEEN_CHANNELS)

    await client.disconnect()
    print(f"\nФаза 1 завершена: просмотрено {total_fetched}, keyword-кандидатов {len(candidates)}")

    # --- Фаза 2 ---
    passed = _embed_and_filter(candidates, centroids)
    print(f"Прошло centroid-фильтр: {len(passed)}")

    con = sqlite3.connect(DB_PATH)
    inserted = _insert(con, passed)
    con.close()

    _write_progress(n_total, "завершено", done=True)

    print(f"\n{'='*50}")
    print(f"  Просмотрено:    {total_fetched:>6}")
    print(f"  Keyword-pass:   {len(candidates):>6}")
    print(f"  Centroid-pass:  {len(passed):>6}")
    print(f"  Добавлено в БД: {inserted:>6}")
    print(f"  Ошибок:         {total_errors:>6}")
    print(f"{'='*50}")

    con2 = sqlite3.connect(DB_PATH)
    print("\nРаспределение по нишам:")
    for row in con2.execute(
        "SELECT centroid_label, COUNT(*) c FROM collector_queue "
        "WHERE status='pending' GROUP BY centroid_label ORDER BY c DESC"
    ).fetchall():
        print(f"  {row[0]:<28} {row[1]:>5}")
    con2.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сбор постов из внешних каналов")
    parser.add_argument("--since", metavar="YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(collect(since_date=args.since, limit=args.limit))
