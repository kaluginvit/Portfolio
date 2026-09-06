#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import html
import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(r"C:\_Рабочая_папка\Федресурс")
TSV_PATH = BASE_DIR / "fedresurs_cards_export.tsv"
OUT_PATH = BASE_DIR / "reports" / "dashboard.html"
DB_PATH = BASE_DIR / "data" / "fedresurs.sqlite3"


DIRECT_FIELDS = [
    "Сообщение",
    "Лот",
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
    "Дата результата",
    "Цена результата",
    "Покупатель",
    "Причина результата",
    "Документы",
]


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())


def esc(value: object) -> str:
    return html.escape(clean(value), quote=True)


def money(value: str) -> str:
    raw = clean(value)
    if not raw:
        return "—"
    digits = "".join(ch for ch in raw if ch.isdigit() or ch in ",.-")
    try:
        amount = float(digits.replace(" ", "").replace(",", "."))
    except ValueError:
        return esc(raw)
    return f"{amount:,.0f}".replace(",", " ") + " ₽"


def date_value(value: str) -> str:
    raw = clean(value)
    if not raw:
        return "—"
    for pattern, size in (("%Y-%m-%dT%H:%M:%S", 19), ("%Y-%m-%dT%H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            parsed = dt.datetime.strptime(raw[:size], pattern)
            if parsed.time() == dt.time():
                return parsed.strftime("%d.%m.%Y")
            return parsed.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            pass
    return esc(raw)


def parse_date(value: str) -> dt.datetime | None:
    raw = clean(value)
    if not raw:
        return None
    for pattern, size in (("%Y-%m-%dT%H:%M:%S", 19), ("%Y-%m-%dT%H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return dt.datetime.strptime(raw[:size], pattern)
        except ValueError:
            pass
    return None


def money_number(value: str) -> float | None:
    raw = clean(value)
    if not raw:
        return None
    normalized = raw.replace("\xa0", " ")
    normalized = re.sub(r"[^\d,.\-]", "", normalized)
    if not normalized:
        return None
    try:
        return float(normalized.replace(",", "."))
    except ValueError:
        return None


def money_from_text(value: str) -> float | None:
    text = clean(value).lower()
    match = re.search(r"(-?\d[\d\s]*(?:[,.]\d{1,2})?)", text)
    if not match:
        return None
    raw = match.group(1).replace(" ", "")
    if "," in raw:
        head, tail = raw.rsplit(",", 1)
        raw = head + "." + tail
    try:
        return float(raw)
    except ValueError:
        return None


def percent_number(value: str) -> float | None:
    match = re.search(r"(\d+(?:[,.]\d+)?)", value)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def iso_date(day: dt.date, time_value: dt.time | None = None) -> str:
    return dt.datetime.combine(day, time_value or dt.time()).isoformat(timespec="minutes")


def date_part(value: str) -> str:
    parsed = parse_date(value)
    return parsed.strftime("%d.%m.%Y") if parsed else "—"


def time_part(value: str, fallback: str = "") -> str:
    parsed = parse_date(value)
    if not parsed:
        return fallback or "—"
    return parsed.strftime("%H:%M")


def trade_type_label(value: str) -> str:
    return {
        "OpenedAuction": "Аукцион",
        "ClosedAuction": "Закрытый аукцион",
        "PublicOffer": "Публичное предложение",
    }.get(clean(value), clean(value) or "—")


def field_value(name: str, row: dict[str, str]) -> str:
    value = row.get(name, "")
    if name in {"Стартовая цена", "Цена результата"}:
        return money(value)
    if name in {"Начало заявок", "Конец заявок", "Торги", "Дата результата"}:
        return date_value(value)
    return esc(value) or "—"


def action_link(url: str, label: str, primary: bool = False) -> str:
    if not clean(url):
        return ""
    class_name = " action-primary" if primary else ""
    return f'<a class="action{class_name}" href="{esc(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>'


def title_from_row(row: dict[str, str]) -> str:
    description = clean(row.get("Описание", ""))
    if not description:
        return "Без описания"
    if len(description) <= 180:
        return description
    return description[:177].rstrip() + "..."


def dl(fields: list[str], row: dict[str, str]) -> str:
    items = []
    for name in fields:
        items.append(
            f"""
            <div class="field">
              <dt>{html.escape(name)}</dt>
              <dd>{field_value(name, row)}</dd>
            </div>
            """
        )
    return "<dl>" + "".join(items) + "</dl>"


def load_lot_meta() -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    if not DB_PATH.exists():
        return {}, {}
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        meta = {
            row["lot_id"]: {
                "trade_type": row["trade_type"] or "",
                "asset_type": row["asset_type"] or "",
                "message_type": row["message_type"] or "",
            }
            for row in db.execute(
                """
                select lots.lot_id, lots.trade_type, lots.asset_type, messages.message_type
                from lots
                left join messages on messages.guid = lots.message_guid
                """
            )
        }
        schedules: dict[str, list[dict[str, str]]] = {}
        for row in db.execute("select * from price_schedule order by lot_id, period_no"):
            item = dict(row)
            schedules.setdefault(item["lot_id"], []).append(item)
    return meta, schedules


def add_days(day: dt.date, count: int) -> dt.date:
    return day + dt.timedelta(days=count)


def add_workdays(day: dt.date, count: int) -> dt.date:
    current = day
    added = 0
    while added < count:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def period_info(text: str) -> tuple[int, bool]:
    lowered = clean(text).lower()
    patterns = [
        r"срок[^.]{0,80}?составляет[^.]{0,20}?(\d+)[^.]{0,25}?(рабоч|раб\.|календар)?\w*\.?\s*дн",
        r"кажд\w*[^.]{0,30}?(\d+)[^.]{0,25}?(рабоч|раб\.|календар)?\w*\.?\s*дн",
        r"период\w*[^.]{0,60}?(\d+)[^.]{0,25}?(рабоч|раб\.|календар)?\w*\.?\s*дн",
        r"(\d+)\s*(?:\([^)]*\)\s*)?(рабоч|раб\.|календар)?\w*\.?\s*дн",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return max(1, int(match.group(1))), "рабоч" in (match.group(2) or "")
    return 5, False


def initial_period_days(text: str) -> int | None:
    lowered = clean(text).lower()
    patterns = [
        r"срок\s+действ\w*\s+начальн\w*\s+цен\w*[^.]{0,40}?(\d+)[^.]{0,25}?дн",
        r"первоначальн\w*\s+цен\w*[^.]{0,40}?действ\w*[^.]{0,40}?(\d+)[^.]{0,25}?дн",
        r"начальн\w*\s+цен\w*[^.]{0,40}?действ\w*[^.]{0,40}?(\d+)[^.]{0,25}?дн",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return max(1, int(match.group(1)))
    return None


def initial_period_is_workday(text: str) -> bool:
    lowered = clean(text).lower()
    match = re.search(r"срок\s+действ\w*\s+начальн\w*\s+цен\w*[^.]{0,80}?рабоч", lowered)
    return bool(match)


def described_stage_count(text: str) -> int:
    lowered = clean(text).lower()
    counts = [int(value) for value in re.findall(r"количеств\w*\s+сниж\w*[^.]{0,30}?(\d+)\s*раз", lowered)]
    if not counts:
        return 0
    total = 1 + sum(counts)
    if "последующ" in lowered or re.search(r"на\s+\d+(?:[,.]\d+)?\s*%\s+от", lowered):
        total += 2
    return total


def stage_count(begin: dt.datetime, end: dt.datetime, period_days: int, first_days: int | None = None) -> int:
    days = max(1, (end.date() - begin.date()).days + 1)
    if first_days and first_days < days:
        return 1 + ((days - first_days + period_days - 1) // period_days)
    return max(1, (days + period_days - 1) // period_days)


def lot_no_from_id(lot_id: str) -> int | None:
    match = re.search(r"-(\d+)$", clean(lot_id))
    return int(match.group(1)) if match else None


def cutoff_price(text: str, start_price: float, lot_no: int | None = None) -> float | None:
    lowered = clean(text).lower()
    if lot_no is not None:
        lot_price_match = re.search(
            rf"(?:минимальн|цена отсечения|нижн\w*\s+предел)[^.]*?для\s+лота\s+{lot_no}\s+составляет\s+(\d+(?:[,.]\d+)?)\s*%",
            lowered,
        )
        if lot_price_match:
            percent = percent_number(lot_price_match.group(1))
            if percent is not None:
                return start_price * percent / 100
    final_period_match = re.search(r"последн\w*\s+период\w*[^.]{0,80}?(\d+(?:[,.]\d+)?)\s*%\s+от\s+нач", lowered)
    if final_period_match:
        percent = percent_number(final_period_match.group(1))
        if percent is not None:
            return start_price * percent / 100
    not_less_match = re.search(r"не\s+менее\s+(\d+(?:[,.]\d+)?)\s*%\s+нач", lowered)
    if not_less_match:
        percent = percent_number(not_less_match.group(1))
        if percent is not None:
            return start_price * percent / 100
    price_match = re.search(r"(?:минимальн|цена отсечения|нижн\w*\s+предел)[^.]{0,120}?(\d[\d\s]*(?:[,.]\d{1,2})?)\s*руб", lowered)
    if price_match:
        return money_from_text(price_match.group(1))
    percent_match = re.search(r"(?:минимальн|цена отсечения|нижн\w*\s+предел)[^.]{0,120}?(\d+(?:[,.]\d+)?)\s*%", lowered)
    if percent_match:
        percent = percent_number(percent_match.group(1))
        if percent is not None:
            return start_price * percent / 100
    return None


def explicit_table_schedule(text: str) -> list[dict[str, object]]:
    stages = []
    pipe_table_pattern = re.compile(
        r"(?:^|\|)\s*(\d{1,3})\s*\|\s*"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)\s*\|\s*"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)\s*\|\s*"
        r"(\d[\d\s]*(?:[,.]\d{1,2})?)",
    )
    inline_period_pattern = re.compile(
        r"(?:^|\|)\s*(\d{1,3})\.?\s*с\s*"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)\s*по\s*"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)"
        r"[^|]{0,180}?(?:цен\w*|стоимост\w*)\s+(\d[\d\s]*(?:[,.]\d{1,2})?)\s*(?:₽|руб)",
        re.IGNORECASE,
    )
    time_first_pattern = re.compile(
        r"(?:^|\|)\s*(\d{1,3})?\.?\s*с\s*"
        r"(\d{2}:\d{2}(?::\d{2})?)\s+(\d{2}\.\d{2}\.\d{4})\s*по\s*"
        r"(\d{2}:\d{2}(?::\d{2})?)\s+(\d{2}\.\d{2}\.\d{4})\s*[-–]\s*"
        r"(\d[\d\s]*(?:[,.]\d{1,2})?)\s*(?:₽|руб)",
        re.IGNORECASE,
    )
    compact_row_pattern = re.compile(
        r"(?:^|\|)\s*(\d{1,3})\s+"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)\s+"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)\s+"
        r"(\d[\d\s]*(?:[,.]\d{1,2})?)",
        re.IGNORECASE,
    )
    iso_range_pattern = re.compile(
        r"(?:^|\|)\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)\s*[-–]\s*"
        r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)\s*[-–]\s*"
        r"(\d[\d\s]*(?:[,.]\d{1,2})?)\s*(?:₽|руб)",
        re.IGNORECASE,
    )
    russian_time_pattern = re.compile(
        r"(?:^|\||,)\s*(?:(?:цен\w*\s+)?в\s+периоде\s+)?с\s*"
        r"(\d{1,2})\s*час\w*\.?\s*(\d{1,2})\s*мин\w*\.?\s*(\d{2}\.\d{2}\.\d{4})\s*по\s*"
        r"(\d{1,2})\s*час\w*\.?\s*(\d{1,2})\s*мин\w*\.?\s*(\d{2}\.\d{2}\.\d{4})"
        r"[^|,]{0,80}?составляет\s+(\d[\d\s]*(?:[,.]\d{1,2})?)\s*(?:₽|руб)",
        re.IGNORECASE,
    )
    date_only_range_pattern = re.compile(
        r"(?:^|\|)\s*(\d{2}\.\d{2}\.\d{4})\s*[-–]\s*(\d{2}\.\d{2}\.\d{4})\s+"
        r"(\d[\d\s]*(?:[,.]\d{1,2})?)",
        re.IGNORECASE,
    )
    for pattern in (pipe_table_pattern, inline_period_pattern, compact_row_pattern):
        for match in pattern.finditer(text):
            start = dt.datetime.strptime(match.group(2) + " " + match.group(3)[:5], "%d.%m.%Y %H:%M")
            end = dt.datetime.strptime(match.group(4) + " " + match.group(5)[:5], "%d.%m.%Y %H:%M")
            stages.append(
                {
                    "period_no": int(match.group(1)),
                    "date_from": start.isoformat(timespec="minutes"),
                    "date_to": end.isoformat(timespec="minutes"),
                    "price": money_from_text(match.group(6)),
                }
            )
    next_period_no = len(stages) + 1
    for match in time_first_pattern.finditer(text):
        start = dt.datetime.strptime(match.group(3) + " " + match.group(2)[:5], "%d.%m.%Y %H:%M")
        end = dt.datetime.strptime(match.group(5) + " " + match.group(4)[:5], "%d.%m.%Y %H:%M")
        stages.append(
            {
                "period_no": int(match.group(1)) if match.group(1) else next_period_no,
                "date_from": start.isoformat(timespec="minutes"),
                "date_to": end.isoformat(timespec="minutes"),
                "price": money_from_text(match.group(6)),
            }
        )
        next_period_no += 1
    for match in iso_range_pattern.finditer(text):
        start = dt.datetime.strptime(match.group(1) + " " + match.group(2)[:5], "%Y-%m-%d %H:%M")
        end = dt.datetime.strptime(match.group(3) + " " + match.group(4)[:5], "%Y-%m-%d %H:%M")
        stages.append(
            {
                "period_no": next_period_no,
                "date_from": start.isoformat(timespec="minutes"),
                "date_to": end.isoformat(timespec="minutes"),
                "price": money_from_text(match.group(5)),
            }
        )
        next_period_no += 1
    for match in russian_time_pattern.finditer(text):
        start_time = f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"
        end_time = f"{int(match.group(4)):02d}:{int(match.group(5)):02d}"
        start = dt.datetime.strptime(match.group(3) + " " + start_time, "%d.%m.%Y %H:%M")
        end = dt.datetime.strptime(match.group(6) + " " + end_time, "%d.%m.%Y %H:%M")
        stages.append(
            {
                "period_no": next_period_no,
                "date_from": start.isoformat(timespec="minutes"),
                "date_to": end.isoformat(timespec="minutes"),
                "price": money_from_text(match.group(7)),
            }
        )
        next_period_no += 1
    for match in date_only_range_pattern.finditer(text):
        start = dt.datetime.strptime(match.group(1) + " 00:00", "%d.%m.%Y %H:%M")
        end = dt.datetime.strptime(match.group(2) + " 23:59", "%d.%m.%Y %H:%M")
        stages.append(
            {
                "period_no": next_period_no,
                "date_from": start.isoformat(timespec="minutes"),
                "date_to": end.isoformat(timespec="minutes"),
                "price": money_from_text(match.group(3)),
            }
        )
        next_period_no += 1
    if stages:
        return sorted(stages, key=lambda item: int(item["period_no"]))
    return stages


def explicit_price_list(text: str, start_price: float) -> list[float]:
    lowered = clean(text).lower()
    prices: list[float] = []
    for pattern in (
        r"(?:период|день|этап)[^;|:.]{0,35}[-–:]\s*(\d[\d\s]*(?:[,.]\d{1,2})?)\s*руб",
        r"(?:первый|второй|третий|четвертый|пятый|шестой|седьмой|восьмой|девятый|десятый|одиннадцатый|двенадцатый|тринадцатый|четырнадцатый|пятнадцатый|шестнадцатый|семнадцатый|восемнадцатый|девятнадцатый|двадцатый|последний)[^;|:.]{0,35}[-–:]\s*(\d[\d\s]*(?:[,.]\d{1,2})?)\s*руб",
    ):
        for match in re.finditer(pattern, lowered):
            price = money_from_text(match.group(1))
            if price is not None:
                prices.append(price)
    deduped: list[float] = []
    seen: set[int] = set()
    for price in prices:
        key = round(price)
        if key not in seen:
            deduped.append(price)
            seen.add(key)
    if len(deduped) >= 2:
        return deduped[:80]
    return []


def cumulative_percent_prices(text: str, start_price: float) -> list[float]:
    lowered = clean(text).lower()
    candidates = []
    for sentence in re.split(r"[.;]", lowered):
        if "сниж" not in sentence and "уменьш" not in sentence and "величин" not in sentence:
            continue
        if "количеств" in sentence or "кажд" in sentence or " до " in sentence or "для лот" in sentence:
            continue
        values = [
            percent_number(item)
            for item in re.findall(r"\d+(?:[,.]\d+)?\s*(?:%|процент\w*)", sentence)
        ]
        values = [value for value in values if value is not None and 0 < value < 100]
        if len(values) >= 2:
            candidates = values
            break
    if not candidates:
        return []
    prices = [start_price]
    for percent in candidates:
        prices.append(max(0, start_price * (1 - percent / 100)))
    return prices[:80]


def grouped_percent_prices(text: str, start_price: float, needed: int) -> list[float]:
    lowered = clean(text).lower()
    groups: list[tuple[float, int | None]] = []
    percent_pattern = re.compile(r"сниж\w+[^.]{0,100}?на\s+(\d+(?:[,.]\d+)?)\s*(?:%|процент\w*)")
    count_pattern = re.compile(r"количеств\w*\s+сниж\w*[^.]{0,40}?(\d+)\s*раз")
    final_percent_match = re.search(
        r"(?:цен\w*\s+продаж\w*\s+)?составит\s+(\d+(?:[,.]\d+)?)\s*%\s+от\s+нц",
        lowered,
    )
    final_price = (
        start_price * (percent_number(final_percent_match.group(1)) or 0) / 100
        if final_percent_match
        else None
    )
    for sentence in re.split(r"[.;]", lowered):
        for match in percent_pattern.finditer(sentence):
            percent = percent_number(match.group(1))
            if percent:
                groups.append((percent, None))
        count_match = count_pattern.search(sentence)
        if count_match and groups and groups[-1][1] is None:
            groups[-1] = (groups[-1][0], int(count_match.group(1)))
    if not groups:
        return []
    prices = [start_price]
    current = start_price
    for index, (percent, count) in enumerate(groups):
        repeat = count if count is not None else max(0, needed - len(prices))
        if index == len(groups) - 1 and count is None:
            repeat = max(0, needed - len(prices))
        for _ in range(repeat):
            if len(prices) >= needed:
                return prices
            current = max(0, current - start_price * percent / 100)
            prices.append(current)
    if final_price is not None and (not prices or final_price < prices[-1]) and len(prices) < needed:
        prices.append(final_price)
    return prices


def absolute_percent_prices(text: str, start_price: float, lot_no: int | None = None) -> list[float]:
    lowered = clean(text).lower()
    step_match = None
    if lot_no is not None:
        step_match = re.search(
            rf"для\s+лота\s+{lot_no}[^.]*?шаг\s+сниж\w*[^.]*?(\d+(?:[,.]\d+)?)\s*%",
            lowered,
        )
    if step_match is None:
        step_match = re.search(
            r"(?:шаг|величин\w*\s+сниж\w*)[^.]{0,100}?(\d+(?:[,.]\d+)?)\s*(?:\([^)]*\)\s*)?%",
            lowered,
        )
    if step_match is None:
        return []
    step_percent = percent_number(step_match.group(1)) or 0
    if step_percent <= 0:
        return []
    floor_percents = [
        percent_number(match.group(1))
        for match in re.finditer(
            r"(?:снижа\w*\s+до|сниж\w*\s+цен\w*\s+до|цен\w*[^.]{0,40}?составит|(?:минимальн|цена отсечения|нижн\w*\s+предел)[^.]{0,120}?составляет)\s+(\d+(?:[,.]\d+)?)\s*%",
            lowered,
        )
    ]
    floor_percents = [value for value in floor_percents if value is not None and 0 < value < 100]
    if not floor_percents:
        cut = cutoff_price(lowered, start_price, lot_no)
        if cut is not None:
            floor_percents = [cut / start_price * 100]
    if not floor_percents:
        return []
    prices = [start_price]
    current_percent = 100.0
    for floor in floor_percents:
        if floor >= current_percent:
            continue
        while current_percent - step_percent > floor:
            current_percent -= step_percent
            prices.append(start_price * current_percent / 100)
        if prices[-1] != start_price * floor / 100:
            prices.append(start_price * floor / 100)
        current_percent = floor
    return prices[:80] if len(prices) > 1 else []


def simple_step_prices(text: str, start_price: float, count: int, lot_no: int | None = None) -> list[float]:
    lowered = clean(text).lower()
    cut = cutoff_price(lowered, start_price, lot_no)
    amount_match = re.search(r"(?:сниж|уменьш)\w+[^.]{0,80}?на\s+(\d[\d\s]*(?:[,.]\d{1,2})?)\s*руб", lowered)
    lot_percent_match = None
    if lot_no is not None:
        lot_percent_match = re.search(
            rf"для\s+лота\s+{lot_no}[^.]*?шаг\s+сниж\w*[^.]*?(\d+(?:[,.]\d+)?)\s*(?:\([^)]*\)\s*)?(?:%|процент\w*)",
            lowered,
        )
    percent_match = re.search(
        r"(?:сниж|уменьш|шаг|величин\w*\s+сниж)[^.]{0,220}?(\d+(?:[,.]\d+)?)\s*(?:\([^)]*\)\s*)?(?:%|процент\w*)",
        lowered,
    )
    if amount_match:
        step = money_from_text(amount_match.group(1)) or 0
    elif lot_percent_match or percent_match:
        match = lot_percent_match or percent_match
        step = start_price * (percent_number(match.group(1)) or 0) / 100
    else:
        return []
    prices = []
    current = start_price
    for _ in range(count):
        prices.append(current)
        next_price = current - step
        if cut is not None:
            next_price = max(next_price, cut)
        current = max(0, next_price)
    return prices


def stages_from_prices(
    prices: list[float],
    begin: dt.datetime,
    end: dt.datetime,
    period_days: int,
    use_workdays: bool,
    first_days: int | None,
    first_use_workdays: bool = False,
) -> list[dict[str, object]]:
    stages: list[dict[str, object]] = []
    current = begin.date()
    start_time = begin.time()
    end_time = end.time()
    for index, price in enumerate(prices, start=1):
        if current > end.date():
            break
        days = first_days if index == 1 and first_days else period_days
        current_use_workdays = first_use_workdays if index == 1 and first_days else use_workdays
        if current_use_workdays:
            finish = min(add_workdays(current, max(1, days) - 1), end.date())
        else:
            finish = min(current + dt.timedelta(days=max(1, days) - 1), end.date())
        stages.append(
            {
                "period_no": index,
                "date_from": iso_date(current, start_time),
                "date_to": iso_date(finish, end_time),
                "price": round(price, 2),
            }
        )
        current = finish + dt.timedelta(days=1)
        while use_workdays and current.weekday() >= 5:
            current += dt.timedelta(days=1)
    if stages:
        last_end = parse_date(str(stages[-1]["date_to"]))
        if last_end and last_end < end:
            stages[-1]["date_to"] = end.isoformat(timespec="minutes")
    return stages


def official_schedule_from_text(row: dict[str, str], trade_type: str) -> list[dict[str, object]]:
    if trade_type != "PublicOffer":
        return []
    begin = parse_date(row.get("Начало заявок", ""))
    end = parse_date(row.get("Конец заявок", ""))
    start_price = money_number(row.get("Стартовая цена", ""))
    text = clean(row.get("Порядок снижения цены", ""))
    if not begin or not end or start_price is None or not text:
        return []
    lot_no = lot_no_from_id(row.get("Лот", ""))

    table = explicit_table_schedule(text)
    if table:
        return table

    period_days, use_workdays = period_info(text)
    first_days = initial_period_days(text)
    needed = max(stage_count(begin, end, period_days, first_days), described_stage_count(text))

    prices = (
        explicit_price_list(text, start_price)
        or grouped_percent_prices(text, start_price, needed)
        or absolute_percent_prices(text, start_price, lot_no)
        or simple_step_prices(text, start_price, needed, lot_no)
        or cumulative_percent_prices(text, start_price)
    )
    effective_end = end
    if len(prices) > stage_count(begin, end, period_days, first_days):
        effective_end = begin + dt.timedelta(days=max(1, period_days) * len(prices))
    return stages_from_prices(
        prices[:needed],
        begin,
        effective_end,
        period_days,
        use_workdays,
        first_days,
        initial_period_is_workday(text),
    )


def fallback_schedule(row: dict[str, str], trade_type: str) -> list[dict[str, object]]:
    if trade_type != "PublicOffer":
        return []
    begin = parse_date(row.get("Начало заявок", ""))
    end = parse_date(row.get("Конец заявок", ""))
    start_price = money_number(row.get("Стартовая цена", ""))
    if not begin or not end or start_price is None:
        return []
    text = clean(row.get("Порядок снижения цены", "")).lower()
    period_match = re.search(r"(\d+)\s*(?:\([^)]*\)\s*)?(?:рабоч|календар)?\w*\s*дн", text)
    period_days = int(period_match.group(1)) if period_match else 5
    percent_match = re.search(r"(?:сниж|уменьш)\w*.{0,60}?([\d,.]+)\s*%", text)
    amount_match = re.search(r"(?:сниж|уменьш)\w*.{0,60}?([\d\s,.]+)\s*руб", text)
    prices = [money_number(match.group(0)) for match in re.finditer(r"\d[\d\s]*(?:[,.]\d{2})?\s*руб", text)]
    prices = [price for price in prices if price is not None]

    if len(prices) >= 2:
        stage_prices = prices[:80]
    elif amount_match:
        step = money_number(amount_match.group(1)) or 0
        count = max(1, min(80, ((end.date() - begin.date()).days // max(1, period_days)) + 1))
        stage_prices = [max(0, start_price - step * index) for index in range(count)]
    elif percent_match:
        step = start_price * (money_number(percent_match.group(1)) or 0) / 100
        count = max(1, min(80, ((end.date() - begin.date()).days // max(1, period_days)) + 1))
        stage_prices = [max(0, start_price - step * index) for index in range(count)]
    else:
        stage_prices = [start_price]

    stages: list[dict[str, object]] = []
    current = begin.date()
    for index, price in enumerate(stage_prices, start=1):
        if current > end.date():
            break
        finish = min(add_days(current, max(1, period_days) - 1), end.date())
        stages.append(
            {
                "period_no": index,
                "date_from": current.isoformat(),
                "date_to": finish.isoformat(),
                "price": price,
            }
        )
        current = finish + dt.timedelta(days=1)
    return stages


def schedule_rows_html(
    row: dict[str, str],
    trade_type: str,
    schedule: list[dict[str, object]],
) -> str:
    stages = official_schedule_from_text(row, trade_type) or schedule or fallback_schedule(row, trade_type)
    if not stages:
        return ""
    default_start_time = time_part(row.get("Начало заявок", ""), "00:00")
    default_end_time = time_part(row.get("Конец заявок", ""), "23:59")
    items = []
    for stage in stages:
        price = stage.get("price")
        date_from = str(stage.get("date_from") or "")
        date_to = str(stage.get("date_to") or "")
        items.append(
            f"""
            <tr>
              <td>{html.escape(str(stage.get("period_no") or ""))}</td>
              <td>{date_part(date_from)}</td>
              <td>{time_part(date_from, default_start_time)}</td>
              <td>{date_part(date_to)}</td>
              <td>{time_part(date_to, default_end_time)}</td>
              <td>{money(str(price)) if price is not None else "—"}</td>
            </tr>
            """
        )
    return f"""
      <details class="section schedule" open>
        <summary>Порядок снижения цены</summary>
        <div class="schedule-wrap">
          <table class="schedule-table">
            <thead>
              <tr><th>Этап</th><th>С какого числа</th><th>С какого времени</th><th>По какое число</th><th>По какое время</th><th>Сумма</th></tr>
            </thead>
            <tbody>{''.join(items)}</tbody>
          </table>
        </div>
      </details>
    """


def row_card(
    row: dict[str, str],
    meta: dict[str, str],
    schedule: list[dict[str, object]],
) -> str:
    source_url = clean(row.get("Ссылка", ""))
    result_url = clean(row.get("Ссылка результата", ""))
    trade_type = meta.get("trade_type") or ""
    if not trade_type and clean(row.get("Торги", "")) and " по " not in clean(row.get("Торги", "")):
        trade_type = "OpenedAuction"
    asset_type = meta.get("asset_type") or ""
    is_real_estate = asset_type in {"real_estate", "commercial_real_estate", "land"} or bool(
        clean(row.get("Кадастровый номер", ""))
    )
    object_section = ""
    if is_real_estate:
        object_section = f"""
        <section class="section object">
          <h3>Объект недвижимости</h3>
          {dl(["Адрес", "Кадастровый номер", "Площадь м2"], row)}
        </section>
        """
    schedule_section = schedule_rows_html(row, trade_type, schedule)
    return f"""
      <article class="lot-card">
        <header class="card-head">
          <div>
            <h2>{esc(title_from_row(row))}</h2>
            <div class="message-line">
              <span>Сообщение: {field_value("Сообщение", row)}</span>
              <span>Лот: {field_value("Лот", row)}</span>
              <span>Тип торгов: {html.escape(trade_type_label(trade_type))}</span>
            </div>
          </div>
          <div class="actions">
            {action_link(source_url, "Объявление", True)}
            {action_link(result_url, "Результат")}
          </div>
        </header>

        {object_section}

        <section class="section price-dates">
          <h3>Цена и сроки</h3>
          {dl(["Стартовая цена", "Начало заявок", "Конец заявок", "Торги"], row)}
        </section>

        <details class="section" open>
          <summary>Описание</summary>
          <p>{field_value("Описание", row)}</p>
        </details>

        {schedule_section}

        <section class="section result">
          <h3>Официальное сообщение результата</h3>
          {dl(["Результат торгов", "Сообщение результата", "Дата результата", "Цена результата", "Покупатель", "Причина результата"], row)}
        </section>

        <section class="section docs">
          <h3>Документы из объявления</h3>
          {dl(["Документы"], row)}
        </section>
      </article>
    """


def render(rows: list[dict[str, str]]) -> str:
    generated_at = dt.datetime.now().strftime("%d.%m.%Y %H:%M")
    lot_meta, schedules = load_lot_meta()
    cards = "\n".join(
        row_card(row, lot_meta.get(clean(row.get("Лот", "")), {}), schedules.get(clean(row.get("Лот", "")), []))
        for row in rows
    )
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Федресурс: карточки объявлений</title>
  <style>
    :root {{
      --bg: #f4f6f8;
      --surface: #ffffff;
      --surface-soft: #f8fafc;
      --text: #1f2933;
      --muted: #667085;
      --line: #d8e0ea;
      --line-strong: #bcc7d4;
      --blue: #1f5fbf;
      --shadow: 0 8px 22px rgba(31, 41, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    header.top {{
      position: sticky;
      top: 0;
      z-index: 10;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(10px);
    }}
    .top-inner {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 16px 20px;
    }}
    h1 {{
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .meta {{
      margin-top: 5px;
      color: var(--muted);
      font-size: 13px;
    }}
    .toolbar {{
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: 14px;
    }}
    .search {{
      width: min(720px, 100%);
      height: 42px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      padding: 0 13px;
      font-size: 14px;
      outline: none;
      background: #fff;
    }}
    main {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 18px 20px 48px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(430px, 1fr));
      gap: 14px;
      align-items: start;
    }}
    .lot-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: var(--shadow);
      padding: 16px;
    }}
    .card-head {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: start;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 18px;
      line-height: 1.3;
      letter-spacing: 0;
    }}
    .message-line {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
    }}
    .message-line span {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 2px 7px;
      background: var(--surface-soft);
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      justify-content: flex-end;
    }}
    .action {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
      border: 1px solid var(--line-strong);
      border-radius: 7px;
      padding: 0 11px;
      color: var(--text);
      background: #fff;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      white-space: nowrap;
    }}
    .action-primary {{
      border-color: var(--blue);
      color: #fff;
      background: var(--blue);
    }}
    .section {{
      margin-top: 13px;
      padding-top: 13px;
      border-top: 1px solid var(--line);
    }}
    .section h3, .section summary {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      line-height: 1.25;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    .section summary {{ cursor: pointer; }}
    .section p {{
      margin: 0;
      font-size: 13px;
      line-height: 1.5;
      overflow-wrap: anywhere;
    }}
    dl {{
      display: grid;
      gap: 7px;
      margin: 0;
    }}
    .field {{
      display: grid;
      grid-template-columns: 150px minmax(0, 1fr);
      gap: 10px;
      align-items: start;
    }}
    dt {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}
    dd {{
      margin: 0;
      font-size: 13px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }}
    .schedule-wrap {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .schedule-table {{
      width: 100%;
      min-width: 680px;
      border-collapse: collapse;
      font-size: 12px;
    }}
    .schedule-table th,
    .schedule-table td {{
      border-bottom: 1px solid var(--line);
      padding: 8px 9px;
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }}
    .schedule-table th {{
      color: var(--muted);
      background: var(--surface-soft);
      font-weight: 700;
    }}
    .schedule-table tr:last-child td {{
      border-bottom: 0;
    }}
    .schedule-table td:last-child {{
      font-weight: 700;
    }}
    .price-dates dd:first-letter, .result dd:first-letter {{ letter-spacing: 0; }}
    .empty {{
      display: none;
      border: 1px dashed var(--line-strong);
      border-radius: 8px;
      background: #fff;
      padding: 28px;
      color: var(--muted);
      text-align: center;
    }}
    @media (max-width: 780px) {{
      .top-inner, main {{ padding-left: 12px; padding-right: 12px; }}
      .cards {{ grid-template-columns: 1fr; }}
      .card-head {{ grid-template-columns: 1fr; }}
      .actions {{ justify-content: flex-start; }}
      .field {{ grid-template-columns: 1fr; gap: 2px; }}
      h1 {{ font-size: 21px; }}
      h2 {{ font-size: 16px; }}
    }}
  </style>
</head>
<body>
  <header class="top">
    <div class="top-inner">
      <h1>Федресурс: карточки объявлений</h1>
      <div class="meta">Сгенерировано {html.escape(generated_at)}. В карточках нет расчетных полей, только поля объявления и официального сообщения результата.</div>
      <div class="toolbar">
        <input id="search" class="search" type="search" placeholder="Поиск по тексту карточек">
      </div>
    </div>
  </header>
  <main>
    <section id="cards" class="cards">
      {cards}
    </section>
    <div id="empty" class="empty">Ничего не найдено</div>
  </main>
  <script>
    const search = document.getElementById('search');
    const cards = [...document.querySelectorAll('.lot-card')];
    const empty = document.getElementById('empty');
    function applySearch() {{
      const query = search.value.trim().toLowerCase();
      let visible = 0;
      for (const card of cards) {{
        const show = !query || card.innerText.toLowerCase().includes(query);
        card.hidden = !show;
        if (show) visible += 1;
      }}
      empty.style.display = visible === 0 ? 'block' : 'none';
    }}
    search.addEventListener('input', applySearch);
  </script>
</body>
</html>
"""


def main() -> int:
    with TSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(render(rows), encoding="utf-8")
    print(OUT_PATH)
    print(f"cards={len(rows)}")
    print("fields=" + ", ".join(DIRECT_FIELDS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
