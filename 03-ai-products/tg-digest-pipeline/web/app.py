"""
web/app.py — FastAPI веб-интерфейс для проекта ИнфоПовод.
"""

from __future__ import annotations

import json
import pickle
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------

HERE = Path(__file__).parent.parent   # корень проекта
sys.path.insert(0, str(HERE))

DB_PATH = HERE / "data" / "messages.db"
INDEX_PATH = HERE / "vectors" / "faiss.index"
META_PATH  = HERE / "vectors" / "meta.pkl"

WEB_DIR = HERE / "web"

# ---------------------------------------------------------------------------
# Приложение
# ---------------------------------------------------------------------------

app = FastAPI(title="ИнфоПовод")

app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
app.mount("/photos", StaticFiles(directory=str(HERE / "photos")), name="photos")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

# ---------------------------------------------------------------------------
# Ниши — маппинг label → теги (из build_centroids.py)
# ---------------------------------------------------------------------------

NICHES = [
    {"label": "Геополитика/Война",  "tags": ["геополитика", "санкции", "сша"]},
    {"label": "Экономика РФ",       "tags": ["экономика", "инфляция", "бюджет", "рубль"]},
    {"label": "Энергетика/Сырьё",   "tags": ["нефть", "энергетика", "экспорт"]},
    {"label": "Финансы/Рынки",      "tags": ["инвестиции", "фондовый рынок", "банки"]},
    {"label": "Промышленность",     "tags": ["промышленность", "импортозамещение"]},
    {"label": "Технологии/AI",      "tags": ["технологии"]},
    {"label": "Китай/Азия",         "tags": ["китай"]},
    {"label": "Макро/Статистика",   "tags": ["макроэкономика", "статистика", "демография"]},
    {"label": "Познавательное",     "tags": ["история", "наука", "образование", "социология"]},
    {"label": "Юмор/Ирония",        "tags": ["юмор", "ирония"]},
]

def _niche_sql(niche_label: str) -> str:
    """Возвращает SQL-условие для фильтрации по нише через теги."""
    for n in NICHES:
        if n["label"] == niche_label:
            parts = [f"e.tags LIKE '%{t}%'" for t in n["tags"]]
            return "(" + " OR ".join(parts) + ")"
    return ""


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _get_con_ro():
    from db import connect_readonly
    return connect_readonly(DB_PATH)


def _get_con_rw():
    from db import connect_rw
    return connect_rw(DB_PATH)


def _db_exists() -> bool:
    return DB_PATH.exists()


def _count_table(table: str, where: str = "") -> int:
    if not _db_exists():
        return 0
    try:
        import sqlite3
        con = sqlite3.connect(DB_PATH)
        sql = f"SELECT COUNT(*) FROM {table}" + (f" WHERE {where}" if where else "")
        result = con.execute(sql).fetchone()[0]
        con.close()
        return result
    except Exception:
        return 0


