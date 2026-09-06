#!/usr/bin/env python3
"""
Fedresurs auction fetcher.

python fedresurs.py                  # sync bookmarks → SQLite + HTML
python fedresurs.py --no-fetch       # only re-render HTML from existing DB
python fedresurs.py --refetch        # re-download cached JSONs
python fedresurs.py --limit 20       # process only N links
python fedresurs.py --sheets         # also sync to Google Sheets (requires client_secrets.json + pip install gspread google-auth google-auth-oauthlib)
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# ── PATHS ──────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).resolve().parent
DATA_DIR    = BASE_DIR / "data"
RAW_DIR     = DATA_DIR / "raw"
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH     = DATA_DIR / "fedresurs.sqlite3"
CREDS_PATH  = BASE_DIR / "credentials.json"

# ── CONFIG ─────────────────────────────────────────────────────────────────

SPREADSHEET_ID  = "1OGxnZ1gp_gxvu4NPVS4OVT__qJQQDrrTCgHkMz3epHs"
SHEET_NAME      = "Лоты"
CHROME_FOLDER   = "Объявления о торгах"
CHROMIUM_FOLDER = "Торги оперативные"
FEDRESURS_API   = "https://fedresurs.ru/backend/bankruptcy-messages/{}"
FEDRESURS_CARD  = "https://fedresurs.ru/bankruptmessages/{}"

BROWSERS = [
    ("Chrome",   os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks"),   CHROME_FOLDER),
    ("Chromium", os.path.expandvars(r"%LOCALAPPDATA%\Chromium\User Data\Default\Bookmarks"),         CHROMIUM_FOLDER),
]

TRADE_TYPE_LABEL = {
    "PublicOffer":   "Публичное предложение",
    "OpenedAuction": "Открытый аукцион",
    "ClosedAuction": "Закрытый аукцион",
}

LOT_STATUS_LABEL = {
    "TradeSuccessed":                      "Состоялись",
    "TradeFailed":                         "Не состоялись",
    "TradeFailedSoldToTheOnlyParticipant": "Единственный участник",
}

# ── SHEET COLUMNS ──────────────────────────────────────────────────────────

SHEET_COLS: list[tuple[str, str]] = [
    ("lot_id",             "ID лота"),
    ("status",             "Статус"),
    ("source_browser",     "Браузер"),
    ("source_folder",      "Папка"),
    ("url",                "Ссылка"),
    ("message_type_name",  "Тип сообщения"),
    ("publish_date",       "Дата публикации"),
    ("bankrupt_name",      "Банкрот"),
    ("bankrupt_inn",       "ИНН банкрота"),
    ("bankrupt_birthdate", "Дата рождения"),
    ("bankrupt_snils",     "СНИЛС"),
    ("bankrupt_ogrn",      "ОГРН/ОГРНИП"),
    ("case_number",        "Номер дела"),
    ("manager_name",       "Управляющий"),
    ("manager_inn",        "ИНН управляющего"),
    ("manager_email",      "Email управляющего"),
    ("lot_order",          "Лот №"),
    ("description",        "Описание"),
    ("classifier",         "Классификатор"),
    ("start_price",        "Стартовая цена, ₽"),
    ("advance_pct",        "Задаток %"),
    ("trade_type",         "Тип торгов"),
    ("trade_site",         "Площадка"),
    ("app_begin",          "Начало заявок"),
    ("app_end",            "Конец заявок"),
    ("auction_datetime",   "Дата торгов"),
    ("price_reduction",    "Порядок снижения"),
    ("schedule_text",      "Расписание цен"),
    ("is_repeat",          "Повторные"),
    ("additional_text",    "Доп. текст"),
    ("result_url",         "Ссылка на результат"),
    ("result_number",      "Номер результата"),
    ("result_date",        "Дата результата"),
    ("result_lot_status",  "Итог торгов"),
    ("result_basis",       "Основание"),
    ("winner_fio",         "Победитель"),
    ("winner_inn",         "ИНН победителя"),
    ("winner_price",       "Цена победителя, ₽"),
    ("result_text",        "Текст результата"),
    ("updated_at",         "Обновлено"),
]
SHEET_KEYS    = [c[0] for c in SHEET_COLS]
SHEET_HEADERS = [c[1] for c in SHEET_COLS]

# ── DB SCHEMA ──────────────────────────────────────────────────────────────

SCHEMA = """
create table if not exists lots (
    lot_id             text primary key,
    status             text default 'Активен',
    source_browser     text,
    source_folder      text,
    url                text,
    message_guid       text,
    message_number     text,
    message_type       text,
    message_type_name  text,
    publish_date       text,
    bankrupt_name      text,
    bankrupt_inn       text,
    bankrupt_type      text,
    bankrupt_address   text,
    bankrupt_birthdate text,
    bankrupt_snils     text,
    bankrupt_ogrn      text,
    case_number        text,
    case_judge         text,
    manager_name       text,
    manager_inn        text,
    manager_email      text,
    manager_address    text,
    manager_sro        text,
    lot_order          integer,
    description        text,
    classifier         text,
    start_price        real,
    advance_pct        real,
    trade_type         text,
    trade_site         text,
    app_begin          text,
    app_end            text,
    auction_datetime   text,
    price_reduction    text,
    schedule_text      text,
    is_repeat          integer,
    additional_text    text,
    result_url         text,
    result_number      text,
    result_date        text,
    result_guid        text,
    result_lot_status  text,
    result_basis       text,
    winner_fio         text,
    winner_inn         text,
    winner_price       real,
    result_text        text,
    first_seen         text,
    last_seen          text,
    updated_at         text
);

