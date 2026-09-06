"""
Форматирование и отправка отчётов в Telegram.
Telegram-специфичная часть, вынесенная из Money_alert_AI.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
import html
import os
import re

from dotenv import load_dotenv
from telegram import Bot
from telegram.request import HTTPXRequest

load_dotenv()

TELEGRAM_MSG_LIMIT = 4096


def _env_flag(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _make_bot(token: str) -> Bot:
    if not _env_flag("TELEGRAM_VERIFY_SSL", default=True):
        return Bot(token=token, request=HTTPXRequest(httpx_kwargs={"verify": False}))
    return Bot(token=token)


def _sanitize_truncated_html(text: str) -> str:
    last_lt = text.rfind("<")
    if last_lt != -1 and ">" not in text[last_lt:]:
        text = text[:last_lt].rstrip()
    open_count = len(re.findall(r"<a[\s>]", text, re.IGNORECASE))
    close_count = len(re.findall(r"</a>", text, re.IGNORECASE))
    text += "</a>" * max(0, open_count - close_count)
    return text


def _truncate_field(text: str, max_chars: int) -> str:
    if not text or len(text) <= max_chars:
        return text
    ref_match = re.search(r"\s*(\[\d+\](?:\[\d+\])*)\s*$", text)
    if ref_match and ref_match.start() < max_chars - 5:
        refs = ref_match.group(1)
        return text[: max_chars - len(refs) - 1].rstrip() + "…" + refs
    return text[: max_chars - 1] + "…"


def format_telegram_report(result: dict, stats: dict) -> str:
    """Форматирует отчёт для Telegram (HTML, ≤ 4096 символов)."""
    final_result = result.get("result")

    sources_map: dict[int, tuple[str, str]] = {}  # id → (url, date_label)
    if final_result:
        for src in final_result.get("sources", []):
            src_id = src.get("id")
            src_url = src.get("url", "")
            if src_id is None or not src_url:
                continue
            raw_date = src.get("date", "")
            date_label = ""
            if raw_date:
                try:
                    from datetime import date as _date
                    d = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).date()
                    date_label = d.strftime("%d.%m.%Y")
                except Exception:
                    date_label = str(raw_date)[:10]
            sources_map[int(src_id)] = (src_url, date_label)

    def _linkify(text: str) -> str:
        escaped = html.escape(str(text))
        if sources_map:
            def _repl(m):
                n = int(m.group(1))
                entry = sources_map.get(n)
                if entry:
                    url, date_label = entry
                    label = f"[{n}]" + (f" {date_label}" if date_label else "")
                    return f'<a href="{html.escape(url)}">{label}</a>'
                return m.group(0)
            escaped = re.sub(r"\[(\d+)\]", _repl, escaped)
        return escaped

    def _item(text: str, limit: int = 160) -> str:
        t = text.lstrip("•").strip() if isinstance(text, str) else str(text)
        return _linkify(_truncate_field(t, limit))

    risk_map = {
        "green":  ("🟢", "НИЗКИЙ"),
        "yellow": ("🟡", "СРЕДНИЙ"),
        "orange": ("🟠", "СУЩЕСТВЕННЫЙ"),
        "red":    ("🔴", "ВЫСОКИЙ"),
        "black":  ("⚫", "АВАРИЙНЫЙ"),
    }

    lines: list[str] = []
    _BQ_PLACEHOLDER = "%%TRIGGERED_BLOCKQUOTE%%"
    bq_items: list[str] = []

    if not final_result:
        return "⚠️ Не удалось получить результат от агента"

    risk_level = final_result.get("risk_level", "unknown")
    emoji, label = risk_map.get(risk_level, ("❓", "НЕИЗВЕСТНО"))
    dep = final_result.get("deposit_access_risk", "green")
    dep_emoji, dep_label = risk_map.get(dep, ("❓", "НЕИЗВЕСТНО"))

    # ── Заголовок ──────────────────────────────────────────────
    today        = date.today().strftime("%d.%m.%Y")
    run_id_h     = stats.get("run_id")
    steps_h      = stats.get("steps", 0)
    searches_h   = stats.get("tool_calls", 0)

    zone_desc = {
        "green":  "0–19 = зелёная зона",
        "yellow": "20–39 = жёлтая зона",
        "orange": "40–69 = оранжевая зона",
        "red":    "70+ = красная зона",
        "black":  "аварийный уровень",
    }.get(risk_level, "")

    subhead_parts = []
    if run_id_h:
        subhead_parts.append(f"Прогон #{run_id_h}")
    if steps_h:
        subhead_parts.append(f"{steps_h} критериев")
    if searches_h:
        subhead_parts.append(f"{searches_h} поисков")

    lines.append(f"<b>Макро-обзор РФ | {today}</b>")
    if subhead_parts:
        lines.append(f"<i>{' · '.join(subhead_parts)}</i>")
    lines.append("")

    max_score = result.get("max_score", 351)
    score_line = f"Очки: <b>{final_result.get('total_score', '?')}</b> / {max_score}"
    if zone_desc:
        score_line += f" <i>({zone_desc})</i>"

    lines += [
        f"Риск кризисного сценария (6м): {emoji} <b>{label}</b>",
        score_line,
        f"Риск доступа к вкладам (1–3м): {dep_emoji} <b>{dep_label}</b>",
    ]
    conf = final_result.get("confidence")
    if conf:
        lines.append(f"Уверенность: {html.escape(str(conf))}")
    lines.append("")

    # ── Сработавшие критерии (expandable) ──────────────────────
    triggered = final_result.get("triggered_criteria", [])
    if triggered:
        lines.append(f"⚠️ <b>Сработавшие критерии ({len(triggered)}):</b>")
        for t in triggered:
            name     = html.escape(str(t.get("name") or t.get("id", "?")))
            weight   = t.get("weight", "")
            evidence = _truncate_field(t.get("evidence", "") or "", 160)
            w_str    = f" [{weight}]" if weight else ""
            bq_items.append(f"• <b>{name}</b>{w_str}: {_linkify(evidence)}")
        lines.append(_BQ_PLACEHOLDER)
        lines.append("")
    else:
        lines.append("✅ Сработавших критериев нет")
        lines.append("")

    # ── Резюме ──────────────────────────────────────────────────
    summary = _truncate_field(final_result.get("summary", "Нет данных"), 400)
    lines.append(f"📝 {_linkify(summary)}")

    # ── Позитивные тенденции ────────────────────────────────────
    positive = final_result.get("positive_trends", []) or []
    if positive:
        lines += ["", "🟢 <b>Позитивные тенденции:</b>"]
        for item in positive:
            lines.append(f"  • {_item(item)}")

    # ── Негативные тенденции ────────────────────────────────────
    negative = final_result.get("negative_trends", []) or []
    if negative:
        lines += ["", "🔴 <b>Негативные тенденции:</b>"]
        for item in negative:
            lines.append(f"  • {_item(item)}")

    # ── Риски на 6 месяцев ──────────────────────────────────────
    risks_6m = final_result.get("key_risks_6m", []) or []
    if risks_6m:
        lines += ["", "⚠️ <b>Риски на 6 месяцев:</b>"]
        for item in risks_6m:
            lines.append(f"  • {_item(item)}")

    # ── Watchlist ───────────────────────────────────────────────
    watchlist = final_result.get("watchlist", []) or []
    if watchlist:
        lines += ["", "👀 <b>Watchlist:</b>"]
        for item in watchlist:
            lines.append(f"  • {_item(item)}")

    # ── Футер ───────────────────────────────────────────────────
    history_trend = stats.get("history_trend", "")
    searches      = stats.get("tool_calls", 0)
    model         = stats.get("model", "")
    cost_usd      = stats.get("cost_usd", 0)

    footer: list[str] = ["", "——"]
    timing_parts = []
    t = stats.get("time_seconds", 0)
    if t:
        timing_parts.append(f"⏱ {t:.0f}с")
    if searches:
        timing_parts.append(f"🔍 {searches} поисков")
    if timing_parts:
        line = " · ".join(timing_parts)
        if history_trend:
            line += f" · {history_trend}"
        footer.append(line)
    if model:
        footer.append(f"🤖 {html.escape(str(model))}")
    if cost_usd and cost_usd > 0:
        footer.append(f"💰 ${cost_usd:.4f}")
    site_url = os.getenv("SITE_URL", "")
    if site_url:
        footer.append(f'🌐 <a href="{html.escape(site_url)}">Полный отчёт на сайте</a>')
    footer += ["", "<i>Не является инвестиционной рекомендацией.</i>"]
    lines.extend(footer)

    report = "\n".join(lines)

    # ── Вставляем expandable blockquote ────────────────────────
    if _BQ_PLACEHOLDER not in report or not bq_items:
        return report.replace(_BQ_PLACEHOLDER, "")

    bq_wrap_len = len("<blockquote expandable>") + len("</blockquote>")
    shell_len   = len(report) - len(_BQ_PLACEHOLDER) + bq_wrap_len
    available   = TELEGRAM_MSG_LIMIT - shell_len - 10
    if available < 0:
        available = 0

    fitted: list[str] = []
    used = 0
    for item in bq_items:
        cost = len(item) + (1 if fitted else 0)
        if used + cost <= available:
            fitted.append(item)
            used += cost
        else:
            remaining = available - used - (1 if fitted else 0)
            if remaining > 30:
                fitted.append(_sanitize_truncated_html(item[: remaining - 1]) + "…")
            break

    bq_html = f"<blockquote expandable>{chr(10).join(fitted)}</blockquote>" if fitted else ""
    return report.replace(_BQ_PLACEHOLDER, bq_html)


def _split_message(text: str, limit: int = TELEGRAM_MSG_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return parts


async def _send_message_parts(
    bot: Bot,
    chat_id: str,
    text: str,
    *,
    parse_mode: str | None = None,
) -> int | None:
    """Отправляет сообщение (по частям если > 4096 символов). Возвращает message_id первой части."""
    first_message_id: int | None = None
    for part in _split_message(text):
        try:
            msg = await bot.send_message(
                chat_id=chat_id,
                text=part,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
            if first_message_id is None:
                first_message_id = msg.message_id
        except Exception as exc:
            if parse_mode and "parse entities" in str(exc).lower():
                plain = re.sub(r"<[^>]+>", "", part)
                msg = await bot.send_message(chat_id=chat_id, text=plain, disable_web_page_preview=True)
                if first_message_id is None:
                    first_message_id = msg.message_id
            else:
                raise
    return first_message_id


async def send_telegram_report(report: str) -> int | None:
    """Отправляет отчёт в канал. Возвращает message_id или None при ошибке/отключении."""
    if _env_flag("DISABLE_TELEGRAM", default=False):
        print("ℹ️ Telegram отключён (DISABLE_TELEGRAM=1)")
        return None

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")

    if not token or not chat_id:
        print(f"⚠️ Telegram не настроен (token: {'есть' if token else 'нет'}, chat_id: {chat_id or 'нет'})")
        return None

    try:
        bot = _make_bot(token)
        message_id = await _send_message_parts(bot, chat_id, report, parse_mode="HTML")
        print(f"✅ Отчёт отправлен в Telegram (chat_id: {chat_id}, message_id: {message_id})")
        return message_id
    except asyncio.CancelledError:
        print("⚠️ Отправка в Telegram отменена")
        return None
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return None


async def notify_admin(message: str, *, parse_mode: str | None = None) -> bool:
    if _env_flag("DISABLE_TELEGRAM", default=False):
        print("ℹ️ Telegram отключён (DISABLE_TELEGRAM=1)")
        return False

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    if not token or not admin_chat_id:
        print(f"⚠️ Админ-чат не настроен (admin_chat_id: {admin_chat_id or 'нет'})")
        return False

    try:
        bot = _make_bot(token)
        await _send_message_parts(bot, admin_chat_id, message, parse_mode=parse_mode)
        print(f"✅ Уведомление отправлено админу (chat_id: {admin_chat_id})")
        return True
    except asyncio.CancelledError:
        print("⚠️ Уведомление отменено")
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        return False