def _ensure_dismissed_table() -> None:
    if not _db_exists():
        return
    try:
        con = _get_con_rw()
        con.execute("CREATE TABLE IF NOT EXISTS dismissed (message_id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()
    except Exception:
        pass

_ensure_dismissed_table()


def _fetch_latest(limit: int = 50, offset: int = 0, source: str = "", niche: str = "",
                  authored: bool = False, from_date: str = "", to_date: str = "") -> list[dict]:
    if not _db_exists():
        return []
    try:
        con = _get_con_ro()
        clauses = ["m.message_id NOT IN (SELECT message_id FROM dismissed)"]
        if authored:
            clauses.append("m.message_id IN (SELECT message_id FROM user_tags WHERE tag='#имеюссообщить')")
        elif source:
            clauses.append(f"m.source = '{source}'")
        if niche:
            nc = _niche_sql(niche)
            if nc:
                clauses.append(nc)
        if from_date:
            clauses.append(f"m.date >= '{from_date}'")
        if to_date:
            clauses.append(f"m.date <= '{to_date}T23:59:59'")
        where = "WHERE " + " AND ".join(clauses)
        rows = con.execute(
            f"""
            SELECT m.message_id, m.date, m.text, m.forwarded_from, m.has_photo, m.photo,
                   e.entities, e.tags, e.insight, m.source
              FROM messages m
              LEFT JOIN enrichments e ON e.message_id = m.message_id
             {where}
             ORDER BY m.date DESC
             LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _parse_json_field(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except Exception:
        return []


def _enrich_posts(posts: list[dict]) -> list[dict]:
    """Парсит JSON-поля entities и tags из строк."""
    for p in posts:
        p["tags"] = _parse_json_field(p.get("tags"))
        p["entities"] = _parse_json_field(p.get("entities"))
    return posts


def _promote_to_archive(post_id: int) -> None:
    """Копирует одобренный пост из collector_queue в messages + messages_filtered."""
    try:
        con = _get_con_rw()
        row = con.execute(
            "SELECT id, channel_title, channel_username, message_id, date, text, has_photo, views, forwards "
            "FROM collector_queue WHERE id=?", (post_id,)
        ).fetchone()
        if not row:
            con.close()
            return
        ext_id = -row[0]  # отрицательный ID, не пересекается с Telegram ID
        forwarded_from = row[1] or row[2] or ""
        con.execute(
            """INSERT OR IGNORE INTO messages
               (message_id, date, text, forwarded_from, has_photo, views, forwards, source)
               VALUES (?,?,?,?,?,?,?,?)""",
            (ext_id, row[4], row[5], forwarded_from, row[6], row[7], row[8], "external")
        )
        con.execute(
            "INSERT OR IGNORE INTO messages_filtered (message_id) VALUES (?)", (ext_id,)
        )
        con.commit()
        con.close()
    except Exception as exc:
        print(f"[promote] ошибка: {exc}", file=sys.stderr)


def _vectors_count() -> int:
    if not META_PATH.exists():
        return 0
    try:
        with open(META_PATH, "rb") as f:
            meta = pickle.load(f)
        return len(meta)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, source: str = "", niche: str = "", authored: int = 0, offset: int = 0):
    posts = _enrich_posts(_fetch_latest(50, offset=offset, source=source, niche=niche, authored=bool(authored), from_date="", to_date=""))
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": posts,
            "query": "",
            "mode": "hybrid",
            "from_date": "",
            "to_date": "",
            "source": source,
            "niche": niche,
            "authored": authored,
            "offset": offset,
            "niches": NICHES,
        },
    )


# ---------------------------------------------------------------------------
# GET /search
# ---------------------------------------------------------------------------

@app.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str = "",
    mode: str = "hybrid",
    from_date: str = "",
    to_date: str = "",
    source: str = "",
    niche: str = "",
    authored: int = 0,
):
    posts: list[dict] = []

    if q.strip():
        try:
            from search import semantic_search, keyword_search, hybrid_search

            kwargs = dict(
                query=q.strip(),
                top_k=50,
                db_path=DB_PATH,
                index_path=INDEX_PATH,
                meta_path=META_PATH,
            )

            if mode == "semantic":
                posts = semantic_search(**kwargs)
            elif mode == "keyword":
                posts = keyword_search(query=q.strip(), top_k=50, db_path=DB_PATH)
            else:
                posts = hybrid_search(**kwargs)

            # Фильтрация по датам
            if from_date:
                posts = [p for p in posts if (p.get("date") or "") >= from_date]
            if to_date:
                posts = [p for p in posts if (p.get("date") or "") <= to_date + "T99"]
            if source:
                posts = [p for p in posts if p.get("source") == source]

        except Exception as exc:
            posts = []
            print(f"[search] ошибка: {exc}", file=sys.stderr)
    else:
        posts = _fetch_latest(50, source=source, niche=niche, authored=bool(authored),
                              from_date=from_date, to_date=to_date)

    posts = _enrich_posts(posts)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": posts,
            "query": q,
            "mode": mode,
            "from_date": from_date,
            "to_date": to_date,
            "source": source,
            "niche": niche,
            "authored": authored,
            "offset": 0,
            "niches": NICHES,
        },
    )


# ---------------------------------------------------------------------------
# POST /card/{message_id}/dismiss
# ---------------------------------------------------------------------------

@app.post("/card/{message_id}/dismiss")
async def dismiss_post(message_id: int):
    if _db_exists():
        try:
            con = _get_con_rw()
            con.execute("INSERT OR IGNORE INTO dismissed (message_id) VALUES (?)", (message_id,))
            con.commit()
            con.close()
        except Exception as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# POST /search/summarize
# ---------------------------------------------------------------------------

@app.post("/search/summarize")
async def search_summarize(request: Request):
    try:
        body = await request.json()
        q = body.get("q", "")
        posts = body.get("posts", [])
        from llm_summarize import summarize_results
        summary = summarize_results(query=q, posts=posts)
        return JSONResponse({"summary": summary})
    except Exception as exc:
        return JSONResponse({"summary": f"Ошибка суммаризации: {exc}"}, status_code=500)


# ---------------------------------------------------------------------------
# GET /card/{message_id}
# ---------------------------------------------------------------------------

@app.get("/card/{message_id}", response_class=HTMLResponse)
async def card(request: Request, message_id: int):
    if not _db_exists():
        return templates.TemplateResponse(
            "card.html",
            {"request": request, "post": None, "user_tags": []},
        )
    try:
        con = _get_con_ro()
        row = con.execute(
            """
            SELECT m.message_id, m.date, m.text, m.forwarded_from, m.has_photo, m.photo,
                   e.entities, e.tags, e.insight,
                   pe.description  AS photo_description,
                   pe.objects      AS photo_objects,
                   pe.text_on_image AS photo_text_on_image
              FROM messages m
              LEFT JOIN enrichments e   ON e.message_id  = m.message_id
              LEFT JOIN photo_enrichments pe ON pe.message_id = m.message_id
             WHERE m.message_id = ?
            """,
            (message_id,),
        ).fetchone()

        post = dict(row) if row else None
        if post:
            post["tags"] = _parse_json_field(post.get("tags"))
            post["entities"] = _parse_json_field(post.get("entities"))
            post["photo_objects"] = _parse_json_field(post.get("photo_objects"))

        utags = con.execute(
            "SELECT id, tag, note, created_at FROM user_tags WHERE message_id = ? ORDER BY created_at",
            (message_id,),
        ).fetchall()
        con.close()
        user_tags = [dict(r) for r in utags]
    except Exception:
        post = None
        user_tags = []

    return templates.TemplateResponse(
        "card.html",
        {"request": request, "post": post, "user_tags": user_tags},
    )


# ---------------------------------------------------------------------------
# POST /card/{message_id}/tags
# ---------------------------------------------------------------------------

@app.post("/card/{message_id}/tags")
async def add_tag(message_id: int, tag: str = Form(...)):
    tag = tag.strip()
    if tag and _db_exists():
        try:
            con = _get_con_rw()
            con.execute(
                "INSERT INTO user_tags (message_id, tag) VALUES (?, ?)",
                (message_id, tag),
            )
            con.commit()
            con.close()
        except Exception as exc:
            print(f"[add_tag] ошибка: {exc}", file=sys.stderr)
    return RedirectResponse(url=f"/card/{message_id}", status_code=303)


# ---------------------------------------------------------------------------
# DELETE /card/{message_id}/tags/{tag_id}
# ---------------------------------------------------------------------------

@app.delete("/card/{message_id}/tags/{tag_id}")
async def delete_tag(message_id: int, tag_id: int):
    if _db_exists():
        try:
            con = _get_con_rw()
            con.execute(
                "DELETE FROM user_tags WHERE id = ? AND message_id = ?",
                (tag_id, message_id),
            )
            con.commit()
            con.close()
        except Exception as exc:
            print(f"[delete_tag] ошибка: {exc}", file=sys.stderr)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# POST /card/{message_id}/note
# ---------------------------------------------------------------------------

@app.post("/card/{message_id}/note")
async def add_note(message_id: int, note: str = Form(...)):
    note = note.strip()
    if note and _db_exists():
        try:
            con = _get_con_rw()
            # Обновляем note у последнего тега этого сообщения
            con.execute(
                """
                UPDATE user_tags SET note = ?
                 WHERE id = (
                     SELECT id FROM user_tags
                      WHERE message_id = ?
                      ORDER BY created_at DESC
                      LIMIT 1
                 )
                """,
                (note, message_id),
            )
            con.commit()
            con.close()
        except Exception as exc:
            print(f"[add_note] ошибка: {exc}", file=sys.stderr)
    return RedirectResponse(url=f"/card/{message_id}", status_code=303)


# ---------------------------------------------------------------------------
# GET /analytics
# ---------------------------------------------------------------------------

@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    posts_per_month: list[dict] = []
    top_forwarded: list[dict] = []
    top_tags: list[dict] = []

    if _db_exists():
        try:
            con = _get_con_ro()

            # Посты по месяцам
            rows = con.execute(
                """
                SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS cnt
                  FROM messages
                 GROUP BY month
                 ORDER BY month DESC
                 LIMIT 24
                """
            ).fetchall()
            posts_per_month = [dict(r) for r in rows]
            posts_per_month.reverse()

            # Топ источников репостов
            rows = con.execute(
                """
                SELECT forwarded_from, COUNT(*) AS cnt
                  FROM messages
                 WHERE forwarded_from IS NOT NULL AND forwarded_from != ''
                 GROUP BY forwarded_from
                 ORDER BY cnt DESC
                 LIMIT 10
                """
            ).fetchall()
            top_forwarded = [dict(r) for r in rows]

            con.close()
        except Exception:
            pass

        # Топ тегов из enrichments — парсим JSON
        try:
            import sqlite3
            con2 = sqlite3.connect(DB_PATH)
            tag_rows = con2.execute(
                "SELECT tags FROM enrichments WHERE tags IS NOT NULL AND tags != ''"
            ).fetchall()
            con2.close()

            tag_counter: dict[str, int] = {}
            for (tags_str,) in tag_rows:
                try:
                    tags = json.loads(tags_str)
                    if isinstance(tags, list):
                        for t in tags:
                            if t:
                                tag_counter[str(t)] = tag_counter.get(str(t), 0) + 1
                except Exception:
                    pass

            top_tags = sorted(
                [{"tag": k, "cnt": v} for k, v in tag_counter.items()],
                key=lambda x: x["cnt"],
                reverse=True,
            )[:20]
        except Exception:
            pass

    # Максимум для CSS bar chart
    max_month = max((p["cnt"] for p in posts_per_month), default=1)

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "posts_per_month": posts_per_month,
            "top_forwarded": top_forwarded,
            "top_tags": top_tags,
            "max_month": max_month,
        },
    )


# ---------------------------------------------------------------------------
# GET /pipeline
# ---------------------------------------------------------------------------

@app.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(request: Request):
    return templates.TemplateResponse("pipeline.html", {"request": request})


# ---------------------------------------------------------------------------
# GET /pipeline/status
# ---------------------------------------------------------------------------

def _pinecone_count() -> int:
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv(HERE / ".env")
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        stats = pc.Index("infopovod").describe_index_stats()
        return int(stats.get("total_vector_count") or stats.total_vector_count)
    except Exception:
        return -1


def _collect_progress() -> dict:
    p = HERE / "data" / "collect_progress.json"
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@app.get("/pipeline/status")
async def pipeline_status():
    messages          = _count_table("messages")
    messages_filtered = _count_table("messages_filtered")
    enrichments       = _count_table("enrichments")
    vectors_faiss     = _vectors_count()
    vectors_pinecone  = _pinecone_count()

    return JSONResponse(
        {
            "messages":          messages,
            "messages_filtered": messages_filtered,
            "enrichments":       enrichments,
            "vectors":           vectors_faiss,
            "vectors_pinecone":  vectors_pinecone,
            "running":           None,
            "collect_progress":  _collect_progress(),
        }
    )


# ---------------------------------------------------------------------------
# POST /pipeline/run
# ---------------------------------------------------------------------------

_STEP_FLAG_MAP = {
    "import-json": "--import-json",
    "collect":     "--collect",
    "gate":        "--gate",
    "analyze":     "--analyze",
    "embed":       "--embed",
}

@app.post("/pipeline/run")
async def pipeline_run(request: Request):
    try:
        body = await request.json()
        step  = body.get("step", "")
        limit = int(body.get("limit", 300))

        flag = _STEP_FLAG_MAP.get(step)
        if not flag:
            return JSONResponse({"ok": False, "error": f"Неизвестный шаг: {step}"}, status_code=400)

        cmd = [sys.executable, str(HERE / "pipeline.py"), flag]
        if step == "analyze" and limit:
            cmd += ["--limit", str(limit)]

        proc = subprocess.Popen(
            cmd,
            cwd=str(HERE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return JSONResponse({"ok": True, "pid": proc.pid})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


# ---------------------------------------------------------------------------
# GET /incoming  — дашборд входящих постов
# ---------------------------------------------------------------------------

def _get_incoming_stats(con) -> dict:
    rows = con.execute(
        "SELECT status, COUNT(*) FROM collector_queue GROUP BY status"
    ).fetchall()
    d = {r[0]: r[1] for r in rows}
    total = sum(d.values())
    return {
        "total":    total,
        "pending":  d.get("pending",  0),
        "approved": d.get("approved", 0),
        "rejected": d.get("rejected", 0),
    }


def _get_niches(con, status_filter: str) -> list[dict]:
    where = f"WHERE status='{status_filter}'" if status_filter else ""
    rows = con.execute(
        f"SELECT centroid_label, COUNT(*) c FROM collector_queue {where} "
        f"GROUP BY centroid_label ORDER BY c DESC"
    ).fetchall()
    return [{"label": r[0] or "—", "count": r[1]} for r in rows]


def _get_top_channels(con, status_filter: str, niche: str) -> list[dict]:
    conditions = []
    if status_filter:
        conditions.append(f"status='{status_filter}'")
    if niche:
        conditions.append(f"centroid_label='{niche}'")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = con.execute(
        f"SELECT channel_title, channel_username, COUNT(*) c FROM collector_queue "
        f"{where} GROUP BY channel_id ORDER BY c DESC LIMIT 15"
    ).fetchall()
    return [{"title": r[0] or r[1] or "?", "count": r[2]} for r in rows]


@app.get("/incoming")
async def incoming_page(
    request: Request,
    status: str = "pending",
    niche: str = "",
    offset: int = 0,
):
    try:
        con = _get_con_ro()
        stats        = _get_incoming_stats(con)
        niches       = _get_niches(con, status)
        top_channels = _get_top_channels(con, status, niche)

        conditions = []
        if status:
            conditions.append(f"status='{status}'")
        if niche:
            conditions.append(f"centroid_label='{niche}'")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        rows = con.execute(
            f"SELECT id, channel_id, channel_title, channel_username, "
            f"message_id, date, text, has_photo, views, forwards, "
            f"centroid_label, centroid_score, keyword_match, status "
            f"FROM collector_queue {where} ORDER BY date DESC LIMIT 50 OFFSET {offset}"
        ).fetchall()

        posts = []
        for r in rows:
            posts.append({
                "id": r[0], "channel_id": r[1], "channel_title": r[2],
                "channel_username": r[3], "message_id": r[4], "date": r[5],
                "text": r[6] or "", "has_photo": r[7], "views": r[8],
                "forwards": r[9], "centroid_label": r[10],
                "centroid_score": r[11] or 0, "keyword_match": r[12],
                "status": r[13],
            })
        # Чарт 1: топ каналов по суммарным просмотрам
        top_by_views = con.execute(
            "SELECT channel_title, channel_username, SUM(views) v "
            "FROM collector_queue WHERE status!='rejected' "
            "GROUP BY channel_id ORDER BY v DESC LIMIT 10"
        ).fetchall()

        # Чарт 2: посты по часам
        by_hour = con.execute(
            "SELECT SUBSTR(date,12,2) h, COUNT(*) c FROM collector_queue "
            "WHERE status!='rejected' GROUP BY h ORDER BY h"
        ).fetchall()

        con.close()

        return templates.TemplateResponse("incoming.html", {
            "request":         request,
            "stats":           stats,
            "niches":          niches,
            "top_channels":    top_channels,
            "posts":           posts,
            "selected_status": status,
            "selected_niche":  niche,
            "top_by_views":    [{"title": r[0] or r[1] or "?", "views": r[2] or 0} for r in top_by_views],
            "by_hour":         [{"hour": r[0], "count": r[1]} for r in by_hour],
        })
    except Exception as exc:
        return HTMLResponse(f"<pre>Ошибка: {exc}</pre>", status_code=500)


@app.post("/incoming/{post_id}/approve")
async def approve_post(post_id: int):
    try:
        con = _get_con_rw()
        con.execute(
            "UPDATE collector_queue SET status='approved', reviewed_at=strftime('%Y-%m-%dT%H:%M:%S','now') WHERE id=?",
            (post_id,)
        )
        con.commit()
        con.close()
        _promote_to_archive(post_id)
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@app.post("/incoming/{post_id}/reject")
async def reject_post(post_id: int):
    try:
        con = _get_con_rw()
        con.execute(
            "UPDATE collector_queue SET status='rejected', reviewed_at=strftime('%Y-%m-%dT%H:%M:%S','now') WHERE id=?",
            (post_id,)
        )
        con.commit()
        con.close()
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


# ---------------------------------------------------------------------------
# GET /trends  — кластеры историй
# ---------------------------------------------------------------------------

@app.get("/trends", response_class=HTMLResponse)
async def trends_page(request: Request, niche: str = ""):
    try:
        con = _get_con_ro()

        conditions = ["sc.id >= 0"]
        if niche:
            conditions.append(f"sc.niche='{niche}'")
        where = "WHERE " + " AND ".join(conditions)

        clusters = con.execute(
            f"""SELECT sc.id, sc.label, sc.niche, sc.post_count, sc.channel_count,
                       sc.total_views, sc.max_views, sc.score, sc.clustered_at
                  FROM story_clusters sc
                 {where}
                 ORDER BY sc.score DESC"""
        ).fetchall()

        result = []
        for c in clusters:
            cid = c[0]
            posts = con.execute(
                """SELECT id, channel_title, channel_username, date, text,
                          views, forwards, centroid_label, centroid_score, status
                     FROM collector_queue
                    WHERE cluster_id=? ORDER BY views DESC""",
                (cid,)
            ).fetchall()
            result.append({
                "id": cid, "label": c[1], "niche": c[2],
                "post_count": c[3], "channel_count": c[4],
                "total_views": c[5], "max_views": c[6],
                "score": c[7], "clustered_at": c[8],
                "posts": [
                    {
                        "id": p[0], "channel_title": p[1], "channel_username": p[2],
                        "date": p[3], "text": (p[4] or "")[:300],
                        "views": p[5], "forwards": p[6],
                        "centroid_label": p[7], "status": p[9],
                    }
                    for p in posts
                ],
            })

        niches = con.execute(
            "SELECT DISTINCT niche FROM story_clusters ORDER BY niche"
        ).fetchall()
        clustered_at = con.execute(
            "SELECT MAX(clustered_at) FROM story_clusters"
        ).fetchone()[0]

        # Одиночные посты (шум)
        noise_where = "cluster_id=-1 AND status='pending'"
        if niche:
            noise_where += f" AND centroid_label='{niche}'"
        noise_rows = con.execute(
            f"SELECT id, channel_title, channel_username, date, text, "
            f"views, forwards, centroid_label, status "
            f"FROM collector_queue WHERE {noise_where} ORDER BY centroid_label, views DESC"
        ).fetchall()
        con.close()
        noise_posts = [
            {
                "id": r[0], "channel_title": r[1], "channel_username": r[2],
                "date": r[3], "text": (r[4] or "")[:300],
                "views": r[5], "forwards": r[6],
                "centroid_label": r[7], "status": r[8],
            }
            for r in noise_rows
        ]

        return templates.TemplateResponse("trends.html", {
            "request":        request,
            "clusters":       result,
            "noise_posts":    noise_posts,
            "niches":         [r[0] for r in niches if r[0]],
            "selected_niche": niche,
            "clustered_at":   clustered_at,
        })
    except Exception as exc:
        return HTMLResponse(f"<pre>Ошибка: {exc}</pre>", status_code=500)


@app.post("/trends/{cluster_id}/approve")
async def approve_cluster(cluster_id: int):
    try:
        con = _get_con_rw()
        ids = [r[0] for r in con.execute(
            "SELECT id FROM collector_queue WHERE cluster_id=? AND status='pending'", (cluster_id,)
        ).fetchall()]
        con.execute(
            "UPDATE collector_queue SET status='approved', reviewed_at=strftime('%Y-%m-%dT%H:%M:%S','now') "
            "WHERE cluster_id=? AND status='pending'",
            (cluster_id,)
        )
        con.commit()
        con.close()
        for post_id in ids:
            _promote_to_archive(post_id)
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@app.post("/trends/{cluster_id}/reject")
async def reject_cluster(cluster_id: int):
    try:
        con = _get_con_rw()
        con.execute(
            "UPDATE collector_queue SET status='rejected', reviewed_at=strftime('%Y-%m-%dT%H:%M:%S','now') "
            "WHERE cluster_id=? AND status='pending'",
            (cluster_id,)
        )
        con.commit()
        con.close()
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@app.post("/trends/recluster")
async def recluster():
    try:
        proc = subprocess.Popen(
            [sys.executable, str(HERE / "cluster_queue.py")],
            cwd=str(HERE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return JSONResponse({"ok": True, "pid": proc.pid})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@app.post("/incoming/collect")
async def trigger_collect():
    try:
        proc = subprocess.Popen(
            [sys.executable, str(HERE / "collect_external.py")],
            cwd=str(HERE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return RedirectResponse("/incoming", status_code=303)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


# ---------------------------------------------------------------------------
# GET /generate  — страница генерации постов
# ---------------------------------------------------------------------------

@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    import sqlite3 as _sq
    con = _sq.connect(DB_PATH)
    clusters = con.execute(
        "SELECT id, label, niche, channel_count, total_views FROM story_clusters ORDER BY score DESC LIMIT 50"
    ).fetchall()
    con.close()
    cluster_list = [
        {"id": r[0], "label": r[1] or "", "niche": r[2] or "", "channel_count": r[3], "total_views": r[4]}
        for r in clusters
    ]
    return templates.TemplateResponse(
        "generate.html",
        {"request": request, "clusters": cluster_list},
    )


# ---------------------------------------------------------------------------
# POST /generate/run  — запуск генерации (AJAX)
# ---------------------------------------------------------------------------

@app.post("/generate/run")
async def generate_run(request: Request):
    try:
        body = await request.json()
        topic      = (body.get("topic") or "").strip()
        cluster_id = body.get("cluster_id")
        if cluster_id is not None:
            try:
                cluster_id = int(cluster_id)
            except (ValueError, TypeError):
                cluster_id = None

        if not topic and cluster_id is None:
            return JSONResponse({"ok": False, "error": "Нужно указать тему или кластер"}, status_code=400)

        # Если тема не задана — берём label кластера
        if not topic and cluster_id is not None:
            import sqlite3 as _sq
            con = _sq.connect(DB_PATH)
            row = con.execute("SELECT label FROM story_clusters WHERE id=?", (cluster_id,)).fetchone()
            con.close()
            topic = (row[0] or "") if row else ""

        from generate import generate_post
        result = generate_post(topic=topic, cluster_id=cluster_id, db_path=DB_PATH)
        return JSONResponse({"ok": True, **result})
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