create table if not exists price_schedule (
    id        integer primary key autoincrement,
    lot_id    text,
    period_no integer,
    date_from text,
    time_from text,
    date_to   text,
    time_to   text,
    price     real,
    unique(lot_id, period_no)
);
"""

_LOT_COLS = [
    "lot_id", "status", "source_browser", "source_folder", "url",
    "message_guid", "message_number", "message_type", "message_type_name",
    "publish_date", "bankrupt_name", "bankrupt_inn", "bankrupt_type",
    "bankrupt_address", "bankrupt_birthdate", "bankrupt_snils", "bankrupt_ogrn",
    "case_number", "case_judge", "manager_name", "manager_inn", "manager_email",
    "manager_address", "manager_sro", "lot_order", "description", "classifier",
    "start_price", "advance_pct", "trade_type", "trade_site",
    "app_begin", "app_end", "auction_datetime", "price_reduction", "schedule_text",
    "is_repeat", "additional_text",
    "result_url", "result_number", "result_date", "result_guid",
    "result_lot_status", "result_basis", "winner_fio", "winner_inn", "winner_price",
    "result_text", "first_seen", "last_seen", "updated_at",
]


def init_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


# ── BOOKMARKS ──────────────────────────────────────────────────────────────

def _find_folders(node: dict, name: str) -> list[dict]:
    found = []
    if node.get("type") == "folder" and node.get("name") == name:
        found.append(node)
    for child in node.get("children", []):
        found.extend(_find_folders(child, name))
    return found


def _collect_links(node: dict, path: str) -> list[dict]:
    links = []
    for child in node.get("children", []):
        if child.get("type") == "url":
            url = child.get("url", "")
            if "fedresurs.ru/bankruptmessages/" in url:
                links.append({"url": url, "folder": path})
        elif child.get("type") == "folder":
            sub = f"{path} / {child.get('name', '')}"
            links.extend(_collect_links(child, sub))
    return links


def read_bookmarks(browser: str, bm_path: str, folder_name: str) -> list[dict]:
    path = Path(bm_path)
    if not path.exists():
        print(f"[{browser}] bookmarks file not found: {path}")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    roots = data.get("roots", {})
    seen: set[str] = set()
    result = []
    for root in filter(None, [roots.get("bookmark_bar"), roots.get("other"), roots.get("synced")]):
        for folder in _find_folders(root, folder_name):
            for link in _collect_links(folder, folder.get("name", folder_name)):
                if link["url"] not in seen:
                    seen.add(link["url"])
                    result.append({**link, "browser": browser})
    print(f"[{browser}] {len(result)} links in '{folder_name}'")
    return result


# ── HTTP ───────────────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124",
    "Accept": "application/json,*/*",
}

_browser_cookie_str: str = ""


def get_browser_cookies() -> str:
    """Читает куки fedresurs.ru из Chromium (браузер должен быть закрыт)."""
    global _browser_cookie_str
    try:
        import browser_cookie3
        jar = browser_cookie3.chromium(domain_name="fedresurs.ru")
        _browser_cookie_str = "; ".join(f"{c.name}={c.value}" for c in jar)
        if _browser_cookie_str:
            print("[cookies] куки Chromium загружены")
        else:
            print("[cookies] куки не найдены — Chromium открыт или нет сессии")
    except Exception as e:
        print(f"[cookies] не удалось прочитать куки: {e}")
    return _browser_cookie_str


def fetch_json(url: str, retries: int = 3) -> dict:
    headers = {**_HEADERS,
               "Referer": "https://fedresurs.ru/",
               "Accept-Language": "ru-RU,ru;q=0.9"}
    if _browser_cookie_str:
        headers["Cookie"] = _browser_cookie_str
    req = urllib.request.Request(url, headers=headers)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed {url}: {last}")


def compact_guid(raw: str) -> str:
    return raw.upper().replace("-", "")


def message_id_from_url(url: str) -> str:
    raw = url.rstrip("/").split("/")[-1]
    cid = compact_guid(raw)
    if not re.fullmatch(r"[0-9A-F]{32}", cid):
        raise ValueError(f"bad message id in URL: {url}")
    return cid


def fetch_cached(mid: str, refetch: bool = False) -> dict:
    path = RAW_DIR / f"{mid}.json"
    if path.exists() and not refetch:
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        data = fetch_json(FEDRESURS_API.format(mid))
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data
    except Exception:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        raise


# ── FIELD HELPERS ──────────────────────────────────────────────────────────

def _s(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _dt(v: Any) -> str | None:
    if not v:
        return None
    raw = str(v).replace("Z", "").split(".")[0].strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(raw, fmt)
            return parsed.strftime("%d.%m.%Y %H:%M") if "T" in str(v) else parsed.strftime("%d.%m.%Y")
        except ValueError:
            pass
    # already DD.MM.YYYY
    m = re.match(r"(\d{2}\.\d{2}\.\d{4})", raw)
    return m.group(1) if m else _s(v)


def _dt_node(node: Any) -> str | None:
    if not node:
        return None
    if isinstance(node, dict):
        return _dt(node.get("dateTime") or node.get("date"))
    return _dt(node)


def _money(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v).replace("\xa0", ""))
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _fio(d: dict | None) -> str | None:
    if not d:
        return None
    parts = [d.get("lastName"), d.get("firstName"), d.get("middleName")]
    joined = " ".join(p for p in parts if p).strip()
    return joined or _s(d.get("fio") or d.get("name"))


# ── SCHEDULE PARSING ───────────────────────────────────────────────────────

# «В период с 22.06.2026 10:00 по 30.06.2026 10:00 цена устанавливается X руб.»
_SCHED_RE = re.compile(
    r"[Вв]\s+период\s+с\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})"
    r"\s+по\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})"
    r"[^;.\n]*?цена\s+устанавливается\s+"
    r"(в\s+размере\s+начальной\s+цены|([\d\s\xa0 ]+(?:[,.]\d+)?)(?:\s*руб)?)",
    re.IGNORECASE,
)


def parse_schedule(text: str, start_price: float | None) -> list[dict]:
    """Parse explicit «В период с … по … цена устанавливается X руб.» schedule."""
    periods = []
    for i, m in enumerate(_SCHED_RE.finditer(text), 1):
        raw_price = m.group(5).strip()
        if re.match(r"в\s+размере\s+начальной", raw_price, re.IGNORECASE):
            price = start_price
        else:
            price = _money(raw_price)
        periods.append({
            "period_no": i,
            "date_from": m.group(1),
            "time_from": m.group(2),
            "date_to":   m.group(3),
            "time_to":   m.group(4),
            "price":     price,
        })
    return periods


# ── COMPUTED SCHEDULE (fallback when no explicit date ranges in text) ───────

def _parse_step_amount(text: str) -> float | None:
    m = re.search(r"(?:снижения?\s+цен[аы]?|уменьш\w+)\D{0,40}([\d\s\xa0]+(?:[,.]\d+)?)\s*руб", text, re.IGNORECASE)
    return _money(m.group(1)) if m else None


def _parse_step_percent(text: str) -> float | None:
    _P = r"(?:%|проц\w*)"
    _W = r"(?:\([^)]+\)\s*)?"
    patterns = [
        r"величин[аы]?\s+(?:снижени[ея]|дальнейшего\s+снижения|сниж\w+).{0,100}?([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
        r"шаг\s+снижения.{0,80}?([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
        r"сниж\w+\s+цен\w+.{0,80}?([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
        r"(?:на|составляет|равн\w+)\s+([\d]+(?:[,.]\d+)?)\s*" + _W + _P + r"\s*(?:от|от\s+начальн|$)",
        r"(?:понижается?|снижается?|уменьшается?)\s+на\s+([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
        r"([\d]+(?:[,.]\d+)?)\s*" + _W + _P + r"\s+(?:от\s+начальн|каждые?)",
        r"\bна\s+([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = _money(m.group(1))
            if v and 0.1 <= v <= 99:
                return v
    return None


def _parse_calendar_days(text: str) -> int | None:
    patterns = [
        r"(?:каждые?|период.{0,20}составляет|в\s+течени[ие]).{0,30}?(\d+).{0,20}?(?:календарн\w+\s+)?дн[еёяий]",
        r"(?:срок.{0,60}?(?:устанавливается\s+в|составляет)).{0,20}?(\d+).{0,20}?(?:календарн\w+\s+)?дн[еёяий]",
        r"(\d+)\s*(?:календарн\w+\s+)?дн[ей]\s+(?:с\s+момента|проведения)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = int(m.group(1))
            if 1 <= v <= 365:
                return v
    return None


def _parse_workdays(text: str) -> int | None:
    patterns = [
        r"(?:каждые?|период.{0,20}составляет|в\s+течени[ие]).{0,30}?(\d+).{0,20}?рабоч",
        r"(?:срок.{0,60}?(?:устанавливается\s+в|составляет)).{0,20}?(\d+).{0,20}?рабоч",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = int(m.group(1))
            if 1 <= v <= 365:
                return v
    return None


def _parse_cutoff_price(text: str) -> float | None:
    m = re.search(r"(?:цена|цен[аы])\s+отсечени[яю].{0,60}?([\d\s\xa0]+(?:[,.]\d+)?)\s*руб", text, re.IGNORECASE)
    return _money(m.group(1)) if m else None


def _parse_cutoff_percent(text: str) -> float | None:
    _P = r"(?:%|проц\w*)"
    _W = r"(?:\([^)]+\)\s*)?"
    patterns = [
        r"(?:нижн\w+\s+предел|цен[аы]\s+отсечени[яю]).{0,80}?([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
        r"минимальн\w+\s+цен[аы].{0,100}?([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
        r"цена\s+отсечения.{0,80}?([\d]+(?:[,.]\d+)?)\s*" + _W + _P + r"\s+от\s+начальн",
        r"продано?\s+(?:ниже|не\s+ниже).{0,80}?([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
        r"снижается?\s+(?:до|не\s+ниже)\s+([\d]+(?:[,.]\d+)?)\s*" + _W + _P,
    ]
    best = None
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = _money(m.group(1))
            if v and 0.1 <= v < 100:
                if best is None or v < best:
                    best = v
    return best


def _add_workdays(d: dt.date, n: int) -> dt.date:
    added = 0
    while added < n:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d


def _ru_date(s: str) -> dt.date | None:
    """Parse DD.MM.YYYY or DD.MM.YYYY HH:MM."""
    if not s:
        return None
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    if m:
        try:
            return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def compute_schedule(
    text: str,
    start_price: float | None,
    begin: str | None,
    end: str | None,
) -> list[dict]:
    """Compute schedule from reduction rules when explicit ranges are not in text."""
    if not start_price or not begin or not end:
        return []
    begin_d = _ru_date(begin)
    end_d   = _ru_date(end)
    if not begin_d or not end_d:
        return []

    step_amt  = _parse_step_amount(text)
    step_pct  = _parse_step_percent(text)
    cal_days  = _parse_calendar_days(text)
    work_days = _parse_workdays(text)
    cutoff_p  = _parse_cutoff_price(text)
    cutoff_pct= _parse_cutoff_percent(text)

    if step_amt is None and step_pct:
        step_amt = start_price * step_pct / 100
    if step_amt is None or step_amt <= 0:
        return []

    period_days = cal_days or work_days or 7
    use_cal = bool(cal_days) or not bool(work_days)

    cutoff = cutoff_p
    if cutoff is None and cutoff_pct:
        cutoff = start_price * cutoff_pct / 100
    if cutoff is None:
        cutoff = 0.0

    periods = []
    current = begin_d
    price   = start_price
    no      = 1

    while current <= end_d and no <= 80:
        if use_cal:
            period_end = min(current + dt.timedelta(days=period_days - 1), end_d)
        else:
            period_end = min(_add_workdays(current, period_days - 1), end_d)

        periods.append({
            "period_no": no,
            "date_from": current.strftime("%d.%m.%Y"),
            "time_from": "00:00",
            "date_to":   period_end.strftime("%d.%m.%Y"),
            "time_to":   "23:59",
            "price":     round(price, 2),
        })

        next_start = period_end + dt.timedelta(days=1)
        if not use_cal:
            while next_start.weekday() >= 5:
                next_start += dt.timedelta(days=1)
        if next_start > end_d or price <= cutoff:
            break

        price = max(round(price - step_amt, 2), cutoff)
        current = next_start
        no += 1

    return periods


def _schedule_text(periods: list[dict]) -> str | None:
    if not periods:
        return None
    lines = []
    for p in periods:
        price = f"{p['price']:,.0f} ₽".replace(",", " ") if p["price"] is not None else "?"
        lines.append(f"{p['date_from']} {p['time_from']} – {p['date_to']} {p['time_to']}: {price}")
    return "\n".join(lines)


# ── RESULT PARSING ─────────────────────────────────────────────────────────

def parse_result_for_lot(result_data: dict, lot_order: int) -> dict:
    mc = (result_data.get("content", {}).get("messageInfo") or {}).get("messageContent") or {}
    lot_table = mc.get("lotTable") or []
    raw_guid = result_data.get("guid", "")
    result_url = FEDRESURS_CARD.format(compact_guid(raw_guid)) if raw_guid else None

    base = {
        "result_url":    result_url,
        "result_number": _s(result_data.get("number")),
        "result_date":   _dt(result_data.get("datePublish")),
        "result_guid":   _s(raw_guid),
        "result_text":   _s(mc.get("text")),
    }

    for rl in lot_table:
        try:
            order = int(rl.get("order") or 0)
        except (TypeError, ValueError):
            continue
        if order != lot_order:
            continue
        winner_data = rl.get("winner") or {}
        ap = winner_data.get("auctionParticipant") or winner_data.get("participant") or {}
        winner_fio = _s(ap.get("fio")) or _fio(ap)
        return {
            **base,
            "result_lot_status": LOT_STATUS_LABEL.get(
                _s(rl.get("lotStatus")), _s(rl.get("lotStatus"))
            ),
            "result_basis": _s(rl.get("basis")),
            "winner_fio":   winner_fio,
            "winner_inn":   _s(ap.get("inn")),
            "winner_price": _money(ap.get("priceOffer") or ap.get("price")),
        }

    return {**base, "result_lot_status": None, "result_basis": None,
            "winner_fio": None, "winner_inn": None, "winner_price": None}




# Явное расписание в формате «N этап: с DD.MM.YYYY по DD.MM.YYYY ... (X руб.)»
_STAGE_RE = re.compile(
    r"(\d+)\s*этап\s*[:.]\s*с\s+(\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})"
    r"[^(]{0,120}\(([\d\s ]+(?:[,.]\d+)?)\s*руб",
    re.IGNORECASE,
)


# Explicit per-stage prices without dates: 1-й эт. PRICE р.; OR 1) PRICE; 2) PRICE
_STAGED_PRICE_RE = re.compile(
    r"(\d+)(?:-\w+\s+эт(?:ап)?\.?|\))\s*([\d\s\xa0]+(?:[,.]\d+)?)\s*(?:р(?:уб)?\.?|,)",
    re.IGNORECASE,
)


def parse_stage_schedule(text: str) -> list[dict]:
    periods = []
    for m in _STAGE_RE.finditer(text):
        price = _money(m.group(4))
        if price is None:
            continue
        periods.append({
            "period_no": int(m.group(1)),
            "date_from": m.group(2),
            "time_from": "00:00",
            "date_to":   m.group(3),
            "time_to":   "23:59",
            "price":     price,
        })
    periods.sort(key=lambda p: p["period_no"])
    return periods




def parse_interval_schedule(text: str) -> list[dict]:
    """Parse explicit date-range schedules in formats not covered by parse_schedule."""
    # Each pattern: (date_from_group, time_from_group_or_None, date_to_group, time_to_group_or_None, price_group)
    _patterns = [
        # Tab-table: N\tDATE H:MM\tDATE H:MM\tPRICE\t...
        (re.compile(
            r"\d+\t(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\t(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\t([\d\s\xa0]+(?:[,.]\d+)?)",
        ), True),
        # с DATE г. по DATE г. [–—-] PRICE руб.
        (re.compile(
            r"с\s+(\d{2}\.\d{2}\.\d{4})\s*(?:г\.?)?\s+по\s+(\d{2}\.\d{2}\.\d{4})\s*(?:г\.?)?\s*[–—\-]\s*([\d\s\xa0]+(?:[,.]\d+)?)\s*руб",
            re.IGNORECASE,
        ), False),
        # с DATE H:MM по DATE H:MM цена на интервале PRICE
        (re.compile(
            r"с\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+по\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})[^\d]*?цена\s+на\s+интервале\s*(?:,\s*руб\.?\s*)?([\d\s\xa0]+(?:[,.]\d+)?)",
            re.IGNORECASE,
        ), True),
        # Период: DATE H:MM-DATE H:MM стоимость PRICE руб.
        (re.compile(
            r"[Пп]ериод[:\s]+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})[\s\-]+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+стоимость\s+([\d\s\xa0]+(?:[,.]\d+)?)\s*руб",
            re.IGNORECASE,
        ), True),
        # DATE H:MM-DATE H:MM ... Цена на интервале, руб.\tPRICE
        (re.compile(
            r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})-(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})[^\n]*?[\t\s]([\d\s\xa0]+(?:[,.]\d+)?)\s*Цена\s+на\s+интервале",
            re.IGNORECASE,
        ), True),
    ]

    for pat, has_time in _patterns:
        matches = list(pat.finditer(text))
        if len(matches) >= 2:
            periods = []
            for i, m in enumerate(matches, 1):
                if has_time:
                    df, tf, dt_, tt, raw_p = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
                else:
                    df, dt_, raw_p = m.group(1), m.group(2), m.group(3)
                    tf, tt = "00:00", "23:59"
                price = _money(raw_p)
                if price is None or price <= 0:
                    break
                periods.append({
                    "period_no": i,
                    "date_from": df,
                    "time_from": tf,
                    "date_to":   dt_,
                    "time_to":   tt,
                    "price":     price,
                })
            else:
                if periods:
                    return periods
    return []


def parse_staged_prices(text: str) -> list[float]:
    """Parse per-stage prices: 1-й эт. 1 169 000 р.; 2-й эт. ..."""
    found: dict[int, float] = {}
    for m in _STAGED_PRICE_RE.finditer(text):
        n = int(m.group(1))
        p = _money(m.group(2))
        if p is not None and p > 0:
            found[n] = p
    if not found:
        return []
    max_n = max(found)
    if max_n < 2:
        return []
    return [found[i] for i in range(1, max_n + 1) if i in found]


def compute_schedule_from_staged_prices(
    prices: list[float],
    begin: str | None,
    end: str | None,
) -> list[dict]:
    """Compute date ranges by dividing the application period evenly over explicit stage prices."""
    if not prices or not begin or not end:
        return []
    begin_d = _ru_date(begin)
    end_d   = _ru_date(end)
    if not begin_d or not end_d or begin_d >= end_d:
        return []
    n = len(prices)
    total_days = (end_d - begin_d).days
    periods = []
    for i, price in enumerate(prices):
        start = begin_d + dt.timedelta(days=round(i * total_days / n))
        stop  = begin_d + dt.timedelta(days=round((i + 1) * total_days / n) - 1)
        if stop > end_d:
            stop = end_d
        periods.append({
            "period_no": i + 1,
            "date_from": start.strftime("%d.%m.%Y"),
            "time_from": "00:00",
            "date_to":   stop.strftime("%d.%m.%Y"),
            "time_to":   "23:59",
            "price":     price,
        })
    return periods


# ── NORMALIZE ──────────────────────────────────────────────────────────────

def normalize_lot(
    data: dict,
    lot: dict,
    source_url: str,
    browser: str,
    folder: str,
    result: dict | None,
) -> tuple[dict, list[dict]]:
    content   = data.get("content") or {}
    mc        = (content.get("messageInfo") or {}).get("messageContent") or {}
    bankrupt  = data.get("bankrupt") or content.get("bankrupt") or {}
    publisher = data.get("publisher") or content.get("publisher") or {}
    sro       = publisher.get("sro") or publisher.get("sroInfo") or {}
    app       = mc.get("application") or {}

    manager_name = _s(publisher.get("name")) or _fio(publisher.get("fio"))
    classifiers  = lot.get("classifierCollection") or []
    classifier   = "; ".join(c.get("name", "") for c in classifiers if c.get("name")) or None

    lot_order   = int(lot.get("order") or 1)
    mid         = message_id_from_url(source_url)
    lot_id      = f"{data.get('number') or mid}-{lot_order}"
    start_price = _money(lot.get("startPrice"))

    trade_type_raw = _s(mc.get("tradeType"))
    is_public_offer = trade_type_raw == "PublicOffer"

    text_content = _s(mc.get("text")) or ""
    price_red    = _s(lot.get("priceReduction")) or ""
    combined_text = text_content + "\n" + price_red

    if is_public_offer:
        periods = parse_schedule(combined_text, start_price)
        if not periods:
            periods = parse_stage_schedule(combined_text)
        if not periods:
            periods = compute_schedule(
                combined_text, start_price,
                _dt_node(app.get("dateTimeBegin")),
                _dt_node(app.get("dateTimeEnd")),
            )
        if not periods:
            periods = parse_interval_schedule(combined_text)
        if not periods:
            staged = parse_staged_prices(combined_text)
            if staged:
                periods = compute_schedule_from_staged_prices(
                    staged,
                    _dt_node(app.get("dateTimeBegin")),
                    _dt_node(app.get("dateTimeEnd")),
                )
    else:
        periods = []

    now = dt.datetime.now().strftime("%d.%m.%Y %H:%M")
    row: dict[str, Any] = {
        "lot_id":             lot_id,
        "status":             "Активен",
        "source_browser":     browser,
        "source_folder":      folder,
        "url":                source_url,
        "message_guid":       _s(data.get("guid")),
        "message_number":     _s(data.get("number")),
        "message_type":       _s(data.get("messageType")),
        "message_type_name":  _s(data.get("typeName")),
        "publish_date":       _dt(data.get("datePublish")),
        "bankrupt_name":      _s(bankrupt.get("name")),
        "bankrupt_inn":       _s(bankrupt.get("inn")),
        "bankrupt_type":      _s(bankrupt.get("type")),
        "bankrupt_address":   _s(bankrupt.get("address")),
        "bankrupt_birthdate": _dt(bankrupt.get("birthdate")),
        "bankrupt_snils":     _s(bankrupt.get("snils")),
        "bankrupt_ogrn":      _s(bankrupt.get("ogrnip") or bankrupt.get("ogrn")),
        "case_number":        _s(content.get("caseNumber") or bankrupt.get("legalCaseNumber")),
        "case_judge":         _s(content.get("caseNumberJudgeCode")),
        "manager_name":       manager_name,
        "manager_inn":        _s(publisher.get("inn")),
        "manager_email":      _s(publisher.get("email")),
        "manager_address":    _s(publisher.get("correspondenceAddress")),
        "manager_sro":        _s(sro.get("name")),
        "lot_order":          lot_order,
        "description":        _s(lot.get("description")),
        "classifier":         classifier,
        "start_price":        start_price,
        "advance_pct":        _money(lot.get("advance")),
        "trade_type":         TRADE_TYPE_LABEL.get(trade_type_raw, trade_type_raw),
        "trade_site":         _s(mc.get("tradeSite")),
        "app_begin":          _dt_node(app.get("dateTimeBegin")),
        "app_end":            _dt_node(app.get("dateTimeEnd")),
        "auction_datetime":   _dt_node(mc.get("auctionDateTime")),
        "price_reduction":    _s(lot.get("priceReduction")),
        "schedule_text":      _schedule_text(periods),
        "is_repeat":          1 if mc.get("isRepeat") else 0,
        "additional_text":    _s(mc.get("additionalText")),
        "result_url":         None,
        "result_number":      None,
        "result_date":        None,
        "result_guid":        None,
        "result_lot_status":  None,
        "result_basis":       None,
        "winner_fio":         None,
        "winner_inn":         None,
        "winner_price":       None,
        "result_text":        None,
        "first_seen":         now,
        "last_seen":          now,
        "updated_at":         now,
    }

    if result:
        row.update(result)

    return row, periods


# ── DB OPERATIONS ──────────────────────────────────────────────────────────

def upsert_lot(db: sqlite3.Connection, row: dict, periods: list[dict]) -> None:
    now = dt.datetime.now().strftime("%d.%m.%Y %H:%M")
    existing = db.execute(
        "select first_seen from lots where lot_id=?", (row["lot_id"],)
    ).fetchone()
    if existing:
        row["first_seen"] = existing["first_seen"]
    row["last_seen"] = now
    row["updated_at"] = now

    cols = [c for c in _LOT_COLS if c in row]
    placeholders = ",".join("?" for _ in cols)
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c not in ("lot_id", "first_seen"))
    db.execute(
        f"insert into lots ({','.join(cols)}) values ({placeholders}) "
        f"on conflict(lot_id) do update set {updates}",
        [row[c] for c in cols],
    )

    if periods:
        db.execute("delete from price_schedule where lot_id=?", (row["lot_id"],))
        db.executemany(
            "insert or replace into price_schedule "
            "(lot_id,period_no,date_from,time_from,date_to,time_to,price) "
            "values (?,?,?,?,?,?,?)",
            [
                (row["lot_id"], p["period_no"], p["date_from"], p["time_from"],
                 p["date_to"], p["time_to"], p["price"])
                for p in periods
            ],
        )


def _remove_urls_from_node(node: dict, urls: set[str]) -> bool:
    """Recursively remove bookmark nodes whose url is in urls. Returns True if node should be kept."""
    if node.get("type") == "url":
        return node.get("url", "") not in urls
    if node.get("type") == "folder":
        node["children"] = [c for c in node.get("children", []) if _remove_urls_from_node(c, urls)]
    return True


def remove_from_bookmarks(urls: set[str]) -> None:
    """Remove URLs from Chrome/Chromium bookmarks files. Chrome must be closed."""
    if not urls:
        return
    for browser, bm_path, _ in BROWSERS:
        path = Path(bm_path)
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            roots = data.get("roots", {})
            removed = 0
            for root_key in ("bookmark_bar", "other", "synced"):
                root = roots.get(root_key)
                if root:
                    before = sum(1 for _ in str(root).split('"type": "url"'))
                    _remove_urls_from_node(root, urls)
                    after = sum(1 for _ in str(root).split('"type": "url"'))
                    removed += max(0, before - after)
            backup = path.with_suffix(".bak")
            backup.write_bytes(path.read_bytes())
            path.write_text(json.dumps(data, ensure_ascii=False, indent=3), encoding="utf-8")
            print(f"[{browser}] bookmarks: removed completed lots (backup saved to .bak)")
        except PermissionError:
            print(f"[{browser}] Cannot write bookmarks — close {browser} first")
        except Exception as e:
            print(f"[{browser}] bookmark write error: {e}")


def mark_archived(db: sqlite3.Connection, active_ids: set[str]) -> None:
    current_active = {
        r[0] for r in db.execute("select lot_id from lots where status='Активен'")
    }
    to_archive = current_active - active_ids
    if to_archive:
        now = dt.datetime.now().strftime("%d.%m.%Y %H:%M")
        db.executemany(
            "update lots set status='Архив', updated_at=? where lot_id=?",
            [(now, lid) for lid in to_archive],
        )
        print(f"Archived {len(to_archive)} lots removed from bookmarks")


# ── SYNC ───────────────────────────────────────────────────────────────────

def _fetch_one(db: sqlite3.Connection, link: dict, refetch: bool) -> set[str]:
    """Fetch one bookmark URL, upsert lots into DB. Returns set of lot_ids."""
    url = link["url"]
    lot_ids: set[str] = set()
    try:
        mid = message_id_from_url(url)
    except ValueError as e:
        print(f"  skip {url}: {e}")
        return lot_ids

    try:
        data = fetch_cached(mid, refetch=refetch)
    except Exception as e:
        print(f"  fetch error {mid}: {e}")
        return lot_ids

    # Fetch TradeResult linked messages
    result_data_map: dict[int, dict] = {}
    for linked in data.get("linkedMessages") or []:
        if linked.get("type") != "TradeResult":
            continue
        rguid = compact_guid(linked.get("guid") or "")
        if not rguid:
            continue
        try:
            rdata = fetch_cached(rguid, refetch=False)
            rlots = (
                (rdata.get("content") or {})
                .get("messageInfo", {})
                .get("messageContent", {})
                .get("lotTable") or []
            )
            for rl in rlots:
                try:
                    result_data_map.setdefault(int(rl.get("order") or 0), rdata)
                except (TypeError, ValueError):
                    pass
            if not rlots:
                result_data_map.setdefault(0, rdata)
        except Exception as e:
            print(f"  result fetch error {rguid}: {e}")

    mc = ((data.get("content") or {}).get("messageInfo") or {}).get("messageContent") or {}
    lot_table = mc.get("lotTable") or []
    if not lot_table:
        print(f"  {mid}: no lots")
        return lot_ids

    for lot in lot_table:
        lot_order = int(lot.get("order") or 1)
        rdata = result_data_map.get(lot_order) or result_data_map.get(0)
        result = parse_result_for_lot(rdata, lot_order) if rdata else None
        row, periods = normalize_lot(data, lot, url, link["browser"], link["folder"], result)
        lot_ids.add(row["lot_id"])
        upsert_lot(db, row, periods)
        status_str = row.get("result_lot_status") or row.get("trade_type") or "?"
        print(f"  {row['lot_id']}: {status_str} | {(row.get('bankrupt_name') or '?')[:40]}")

    return lot_ids


def sync(db: sqlite3.Connection, limit: int | None, refetch: bool, reprocess: bool = False, browser_filter: str | None = None) -> set[str]:
    """Read bookmarks, fetch only new URLs (or all if reprocess=True), return lot_ids of all bookmarked lots."""
    get_browser_cookies()
    all_links: list[dict] = []
    for browser, bm_path, folder_name in BROWSERS:
        if browser_filter and browser.lower() != browser_filter.lower():
            continue
        all_links.extend(read_bookmarks(browser, bm_path, folder_name))

    if limit:
        all_links = all_links[:limit]

    bookmark_urls: set[str] = {lnk["url"] for lnk in all_links}

    if reprocess:
        links_to_fetch = all_links
        print(f"Total: {len(all_links)} | Reprocessing all")
    else:
        # URLs already in DB — skip them (only fetch new)
        known_urls: set[str] = {
            row[0] for row in db.execute("select distinct url from lots where url is not null")
        }
        links_to_fetch = [lnk for lnk in all_links if lnk["url"] not in known_urls]
        skip_count = len(all_links) - len(links_to_fetch)
        print(f"Total: {len(all_links)} | New: {len(links_to_fetch)} | Skipped (already in DB): {skip_count}")

    for i, link in enumerate(links_to_fetch):
        _fetch_one(db, link, refetch=refetch)
        db.commit()
        if i < len(links_to_fetch) - 1:
            time.sleep(1.5)

    # active = all lots whose source URL is still in bookmarks
    active_ids: set[str] = {
        row[0]
        for row in db.execute("select lot_id from lots where url is not null")
        if row[0]  # shouldn't be null, but guard
    }
    # Filter: keep only those whose url is in current bookmarks
    active_ids = {
        row[0]
        for row in db.execute(
            "select lot_id from lots where url in ({})".format(
                ",".join("?" * len(bookmark_urls))
            ),
            list(bookmark_urls),
        )
    } if bookmark_urls else set()

    return active_ids


# ── GOOGLE SHEETS ──────────────────────────────────────────────────────────

CLIENT_SECRETS_PATH = BASE_DIR / "client_secrets.json"
TOKEN_PATH          = BASE_DIR / "token.json"
SHEETS_SCOPES       = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_google_creds():
    """OAuth flow: opens browser on first run, caches token.json for subsequent runs."""
    try:
        from google.oauth2.credentials import Credentials as OAuthCreds
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("[sheets] pip install gspread google-auth google-auth-oauthlib")
        return None

    creds = None
    if TOKEN_PATH.exists():
        creds = OAuthCreds.from_authorized_user_file(str(TOKEN_PATH), SHEETS_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_PATH.exists():
                print(
                    f"[sheets] {CLIENT_SECRETS_PATH.name} not found.\n"
                    "  Создай OAuth-клиент:\n"
                    "  1. console.cloud.google.com → APIs & Services → Enable: Google Sheets API\n"
                    "  2. Credentials → Create → OAuth client ID → Desktop app → скачать JSON\n"
                    f"  3. Сохранить как {CLIENT_SECRETS_PATH}"
                )
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_PATH), SHEETS_SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds


def sheets_sync(db: sqlite3.Connection) -> None:
    creds = _get_google_creds()
    if not creds:
        return

    try:
        import gspread
    except ImportError:
        print("[sheets] pip install gspread")
        return

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)

    try:
        ws = sh.worksheet(SHEET_NAME)
    except Exception:
        ws = sh.add_worksheet(title=SHEET_NAME, rows=10000, cols=len(SHEET_KEYS))

    existing = ws.get_all_values()
    if not existing or existing[0] != SHEET_HEADERS:
        ws.clear()
        ws.append_row(SHEET_HEADERS)
        existing = [SHEET_HEADERS]

    id_col = SHEET_KEYS.index("lot_id")
    row_map: dict[str, int] = {}
    for i, row in enumerate(existing[1:], start=2):
        if len(row) > id_col and row[id_col]:
            row_map[row[id_col]] = i

    lots = [dict(r) for r in db.execute(
        "select * from lots order by publish_date desc, lot_id"
    )]

    def to_row(lot: dict) -> list[str]:
        return [str(lot.get(k) or "") for k in SHEET_KEYS]

    updates: list[tuple[int, list]] = []
    appends: list[list] = []
    for lot in lots:
        vals = to_row(lot)
        if lot["lot_id"] in row_map:
            updates.append((row_map[lot["lot_id"]], vals))
        else:
            appends.append(vals)

    if updates:
        sh.values_batch_update({
            "valueInputOption": "RAW",
            "data": [
                {
                    "range": f"A{rn}:{gspread.utils.rowcol_to_a1(rn, len(SHEET_KEYS))}",
                    "values": [vals],
                }
                for rn, vals in updates
            ],
        })

    if appends:
        ws.append_rows(appends, value_input_option="RAW")

    print(f"[sheets] updated {len(updates)}, appended {len(appends)}")


# ── HTML RENDER ────────────────────────────────────────────────────────────

def _e(s: Any) -> str:
    return html.escape(str(s or ""))


def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):,.0f} ₽".replace(",", " ")
    except (TypeError, ValueError):
        return str(v)


def render_html(db: sqlite3.Connection) -> None:
    lots = [dict(r) for r in db.execute(
        "select * from lots order by status, publish_date desc"
    )]
    schedules = [dict(r) for r in db.execute(
        "select * from price_schedule order by lot_id, period_no"
    )]

    sched_by_lot: dict[str, list] = {}
    for s in schedules:
        sched_by_lot.setdefault(s["lot_id"], []).append(s)

    # ── Urgency computation ──────────────────────────────────────────────────
    def _parse_ru_date(s: str | None) -> dt.date | None:
        if not s:
            return None
        try:
            return dt.datetime.strptime(s[:10], "%d.%m.%Y").date()
        except ValueError:
            return None

    _today = dt.date.today()

    def _lot_urgency(lot: dict, schedule: list[dict]) -> dict:
        days_period, cur_price, discount = None, None, None
        for p in schedule:
            df  = _parse_ru_date(p["date_from"])
            dto = _parse_ru_date(p["date_to"])
            if df and dto and df <= _today <= dto:
                days_period = (dto - _today).days
                cur_price   = p["price"]
                sp = lot.get("start_price")
                if sp and sp > 0 and cur_price:
                    discount = round((sp - cur_price) / sp * 100, 1)
                break
        app_d = _parse_ru_date(lot.get("app_end"))
        days_app = (app_d - _today).days if app_d else None
        auc_d = _parse_ru_date(lot.get("auction_datetime"))
        days_auc = (auc_d - _today).days if auc_d else None

        # Определяем ближайший дедлайн и его тип
        deadline_cands = []
        if days_period is not None and days_period >= 0:
            deadline_cands.append((days_period, "price"))
        if days_app is not None and days_app >= 0:
            deadline_cands.append((days_app, "deadline"))
        if days_auc is not None and days_auc >= 0:
            deadline_cands.append((days_auc, "deadline"))

        if deadline_cands:
            urgency_days, deadline_type = min(deadline_cands, key=lambda x: x[0])
        else:
            urgency_days, deadline_type = 99999, None

        # Price attractiveness factor vs LLM auction estimate
        price_min = lot.get("price_min")
        price_factor = 1.0
        price_vs_estimate = None  # % выше оценки (отрицательное = ниже оценки)
        if price_min and price_min > 0 and cur_price:
            ratio = cur_price / price_min
            price_vs_estimate = round((ratio - 1) * 100)
            if ratio <= 1.0:
                price_factor = 0.25
            elif ratio <= 1.5:
                price_factor = 0.50
            elif ratio <= 2.0:
                price_factor = 0.75
            elif ratio <= 3.0:
                price_factor = 1.00
            else:
                price_factor = 1.50

        urgency_score = round(urgency_days * price_factor) if urgency_days < 99999 else 99999

        return {
            "urgency":           urgency_score,   # composite — для сортировки
            "urgency_days":      urgency_days,     # raw дни — для отображения
            "deadline_type":     deadline_type,    # "price" | "deadline" | None
            "cur_price":         cur_price,
            "discount":          discount,
            "days_period":       days_period,
            "days_app":          days_app,
            "price_vs_estimate": price_vs_estimate,
        }

    urgency_by_lot: dict[str, dict] = {
        lot["lot_id"]: _lot_urgency(lot, sched_by_lot.get(lot["lot_id"], []))
        for lot in lots
        if lot.get("status") == "Активен"
    }

    # Timeline data embedded as JSON for JS
    timeline_data: dict[str, list] = {}
    for lot in lots:
        ps = sched_by_lot.get(lot["lot_id"])
        if ps:
            timeline_data[lot["lot_id"]] = [
                {"n": p["period_no"], "df": p["date_from"], "tf": p["time_from"],
                 "dt": p["date_to"],  "tt": p["time_to"],   "p":  p["price"]}
                for p in ps
            ]

    chrome_count   = sum(1 for l in lots if l.get("source_browser") == "Chrome")
    chromium_count = sum(1 for l in lots if l.get("source_browser") == "Chromium")

    today_iso = dt.date.today().strftime("%d.%m.%Y")
    now_str   = dt.datetime.now().strftime("%d.%m.%Y %H:%M")

    cards = []
    for lot in lots:
        lid = lot["lot_id"]
        archived = lot.get("status") == "Архив"
        result_status = lot.get("result_lot_status") or ""
        card_cls = (
            "sold"   if "Состоялись" in result_status else
            "failed" if "Не состоялись" in result_status or "Единственный" in result_status else
            ""
        )
        if archived:
            card_cls += " archived"

        result_link = (
            f'<a class="btn btn-result" href="{_e(lot["result_url"])}" '
            f'target="_blank" rel="noopener">↗ Результат</a>'
            if lot.get("result_url") else ""
        )

        timeline_block = (
            f'<div class="timeline" id="tl-{_e(lid)}" data-lot="{_e(lid)}"></div>'
            if lid in timeline_data else ""
        )

        def row(label: str, value: Any, cls: str = "") -> str:
            if value is None or value == "":
                return ""
            return (
                f'<div class="field {cls}"><dt>{_e(label)}</dt>'
                f'<dd>{_e(value)}</dd></div>'
            )

        u = urgency_by_lot.get(lid, {})
        urg_score     = u.get("urgency", 99999)
        urg_days      = u.get("urgency_days", 99999)
        deadline_type = u.get("deadline_type")
        urg_val       = urg_score
        if urg_score < 99999:
            urg_cls = "urg-red" if urg_days <= 3 else "urg-yellow" if urg_days <= 7 else "urg-green"
            # Иконка: 🏷 смена цены, ⏰ дедлайн заявок/торгов
            if deadline_type == "price":
                urg_icon = "🏷"
                urg_label = f"цена до {urg_days} дн"
            else:
                urg_icon = "⏰"
                urg_label = f"дедлайн {urg_days} дн"
            urg_badge = f'<span class="urg-badge {urg_cls}">{urg_icon} {urg_label}</span>'
            extras = []
            if u.get("cur_price"):
                disc_s = f" &minus;{u['discount']}%" if u.get("discount") else ""
                extras.append(f'{_fmt(u["cur_price"])}{disc_s}')
            pve = u.get("price_vs_estimate")
            if pve is not None:
                sign = "+" if pve >= 0 else ""
                extras.append(f'{sign}{pve}% к оценке')
            if extras:
                urg_badge += f' <span class="urg-info">{" · ".join(extras)}</span>'
        else:
            urg_badge = ""

        has_result = 1 if lot.get("result_lot_status") else 0
        cards.append(f"""
