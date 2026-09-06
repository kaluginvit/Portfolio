#!/usr/bin/env python3
"""Fedresurs auction monitor MVP.

This prototype reads Chrome bookmarks, fetches Fedresurs bankruptcy messages,
normalizes lots, stores them in SQLite, scans local documents, and renders a
static HTML dashboard.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import os
import re
import sqlite3
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


APP_NAME = "fedresurs_mvp"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DOCS_DIR = DATA_DIR / "documents"
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = DATA_DIR / "fedresurs.sqlite3"

BOOKMARK_ROOT = ["Объявления о торгах", "Квартиры"]
FEDRESURS_BACKEND = "https://fedresurs.ru/backend/bankruptcy-messages/{message_id}"
FEDRESURS_CARD = "https://fedresurs.ru/bankruptmessages/{message_id}"
MARKET_SOURCES = (
    "n1.ru",
    "cian.ru",
    "avito.ru",
    "domclick.ru",
    "yandex.ru/realty",
    "realty.yandex.ru",
    "etagi.com",
    "mirkvartir.ru",
)


def ensure_dirs() -> None:
    for path in (DATA_DIR, RAW_DIR, DOCS_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def default_bookmarks_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        raise RuntimeError("LOCALAPPDATA is not set; pass --bookmarks explicitly.")
    return Path(local_appdata) / "Google" / "Chrome" / "User Data" / "Default" / "Bookmarks"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_child_folder(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    for child in node.get("children", []):
        if child.get("type") == "folder" and child.get("name") == name:
            return child
    return None


def find_folder_by_path(bookmarks: dict[str, Any], names: list[str]) -> dict[str, Any]:
    roots = bookmarks["roots"]
    candidates = [
        roots.get("bookmark_bar"),
        roots.get("other"),
        roots.get("synced"),
    ]
    for root in candidates:
        node = root
        if not node:
            continue
        for name in names:
            node = find_child_folder(node, name)
            if node is None:
                break
        if node is not None:
            return node
    raise RuntimeError(f"Bookmark folder not found: {' / '.join(names)}")


def get_bookmark_links(bookmarks_path: Path, limit: int) -> list[dict[str, str]]:
    bookmarks = read_json(bookmarks_path)
    folder = find_folder_by_path(bookmarks, BOOKMARK_ROOT)
    links = [
        {"name": child.get("name", ""), "url": child.get("url", "")}
        for child in folder.get("children", [])
        if child.get("type") == "url" and "fedresurs.ru/bankruptmessages/" in child.get("url", "")
    ]
    return links[:limit]


def message_id_from_url(url: str) -> str:
    message_id = url.rstrip("/").split("/")[-1]
    if not re.fullmatch(r"[0-9a-fA-F-]{32,36}", message_id):
        raise ValueError(f"Cannot extract Fedresurs message id from URL: {url}")
    return message_id.upper().replace("-", "")


def message_id_from_guid(value: str | None) -> str | None:
    if not value:
        return None
    compact = value.upper().replace("-", "")
    if re.fullmatch(r"[0-9A-F]{32}", compact):
        return compact
    return None


def fedresurs_message_url(message_id: str) -> str:
    return FEDRESURS_CARD.format(message_id=message_id.upper())


def fetch_json(url: str, referer: str | None = None, retries: int = 3) -> dict[str, Any]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
    }
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def fetch_text(url: str, referer: str | None = None, retries: int = 2) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                return raw.decode(charset, errors="ignore")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def fetch_text_with_curl(url: str, referer: str | None = None, timeout: int = 45) -> str:
    cmd = [
        "curl.exe",
        "-L",
        "--silent",
        "--show-error",
        "--max-time",
        str(timeout),
        "-A",
        "Mozilla/5.0 Chrome/124 Safari/537.36",
    ]
    if referer:
        cmd.extend(["-e", referer])
    cmd.append(url)
    completed = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return completed.stdout.decode("utf-8", errors="ignore")


def init_db() -> None:
    ensure_dirs()
    with sqlite3.connect(DB_PATH) as db:
        db.executescript(
            """
            create table if not exists source_links (
                url text primary key,
                title text,
                folder text,
                created_at text
            );

            create table if not exists messages (
                guid text primary key,
                message_id text,
                url text,
                number text,
                type_name text,
                message_type text,
                date_publish text,
                trade_type text,
                case_number text,
                bankrupt_name text,
                bankrupt_inn text,
                publisher_name text,
                publisher_email text,
                raw_json_path text,
                fetched_at text
            );

            create table if not exists lots (
                lot_id text primary key,
                message_guid text,
                message_number text,
                source_url text,
                lot_order integer,
                asset_type text,
                trade_type text,
                description text,
                address text,
                cadastral_number text,
                area_m2 real,
                start_price real,
                current_price real,
                application_begin text,
                application_end text,
                auction_datetime text,
                price_reduction text,
                market_min real,
                market_mid real,
                market_max real,
                target_price real,
                valuation_method text,
                confidence text,
                decision text,
                status text,
                interesting_from text,
                interesting_to text,
                result_status text,
                result_text text,
                updated_at text
            );

            create table if not exists documents (
                doc_guid text primary key,
                message_guid text,
                name text,
                size integer,
                hash text,
                local_path text,
                text_excerpt text,
                status text,
                updated_at text
            );

            create table if not exists price_schedule (
                id integer primary key autoincrement,
                lot_id text,
                period_no integer,
                date_from text,
                date_to text,
                price real,
                is_interesting integer
            );

            create table if not exists market_evidence (
                id integer primary key autoincrement,
                lot_id text,
                source text,
                url text,
                title text,
                snippet text,
                price real,
                area_m2 real,
                price_per_m2 real,
                currency text,
                relevance real,
                query text,
                fetched_at text,
                unique(lot_id, url)
            );
            """
        )
        ensure_column(db, "lots", "evidence_count", "integer")
        ensure_column(db, "lots", "sources_count", "integer")
        ensure_column(db, "lots", "price_m2_p25", "real")
        ensure_column(db, "lots", "price_m2_p50", "real")
        ensure_column(db, "lots", "price_m2_p75", "real")
        ensure_column(db, "lots", "result_message_number", "text")
        ensure_column(db, "lots", "result_message_url", "text")
        ensure_column(db, "lots", "result_date_publish", "text")
        ensure_column(db, "lots", "result_price", "real")
        ensure_column(db, "lots", "result_buyer", "text")
        ensure_column(db, "lots", "result_reason", "text")


def ensure_column(db: sqlite3.Connection, table: str, column: str, declaration: str) -> None:
    columns = {row[1] for row in db.execute(f"pragma table_info({table})")}
    if column not in columns:
        db.execute(f"alter table {table} add column {column} {declaration}")


def parse_date(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    value = value.replace("Z", "")
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def iso(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("dateTime") or value.get("date")
    if not value:
        return None
    parsed = parse_date(str(value))
    return parsed.isoformat(timespec="minutes") if parsed else str(value)


def money(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("\xa0", " ")
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(" ", "").replace(",", "")
    else:
        text = text.replace(" ", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * pct
    lower = int(pos)
    upper = min(lower + 1, len(ordered) - 1)
    weight = pos - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(" ".join(value.split()))


def source_from_url(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    for source in MARKET_SOURCES:
        if source in host:
            return source
    return host or "unknown"


def clean_result_url(url: str) -> str:
    url = html.unescape(url)
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query:
        return query["uddg"][0]
    if "u" in query:
        value = query["u"][0]
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith("a1"):
            encoded = value[2:]
            padding = "=" * (-len(encoded) % 4)
            try:
                decoded = base64.urlsafe_b64decode((encoded + padding).encode("ascii")).decode("utf-8", errors="ignore")
                if decoded.startswith(("http://", "https://")):
                    return decoded
            except Exception:
                pass
    return url


def generate_market_queries(lot: dict[str, Any], query_mode: str = "broad") -> list[str]:
    description = lot.get("description") or ""
    address = lot.get("address") or ""
    cadastral = lot.get("cadastral_number")
    area = lot.get("area_m2")
    area_int = str(round(float(area))) if area else ""

    queries: list[str] = []
    if query_mode == "exact":
        if cadastral:
            queries.append(f'"{cadastral}"')
        if address:
            queries.append(f'"{address}" продажа')
            if area_int:
                queries.append(f'"{address}" "{area_int}" кв м цена')
    if "Екатеринбург" in address or "Екатеринбург" in description:
        street = extract_street_hint(address or description)
        if query_mode == "exact" and street and area_int:
            queries.append(f'Екатеринбург "{street}" "{area_int}" кв м квартира цена')
        if area_int:
            queries.append(f'Екатеринбург квартира {area_int} кв м цена')
            queries.append(f'Екатеринбург квартира {area_int} м2 купить')
        else:
            queries.append("Екатеринбург квартира цена за м2")

    if not queries and description:
        if query_mode == "exact":
            queries.append(description[:120])
        elif area_int:
            queries.append(f"квартира {area_int} кв м цена")

    source_queries = []
    for query in queries[:4]:
        source_queries.append(query)
        for source in ("cian.ru", "domclick.ru", "avito.ru", "realty.yandex.ru"):
            source_queries.append(f"site:{source} {query}")
    seen: set[str] = set()
    unique = []
    for query in source_queries:
        normalized = " ".join(query.split())
        if normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique[:12]


def extract_street_hint(text: str) -> str | None:
    patterns = [
        r"(?:улица|ул\.?)\s+([^,\d]+)",
        r"(?:проспект|пр-т|пр\.)\s+([^,\d]+)",
        r"(?:переулок|пер\.?)\s+([^,\d]+)",
        r"(?:бульвар|бул\.?)\s+([^,\d]+)",
    ]
    for pattern in patterns:
        found = re.search(pattern, text, flags=re.IGNORECASE)
        if found:
            return found.group(1).strip(" .")
    return None


def extract_price(text: str) -> float | None:
    cleaned = text.replace("\xa0", " ")
    candidates = []
    patterns = [
        r"(\d[\d\s]{4,15}(?:[,.]\d+)?)\s*(?:₽|руб(?:\.|лей|ля|ль)?)",
        r"(?:цена|стоимость)\D{0,20}(\d[\d\s]{4,15}(?:[,.]\d+)?)",
    ]
    for pattern in patterns:
        for found in re.finditer(pattern, cleaned, flags=re.IGNORECASE):
            value = money(found.group(1))
            if value and 100_000 <= value <= 500_000_000:
                candidates.append(value)
    return min(candidates) if candidates else None


def extract_price_per_m2(text: str) -> float | None:
    cleaned = text.replace("\xa0", " ")
    patterns = [
        r"(\d[\d\s]{3,10}(?:[,.]\d+)?)\s*(?:₽|руб(?:\.|лей|ля|ль)?)\s*/\s*(?:м2|м²|кв\.?\s*м)",
        r"(\d[\d\s]{3,10}(?:[,.]\d+)?)\s*(?:₽|руб(?:\.|лей|ля|ль)?)\s+за\s+(?:м2|м²|кв\.?\s*м)",
    ]
    for pattern in patterns:
        found = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if found:
            value = money(found.group(1))
            if value and 10_000 <= value <= 2_000_000:
                return value
    return None


def relevance_score(lot: dict[str, Any], title: str, snippet: str, url: str) -> float:
    text = f"{title} {snippet} {url}".lower()
    score = 0.15
    if "прод" in text or "куп" in text:
        score += 0.15
    if any(word in text for word in ("квартир", "помещен", "недвиж")):
        score += 0.2
    cadastral = lot.get("cadastral_number")
    if cadastral and cadastral.lower() in text:
        score += 0.35
    area = lot.get("area_m2")
    if area:
        rounded = str(round(float(area)))
        if rounded in text and ("м2" in text or "м²" in text or "кв" in text):
            score += 0.15
    address = lot.get("address") or ""
    street = extract_street_hint(address)
    if street and street.lower() in text:
        score += 0.2
    if source_from_url(url) in MARKET_SOURCES:
        score += 0.1
    return min(score, 1.0)


def parse_duckduckgo_results(raw_html: str) -> list[dict[str, str]]:
    results = []
    blocks = re.split(r'<div[^>]+class="[^"]*result[^"]*"[^>]*>', raw_html, flags=re.IGNORECASE)
    for block in blocks[1:]:
        link_match = re.search(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, flags=re.IGNORECASE | re.DOTALL)
        if not link_match:
            continue
        url = clean_result_url(link_match.group(1))
        title = strip_tags(link_match.group(2))
        snippet_match = re.search(r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', block, flags=re.IGNORECASE | re.DOTALL)
        if not snippet_match:
            snippet_match = re.search(r'<div[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>', block, flags=re.IGNORECASE | re.DOTALL)
        snippet = strip_tags(snippet_match.group(1)) if snippet_match else ""
        if url and title:
            results.append({"url": url, "title": title, "snippet": snippet})
    return results


def search_duckduckgo(query: str) -> list[dict[str, str]]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query, "kl": "ru-ru"})
    raw = fetch_text(url, referer="https://duckduckgo.com/")
    return parse_duckduckgo_results(raw)


def parse_bing_results(raw_html: str) -> list[dict[str, str]]:
    results = []
    blocks = re.findall(r'<li[^>]+class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>', raw_html, flags=re.IGNORECASE | re.DOTALL)
    for block in blocks:
        link_match = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>', block, flags=re.IGNORECASE | re.DOTALL)
        if not link_match:
            continue
        url = clean_result_url(link_match.group(1))
        title = strip_tags(link_match.group(2))
        snippet_match = re.search(r'<p[^>]*>(.*?)</p>', block, flags=re.IGNORECASE | re.DOTALL)
        snippet = strip_tags(snippet_match.group(1)) if snippet_match else ""
        if url and title:
            results.append({"url": url, "title": title, "snippet": snippet})
    return results


def search_bing(query: str) -> list[dict[str, str]]:
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({"q": query, "cc": "ru"})
    raw = fetch_text(url, referer="https://www.bing.com/")
    return parse_bing_results(raw)


def search_market(query: str, engine: str) -> list[dict[str, str]]:
    if engine == "duckduckgo":
        return search_duckduckgo(query)
    if engine == "bing":
        return search_bing(query)
    raise ValueError(f"Unknown search engine: {engine}")


def build_market_evidence(lot: dict[str, Any], query: str, result: dict[str, str], fetch_pages: bool) -> dict[str, Any] | None:
    url = result["url"]
    source = source_from_url(url)
    title = result.get("title") or ""
    snippet = result.get("snippet") or ""
    combined = f"{title}\n{snippet}"
    if fetch_pages and source in MARKET_SOURCES:
        try:
            page_text = strip_tags(fetch_text(url, referer="https://duckduckgo.com/"))[:20000]
            combined = f"{combined}\n{page_text}"
            time.sleep(0.4)
        except Exception:
            pass

    price_per_m2 = extract_price_per_m2(combined)
    price = extract_price(combined)
    area = extract_area(combined)
    lot_area = lot.get("area_m2")
    if price_per_m2 is None and price and lot_area:
        price_per_m2 = price / float(lot_area)
    if price is None and price_per_m2 and lot_area:
        price = price_per_m2 * float(lot_area)

    if price is None and price_per_m2 is None:
        return None

    relevance = relevance_score(lot, title, snippet, url)
    return {
        "lot_id": lot["lot_id"],
        "source": source,
        "url": url,
        "title": title[:500],
        "snippet": snippet[:1000],
        "price": round(price, 2) if price else None,
        "area_m2": round(area, 2) if area else lot_area,
        "price_per_m2": round(price_per_m2, 2) if price_per_m2 else None,
        "currency": "RUB",
        "relevance": round(relevance, 3),
        "query": query,
        "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
    }


def cian_search_url(lot: dict[str, Any]) -> str:
    params = {
        "deal_type": "sale",
        "engine_version": "2",
        "offer_type": "flat",
        "region": "4743",
    }
    return "https://ekb.cian.ru/cat.php?" + urllib.parse.urlencode(params)


def parse_cian_evidence(raw_html: str, lot: dict[str, Any], max_results: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    lot_area = float(lot["area_m2"]) if lot.get("area_m2") else None
    for match in re.finditer(r'"priceRur"\s*:\s*(\d+)', raw_html):
        start = max(0, match.start() - 2500)
        end = min(len(raw_html), match.end() + 2500)
        block = raw_html[start:end]
        price = money(match.group(1))
        area_match = re.search(r'"totalArea"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?', block)
        cian_match = re.search(r'"cianId"\s*:\s*(\d+)', block)
        title_match = re.search(r'"formattedFullInfo"\s*:\s*"([^"]+)"', block)
        if not price or not area_match or not cian_match:
            continue
        cian_id = cian_match.group(1)
        if cian_id in seen_ids:
            continue
        area = money(area_match.group(1))
        if not area:
            continue
        if lot_area and not (lot_area * 0.65 <= area <= lot_area * 1.45):
            continue
        seen_ids.add(cian_id)
        title = html.unescape((title_match.group(1) if title_match else f"ЦИАН объект {cian_id}").replace("\\u002F", "/"))
        price_per_m2 = price / area
        relevance = 0.65
        if lot_area:
            area_delta = abs(area - lot_area) / lot_area
            relevance += max(0, 0.25 - area_delta) 
        items.append(
            {
                "lot_id": lot["lot_id"],
                "source": "cian.ru",
                "url": f"https://ekb.cian.ru/sale/flat/{cian_id}/",
                "title": title[:500],
                "snippet": f"ЦИАН Екатеринбург, площадь {area} м2, цена {price:.0f} руб.",
                "price": round(price, 2),
                "area_m2": round(area, 2),
                "price_per_m2": round(price_per_m2, 2),
                "currency": "RUB",
                "relevance": round(min(relevance, 1.0), 3),
                "query": cian_search_url(lot),
                "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        )
        if len(items) >= max_results:
            break
    return items


def fetch_cian_market_evidence(lot: dict[str, Any], max_results: int) -> list[dict[str, Any]]:
    if lot.get("asset_type") != "real_estate":
        return []
    url = cian_search_url(lot)
    try:
        raw = fetch_text(url, referer="https://ekb.cian.ru/")
    except Exception:
        raw = fetch_text_with_curl(url, referer="https://ekb.cian.ru/")
    return parse_cian_evidence(raw, lot, max_results)


def n1_search_url() -> str:
    return "https://ekaterinburg.n1.ru/kupit/kvartiry/"


def parse_n1_evidence(raw_html: str, lot: dict[str, Any], max_results: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    lot_area = float(lot["area_m2"]) if lot.get("area_m2") else None
    pattern = (
        r'data-test="offers-list-item-param-price"\s+title="([\d\s]+)\s*руб".{0,900}?'
        r'living-list-card-price__item _per-sqm"\s+title="([\d\s]+)\s*руб"'
    )
    for match in re.finditer(pattern, raw_html, flags=re.IGNORECASE | re.DOTALL):
        price = money(match.group(1))
        price_per_m2 = money(match.group(2))
        if not price or not price_per_m2:
            continue
        area = price / price_per_m2
        if lot_area and not (lot_area * 0.65 <= area <= lot_area * 1.45):
            continue
        block_start = max(0, match.start() - 5000)
        block = raw_html[block_start:match.end()]
        hrefs = re.findall(r'href="([^"]+)"', block)
        href = hrefs[-1] if hrefs else n1_search_url()
        if href.startswith("/"):
            url = "https://ekaterinburg.n1.ru" + href
        elif href.startswith("http"):
            url = href
        else:
            url = n1_search_url()
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title_match = re.search(r'<a[^>]+href="' + re.escape(href) + r'"[^>]*>(.*?)</a>', block, flags=re.IGNORECASE | re.DOTALL)
        title = strip_tags(title_match.group(1)) if title_match else "N1 квартира в Екатеринбурге"
        relevance = 0.7
        if lot_area:
            area_delta = abs(area - lot_area) / lot_area
            relevance += max(0, 0.25 - area_delta)
        items.append(
            {
                "lot_id": lot["lot_id"],
                "source": "n1.ru",
                "url": url,
                "title": title[:500],
                "snippet": f"N1 Екатеринбург, расчетная площадь {area:.1f} м2, цена {price:.0f} руб.",
                "price": round(price, 2),
                "area_m2": round(area, 2),
                "price_per_m2": round(price_per_m2, 2),
                "currency": "RUB",
                "relevance": round(min(relevance, 1.0), 3),
                "query": n1_search_url(),
                "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        )
        if len(items) >= max_results:
            break
    return items


def fetch_n1_market_evidence(lot: dict[str, Any], max_results: int) -> list[dict[str, Any]]:
    if lot.get("asset_type") != "real_estate":
        return []
    raw = fetch_text(n1_search_url(), referer="https://ekaterinburg.n1.ru/")
    return parse_n1_evidence(raw, lot, max_results)


def extract_area(text: str) -> float | None:
    patterns = [
        r"(?:площад[ьюи]|общая площадь)\s*[:\-]?\s*(\d+(?:[,.]\d+)?)\s*(?:кв\.?\s*м|м2|м²)",
        r"(\d+(?:[,.]\d+)?)\s*(?:кв\.?\s*м|м2|м²)",
    ]
    for pattern in patterns:
        found = re.search(pattern, text, flags=re.IGNORECASE)
        if found:
            return money(found.group(1))
    return None


def extract_cadastral(text: str) -> str | None:
    found = re.search(r"\b\d{2}:\d{2}:\d{6,10}:\d+\b", text)
    return found.group(0) if found else None


def extract_address(text: str) -> str | None:
    cadastral_index = text.lower().find("кадастров")
    short = text[:cadastral_index] if cadastral_index > 0 else text
    found = re.search(r"(?:адрес[ау]?\s*[:\-]|по адресу)\s*(.+)", short, flags=re.IGNORECASE | re.DOTALL)
    if not found:
        return None
    address = found.group(1)
    address = re.split(r"\n|;|Имущество|начальная цена", address, flags=re.IGNORECASE)[0]
    return " ".join(address.split()).strip(" .,")


def classify_asset(description: str) -> str:
    text = description.lower()
    if "нежил" in text or "коммерчес" in text or "офис" in text or "торгов" in text:
        return "commercial_real_estate"
    if "земель" in text:
        return "land"
    if "гараж" in text or "машино-мест" in text:
        return "parking_or_garage"
    if "здание" in text or "сооружен" in text:
        return "commercial_real_estate"
    if "квартир" in text or "жилое помещение" in text:
        return "real_estate"
    if any(word in text for word in ("автомоб", "транспорт", "vin", "прицеп", "погрузчик", "экскаватор")):
        return "vehicle"
    if any(word in text for word in ("станок", "оборуд", "линия", "компрессор", "агрегат")):
        return "equipment"
    if any(word in text for word in ("дебитор", "право требования", "задолжен")):
        return "receivable"
    if any(word in text for word in ("доля", "акци", "уставн")):
        return "shares_or_business"
    return "other"


def parse_step_amount(text: str) -> float | None:
    lowered = text.lower().replace("\xa0", " ")
    found = re.search(r"уменьш\w+\s+на\s+([\d\s.,]+)\s*руб", lowered)
    if not found:
        found = re.search(r"сниж\w+\s+на\s+([\d\s.,]+)\s*руб", lowered)
    return money(found.group(1)) if found else None


def parse_step_percent(text: str) -> float | None:
    lowered = text.lower().replace("\xa0", " ")
    patterns = [
        r"величин[аы].{0,80}?сниж\w+.{0,40}?([\d\s.,]+)\s*%",
        r"сниж\w+\s+цен\w+.{0,80}?([\d\s.,]+)\s*%",
        r"уменьш\w+\s+на\s+([\d\s.,]+)\s*%",
    ]
    for pattern in patterns:
        found = re.search(pattern, lowered)
        if found:
            value = money(found.group(1))
            if value:
                return value
    return None


def parse_workday_period(text: str) -> int | None:
    lowered = text.lower()
    found = re.search(r"первые\s+(\d+).{0,40}?рабоч", lowered)
    if not found:
        found = re.search(r"составляет\s+(\d+).{0,40}?рабоч", lowered)
    if found:
        return int(found.group(1))
    return None


def parse_calendar_period(text: str) -> int | None:
    lowered = text.lower()
    found = re.search(r"составляет.{0,40}?(\d+).{0,40}?календар", lowered)
    if not found:
        found = re.search(r"(\d+).{0,30}?календарн\w+\s+д", lowered)
    if found:
        return int(found.group(1))
    return None


def parse_cutoff_price(text: str) -> float | None:
    lowered = text.lower().replace("\xa0", " ")
    found = re.search(r"цен[аы]\s+отсечения.{0,80}?([\d\s.,]+)\s*руб", lowered)
    return money(found.group(1)) if found else None


def parse_cutoff_percent(text: str) -> float | None:
    lowered = text.lower().replace("\xa0", " ")
    patterns = [
        r"нижн\w+\s+предел.{0,120}?([\d\s.,]+)\s*%",
        r"цен[аы]\s+отсечения.{0,80}?([\d\s.,]+)\s*%",
    ]
    for pattern in patterns:
        found = re.search(pattern, lowered)
        if found:
            value = money(found.group(1))
            if value:
                return value
    return None


def add_workdays(day: dt.date, count: int) -> dt.date:
    current = day
    added = 0
    while added < count:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def schedule_public_offer(
    lot_id: str,
    start_price: float | None,
    target_price: float | None,
    reduction_text: str,
    application_begin: str | None,
    application_end: str | None,
) -> list[dict[str, Any]]:
    if not start_price or not application_begin or not application_end:
        return []
    begin_dt = parse_date(application_begin)
    end_dt = parse_date(application_end)
    if not begin_dt or not end_dt:
        return []
    step_amount = parse_step_amount(reduction_text)
    step_percent = parse_step_percent(reduction_text)
    if step_amount is None and step_percent:
        step_amount = start_price * step_percent / 100
    step_amount = step_amount or 0
    calendar_days = parse_calendar_period(reduction_text)
    workday_days = parse_workday_period(reduction_text)
    period_days = calendar_days or workday_days or 5
    cutoff_price = parse_cutoff_price(reduction_text)
    cutoff_percent = parse_cutoff_percent(reduction_text)
    if cutoff_price is None and cutoff_percent:
        cutoff_price = start_price * cutoff_percent / 100

    periods: list[dict[str, Any]] = []
    period_start = begin_dt.date()
    end_date = end_dt.date()
    price = start_price
    period_no = 1
    while period_start <= end_date and period_no <= 80:
        if calendar_days:
            period_end = min(period_start + dt.timedelta(days=period_days - 1), end_date)
        else:
            period_end = min(add_workdays(period_start, period_days - 1), end_date)
        is_interesting = int(bool(target_price and price <= target_price))
        periods.append(
            {
                "lot_id": lot_id,
                "period_no": period_no,
                "date_from": period_start.isoformat(),
                "date_to": period_end.isoformat(),
                "price": round(price, 2),
                "is_interesting": is_interesting,
            }
        )
        next_start = period_end + dt.timedelta(days=1)
        while not calendar_days and next_start.weekday() >= 5:
            next_start += dt.timedelta(days=1)
        if next_start > end_date or step_amount <= 0:
            break
        price = max(price - step_amount, cutoff_price or 0)
        period_start = next_start
        period_no += 1
    return periods


def normalize_message(
    data: dict[str, Any],
    source_url: str,
    raw_path: Path,
    result_details: dict[int, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    content = data.get("content") or {}
    message_info = content.get("messageInfo") or {}
    message_content = message_info.get("messageContent") or {}
    bankrupt = data.get("bankrupt") or content.get("bankrupt") or {}
    publisher = data.get("publisher") or content.get("publisher") or {}
    publisher_name = publisher.get("name")
    if not publisher_name and isinstance(publisher.get("fio"), dict):
        fio = publisher["fio"]
        publisher_name = " ".join(filter(None, [fio.get("lastName"), fio.get("firstName"), fio.get("middleName")]))

    message_guid = data.get("guid") or message_id_from_url(source_url)
    message = {
        "guid": message_guid,
        "message_id": message_id_from_url(source_url),
        "url": source_url,
        "number": data.get("number"),
        "type_name": data.get("typeName"),
        "message_type": data.get("messageType"),
        "date_publish": iso(data.get("datePublish")),
        "trade_type": message_content.get("tradeType"),
        "case_number": content.get("caseNumber") or bankrupt.get("legalCaseNumber"),
        "bankrupt_name": bankrupt.get("name"),
        "bankrupt_inn": bankrupt.get("inn"),
        "publisher_name": publisher_name,
        "publisher_email": publisher.get("email"),
        "raw_json_path": str(raw_path),
        "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
    }

    application = message_content.get("application") or {}
    lots = []
    for lot in message_content.get("lotTable") or []:
        description = lot.get("description") or ""
        order = int(lot.get("order") or len(lots) + 1)
        lot_id = f"{message.get('number') or message_guid}-{order}"
        start_price = money(lot.get("startPrice"))
        result = (result_details or {}).get(order) or {}
        lots.append(
            {
                "lot_id": lot_id,
                "message_guid": message_guid,
                "message_number": message.get("number"),
                "source_url": source_url,
                "lot_order": order,
                "asset_type": classify_asset(description),
                "trade_type": message.get("trade_type"),
                "description": description,
                "address": extract_address(description),
                "cadastral_number": extract_cadastral(description),
                "area_m2": extract_area(description),
                "start_price": start_price,
                "current_price": start_price,
                "application_begin": iso(application.get("dateTimeBegin")),
                "application_end": iso(application.get("dateTimeEnd")),
                "auction_datetime": iso(message_content.get("auctionDateTime")),
                "price_reduction": lot.get("priceReduction"),
                "result_status": result.get("status") or infer_result_status(data),
                "result_text": result.get("text") or "",
                "result_message_number": result.get("number"),
                "result_message_url": result.get("url"),
                "result_date_publish": result.get("date_publish"),
                "result_price": result.get("price"),
                "result_buyer": result.get("buyer"),
                "result_reason": result.get("reason"),
                "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        )

    file_hashes = {
        item.get("name"): item.get("hash")
        for item in content.get("fileInfoList") or []
        if isinstance(item, dict)
    }
    docs = []
    for doc in data.get("docs") or []:
        docs.append(
            {
                "doc_guid": doc.get("guid"),
                "message_guid": message_guid,
                "name": doc.get("name"),
                "size": doc.get("size"),
                "hash": file_hashes.get(doc.get("name")),
                "status": "metadata_only",
                "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        )

    return message, lots, docs


def infer_result_status(data: dict[str, Any]) -> str | None:
    text = json.dumps(data.get("linkedMessages") or [], ensure_ascii=False).lower()
    type_name = str(data.get("typeName") or "").lower()
    if "торг" in type_name and "результ" in type_name:
        if "несостоя" in text or "не состоя" in text:
            return "failed"
        if "победител" in text or "покупател" in text:
            return "sold"
    if "несостоя" in text or "не состоя" in text:
        return "failed"
    if "победител" in text or "покупател" in text:
        return "sold"
    return None


def result_message_kind(message: dict[str, Any]) -> str | None:
    text = " ".join(
        str(message.get(key) or "")
        for key in ("type", "typeName", "messageType")
    ).lower()
    if any(word in text for word in ("traderesult", "result", "результ", "cancel", "отмен", "аннулир", "заверш")):
        return text
    return None


def message_text(data: dict[str, Any]) -> str:
    content = data.get("content") or {}
    message_info = content.get("messageInfo") or {}
    message_content = message_info.get("messageContent") or {}
    values = [
        data.get("typeName"),
        message_content.get("text"),
        message_content.get("cancellationReason"),
    ]
    return "\n".join(str(value) for value in values if value)


def status_from_lot_status(value: Any) -> str | None:
    text = str(value or "").lower()
    if any(word in text for word in ("success", "succeed", "побед", "прод")):
        return "sold"
    if any(word in text for word in ("fail", "несостоя", "not")):
        return "failed"
    if any(word in text for word in ("cancel", "отмен")):
        return "cancelled"
    if any(word in text for word in ("suspend", "приостанов")):
        return "suspended"
    return None


def status_from_text(text: str, order: int | None = None) -> tuple[str | None, str | None]:
    lowered = text.lower()
    fragments = [lowered]
    if order is not None:
        pattern = rf"лот\s*№?\s*{order}\b"
        match = re.search(pattern, lowered)
        if match:
            start = max(0, match.start() - 250)
            end = min(len(lowered), match.end() + 700)
            fragments = [lowered[start:end]]
    fragment = fragments[0]
    if "приостанов" in fragment:
        return "suspended", "торги приостановлены"
    if "отмен" in fragment:
        return "cancelled", "торги отменены"
    if "не состоя" in fragment or "несостоя" in fragment:
        return "failed", "торги не состоялись"
    if "победител" in fragment or "покупател" in fragment or "договор" in fragment and "заключ" in fragment:
        return "sold", "есть победитель/покупатель"
    return None, None


def result_status_label(value: str | None) -> str:
    labels = {
        "sold": "Продано",
        "failed": "Торги не состоялись",
        "cancelled": "Отменено",
        "suspended": "Приостановлено",
    }
    return labels.get(value or "", value or "Не определено")


def winner_info(winner: dict[str, Any] | None) -> tuple[str | None, float | None]:
    if not winner:
        return None, None
    participant = winner.get("auctionParticipant") or winner.get("participant") or winner
    buyer = participant.get("fio")
    if not buyer:
        buyer = " ".join(
            part
            for part in [
                participant.get("lastName"),
                participant.get("firstName"),
                participant.get("middleName"),
            ]
            if part
        )
    price = money(participant.get("priceOffer") or participant.get("price") or winner.get("priceOffer"))
    return buyer or None, price


def collect_result_details(data: dict[str, Any], source_url: str, use_cache: bool) -> dict[int, dict[str, Any]]:
    original_id = message_id_from_guid(data.get("guid")) or message_id_from_url(source_url)
    results: dict[int, dict[str, Any]] = {}
    for linked in data.get("linkedMessages") or []:
        if not result_message_kind(linked):
            continue
        linked_id = message_id_from_guid(linked.get("guid"))
        if not linked_id or linked_id == original_id:
            continue
        raw_path = RAW_DIR / f"{linked_id}.json"
        try:
            if use_cache and raw_path.exists():
                linked_data = read_json(raw_path)
            else:
                linked_data = fetch_json(FEDRESURS_BACKEND.format(message_id=linked_id), referer=source_url)
                raw_path.write_text(json.dumps(linked_data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            continue

        content = linked_data.get("content") or {}
        message_info = content.get("messageInfo") or {}
        message_content = message_info.get("messageContent") or {}
        text = message_text(linked_data)
        result_url = fedresurs_message_url(linked_id)
        result_base = {
            "number": linked_data.get("number") or linked.get("number"),
            "url": result_url,
            "date_publish": iso(linked_data.get("datePublish") or linked.get("datePublish")),
        }

        for result_lot in message_content.get("lotTable") or []:
            try:
                order = int(result_lot.get("order"))
            except (TypeError, ValueError):
                continue
            buyer, price = winner_info(result_lot.get("winner"))
            status = status_from_lot_status(result_lot.get("lotStatus"))
            text_status, text_reason = status_from_text(text, order)
            if not status:
                status = text_status
                reason = text_reason
            else:
                reason = text_reason if text_status == status else None
            summary_parts = [result_status_label(status)]
            if price:
                summary_parts.append(f"цена {fmt_money(price)} ₽")
            if buyer:
                summary_parts.append(f"покупатель: {buyer}")
            results[order] = {
                **result_base,
                "status": status,
                "price": price,
                "buyer": buyer,
                "reason": reason,
                "text": "; ".join(part for part in summary_parts if part),
            }

        source_lots = (((data.get("content") or {}).get("messageInfo") or {}).get("messageContent") or {}).get("lotTable") or []
        for source_lot in source_lots:
            try:
                order = int(source_lot.get("order"))
            except (TypeError, ValueError):
                continue
            if order in results:
                continue
            status, reason = status_from_text(text, order)
            if status:
                results[order] = {
                    **result_base,
                    "status": status,
                    "price": None,
                    "buyer": None,
                    "reason": reason,
                    "text": result_status_label(status) + (f": {reason}" if reason else ""),
                }
    return results


def upsert_message(db: sqlite3.Connection, message: dict[str, Any]) -> None:
    keys = list(message)
    placeholders = ",".join("?" for _ in keys)
    updates = ",".join(f"{key}=excluded.{key}" for key in keys if key != "guid")
    db.execute(
        f"insert into messages ({','.join(keys)}) values ({placeholders}) "
        f"on conflict(guid) do update set {updates}",
        [message[key] for key in keys],
    )


def upsert_lot(db: sqlite3.Connection, lot: dict[str, Any]) -> None:
    keys = list(lot)
    placeholders = ",".join("?" for _ in keys)
    updates = ",".join(f"{key}=excluded.{key}" for key in keys if key != "lot_id")
    db.execute(
        f"insert into lots ({','.join(keys)}) values ({placeholders}) "
        f"on conflict(lot_id) do update set {updates}",
        [lot[key] for key in keys],
    )


def upsert_doc(db: sqlite3.Connection, doc: dict[str, Any]) -> None:
    if not doc.get("doc_guid"):
        return
    keys = list(doc)
    placeholders = ",".join("?" for _ in keys)
    updates = ",".join(f"{key}=excluded.{key}" for key in keys if key != "doc_guid")
    db.execute(
        f"insert into documents ({','.join(keys)}) values ({placeholders}) "
        f"on conflict(doc_guid) do update set {updates}",
        [doc[key] for key in keys],
    )


def upsert_market_evidence(db: sqlite3.Connection, item: dict[str, Any]) -> None:
    keys = list(item)
    placeholders = ",".join("?" for _ in keys)
    updates = ",".join(f"{key}=excluded.{key}" for key in keys if key not in {"id"})
    db.execute(
        f"insert into market_evidence ({','.join(keys)}) values ({placeholders}) "
        f"on conflict(lot_id, url) do update set {updates}",
        [item[key] for key in keys],
    )


def fetch_market_command(args: argparse.Namespace) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        lots = [
            dict(row)
            for row in db.execute(
                "select * from lots where asset_type='real_estate' order by message_number, lot_order limit ?",
                (args.limit,),
            )
        ]
        if args.clear:
            if lots:
                db.execute("delete from market_evidence where lot_id in (%s)" % ",".join("?" for _ in lots), [lot["lot_id"] for lot in lots])
                db.commit()

        for lot in lots:
            queries = generate_market_queries(lot, args.query_mode)
            print(f"market {lot['lot_id']}: {len(queries)} queries")
            seen_urls: set[str] = set()
            saved = 0
            if not args.skip_n1:
                try:
                    for item in fetch_n1_market_evidence(lot, args.max_results_per_lot):
                        if item["relevance"] < args.min_relevance:
                            continue
                        upsert_market_evidence(db, item)
                        seen_urls.add(item["url"])
                        saved += 1
                        print(f"  + n1.ru: {item.get('price_per_m2') or ''} m2, {item.get('price') or ''} total")
                        if saved >= args.max_results_per_lot:
                            break
                    db.commit()
                except Exception as exc:
                    print(f"  n1 failed: {exc}")
            if not args.skip_cian:
                try:
                    for item in fetch_cian_market_evidence(lot, args.max_results_per_lot):
                        if item["relevance"] < args.min_relevance:
                            continue
                        upsert_market_evidence(db, item)
                        seen_urls.add(item["url"])
                        saved += 1
                        print(f"  + cian.ru: {item.get('price_per_m2') or ''} m2, {item.get('price') or ''} total")
                        if saved >= args.max_results_per_lot:
                            break
                    db.commit()
                except Exception as exc:
                    print(f"  cian failed: {exc}")
            if args.skip_search:
                continue
            for query in queries:
                if saved >= args.max_results_per_lot:
                    break
                try:
                    results = search_market(query, args.search_engine)
                except Exception as exc:
                    print(f"  search failed: {query}: {exc}")
                    continue
                for result in results:
                    if saved >= args.max_results_per_lot:
                        break
                    url = result["url"]
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    source = source_from_url(url)
                    if args.only_known_sources and source not in MARKET_SOURCES:
                        continue
                    item = build_market_evidence(lot, query, result, args.fetch_pages)
                    if not item:
                        continue
                    if item["relevance"] < args.min_relevance:
                        continue
                    upsert_market_evidence(db, item)
                    saved += 1
                    print(f"  + {source}: {item.get('price_per_m2') or ''} m2, {item.get('price') or ''} total")
                db.commit()
                time.sleep(args.delay)
    value_command(argparse.Namespace(margin_of_safety=args.margin_of_safety))
    render_command(args)


def fetch_command(args: argparse.Namespace) -> None:
    init_db()
    bookmarks_path = Path(args.bookmarks) if args.bookmarks else default_bookmarks_path()
    links = get_bookmark_links(bookmarks_path, args.limit)
    fetch_links(links, args.use_cache)
    value_command(args)
    print(f"Fetched {len(links)} links into {DB_PATH}")


def fetch_links(links: list[dict[str, str]], use_cache: bool) -> None:
    with sqlite3.connect(DB_PATH) as db:
        for link in links:
            db.execute(
                "insert or ignore into source_links (url,title,folder,created_at) values (?,?,?,?)",
                (link["url"], link["name"], link.get("folder") or " / ".join(BOOKMARK_ROOT), dt.datetime.now().isoformat(timespec="seconds")),
            )
            message_id = message_id_from_url(link["url"])
            raw_path = RAW_DIR / f"{message_id}.json"
            if use_cache and raw_path.exists():
                data = read_json(raw_path)
            else:
                backend_url = FEDRESURS_BACKEND.format(message_id=message_id)
                print(f"fetch {backend_url}")
                data = fetch_json(backend_url, referer=link["url"])
                raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            result_details = collect_result_details(data, link["url"], use_cache)
            message, lots, docs = normalize_message(data, link["url"], raw_path, result_details)
            upsert_message(db, message)
            for lot in lots:
                upsert_lot(db, lot)
            for doc in docs:
                upsert_doc(db, doc)
        db.commit()


def fetch_url_command(args: argparse.Namespace) -> None:
    init_db()
    fetch_links(
        [{"url": args.url, "name": args.title or args.url, "folder": "manual"}],
        args.use_cache,
    )
    value_command(args)
    render_command(args)
    print(f"Fetched URL into {DB_PATH}: {args.url}")


def value_command(args: argparse.Namespace) -> None:
    init_db()
    today = dt.date.today()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        lots = [dict(row) for row in db.execute("select * from lots order by message_number, lot_order")]

        db.execute("delete from price_schedule")
        for lot in lots:
            market_min = market_mid = market_max = target_price = None
            method = "manual_required"
            confidence = "none"
            evidence_count = sources_count = 0
            price_m2_p25 = price_m2_p50 = price_m2_p75 = None
            if lot["asset_type"] == "real_estate" and lot["area_m2"]:
                evidence_rows = [
                    dict(row)
                    for row in db.execute(
                        """
                        select source, price_per_m2
                        from market_evidence
                        where lot_id=? and price_per_m2 is not null and relevance >= 0.45
                        order by relevance desc
                        """,
                        (lot["lot_id"],),
                    )
                ]
                rates = [
                    float(row["price_per_m2"])
                    for row in evidence_rows
                    if row["price_per_m2"] and 10_000 <= float(row["price_per_m2"]) <= 2_000_000
                ]
                evidence_count = len(rates)
                sources_count = len({row["source"] for row in evidence_rows if row.get("source")})
                if evidence_count >= 3:
                    price_m2_p25 = percentile(rates, 0.25)
                    price_m2_p50 = percentile(rates, 0.50)
                    price_m2_p75 = percentile(rates, 0.75)
                    area = float(lot["area_m2"])
                    market_min = price_m2_p25 * area if price_m2_p25 else None
                    market_mid = price_m2_p50 * area if price_m2_p50 else None
                    market_max = price_m2_p75 * area if price_m2_p75 else None
                    method = "market_evidence_price_m2_quantiles_p25_p50_p75"
                    if evidence_count >= 10 and sources_count >= 3:
                        confidence = "high"
                    elif evidence_count >= 6 and sources_count >= 2:
                        confidence = "medium"
                    else:
                        confidence = "low"
            if market_min:
                target_price = market_min * float(args.margin_of_safety)

            trade_type = lot["trade_type"] or ""
            application_end = parse_date(lot.get("application_end"))
            status = "active"
            if application_end and application_end.date() < today and not lot.get("result_status"):
                status = "needs_result_check"
            if lot.get("result_status"):
                status = lot["result_status"]

            decision = "valuation_required"
            interesting_from = interesting_to = None
            current_price = lot["start_price"]

            if trade_type == "OpenedAuction":
                if target_price and current_price and target_price >= current_price:
                    decision = "auction_interesting"
                elif target_price and current_price:
                    decision = "overpriced_skip"
                else:
                    decision = "valuation_required"
            elif trade_type == "PublicOffer":
                periods = schedule_public_offer(
                    lot["lot_id"],
                    lot["start_price"],
                    target_price,
                    lot.get("price_reduction") or "",
                    lot.get("application_begin"),
                    lot.get("application_end"),
                )
                for period in periods:
                    db.execute(
                        "insert into price_schedule (lot_id,period_no,date_from,date_to,price,is_interesting) values (?,?,?,?,?,?)",
                        (
                            lot["lot_id"],
                            period["period_no"],
                            period["date_from"],
                            period["date_to"],
                            period["price"],
                            period["is_interesting"],
                        ),
                    )
                interesting = [period for period in periods if period["is_interesting"]]
                current_period = next(
                    (
                        period
                        for period in periods
                        if dt.date.fromisoformat(period["date_from"]) <= today <= dt.date.fromisoformat(period["date_to"])
                    ),
                    None,
                )
                if current_period:
                    current_price = current_period["price"]
                if interesting:
                    interesting_from = interesting[0]["date_from"]
                    interesting_to = interesting[-1]["date_to"]
                    decision = "public_offer_wait_until_target"
                    if dt.date.fromisoformat(interesting_from) <= today <= dt.date.fromisoformat(interesting_to):
                        decision = "public_offer_price_reached"
                else:
                    decision = "public_offer_no_target_period"

            db.execute(
                """
                update lots set
                    current_price=?, market_min=?, market_mid=?, market_max=?, target_price=?,
                    valuation_method=?, confidence=?, decision=?, status=?,
                    interesting_from=?, interesting_to=?, evidence_count=?, sources_count=?,
                    price_m2_p25=?, price_m2_p50=?, price_m2_p75=?, updated_at=?
                where lot_id=?
                """,
                (
                    round(current_price, 2) if current_price else None,
                    round(market_min, 2) if market_min else None,
                    round(market_mid, 2) if market_mid else None,
                    round(market_max, 2) if market_max else None,
                    round(target_price, 2) if target_price else None,
                    method,
                    confidence,
                    decision,
                    status,
                    interesting_from,
                    interesting_to,
                    evidence_count,
                    sources_count,
                    round(price_m2_p25, 2) if price_m2_p25 else None,
                    round(price_m2_p50, 2) if price_m2_p50 else None,
                    round(price_m2_p75, 2) if price_m2_p75 else None,
                    dt.datetime.now().isoformat(timespec="seconds"),
                    lot["lot_id"],
                ),
            )
        db.commit()


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    return html.unescape(" ".join(text.split()))


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "PDF text extraction unavailable: install pypdf or use manual review."
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages[:10]:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def read_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)
    if suffix in {".txt", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    return "Unsupported document type for text extraction in MVP."


def scan_docs_command(args: argparse.Namespace) -> None:
    init_db()
    scan_dir = Path(args.dir) if args.dir else DOCS_DIR
    scan_dir.mkdir(parents=True, exist_ok=True)
    files = [path for path in scan_dir.rglob("*") if path.is_file()]
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        docs = [dict(row) for row in db.execute("select * from documents")]
        for doc in docs:
            name = doc.get("name")
            if not name:
                continue
            candidates = [path for path in files if path.name.lower() == name.lower()]
            if not candidates:
                continue
            path = candidates[0]
            text = read_document_text(path)[:6000]
            db.execute(
                "update documents set local_path=?, text_excerpt=?, status=?, updated_at=? where doc_guid=?",
                (str(path), text, "loaded", dt.datetime.now().isoformat(timespec="seconds"), doc["doc_guid"]),
            )
        db.commit()
    print(f"Scanned {len(files)} local files in {scan_dir}")


def fmt_money(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def fmt_date(value: Any) -> str:
    parsed = parse_date(str(value)) if value else None
    return parsed.strftime("%d.%m.%Y") if parsed else ""


def interesting_period_text(lot: dict[str, Any]) -> str:
    if lot.get("interesting_from") and lot.get("interesting_to"):
        start = fmt_date(lot["interesting_from"])
        end = fmt_date(lot["interesting_to"])
        if start == end:
            return f"с {start}"
        return f"с {start} по {end}"

    trade_type = lot.get("trade_type") or ""
    decision = lot.get("decision") or ""
    status = lot.get("status") or ""

    if trade_type == "OpenedAuction":
        after = fmt_date(lot.get("auction_datetime")) or fmt_date(lot.get("application_end"))
        if after:
            if status == "needs_result_check":
                return f"после {after}: проверить результат"
            if decision == "auction_interesting":
                return f"после {after}: ждать результат"
            if decision == "overpriced_skip":
                return f"после {after}: только контроль результата"
            return f"после {after}"

    if trade_type == "PublicOffer":
        if decision == "public_offer_no_target_period":
            if lot.get("target_price"):
                return "цель не наступает"
            return "после оценки"
        after = fmt_date(lot.get("application_end"))
        if after:
            return f"после {after}: проверить результат"

    if decision == "valuation_required":
        return "после оценки"
    return ""


def render_calendar_plan(periods: list[dict[str, Any]]) -> str:
    if not periods:
        return '<span class="muted">—</span>'
    parts = []
    for period in periods:
        cls = "stage interesting" if period["is_interesting"] else "stage"
        parts.append(
            f"""
            <li class="{cls}">
              <div class="stage-top">
                <b>Этап {period["period_no"]}</b>
                <span>{html.escape(fmt_date(period["date_from"]))} - {html.escape(fmt_date(period["date_to"]))}</span>
              </div>
              <div class="stage-price">{fmt_money(period["price"])} ₽</div>
              <div class="stage-note">{"интересная цена" if period["is_interesting"] else "выше цели"}</div>
            </li>
            """
        )
    return '<ol class="calendar-plan">' + "".join(parts) + "</ol>"


def has_trade_result(lot: dict[str, Any]) -> bool:
    keys = (
        "result_status",
        "result_message_number",
        "result_date_publish",
        "result_price",
        "result_buyer",
        "result_reason",
    )
    return any(lot.get(key) for key in keys)


def render_trade_result(lot: dict[str, Any]) -> str:
    status = lot.get("result_status")
    message_number = lot.get("result_message_number")
    text = (lot.get("result_text") or "").strip()
    if text.startswith("[") or text.startswith("{"):
        text = ""
    if not status and not message_number and not text:
        return '<span class="muted">—</span>'

    status_label = html.escape(result_status_label(status))
    status_class = html.escape(status or "unknown")
    lines = [f'<div class="result-status {status_class}">{status_label}</div>']

    if message_number:
        url = html.escape(lot.get("result_message_url") or "")
        number = html.escape(str(message_number))
        if url:
            lines.append(f'сообщение: <a href="{url}" target="_blank">{number}</a>')
        else:
            lines.append(f"сообщение: {number}")
    if lot.get("result_date_publish"):
        lines.append(f"опубликовано: {html.escape(str(lot['result_date_publish']))}")
    if lot.get("result_price"):
        lines.append(f"цена: <b>{fmt_money(lot['result_price'])} ₽</b>")
    if lot.get("result_buyer"):
        lines.append(f"покупатель: {html.escape(str(lot['result_buyer']))}")
    if lot.get("result_reason"):
        lines.append(f"причина: {html.escape(str(lot['result_reason']))}")
    if text and not any(lot.get(key) for key in ("result_price", "result_buyer", "result_reason")):
        lines.append(html.escape(text))

    return '<div class="result-box">' + "<br>".join(lines) + "</div>"


def render_command(args: argparse.Namespace) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        lots = [dict(row) for row in db.execute("select * from lots order by decision, application_end, message_number")]
        docs = [dict(row) for row in db.execute("select * from documents order by name")]
        schedules = [dict(row) for row in db.execute("select * from price_schedule order by lot_id, period_no")]

    schedule_by_lot: dict[str, list[dict[str, Any]]] = {}
    for item in schedules:
        schedule_by_lot.setdefault(item["lot_id"], []).append(item)

    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    cards = []
    for lot in lots:
        periods = schedule_by_lot.get(lot["lot_id"], [])
        schedule_html = render_calendar_plan(periods) if periods else ""
        doc_count = sum(1 for doc in docs if doc["message_guid"] == lot["message_guid"])
        interest_text = interesting_period_text(lot)
        decision_raw = lot.get("decision") or ""
        status_raw = lot.get("status") or ""
        decision = html.escape(decision_raw)
        title = html.escape((lot.get("description") or "")[:180])
        if len(lot.get("description") or "") > 180:
            title += "..."
        description = html.escape(lot.get("description") or "")
        address_parts = [
            html.escape(lot.get("address") or ""),
            html.escape(lot.get("cadastral_number") or ""),
            f"{lot.get('area_m2')} м2" if lot.get("area_m2") else "",
        ]
        address_html = "<br>".join(part for part in address_parts if part) or "—"
        price_html = (
            f"старт: {fmt_money(lot.get('start_price')) or '—'}<br>"
            f"текущая: {fmt_money(lot.get('current_price')) or '—'}<br>"
            f"цель: {fmt_money(lot.get('target_price')) or '—'}"
        )
        market_html = (
            f"min: {fmt_money(lot.get('market_min')) or '—'}<br>"
            f"mid: <b>{fmt_money(lot.get('market_mid')) or '—'}</b><br>"
            f"max: {fmt_money(lot.get('market_max')) or '—'}"
        )
        evidence_html = (
            f"аналогов: {lot.get('evidence_count') or 0}<br>"
            f"источников: {lot.get('sources_count') or 0}<br>"
            f"p25: {fmt_money(lot.get('price_m2_p25')) or '—'} руб./м2<br>"
            f"p50: <b>{fmt_money(lot.get('price_m2_p50')) or '—'}</b> руб./м2<br>"
            f"p75: {fmt_money(lot.get('price_m2_p75')) or '—'} руб./м2"
        )
        dates_html = (
            f"начало заявок: {html.escape(lot.get('application_begin') or '—')}<br>"
            f"конец заявок: {html.escape(lot.get('application_end') or '—')}<br>"
            f"торги: {html.escape(lot.get('auction_datetime') or '—')}"
        )
        result_html = render_trade_result(lot)
        result_banner = f'<div class="result-card-top">{result_html}</div>' if has_trade_result(lot) else ""
        schedule_block = schedule_html or '<span class="muted">—</span>'
        cards.append(
            f"""
            <article class="lot-card {decision}" id="lot-{html.escape(lot['lot_id'])}">
              <div class="card-head">
                <div>
                  <a class="message-link" href="{html.escape(lot['source_url'])}" target="_blank">{html.escape(str(lot['message_number']))}</a>
                  <div class="lot-id">{html.escape(lot['lot_id'])}</div>
                </div>
                <div class="badges">
                  <span class="badge">{decision or 'без решения'}</span>
                  <span class="badge light">{html.escape(status_raw or '—')}</span>
                  <span class="badge light">{html.escape(lot.get('confidence') or '—')}</span>
                </div>
              </div>
              <h3>{title or 'Лот без описания'}</h3>
              {result_banner}
              <div class="description">{description or '<span class="muted">—</span>'}</div>
              <div class="card-sections">
                <section class="card-section">
                  <h4>Адрес и объект</h4>
                  <div>{address_html}</div>
                </section>
                <section class="card-section">
                  <h4>Цена</h4>
                  <div>{price_html}</div>
                </section>
                <section class="card-section">
                  <h4>Даты</h4>
                  <div>{dates_html}</div>
                </section>
                <section class="card-section result">
                  <h4>Результат торгов</h4>
                  <div>{result_html}</div>
                </section>
                <section class="card-section important">
                  <h4>Интересный период</h4>
                  <div>{html.escape(interest_text) or '—'}</div>
                </section>
                <section class="card-section">
                  <h4>Оценка рынка</h4>
                  <div>{market_html}</div>
                </section>
                <section class="card-section">
                  <h4>Аналоги</h4>
                  <div>{evidence_html}</div>
                </section>
                <section class="card-section">
                  <h4>Решение</h4>
                  <div><b>{decision or '—'}</b></div>
                </section>
                <section class="card-section">
                  <h4>Документы</h4>
                  <div>{doc_count}</div>
                </section>
                <section class="card-section schedule">
                  <h4>Календарный план</h4>
                  <div>{schedule_block}</div>
                </section>
              </div>
            </article>
            """
        )

    doc_rows = []
    for doc in docs:
        doc_rows.append(
            f"""
            <tr>
              <td>{html.escape(doc.get('name') or '')}</td>
              <td>{html.escape(doc.get('status') or '')}</td>
              <td>{html.escape(doc.get('local_path') or '')}</td>
              <td>{html.escape((doc.get('text_excerpt') or '')[:320])}</td>
            </tr>
            """
        )

    dashboard = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Федресурс MVP</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #1f2933; background: #f6f7f9; }}
    header {{ padding: 18px 24px; background: #1d3557; color: white; }}
    main {{ padding: 18px 24px 40px; }}
    h1 {{ margin: 0 0 6px; font-size: 24px; }}
    h2 {{ margin-top: 26px; }}
    .meta {{ color: #dce7f5; font-size: 13px; }}
    .toolbar {{ display: flex; gap: 12px; align-items: center; margin: 12px 0; }}
    input {{ padding: 9px 10px; min-width: 360px; border: 1px solid #bcc5d1; border-radius: 4px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 14px; align-items: start; }}
    .lot-card {{ background: white; border: 1px solid #d9e0e8; border-left: 5px solid #7b8794; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(20, 35, 50, 0.06); }}
    .lot-card.auction_interesting, .lot-card.public_offer_price_reached {{ border-left-color: #178a4a; background: #f2fbf5; }}
    .lot-card.public_offer_wait_until_target {{ border-left-color: #d49a00; background: #fffaf0; }}
    .lot-card.overpriced_skip {{ border-left-color: #c84646; background: #fff5f5; }}
    .lot-card h3 {{ margin: 10px 0 8px; font-size: 16px; line-height: 1.35; }}
    .card-head {{ display: flex; gap: 12px; justify-content: space-between; align-items: flex-start; }}
    .message-link {{ font-weight: 700; font-size: 15px; }}
    .lot-id {{ margin-top: 3px; color: #667085; font-size: 12px; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }}
    .badge {{ display: inline-flex; align-items: center; min-height: 22px; padding: 2px 7px; border-radius: 999px; background: #1d3557; color: white; font-size: 11px; line-height: 1.2; }}
    .badge.light {{ background: #eef2f6; color: #344054; }}
    .description {{ margin: 8px 0 12px; color: #344054; font-size: 13px; line-height: 1.45; }}
    .result-card-top {{ margin: 8px 0 12px; }}
    .card-sections {{ display: grid; gap: 10px; }}
    .card-section {{ padding: 10px 0 0; border-top: 1px solid #e5eaf0; }}
    .card-section:first-child {{ border-top: 0; padding-top: 0; }}
    .card-section h4 {{ margin: 0 0 5px; color: #667085; font-size: 12px; line-height: 1.25; font-weight: 700; }}
    .card-section div {{ min-width: 0; font-size: 13px; line-height: 1.45; overflow-wrap: anywhere; }}
    .card-section.important div {{ font-weight: 700; color: #0f5132; }}
    .result-box {{ padding: 8px 9px; border: 1px solid #d9e0e8; border-radius: 6px; background: #f8fafc; }}
    .result-status {{ display: inline-flex; margin-bottom: 4px; padding: 2px 7px; border-radius: 999px; background: #eef2f6; color: #344054; font-weight: 700; }}
    .result-status.sold {{ background: #d8f5df; color: #11613a; }}
    .result-status.failed, .result-status.cancelled {{ background: #ffe0e0; color: #9f1f1f; }}
    .result-status.suspended {{ background: #fff0c2; color: #8a5b00; }}
    .calendar-plan {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 7px; }}
    .stage {{ border: 1px solid #d9e0e8; border-radius: 6px; padding: 7px 8px; background: #f8fafc; }}
    .stage.interesting {{ border-color: #8bd3a4; background: #ebf8ef; }}
    .stage-top {{ display: flex; justify-content: space-between; gap: 10px; color: #344054; }}
    .stage-top span {{ color: #667085; white-space: nowrap; }}
    .stage-price {{ margin-top: 4px; font-size: 15px; font-weight: 700; }}
    .stage-note {{ margin-top: 2px; color: #667085; font-size: 12px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; font-size: 13px; }}
    th, td {{ border: 1px solid #d9e0e8; padding: 8px; vertical-align: top; }}
    th {{ background: #e9eef5; position: sticky; top: 0; z-index: 1; }}
    .good {{ display: inline-block; padding: 2px 4px; background: #c7f0d4; border-radius: 3px; }}
    .muted {{ color: #8792a2; }}
    a {{ color: #0b5cad; }}
    @media (max-width: 760px) {{
      main {{ padding: 14px; }}
      input {{ min-width: 0; width: 100%; }}
      .toolbar {{ align-items: stretch; flex-direction: column; }}
      .cards {{ grid-template-columns: 1fr; }}
      .field {{ grid-template-columns: 1fr; gap: 3px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Федресурс MVP</h1>
    <div class="meta">Сгенерировано: {html.escape(generated_at)}. Оценка строится по market_evidence: p25 / p50 / p75; если аналогов мало, лот уходит в valuation_required.</div>
  </header>
  <main>
    <div class="toolbar">
      <input id="q" placeholder="Фильтр по тексту, адресу, решению, номеру">
      <span>Лотов: {len(lots)} | Документов: {len(docs)}</span>
    </div>
    <h2>Лоты</h2>
    <section id="lots" class="cards">
      {''.join(cards)}
    </section>
    <h2>Документы</h2>
    <p>Кладите вручную скачанные PDF/DOCX в <code>{html.escape(str(DOCS_DIR))}</code>, затем запускайте <code>python fedresurs_mvp.py scan-docs</code>.</p>
    <table>
      <thead><tr><th>Файл</th><th>Статус</th><th>Локальный путь</th><th>Извлеченный текст</th></tr></thead>
      <tbody>{''.join(doc_rows)}</tbody>
    </table>
  </main>
  <script>
    const q = document.getElementById('q');
    q.addEventListener('input', () => {{
      const value = q.value.toLowerCase();
      document.querySelectorAll('.lot-card').forEach(card => {{
        card.style.display = card.innerText.toLowerCase().includes(value) ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>
"""
    out_path = REPORTS_DIR / "dashboard.html"
    out_path.write_text(dashboard, encoding="utf-8")
    print(out_path)


