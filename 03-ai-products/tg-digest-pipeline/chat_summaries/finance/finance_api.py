"""
Local FastAPI interface for finance insight cards.

Run:
    uv run python -m uvicorn finance.finance_api:app --port 8765 --reload
or via refresh_finance.py:
    uv run python finance/refresh_finance.py --serve
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DB_PATH = ROOT / "finance_messages.db"
PIPELINE_VERSION = "finance-practical-v1"

CATEGORIES = {
    1: "Управленческий учет / P&L / ДДС / баланс",
    2: "CFO / финдир / финслужба",
    3: "Налоги / бухучет / регуляторика",
    4: "Маркетплейсы",
    5: "Платежи / ВЭД / SWIFT / SEPA",
    6: "Автоматизация / Excel / BI / AI для финансов",
    7: "Продажи финуслуг / лидогенерация / воронки",
    8: "Инвестиции / рынки / макро",
    9: "Обучение / курсы / вебинары",
    10: "Шаблоны / документы / чек-листы",
    11: "Мусор / реклама / нерелевантное",
}

TARGET_USERS = ["owner", "cfo", "accountant", "marketplace_seller", "investor", "consultant", "ops", "other"]

app = FastAPI(title="Finance Insights", docs_url="/api/docs")


def get_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for field in ("action_plan_json", "tools_json", "tags_json", "links_json", "entities_json"):
        if field in d and d[field]:
            try:
                d[field.replace("_json", "")] = json.loads(d[field])
            except Exception:
                d[field.replace("_json", "")] = []
        else:
            d[field.replace("_json", "")] = []
    # Подставляем v2 insight/entities если есть
    if "insight_merged" in d:
        d["insight"] = d.pop("insight_merged") or ""
    if "entities_merged" in d:
        try:
            d["entities"] = json.loads(d.pop("entities_merged") or "[]")
        except Exception:
            d["entities"] = []
    return d


@app.get("/cards")
def get_cards(
    q: Optional[str] = Query(None, description="Full-text search"),
    category_id: Optional[int] = Query(None),
    target_user: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    actionability: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    con = get_db()
    try:
        filters = ["a.pipeline_version = ?", "a.status = 'reviewed'", "a.category_id != 11"]
        params: list = [PIPELINE_VERSION]

        if category_id is not None:
            filters.append("a.category_id = ?")
            params.append(category_id)
        if target_user:
            filters.append("a.target_user = ?")
            params.append(target_user)
        if priority:
            filters.append("a.priority = ?")
            params.append(priority)
        if actionability:
            filters.append("a.actionability = ?")
            params.append(actionability)
        if date_from:
            filters.append("a.date >= ?")
            params.append(date_from)
        if date_to:
            filters.append("a.date <= ?")
            params.append(date_to)

        where = " AND ".join(filters)

        v2_join = """LEFT JOIN finance_item_analysis a2
                ON a2.source_peer_id=a.source_peer_id AND a2.message_id=a.message_id
                AND a2.pipeline_version='finance-practical-v2' AND a2.status='reviewed'"""

        if q:
            sql = f"""
                SELECT a.*, COALESCE(a2.insight, a.insight, '') AS insight_merged,
                       COALESCE(a2.entities_json, a.entities_json, '[]') AS entities_merged
                FROM finance_item_analysis a
                {v2_join}
                JOIN finance_fts f ON f.rowid = a.rowid
                WHERE {where} AND finance_fts MATCH ?
                ORDER BY rank, COALESCE(a.engagement_score, 0) DESC
                LIMIT ? OFFSET ?
            """
            params_fts = params + [q, limit, offset]
            rows = con.execute(sql, params_fts).fetchall()
        else:
            sql = f"""
                SELECT a.*, COALESCE(a2.insight, a.insight, '') AS insight_merged,
                       COALESCE(a2.entities_json, a.entities_json, '[]') AS entities_merged
                FROM finance_item_analysis a
                {v2_join}
                WHERE {where}
                ORDER BY
                    CASE a.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                    a.category_id,
                    COALESCE(a.engagement_score, 0) DESC,
                    a.date DESC
                LIMIT ? OFFSET ?
            """
            rows = con.execute(sql, params + [limit, offset]).fetchall()

        total_sql = f"""
            SELECT COUNT(*) FROM finance_item_analysis a
            {"JOIN finance_fts f ON f.rowid = a.rowid" if q else ""}
            WHERE {where} {"AND finance_fts MATCH ?" if q else ""}
        """
        total_params = params + ([q] if q else [])
        total = con.execute(total_sql, total_params).fetchone()[0]

        return {"total": total, "offset": offset, "limit": limit, "items": [row_to_dict(r) for r in rows]}
    finally:
        con.close()


@app.get("/card/{source_peer_id}/{message_id}")
def get_card(source_peer_id: int, message_id: int):
    con = get_db()
    try:
        row = con.execute(
            """SELECT a.*, COALESCE(a2.insight, a.insight, '') AS insight_merged,
                      COALESCE(a2.entities_json, a.entities_json, '[]') AS entities_merged
               FROM finance_item_analysis a
               LEFT JOIN finance_item_analysis a2
                 ON a2.source_peer_id=a.source_peer_id AND a2.message_id=a.message_id
                AND a2.pipeline_version='finance-practical-v2' AND a2.status='reviewed'
               WHERE a.source_peer_id=? AND a.message_id=? AND a.pipeline_version=?""",
            (source_peer_id, message_id, PIPELINE_VERSION),
        ).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": "not found"})
        return row_to_dict(row)
    finally:
        con.close()


@app.get("/stats")
def get_stats():
    con = get_db()
    try:
        cats = con.execute(
            """SELECT category_id, category_name, COUNT(*) as cnt
               FROM finance_item_analysis
               WHERE pipeline_version=? AND status='reviewed' AND category_id != 11
               GROUP BY category_id ORDER BY cnt DESC""",
            (PIPELINE_VERSION,),
        ).fetchall()
        prios = con.execute(
            """SELECT priority, COUNT(*) as cnt
               FROM finance_item_analysis
               WHERE pipeline_version=? AND status='reviewed'
               GROUP BY priority""",
            (PIPELINE_VERSION,),
        ).fetchall()
        top_eng = con.execute(
            """SELECT title, source_title, post_url, engagement_score, priority, category_name
               FROM finance_item_analysis
               WHERE pipeline_version=? AND status='reviewed' AND engagement_score IS NOT NULL
               ORDER BY engagement_score DESC LIMIT 10""",
            (PIPELINE_VERSION,),
        ).fetchall()
        insight_count = con.execute(
            """SELECT COUNT(*) FROM finance_item_analysis
               WHERE pipeline_version='finance-practical-v2' AND status='reviewed'
               AND insight != '' AND insight IS NOT NULL""",
        ).fetchone()[0]
        total = con.execute(
            "SELECT COUNT(*) FROM finance_item_analysis WHERE pipeline_version=? AND status='reviewed'",
            (PIPELINE_VERSION,),
        ).fetchone()[0]
        return {
            "total": total,
            "insight_coverage_pct": round(insight_count / total * 100, 1) if total else 0,
            "categories": [dict(r) for r in cats],
            "priorities": {r["priority"]: r["cnt"] for r in prios},
            "top_engagement": [dict(r) for r in top_eng],
        }
    finally:
        con.close()


_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finance Insights</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f5f5f5;color:#222}
header{background:#1a1a2e;color:#fff;padding:12px 20px;display:flex;align-items:center;gap:12px}
header h1{font-size:1.1rem;font-weight:600}
#count{font-size:.85rem;opacity:.7;margin-left:auto}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;padding:12px 20px;background:#fff;border-bottom:1px solid #e0e0e0}
.toolbar input,.toolbar select{padding:6px 10px;border:1px solid #ccc;border-radius:6px;font-size:.9rem;background:#fff}
.toolbar input[type=text]{flex:1;min-width:200px}
.toolbar button{padding:6px 14px;background:#1a1a2e;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:.9rem}
.toolbar button:hover{background:#2d2d5e}
#cards{padding:16px 20px;display:flex;flex-direction:column;gap:12px}
.card{background:#fff;border-radius:8px;padding:16px;border-left:4px solid #ccc;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card.high{border-left-color:#e53935}
.card.medium{border-left-color:#fb8c00}
.card.low{border-left-color:#43a047}
.card-title{font-weight:600;font-size:1rem;margin-bottom:6px}
.card-meta{font-size:.78rem;color:#666;margin-bottom:8px;display:flex;gap:10px;flex-wrap:wrap}
.badge{background:#eee;border-radius:4px;padding:2px 6px;font-size:.75rem}
.badge.high{background:#fde8e8;color:#c62828}
.badge.medium{background:#fff3e0;color:#e65100}
.badge.low{background:#e8f5e9;color:#1b5e20}
.card-summary{font-size:.88rem;color:#333;margin-bottom:6px}
.card-insight{font-size:.85rem;color:#1565c0;background:#e3f2fd;border-radius:4px;padding:6px 10px;margin-bottom:6px;border-left:3px solid #1565c0}
.card-actions{margin-top:8px;display:flex;gap:8px;flex-wrap:wrap}
.card-actions a{font-size:.8rem;color:#1a73e8;text-decoration:none}
.card-actions a:hover{text-decoration:underline}
.card-steps{font-size:.83rem;margin:6px 0;padding-left:16px;color:#444}
.card-steps li{margin-bottom:3px}
.tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.tag{background:#f0f0f0;border-radius:12px;padding:2px 8px;font-size:.73rem;color:#555}
#pagination{display:flex;justify-content:center;gap:8px;padding:16px;align-items:center}
#pagination button{padding:6px 14px;border:1px solid #ccc;background:#fff;border-radius:6px;cursor:pointer}
#pagination button:disabled{opacity:.4;cursor:default}
#pagination span{font-size:.9rem;color:#666}
.loading{text-align:center;padding:40px;color:#888}
</style>
</head>
<body>
<header>
  <h1>Finance Insights</h1>
  <span id="count"></span>
</header>
<div class="toolbar">
  <input type="text" id="q" placeholder="Поиск (FTS)..." />
  <select id="cat">
    <option value="">Все категории</option>
    <option value="1">Управленческий учет</option>
    <option value="2">CFO / финдир</option>
    <option value="3">Налоги / бухучет</option>
    <option value="4">Маркетплейсы</option>
    <option value="5">Платежи / ВЭД</option>
    <option value="6">Автоматизация / AI</option>
    <option value="7">Продажи финуслуг</option>
    <option value="8">Инвестиции / макро</option>
    <option value="9">Обучение / курсы</option>
    <option value="10">Шаблоны / чек-листы</option>
  </select>
  <select id="prio">
    <option value="">Все приоритеты</option>
    <option value="high">High</option>
    <option value="medium">Medium</option>
    <option value="low">Low</option>
  </select>
  <select id="user">
    <option value="">Все аудитории</option>
    <option value="cfo">CFO</option>
    <option value="owner">Owner</option>
    <option value="accountant">Accountant</option>
    <option value="marketplace_seller">Marketplace seller</option>
    <option value="investor">Investor</option>
    <option value="consultant">Consultant</option>
  </select>
  <input type="date" id="date_from" title="Дата от" />
  <input type="date" id="date_to" title="Дата до" />
  <button onclick="search(0)">Найти</button>
</div>
<div id="cards"><div class="loading">Загрузка...</div></div>
<div id="pagination">
  <button id="prev" onclick="prev()">← Назад</button>
  <span id="page_info"></span>
  <button id="next" onclick="next()">Вперёд →</button>
</div>
<script>
let currentOffset = 0;
const LIMIT = 30;

function esc(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') }

async function search(offset) {
  currentOffset = offset;
  const params = new URLSearchParams();
  const q = document.getElementById('q').value.trim();
  if (q) params.set('q', q);
  const cat = document.getElementById('cat').value;
  if (cat) params.set('category_id', cat);
  const prio = document.getElementById('prio').value;
  if (prio) params.set('priority', prio);
  const user = document.getElementById('user').value;
  if (user) params.set('target_user', user);
  const df = document.getElementById('date_from').value;
  if (df) params.set('date_from', df + 'T00:00:00+00:00');
  const dt = document.getElementById('date_to').value;
  if (dt) params.set('date_to', dt + 'T23:59:59+00:00');
  params.set('limit', LIMIT);
  params.set('offset', offset);

  document.getElementById('cards').innerHTML = '<div class="loading">Загрузка...</div>';
  const resp = await fetch('/cards?' + params.toString());
  const data = await resp.json();
  renderCards(data);
}

function renderCards(data) {
  const total = data.total;
  document.getElementById('count').textContent = total + ' записей';
  const items = data.items;
  if (!items.length) {
    document.getElementById('cards').innerHTML = '<div class="loading">Ничего не найдено</div>';
    return;
  }
  const html = items.map(r => {
    const steps = (r.action_plan||[]).map(s => `<li>${esc(s)}</li>`).join('');
    const tags = (r.tags||[]).map(t => `<span class="tag">${esc(t)}</span>`).join('');
    const insight = r.insight ? `<div class="card-insight">💡 ${esc(r.insight)}</div>` : '';
    const tools = (r.tools||[]).length ? `<span class="badge">${esc((r.tools||[]).join(', '))}</span>` : '';
    const eng = r.engagement_score ? `<span class="badge">eng: ${r.engagement_score}</span>` : '';
    return `<div class="card ${esc(r.priority)}">
      <div class="card-title">${esc(r.title||'Без названия')}</div>
      <div class="card-meta">
        <span class="badge ${esc(r.priority)}">${esc(r.priority)}</span>
        <span>${esc(r.source_title)}</span>
        <span>${(r.date||'').slice(0,10)}</span>
        <span class="badge">${esc(r.category_name)}</span>
        <span class="badge">${esc(r.target_user)}</span>
        ${tools}${eng}
      </div>
      <div class="card-summary">${esc(r.summary)}</div>
      ${insight}
      ${steps ? `<ul class="card-steps">${steps}</ul>` : ''}
      <div class="tags">${tags}</div>
      <div class="card-actions">
        ${r.post_url ? `<a href="${esc(r.post_url)}" target="_blank">Открыть пост →</a>` : ''}
        ${(r.links||[]).map(l=>`<a href="${esc(l)}" target="_blank">${esc(l.replace(/^https?:\/\//,'').slice(0,40))}</a>`).join('')}
      </div>
    </div>`;
  }).join('');
  document.getElementById('cards').innerHTML = html;

  const page = Math.floor(currentOffset / LIMIT) + 1;
  const totalPages = Math.ceil(total / LIMIT);
  document.getElementById('page_info').textContent = `Стр. ${page} / ${totalPages}`;
  document.getElementById('prev').disabled = currentOffset === 0;
  document.getElementById('next').disabled = currentOffset + LIMIT >= total;
}

function prev() { if (currentOffset >= LIMIT) search(currentOffset - LIMIT); }
function next() { search(currentOffset + LIMIT); }

document.getElementById('q').addEventListener('keydown', e => { if (e.key === 'Enter') search(0); });
search(0);
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return _HTML