<article class="lot-card {card_cls}" id="card-{_e(lid)}" data-browser="{_e(lot.get('source_browser') or '')}" data-folder="{_e(lot.get('source_folder') or '')}" data-urgency="{urg_val}" data-result="{has_result}">
  <div class="card-head">
    <span class="badge badge-status">{_e(lot.get("status") or "")}</span>
    <span class="badge badge-trade">{_e(lot.get("trade_type") or "")}</span>
    {urg_badge}
    <div class="card-links">
      <a class="btn" href="{_e(lot.get("url") or "")}" target="_blank" rel="noopener">↗ Объявление</a>
      {result_link}
      <button class="btn val-card-btn" data-lot-id="{_e(lid)}" data-description="{_e(lot.get('description') or '')}" data-classifier="{_e(lot.get('classifier') or '')}">⚖ Оценить</button>
    </div>
  </div>
  <h2 class="card-title">{_e((lot.get("description") or "")[:220])}</h2>
  <div class="card-meta">
    <span>{_e(lot.get("source_browser") or "")} / {_e(lot.get("source_folder") or "")}</span>
    <span>{_e(lot.get("publish_date") or "")}</span>
  </div>
  <dl class="fields">
    {row("Банкрот", lot.get("bankrupt_name"))}
    {row("ИНН банкрота", lot.get("bankrupt_inn"))}
    {row("Дата рождения", lot.get("bankrupt_birthdate"))}
    {row("СНИЛС", lot.get("bankrupt_snils"))}
    {row("ОГРН/ОГРНИП", lot.get("bankrupt_ogrn"))}
    {row("Номер дела", lot.get("case_number"))}
    {row("Управляющий", lot.get("manager_name"))}
    {row("ИНН управляющего", lot.get("manager_inn"))}
    {row("Email", lot.get("manager_email"))}
    {row("Лот №", lot.get("lot_order"))}
    {row("Классификатор", lot.get("classifier"))}
    {row("Стартовая цена", _fmt(lot.get("start_price")))}
    {row("Задаток", f'{lot.get("advance_pct")} %' if lot.get("advance_pct") else None)}
    {row("Площадка", lot.get("trade_site"))}
    {row("Начало заявок", lot.get("app_begin"))}
    {row("Конец заявок", lot.get("app_end"))}
    {row("Дата торгов", lot.get("auction_datetime"))}
    {row("Повторные", "Да" if lot.get("is_repeat") else None)}
    {row("Итог торгов", lot.get("result_lot_status"), "result")}
    {row("Победитель", lot.get("winner_fio"), "result")}
    {row("ИНН победителя", lot.get("winner_inn"), "result")}
    {row("Цена победителя", _fmt(lot.get("winner_price")) if lot.get("winner_price") else None, "result")}
    {row("Основание", lot.get("result_basis"), "result")}
    {row("Дата результата", lot.get("result_date"))}
  </dl>
  {timeline_block}
  <div class="val-block" id="vb-{_e(lid)}"{' style="display:none"' if not lot.get("price_min") else ''}>
    <div class="val-block-label">Цена торгов</div>
    <div class="val-block-price" id="vbp-{_e(lid)}">{f'{_fmt(lot.get("price_min"))} — {_fmt(lot.get("price_max"))}' if lot.get("price_min") else ''}</div>
    {f'''<div class="val-block-scenarios">
      <span class="val-scen"><span class="val-scen-lbl">Лот перекупу</span><span class="val-scen-val">{_fmt(lot.get("price_quick_lot_min"))} — {_fmt(lot.get("price_quick_lot_max"))}</span></span>
      <span class="val-scen"><span class="val-scen-lbl">Опт партиями</span><span class="val-scen-val">{_fmt(lot.get("price_wholesale_min"))} — {_fmt(lot.get("price_wholesale_max"))}</span></span>
      <span class="val-scen"><span class="val-scen-lbl">Розница</span><span class="val-scen-val">{_fmt(lot.get("price_retail_min"))} — {_fmt(lot.get("price_retail_max"))}</span></span>
    </div>''' if lot.get("price_quick_lot_min") else ''}
    <div class="val-block-meta" id="vbm-{_e(lid)}">{f'{lot.get("valuation_confidence","")} · {lot.get("valuated_at","")}' if lot.get("price_min") else ''}</div>
    <div class="val-block-text" id="vbt-{_e(lid)}">{_e(lot.get("valuation_reasoning") or "")}</div>
  </div>