def all_command(args: argparse.Namespace) -> None:
    fetch_command(args)
    scan_docs_command(argparse.Namespace(dir=str(DOCS_DIR)))
    render_command(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fedresurs auction monitor MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--bookmarks", help="Path to Chrome Bookmarks file")
        p.add_argument("--limit", type=int, default=15, help="Number of bookmark links to process")
        p.add_argument("--use-cache", action="store_true", help="Use cached raw JSON files")
        p.add_argument("--margin-of-safety", type=float, default=0.90, help="Target buy price = market_min * margin")

    p_fetch = sub.add_parser("fetch", help="Read bookmarks, fetch Fedresurs JSON, fill SQLite")
    common(p_fetch)
    p_fetch.set_defaults(func=fetch_command)

    p_fetch_url = sub.add_parser("fetch-url", help="Fetch one Fedresurs URL, fill SQLite, render dashboard")
    p_fetch_url.add_argument("url", help="Fedresurs bankruptmessages URL")
    p_fetch_url.add_argument("--title", help="Optional source title")
    p_fetch_url.add_argument("--use-cache", action="store_true", help="Use cached raw JSON file")
    p_fetch_url.add_argument("--margin-of-safety", type=float, default=0.90)
    p_fetch_url.set_defaults(func=fetch_url_command)

    p_value = sub.add_parser("value", help="Recalculate MVP valuations and decisions")
    p_value.add_argument("--margin-of-safety", type=float, default=0.90)
    p_value.set_defaults(func=value_command)

    p_market = sub.add_parser("fetch-market", help="Search web for market comparables and recalculate valuation")
    p_market.add_argument("--limit", type=int, default=15, help="Number of loaded real estate lots to process")
    p_market.add_argument("--max-results-per-lot", type=int, default=8, help="Max priced evidence rows to save per lot")
    p_market.add_argument("--min-relevance", type=float, default=0.45, help="Minimum relevance score for evidence")
    p_market.add_argument("--fetch-pages", action="store_true", help="Also fetch source pages, slower and more likely to be blocked")
    p_market.add_argument("--only-known-sources", action="store_true", help="Keep only known real-estate sources")
    p_market.add_argument("--skip-n1", action="store_true", help="Disable direct N1 area-range fetcher")
    p_market.add_argument("--skip-cian", action="store_true", help="Disable direct CIAN area-range fetcher")
    p_market.add_argument("--skip-search", action="store_true", help="Disable generic search engine fallback")
    p_market.add_argument("--search-engine", choices=("bing", "duckduckgo"), default="bing", help="Search backend for market evidence")
    p_market.add_argument("--query-mode", choices=("broad", "exact"), default="broad", help="broad avoids exact addresses/cadastral numbers; exact is more useful but sends sensitive lot data to search")
    p_market.add_argument("--clear", action="store_true", help="Clear old market evidence for selected lots first")
    p_market.add_argument("--delay", type=float, default=1.0, help="Delay between search queries")
    p_market.add_argument("--margin-of-safety", type=float, default=0.90)
    p_market.set_defaults(func=fetch_market_command)

    p_docs = sub.add_parser("scan-docs", help="Read manually downloaded documents from data/documents")
    p_docs.add_argument("--dir", help="Directory with downloaded documents")
    p_docs.set_defaults(func=scan_docs_command)

    p_render = sub.add_parser("render", help="Render HTML dashboard")
    p_render.set_defaults(func=render_command)

    p_all = sub.add_parser("all", help="Run fetch, scan-docs, render")
    common(p_all)
    p_all.set_defaults(func=all_command)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
