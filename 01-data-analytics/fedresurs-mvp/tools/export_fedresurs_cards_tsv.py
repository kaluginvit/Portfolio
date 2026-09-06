#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sqlite3
import urllib.request
from pathlib import Path
from typing import Any


FEDRESURS_BACKEND = "https://fedresurs.ru/backend/bankruptcy-messages/{message_id}"


def fmt_money(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return str(value)


def parse_date(value: Any) -> dt.datetime | None:
    if not value:
        return None
    text = str(value)
    for pattern in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(text[: len(pattern)], pattern)
        except ValueError:
            pass
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        return None


def fmt_date(value: Any) -> str:
    parsed = parse_date(value)
    return parsed.strftime("%d.%m.%Y") if parsed else ""


def iso_date(value: dt.datetime | None) -> str:
    if not value:
        return ""
    return value.isoformat(timespec="minutes")


def parse_ru_datetime(text: str) -> dt.datetime | None:
    patterns = [
        r"(?P<time>\d{1,2})[:\-](?P<minute>\d{2})\s*(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4})\D{0,18}(?P<time>\d{1,2})[:\-](?P<minute>\d{2})",
        r"(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        day, month, year = [int(part) for part in re.split(r"[./]", match.group("date"))]
        if year < 100:
            year += 2000
        hour = int(match.groupdict().get("time") or 0)
        minute = int(match.groupdict().get("minute") or 0)
        try:
            return dt.datetime(year, month, day, hour, minute)
        except ValueError:
            continue
    return None


def raw_text_for_dates(raw_path: str) -> str:
    data = load_raw_data(raw_path)
    if not data:
        return ""
    return text_for_dates_from_data(data)


def load_raw_data(raw_path: str) -> dict[str, Any]:
    if not raw_path:
        return {}
    try:
        return json.loads(Path(raw_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def text_for_dates_from_data(data: dict[str, Any]) -> str:
    content = data.get("content") or {}
    message_info = content.get("messageInfo") or {}
    message_content = message_info.get("messageContent") or {}
    application = message_content.get("application") or {}
    parts = [
        message_content.get("text") or "",
        message_content.get("additionalText") or "",
        application.get("rules") or "",
    ]
    for lot in message_content.get("lotTable") or []:
        if isinstance(lot, dict):
            parts.append(lot.get("priceReduction") or "")
    return "\n".join(str(part) for part in parts if part)


def message_id_from_guid(guid: Any) -> str:
    return str(guid or "").upper().replace("-", "")


def fetch_raw_message(message_id: str, raw_dir: Path, referer: str = "") -> dict[str, Any]:
    raw_path = raw_dir / f"{message_id}.json"
    if raw_path.exists():
        return load_raw_data(str(raw_path))
    request = urllib.request.Request(
        FEDRESURS_BACKEND.format(message_id=message_id),
        headers={
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0",
            **({"Referer": referer} if referer else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def fedresurs_datetime(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("dateTime") or value.get("date")
    parsed = parse_date(value)
    return iso_date(parsed) if parsed else ""


def structured_dates(data: dict[str, Any]) -> dict[str, str]:
    content = data.get("content") or {}
    message_info = content.get("messageInfo") or {}
    message_content = message_info.get("messageContent") or {}
    application = message_content.get("application") or {}
    return {
        "trade_type": str(message_content.get("tradeType") or ""),
        "application_begin": fedresurs_datetime(application.get("dateTimeBegin")),
        "application_end": fedresurs_datetime(application.get("dateTimeEnd")),
        "auction_datetime": fedresurs_datetime(message_content.get("auctionDateTime")),
    }


def linked_auction_dates(raw_path: str, raw_dir: Path, referer: str) -> dict[str, str]:
    data = load_raw_data(raw_path)
    if not data:
        return {}
    for linked in data.get("linkedMessages") or []:
        if not isinstance(linked, dict):
            continue
        linked_type = str(linked.get("type") or "").lower()
        linked_type_name = str(linked.get("typeName") or "").lower()
        if not (
            "auction" in linked_type
            or "торг" in linked_type_name
            or "сообщение о продаже" in linked_type_name
        ):
            continue
        message_id = message_id_from_guid(linked.get("guid"))
        if not message_id:
            continue
        try:
            linked_data = fetch_raw_message(message_id, raw_dir, referer)
        except Exception:
            continue
        dates = structured_dates(linked_data)
        if not dates.get("application_end"):
            dates["application_end"] = infer_application_end(
                text_for_dates_from_data(linked_data),
                dates.get("application_begin"),
            )
        if not dates.get("auction_datetime"):
            dates["auction_datetime"] = trade_display(
                {
                    "trade_type": dates.get("trade_type"),
                    "application_begin": dates.get("application_begin"),
                },
                dates.get("application_end") or "",
            )
        return dates
    return {}


def add_workdays(day: dt.date, count: int) -> dt.date:
    current = day
    added = 0
    while added < count:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def dates_in_text(text: str, begin: dt.datetime | None = None) -> list[dt.datetime]:
    found: list[dt.datetime] = []
    for match in re.finditer(r"\d{1,2}[./]\d{1,2}[./]\d{2,4}", text):
        parsed = parse_ru_datetime(text[max(0, match.start() - 25) : min(len(text), match.end() + 25)])
        if parsed and (not begin or parsed >= begin):
            found.append(parsed)
    return found


def infer_end_from_price_reduction(text: str, application_begin: Any) -> str:
    begin = parse_date(application_begin)
    if not begin or not text:
        return ""

    explicit_dates = dates_in_text(text, begin)
    if explicit_dates:
        return iso_date(max(explicit_dates))

    duration_match = re.search(
        r"(\d+)\s*(?:\([^)]*\)\s*)?(?:(рабоч|календар)\w*\s+)?дн",
        text,
        flags=re.IGNORECASE,
    )
    if not duration_match:
        return ""

    period_days = int(duration_match.group(1))
    is_workday = "рабоч" in (duration_match.group(2) or "").lower()
    counts = [
        int(match.group(1))
        for match in re.finditer(r"количеств\w*\s+период\w*\D{0,20}(\d+)", text, flags=re.IGNORECASE)
    ]
    price_count = len(re.findall(r"\d[\d\s]*(?:[,.]\d{2})?\s*руб", text, flags=re.IGNORECASE))

    if counts:
        periods = sum(counts)
        if "последн" in text.lower():
            periods += 1
    elif price_count >= 2:
        periods = price_count
    else:
        periods = 1

    total_days = max(1, period_days * periods)
    if is_workday:
        end_date = add_workdays(begin.date(), total_days)
    else:
        end_date = begin.date() + dt.timedelta(days=total_days)
    return iso_date(dt.datetime.combine(end_date, begin.time()))


def infer_application_end(raw_text: str, application_begin: Any) -> str:
    begin = parse_date(application_begin)
    if not raw_text:
        return ""
    candidates: list[tuple[int, dt.datetime]] = []
    for match in re.finditer(r"\d{1,2}[./]\d{1,2}[./]\d{2,4}", raw_text):
        start = max(0, match.start() - 140)
        end = min(len(raw_text), match.end() + 80)
        context = raw_text[start:end].lower()
        if "заяв" not in context:
            continue
        parsed = parse_ru_datetime(raw_text[max(0, match.start() - 25) : min(len(raw_text), match.end() + 25)])
        if not parsed:
            continue
        if begin and parsed < begin:
            continue
        score = 0
        if "оконча" in context or "окончан" in context or "заверш" in context:
            score += 8
        if "прием" in context or "приём" in context or "подач" in context:
            score += 3
        if "до " in context or "по " in context:
            score += 2
        if score:
            candidates.append((score, parsed))
    if not candidates:
        return infer_end_from_price_reduction(raw_text, application_begin)
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return iso_date(candidates[0][1])


def trade_display(lot: dict[str, Any], application_end: str, application_begin: str | None = None) -> str:
    auction_datetime = lot.get("auction_datetime") or ""
    if auction_datetime:
        return str(auction_datetime)
    begin = application_begin if application_begin is not None else lot.get("application_begin") or ""
    if lot.get("trade_type") == "PublicOffer":
        if begin and application_end:
            return f"с {begin} по {application_end}"
        if begin:
            return f"с {begin}"
        if application_end:
            return f"по {application_end}"
    if begin and application_end:
        return f"с {begin} по {application_end}"
    return begin or application_end


def result_label(value: str | None) -> str:
    return {
        "sold": "Продано",
        "failed": "Торги не состоялись",
        "cancelled": "Отменено",
        "suspended": "Приостановлено",
    }.get(value or "", value or "")


def interesting_period(lot: dict[str, Any]) -> str:
    if lot.get("interesting_from") and lot.get("interesting_to"):
        start = fmt_date(lot["interesting_from"])
        end = fmt_date(lot["interesting_to"])
        return f"с {start}" if start == end else f"с {start} по {end}"

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
            return "цель не наступает" if lot.get("target_price") else "после оценки"
        after = fmt_date(lot.get("application_end"))
        if after:
            return f"после {after}: проверить результат"
    if decision == "valuation_required":
        return "после оценки"
    return ""


def norm_url(url: str) -> str:
    return (url or "").strip().replace("http://", "https://")


def old_to_new(url: str) -> str:
    if "old.bankrot.fedresurs.ru/MessageWindow.aspx" not in url:
        return norm_url(url)
    match = re.search(r"[?&]ID=([0-9A-Fa-f-]{32,36})", url)
    if not match:
        return norm_url(url)
    return "https://fedresurs.ru/bankruptmessages/" + match.group(1).upper().replace("-", "")


def walk_bookmarks(node: dict[str, Any], trail: list[str], out: dict[str, str]) -> None:
    if node.get("type") == "url":
        out[old_to_new(node.get("url") or "")] = " / ".join(trail)
        return
    if node.get("type") == "folder":
        trail = trail + [node.get("name") or ""]
    for child in node.get("children") or []:
        if isinstance(child, dict):
            walk_bookmarks(child, trail, out)


def folder_name(path: str) -> str:
    marker = "Объявления о торгах / "
    if marker in path:
        return path.split(marker, 1)[1]
    if path.endswith("Объявления о торгах"):
        return "Объявления о торгах"
    return path


def main() -> int:
    base_dir = Path(r"C:\_Рабочая_папка\Федресурс")
    db_path = base_dir / "data" / "fedresurs.sqlite3"
    raw_dir = db_path.parent / "raw"
    bookmarks_path = Path(r"C:\Users\Виталий\AppData\Local\Google\Chrome\User Data\Default\Bookmarks")
    out_path = base_dir / "fedresurs_cards_export.tsv"

    bookmarks = json.loads(bookmarks_path.read_text(encoding="utf-8"))
    folder_by_url: dict[str, str] = {}
    for root in (bookmarks.get("roots") or {}).values():
        if isinstance(root, dict):
            walk_bookmarks(root, [], folder_by_url)

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        lots = [
            dict(row)
            for row in db.execute(
                """
                select lots.*, messages.raw_json_path
                from lots
                left join messages on messages.guid = lots.message_guid
                order by lots.decision, lots.application_end, lots.message_number, lots.lot_order
                """
            )
        ]
        doc_counts = {
            row["message_guid"]: row["cnt"]
            for row in db.execute("select message_guid, count(*) cnt from documents group by message_guid")
        }
        schedules: dict[str, list[dict[str, Any]]] = {}
        for row in db.execute("select * from price_schedule order by lot_id, period_no"):
            item = dict(row)
            schedules.setdefault(item["lot_id"], []).append(item)

    headers = [
        "Папка",
        "Сообщение",
        "Лот",
        "Ссылка",
        "Описание",
        "Адрес",
        "Кадастровый номер",
        "Площадь м2",
        "Стартовая цена",
        "Начало заявок",
        "Конец заявок",
        "Торги",
        "Порядок снижения цены",
        "Результат торгов",
        "Сообщение результата",
        "Ссылка результата",
        "Дата результата",
        "Цена результата",
        "Покупатель",
        "Причина результата",
        "Документы",
    ]
    rows: list[list[Any]] = []
    raw_text_cache: dict[str, str] = {}
    linked_dates_cache: dict[str, dict[str, str]] = {}
    for lot in lots:
        url = norm_url(lot.get("source_url") or "")
        raw_path = lot.get("raw_json_path") or ""
        if raw_path not in raw_text_cache:
            raw_text_cache[raw_path] = raw_text_for_dates(raw_path)
        if raw_path not in linked_dates_cache:
            linked_dates_cache[raw_path] = linked_auction_dates(raw_path, raw_dir, url)
        linked_dates = linked_dates_cache.get(raw_path, {})
        application_begin = lot.get("application_begin") or linked_dates.get("application_begin") or ""
        application_end = lot.get("application_end") or linked_dates.get("application_end") or infer_application_end(
            raw_text_cache.get(raw_path, ""),
            application_begin,
        )
        trade_value = lot.get("auction_datetime") or linked_dates.get("auction_datetime") or trade_display(
            lot,
            application_end,
            application_begin,
        )
        plan = []
        for period in schedules.get(lot["lot_id"], []):
            mark = "интересно" if period.get("is_interesting") else "выше цели"
            plan.append(
                f"Этап {period.get('period_no')}: {fmt_date(period.get('date_from'))}-{fmt_date(period.get('date_to'))}, "
                f"{fmt_money(period.get('price'))} руб., {mark}"
            )
        result_parts = []
        if lot.get("result_status"):
            result_parts.append(result_label(lot.get("result_status")))
        if lot.get("result_price"):
            result_parts.append("цена " + fmt_money(lot.get("result_price")))
        if lot.get("result_buyer"):
            result_parts.append("покупатель: " + str(lot.get("result_buyer")))
        if lot.get("result_reason"):
            result_parts.append("причина: " + str(lot.get("result_reason")))
        rows.append(
            [
                folder_name(folder_by_url.get(url) or ""),
                lot.get("message_number") or "",
                lot.get("lot_id") or "",
                url,
                lot.get("description") or "",
                lot.get("address") or "",
                lot.get("cadastral_number") or "",
                lot.get("area_m2") or "",
                fmt_money(lot.get("start_price")),
                application_begin,
                application_end,
                trade_value,
                lot.get("price_reduction") or "",
                "; ".join(result_parts),
                lot.get("result_message_number") or "",
                lot.get("result_message_url") or "",
                lot.get("result_date_publish") or "",
                fmt_money(lot.get("result_price")),
                lot.get("result_buyer") or "",
                lot.get("result_reason") or "",
                doc_counts.get(lot.get("message_guid"), 0),
            ]
        )

    with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(
            [
                [str(cell).replace("\r", " ").replace("\n", " | ") for cell in row]
                for row in rows
            ]
        )

    print(out_path)
    print(f"rows={len(rows)} cols={len(headers)}")
    print("folders=" + ", ".join(sorted({str(row[0]) for row in rows})))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