</article>""")

    sched_json = json.dumps(timeline_data, ensure_ascii=False)

    folders = sorted({lot.get("source_folder") or "" for lot in lots if lot.get("source_folder")})
    folder_options = "\n".join(
        f'<option value="{_e(f)}">{_e(f)}</option>' for f in folders
    )

    page = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Федресурс — торги</title>
<style>
:root{{--bg:#f0f2f5;--surface:#fff;--border:#d8e0ea;--text:#1f2933;--muted:#667085;
  --blue:#1d3557;--green:#178a4a;--red:#c84646;--shadow:0 2px 8px rgba(0,0,0,.07)}}
*{{box-sizing:border-box}}
body{{margin:0;font:14px/1.5 Arial,sans-serif;color:var(--text);background:var(--bg)}}
header{{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.96);
  border-bottom:1px solid var(--border);backdrop-filter:blur(8px)}}
.top{{max-width:1440px;margin:0 auto;padding:10px 20px;display:flex;flex-wrap:wrap;
  gap:8px;align-items:center}}
h1{{margin:0;font-size:19px;flex:1 1 auto}}
.meta{{color:var(--muted);font-size:12px}}
input[type=search],select{{height:34px;padding:0 10px;border:1px solid var(--border);
  border-radius:6px;font-size:13px;outline:none;background:#fff}}
input[type=search]{{min-width:280px}}
main{{max-width:1440px;margin:0 auto;padding:14px 20px 60px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:12px;align-items:start}}
.lot-card{{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--border);
  border-radius:8px;box-shadow:var(--shadow);padding:14px}}
.lot-card.sold{{border-left-color:var(--green);background:#f4fbf6}}
.lot-card.failed{{border-left-color:var(--red);background:#fff5f5}}
.lot-card.archived{{opacity:.55}}
.card-head{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700}}
.badge-status{{background:var(--blue);color:#fff}}
.archived .badge-status{{background:var(--muted)}}
.badge-trade{{background:#eef2f6;color:var(--text)}}
.urg-badge{{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap}}
.urg-red{{background:#fde8e8;color:#c84646}}
.urg-yellow{{background:#fff8e1;color:#9a6000}}
.urg-green{{background:#e8f5e9;color:#178a4a}}
.urg-info{{font-size:11px;color:var(--muted);white-space:nowrap}}
.filter-check{{display:flex;align-items:center;gap:5px;font-size:13px;white-space:nowrap;cursor:pointer}}
.card-links{{margin-left:auto;display:flex;gap:6px}}
.btn{{display:inline-block;padding:3px 9px;border:1px solid var(--border);border-radius:5px;
  font-size:12px;color:var(--blue);text-decoration:none;background:#fff;white-space:nowrap}}
.btn-result{{color:var(--green);border-color:#a8ddb8}}
.card-title{{margin:4px 0 6px;font-size:14px;line-height:1.4}}
.card-meta{{display:flex;gap:10px;color:var(--muted);font-size:12px;margin-bottom:10px}}
dl.fields{{margin:0;display:grid;gap:4px}}
.field{{display:grid;grid-template-columns:145px 1fr;gap:6px;font-size:12px}}
dt{{color:var(--muted)}}
dd{{margin:0;overflow-wrap:anywhere}}
.field.result dt{{color:var(--green);font-weight:700}}
/* ── Timeline ─────────────────────────────────── */
.timeline{{margin-top:12px;border:1px solid var(--border);border-radius:6px;overflow:hidden}}
.tl-head{{padding:5px 10px;font-size:11px;font-weight:700;color:var(--muted);
  text-transform:uppercase;background:#f0f2f5;border-bottom:1px solid var(--border)}}
.tl-wrap{{overflow-x:auto;padding:6px 10px 8px}}
.tl-canvas{{position:relative;height:110px;min-width:520px}}
.tl-bar{{position:absolute;top:14px;height:36px;border-radius:4px;
  cursor:default;border:1px solid rgba(0,0,0,.12)}}
.tl-bar.future{{background:#bcd4f0;border-color:#7aaddf}}
.tl-bar.current{{background:#ffdf80;border-color:#e6a800}}
.tl-bar.past{{background:#d5d5d5;border-color:#aaa}}
.tl-price{{position:absolute;top:52px;font-size:10px;font-weight:700;
  white-space:nowrap;transform:translateX(-50%);pointer-events:none}}
.tl-price.future{{color:#1a3a5c}}
.tl-price.current{{color:#5c3a00}}
.tl-price.past{{color:#555}}
.tl-tick{{position:absolute;top:68px;width:1px;height:8px;background:var(--muted)}}
.tl-date{{position:absolute;top:78px;font-size:10px;color:var(--muted);
  white-space:nowrap;transform:translateX(-50%);user-select:none}}
.tl-date.first{{transform:none}}
.tl-date.last{{transform:translateX(-100%)}}
.tl-today{{position:absolute;top:0;bottom:0;width:2px;background:rgba(220,50,50,.7)}}
/* ── Filter empty ─────────────────────────────── */
.no-results{{display:none;padding:40px;text-align:center;color:var(--muted)}}
@media(max-width:680px){{
  .cards{{grid-template-columns:1fr}}
  .field{{grid-template-columns:1fr;gap:1px}}
  input[type=search]{{min-width:0;width:100%}}
}}

/* ── Valuation block in card ───────────────────────── */
.val-block{{margin-top:10px;padding:10px 12px;background:#f0f6ff;border-left:3px solid var(--blue);border-radius:0 6px 6px 0}}
.val-block-label{{font-size:10px;font-weight:700;text-transform:uppercase;color:var(--muted);margin-bottom:2px}}
.val-block-price{{font-size:16px;font-weight:700;color:var(--blue);margin-bottom:6px}}
.val-block-scenarios{{display:flex;flex-direction:column;gap:3px;margin-bottom:6px;padding:6px 8px;background:#e6f0ff;border-radius:4px}}
.val-scen{{display:flex;justify-content:space-between;font-size:11px}}
.val-scen-lbl{{color:var(--muted)}}
.val-scen-val{{font-weight:600;color:var(--blue)}}
.val-block-meta{{font-size:11px;color:var(--muted);margin-bottom:4px}}
.val-block-text{{font-size:12px;color:#444;line-height:1.5}}
/* ── Valuation panel ───────────────────────────────── */
#val-btn{{position:fixed;bottom:24px;right:24px;z-index:100;background:var(--blue);color:#fff;border:none;border-radius:50px;padding:12px 20px;font-size:15px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)}}
#val-btn:hover{{background:#1a6bbf}}
#val-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:200}}
#val-panel{{position:fixed;top:0;right:0;bottom:0;width:420px;max-width:100vw;background:#fff;z-index:201;display:flex;flex-direction:column;box-shadow:-4px 0 20px rgba(0,0,0,.15);transform:translateX(100%);transition:transform .25s}}
#val-panel.open{{transform:none}}
#val-panel header{{padding:16px 20px;border-bottom:1px solid #eee;display:flex;align-items:center;justify-content:space-between}}
#val-panel header h2{{margin:0;font-size:16px}}
#val-close{{background:none;border:none;font-size:22px;cursor:pointer;color:var(--muted)}}
#val-body{{padding:16px 20px;flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:12px}}
#val-body label{{font-size:12px;color:var(--muted);margin-bottom:2px;display:block}}
#val-desc{{width:100%;height:140px;resize:vertical;border:1px solid #ddd;border-radius:6px;padding:8px;font-size:13px;font-family:inherit}}
#val-classifier,#val-lot-id{{width:100%;border:1px solid #ddd;border-radius:6px;padding:8px;font-size:13px;font-family:inherit}}
#val-submit{{background:var(--blue);color:#fff;border:none;border-radius:6px;padding:10px;font-size:14px;cursor:pointer;width:100%}}
#val-submit:disabled{{opacity:.5;cursor:default}}
#val-result{{background:#f5f7fa;border-radius:8px;padding:14px;font-size:13px;line-height:1.6;display:none}}
#val-result .val-price{{font-size:18px;font-weight:700;color:var(--blue);margin-bottom:6px}}
#val-result .val-conf{{font-size:12px;color:var(--muted);margin-bottom:8px}}
#val-result .val-text{{color:#333}}
#val-result .val-sources{{margin-top:8px;font-size:11px;color:var(--muted)}}
#val-error{{color:#c00;font-size:13px;display:none}}
#val-spinner{{text-align:center;color:var(--muted);display:none}}
</style>
</head>
<body>
<header>
  <div class="top">
    <h1>Федресурс — торги</h1>
    <span class="meta">Обновлено {_e(now_str)} · Chrome: {chrome_count} · Chromium: {chromium_count} · Итого: {len(lots)}</span>
    <input type="search" id="q" placeholder="Поиск по тексту...">
    <select id="fStatus">
      <option value="">Все статусы</option>
      <option value="Активен">Активен</option>
      <option value="Архив">Архив</option>
    </select>
    <select id="fTrade">
      <option value="">Все типы</option>
      <option value="Публичное предложение">Публичное предложение</option>
      <option value="Открытый аукцион">Открытый аукцион</option>
      <option value="Закрытый аукцион">Закрытый аукцион</option>
    </select>
    <select id="fBrowser">
      <option value="">Все источники</option>
      <option value="Chrome">Chrome</option>
      <option value="Chromium">Chromium</option>
    </select>
    <select id="fFolder">
      <option value="">Все папки</option>
      {folder_options}
    </select>
    <select id="fSort">
      <option value="">Сортировка: по умолчанию</option>
      <option value="urgency">По срочности</option>
    </select>
    <label class="filter-check"><input type="checkbox" id="fHideFinished"> Скрыть завершённые</label>
  </div>
</header>

<button id="val-btn" onclick="openVal()">⚖ Оценить</button>
<div id="val-overlay" onclick="closeVal()"></div>
<div id="val-panel">
  <header>
    <h2>Рыночная оценка</h2>
    <button id="val-close" onclick="closeVal()">✕</button>
  </header>
  <div id="val-body">
    <div>
      <label>Описание актива *</label>
      <textarea id="val-desc" placeholder="Вставьте описание лота из объявления..."></textarea>
    </div>
    <div>
      <label>Тип актива (опционально)</label>
      <input id="val-classifier" placeholder="Жилые здания; Земельные участки...">
    </div>
    <div>
      <label>ID лота (опционально — для сохранения в БД)</label>
      <input id="val-lot-id" placeholder="23595385-6">
    </div>
    <button id="val-submit" onclick="submitVal()">Оценить</button>
    <div id="val-spinner">Ищем данные и считаем...</div>
    <div id="val-error"></div>
    <div id="val-result">
      <div class="val-price" id="val-price"></div>
      <div class="val-conf" id="val-conf"></div>
      <div class="val-text" id="val-text"></div>
      <div class="val-sources" id="val-sources"></div>
    </div>
  </div>
</div>

<main>
  <div class="cards" id="cards">{''.join(cards)}</div>
  <div class="no-results" id="noResults">Ничего не найдено</div>
</main>
<script>
const TODAY_STR = "{today_iso}";
const SCHED = {sched_json};

// ── Timeline ─────────────────────────────────────────────────────────────

function ruDateToMs(s) {{
  if (!s) return null;
  const [d, mo, y] = s.split('.');
  return Date.UTC(+y, +mo - 1, +d);
}}

function buildTimeline(el, lotId) {{
  const ps = SCHED[lotId];
  if (!ps || !ps.length) return;
  const todayMs = ruDateToMs(TODAY_STR);
  const minMs = ruDateToMs(ps[0].df);
  const maxMs = ruDateToMs(ps[ps.length - 1].dt);
  const spanMs = maxMs - minMs || 1;
  const pct = ms => Math.max(0, Math.min(100, (ms - minMs) / spanMs * 100));
  const fmt     = n  => n != null ? new Intl.NumberFormat('ru').format(n) + ' ₽' : '?';
  const fmtDate = s  => s ? s.slice(0, 5) : ''; // DD.MM

  const canvas = document.createElement('div');
  canvas.className = 'tl-canvas';
  canvas.style.minWidth = Math.max(520, ps.length * 72) + 'px';

  // Bars
  ps.forEach(p => {{
    const fromMs = ruDateToMs(p.df);
    const toMs   = ruDateToMs(p.dt);
    const left   = pct(fromMs);
    const width  = Math.max(pct(toMs) - left, 0.4);
    const bar = document.createElement('div');
    bar.className = 'tl-bar ' + (
      toMs < todayMs    ? 'past' :
      fromMs <= todayMs ? 'current' : 'future'
    );
    bar.style.left  = left + '%';
    bar.style.width = width + '%';
    bar.title = `Этап ${{p.n}}: ${{p.df}} ${{p.tf}} – ${{p.dt}} ${{p.tt}}\n${{fmt(p.p)}}`;
    canvas.appendChild(bar);
    const priceLabel = document.createElement('div');
    priceLabel.className = 'tl-price ' + (toMs < todayMs ? 'past' : fromMs <= todayMs ? 'current' : 'future');
    priceLabel.style.left = (left + width / 2) + '%';
    priceLabel.textContent = fmt(p.p);
    canvas.appendChild(priceLabel);
  }});

  // Даты отсечки на каждой границе периода
  const boundaries = ps.map((p, i) => ({{
    ms: ruDateToMs(p.df), label: fmtDate(p.df), isFirst: i === 0, isLast: false
  }}));
  const last = ps[ps.length - 1];
  boundaries.push({{ ms: ruDateToMs(last.dt), label: fmtDate(last.dt), isFirst: false, isLast: true }});

  const shownX = [];
  boundaries.forEach(b => {{
    const x = pct(b.ms);
    if (shownX.every(sx => Math.abs(sx - x) >= 5)) {{
      shownX.push(x);
      const tick = document.createElement('div');
      tick.className = 'tl-tick';
      tick.style.left = x + '%';
      canvas.appendChild(tick);
      const lbl = document.createElement('div');
      lbl.className = 'tl-date' + (b.isFirst ? ' first' : b.isLast ? ' last' : '');
      lbl.textContent = b.label;
      lbl.style.left = x + '%';
      canvas.appendChild(lbl);
    }}
  }});

  // Today line
  if (todayMs >= minMs && todayMs <= maxMs) {{
    const line = document.createElement('div');
    line.className = 'tl-today';
    line.style.left = pct(todayMs) + '%';
    line.title = 'Сегодня';
    canvas.appendChild(line);
  }}

  el.innerHTML = '<div class="tl-head">Расписание публичного предложения</div>';
  const wrap = document.createElement('div');
  wrap.className = 'tl-wrap';
  wrap.appendChild(canvas);
  el.appendChild(wrap);
}}


document.querySelectorAll('.timeline').forEach(el => buildTimeline(el, el.dataset.lot));

// ── Sort ──────────────────────────────────────────────────────────────────
const grid = document.getElementById('cards');
function applySort(mode) {{
  if (mode !== 'urgency') return;
  const all = [...grid.querySelectorAll('.lot-card')];
  all.sort((a, b) => {{
    const ua = parseInt(a.dataset.urgency ?? '99999');
    const ub = parseInt(b.dataset.urgency ?? '99999');
    return ua - ub;
  }});
  all.forEach(c => grid.appendChild(c));
}}
document.getElementById('fSort').addEventListener('change', e => applySort(e.target.value));

// ── Filtering ─────────────────────────────────────────────────────────────

const cards = [...document.querySelectorAll('.lot-card')];
const noResults = document.getElementById('noResults');

function applyFilters() {{
  const q            = document.getElementById('q').value.toLowerCase();
  const status       = document.getElementById('fStatus').value.toLowerCase();
  const trade        = document.getElementById('fTrade').value.toLowerCase();
  const browser      = document.getElementById('fBrowser').value;
  const folder       = document.getElementById('fFolder').value;
  const hideFinished = document.getElementById('fHideFinished').checked;
  let visible = 0;
  cards.forEach(c => {{
    const t = c.innerText.toLowerCase();
    const show = (!q || t.includes(q))
      && (!status       || t.includes(status))
      && (!trade        || t.includes(trade))
      && (!browser      || c.dataset.browser === browser)
      && (!folder       || c.dataset.folder === folder)
      && (!hideFinished || c.dataset.result === '0');
    c.hidden = !show;
    if (show) visible++;
  }});
  noResults.style.display = visible === 0 ? 'block' : 'none';
}}

['q', 'fStatus', 'fTrade', 'fBrowser', 'fFolder'].forEach(id =>
  document.getElementById(id).addEventListener('input', applyFilters)
);
document.getElementById('fHideFinished').addEventListener('change', applyFilters);

// ── Valuation panel ───────────────────────────────────────────────────────
function openVal() {{
  document.getElementById('val-overlay').style.display = 'block';
  document.getElementById('val-panel').classList.add('open');
}}
function openValFor(lotId, description, classifier) {{
  document.getElementById('val-lot-id').value     = lotId;
  document.getElementById('val-desc').value       = description;
  document.getElementById('val-classifier').value = classifier;
  document.getElementById('val-result').style.display = 'none';
  document.getElementById('val-error').style.display  = 'none';
  openVal();
}}

document.getElementById('cards').addEventListener('click', function(e) {{
  const btn = e.target.closest('.val-card-btn');
  if (!btn) return;
  openValFor(
    btn.dataset.lotId,
    btn.dataset.description,
    btn.dataset.classifier
  );
}});
function closeVal() {{
  document.getElementById('val-overlay').style.display = 'none';
  document.getElementById('val-panel').classList.remove('open');
}}
async function submitVal() {{
  const desc = document.getElementById('val-desc').value.trim();
  if (!desc) {{ alert('Введите описание'); return; }}

  const btn = document.getElementById('val-submit');
  btn.disabled = true;
  document.getElementById('val-spinner').style.display = 'block';
  document.getElementById('val-result').style.display  = 'none';
  document.getElementById('val-error').style.display   = 'none';

  try {{
    const res = await fetch('http://localhost:5000/valuate', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        description: desc,
        classifier:  document.getElementById('val-classifier').value.trim(),
        lot_id:      document.getElementById('val-lot-id').value.trim(),
      }})
    }});
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Ошибка сервера');

    const fmt = n => new Intl.NumberFormat('ru-RU').format(n);
    const priceStr = fmt(data.market_price_min) + ' — ' + fmt(data.market_price_max) + ' ₽';
    const confStr  = 'Уверенность: ' + (data.confidence || '—') + (data.saved_to_db ? ' · сохранено в БД' : '');

    document.getElementById('val-price').textContent   = priceStr;
    document.getElementById('val-conf').textContent    = confStr;
    document.getElementById('val-text').textContent    = data.reasoning || '';
    const src = (data.sources || []).map(s => '— ' + s).join('\\n');
    document.getElementById('val-sources').textContent = src;
    document.getElementById('val-result').style.display = 'block';

    // Обновляем блок в карточке
    const lotId = document.getElementById('val-lot-id').value.trim();
    if (lotId) {{
      const vb = document.getElementById('vb-' + lotId);
      if (vb) {{
        document.getElementById('vbp-' + lotId).textContent = priceStr;
        document.getElementById('vbm-' + lotId).textContent = confStr;
        document.getElementById('vbt-' + lotId).textContent = data.reasoning || '';
        vb.style.display = 'block';
      }}
    }}
  }} catch(e) {{
    document.getElementById('val-error').textContent = e.message;
    document.getElementById('val-error').style.display = 'block';
  }} finally {{
    btn.disabled = false;
    document.getElementById('val-spinner').style.display = 'none';
  }}
}}
</script>
</body>
</html>"""

    out = REPORTS_DIR / "dashboard.html"
    out.write_text(page, encoding="utf-8")
    print(f"[render] {out} ({len(page)//1024} KB, {len(lots)} lots)")


# ── MAIN ───────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Fedresurs auction fetcher")
    p.add_argument("--no-fetch",  action="store_true", help="Skip fetching bookmarks")
    p.add_argument("--no-render", action="store_true", help="Skip HTML rendering")
    p.add_argument("--refetch",    action="store_true", help="Re-download cached JSONs")
    p.add_argument("--reprocess",  action="store_true", help="Re-run full pipeline for all bookmarked URLs (implies --refetch)")
    p.add_argument("--limit",      type=int, default=None, help="Max links to process")
    p.add_argument("--browser",    default=None, choices=["Chrome", "Chromium"], help="Sync only this browser")
    p.add_argument("--sheets",     action="store_true", help="Also sync to Google Sheets (requires credentials.json)")
    args = p.parse_args()

    db = init_db()

    if not args.no_fetch:
        active_ids = sync(db, limit=args.limit, refetch=args.refetch or args.reprocess, reprocess=args.reprocess, browser_filter=args.browser)
        mark_archived(db, active_ids)
        # Auto-remove from bookmarks lots that have a definitive auction result
        completed_urls = {
            row[0] for row in db.execute(
                "select url from lots where result_lot_status is not null and url is not null"
            )
        }
        remove_from_bookmarks(completed_urls)
        db.commit()

    if args.sheets:
        sheets_sync(db)

    if not args.no_render:
        render_html(db)

    db.close()


if __name__ == "__main__":
    main()
