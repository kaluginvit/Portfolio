"""
valuate.py — рыночная оценка лота через OpenRouter + web search (Tavily / Brave)

Usage:
    python valuate.py <lot_id>
    python valuate.py <lot_id> --provider brave
    python valuate.py <lot_id> --model anthropic/claude-sonnet-4-5
"""

import argparse
import io
import json
import logging
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("valuate")


def _fix_stdout_encoding() -> None:
    """Перекодирует stdout/stderr в UTF-8 для корректного вывода кириллицы на Windows.

    Вызывается только из main(), не при импорте модуля — иначе ломает pytest
    и другие инструменты, которые перехватывают sys.stdout.
    """
    if hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except AttributeError:
            pass

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    logger.warning("openai не установлен: pip install -r requirements.txt")

try:
    from tavily import TavilyClient
    _TAVILY_AVAILABLE = True
except ImportError:
    _TAVILY_AVAILABLE = False
    logger.warning("tavily-python не установлен: pip install -r requirements.txt")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).parent


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls"}
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import fitz
        doc = fitz.open(str(path))
        return "\n".join(page.get_text() for page in doc)
    elif suffix in (".docx", ".doc"):
        from docx import Document
        return "\n".join(p.text for p in Document(str(path)).paragraphs if p.text.strip())
    elif suffix in (".xlsx", ".xls"):
        import openpyxl
        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        lines = []
        for sheet in wb.worksheets:
            lines.append(f"[Лист: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c) if c is not None else "" for c in row]
                if any(c.strip() for c in cells):
                    lines.append("\t".join(cells))
        return "\n".join(lines)
    return ""


def load_lot_documents(lot_id: str) -> list[dict]:
    """Ищет файлы лота в корне проекта и в data/documents/ (любой вложенности)."""
    seen: set[Path] = set()
    candidates: list[Path] = []

    # Корень проекта: {lot_id}.*
    for path in sorted(PROJECT_ROOT.glob(f"{lot_id}.*")):
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            candidates.append(path)
            seen.add(path)

    # data/documents/ — файлы содержащие lot_id в имени
    if DOCUMENTS_DIR.exists():
        for path in sorted(DOCUMENTS_DIR.rglob(f"*{lot_id}*")):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS and path not in seen:
                candidates.append(path)

    docs = []
    for path in candidates:
        logger.info("Загружаем документ: %s", path.name)
        try:
            text = extract_text_from_file(path)
        except Exception as e:
            logger.warning("Ошибка чтения документа %s: %s", path.name, e)
            continue
        if text.strip():
            docs.append({"name": path.name, "text": text})
    return docs

DB_PATH = Path(__file__).parent / "data" / "fedresurs.sqlite3"
DEFAULT_MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """Ты — эксперт по оценке активов, продаваемых в процедурах банкротства в России.

## Шаг 1 — Изучи приложенные документы
Если в сообщении есть прикреплённые документы (таблицы, PDF, отчёты об оценке, технические паспорта) — изучи их в первую очередь. Они могут содержать характеристики, кадастровые данные, перечень имущества или независимую оценку.

## Шаг 2 — Определи тип актива и стратегию поиска
Адаптируй поиск под тип актива:
- **Недвижимость** (квартиры, дома, земля) → Авито, ЦИАН, Домклик, кадастровая стоимость, цены в районе
- **Транспорт** (авто, спецтехника) → Авто.ру, Авито авто, год/пробег/марка/модель
- **Оборудование и ТМЦ** → б/у рынок, спецплощадки, аналоги по модели/артикулу
- **Дебиторская задолженность** → реальность взыскания, финансовое состояние должника, дисконт рынка
- **Доли и акции** → выручка, активы, обязательства компании, отраслевые мультипликаторы
- **Ценности** (ювелирка, антиквариат, коллекции) → аукционные дома, специализированные площадки

## Шаг 3 — Поиск аналогов
Используй инструмент web_search. Делай столько запросов, сколько нужно для уверенной оценки.

## Шаг 4 — Оцени три сценария и цену торгов

**Сценарий 1 — Срочная продажа лотом перекупщикам** (quick_lot)
Всё имущество продаётся одним лотом перекупщику/дилеру за наличные, быстро (1–2 недели).
Покупатель закладывает свою маржу и риски. Минимальная цена среди рыночных сценариев.

**Сценарий 2 — Оптовая распродажа партиями** (wholesale)
Разбивка на группы, продажа небольшими партиями оптовым покупателям (1–3 месяца).

**Сценарий 3 — Розничная продажа** (retail)
Поштучная продажа через Авито, Ozon, Wildberries, специализированные площадки (3–12 месяцев).
Максимальная выручка, но требует времени, хранения и усилий.

### Цена торгов (auction_price)
Считай напрямую от розничной цены вторичного рынка по типу актива:

| Тип актива | Коэффициент от розницы вторичного рынка |
|---|---|
| Оборудование / ТМЦ (лот 10+ единиц) | 15–30% |
| Оборудование / ТМЦ (единичное) | 30–50% |
| Транспорт | 50–70% |
| Недвижимость жилая | 60–80% |
| Недвижимость коммерческая / земля | 45–65% |
| Дебиторская задолженность | 3–15% от номинала |
| Доля в ООО | 10–35% от независимой оценки |

Снижай к нижней границе если:
- лот продаётся повторно (каждый раунд −10–15%)
- нет возможности осмотра
- требуется самовывоз крупного / тяжёлого имущества
- есть обременения, прописанные лица, аресты

**Пол цены:** auction_price не может быть ниже стоимости металлолома / утилизации.
Для оборудования это абсолютный минимум — не уходи ниже него.

## Результат
Верни ТОЛЬКО валидный JSON без markdown-обёртки:
{
  "quick_lot_min": <число в рублях>,
  "quick_lot_max": <число в рублях>,
  "wholesale_min": <число в рублях>,
  "wholesale_max": <число в рублях>,
  "retail_min": <число в рублях>,
  "retail_max": <число в рублях>,
  "auction_price_min": <число в рублях>,
  "auction_price_max": <число в рублях>,
  "confidence": "low" | "medium" | "high",
  "price_per_sqm_min": <число или null>,
  "price_per_sqm_max": <число или null>,
  "sources": ["источник 1", "источник 2"],
  "key_factors": ["фактор 1", "фактор 2"],
  "reasoning": "обоснование 3-5 предложений"
}"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Поиск актуальных данных в интернете: цены на аналогичные объекты, кадастровая стоимость, рынок региона",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос на русском языке"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


_BOILERPLATE_RE = re.compile(
    r"(ВНИМАНИЕ[\s!]*ВАЖНАЯ"
    r"|После приобретения"
    r"|Добросовестный Победитель"
    r"|Победитель самостоятельно"
    r"|Для участия в торгах"
    r"|Заявки принимаются"
    r"|Задаток перечисляется"
    r"|Осмотр имущества"
    r"|связаться с собственником"
    r"|Решением Арбитражного суда"
    r"|Финансовым управляющим должника утвержден"
    r"|Организатор торгов\s*–)",
    re.IGNORECASE,
)


def clean_description(text: str) -> str:
    if not text:
        return text
    m = _BOILERPLATE_RE.search(text)
    if m:
        text = text[:m.start()].strip()
    text = re.sub(r"\+7[\s\-\(]?\d[\d\s\-\(\)]{7,}", "", text)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def build_prompt(lot: dict, documents: list[dict] | None = None) -> str:
    lines = []
    if lot.get("classifier"):
        lines.append(f"**Тип актива:** {lot['classifier']}")

    desc = clean_description(lot.get("description") or "")
    lines.append(f"\n**Описание:**\n{desc or '—'}")

    if lot.get("start_price"):
        fmt = lambda n: f"{float(n):,.0f}".replace(",", " ")
        lines.append(f"\n**Начальная цена торгов:** {fmt(lot['start_price'])} ₽")

    if documents:
        lines.append("\n---")
        for doc in documents:
            lines.append(f"\n**Документ: {doc['name']}**\n{doc['text']}")

    lines.append("\n---\nОпредели рыночную стоимость этого актива.")
    return "\n".join(lines)


def format_search_results(results: dict) -> str:
    items = results.get("results", [])
    if not items:
        return "Результаты не найдены."
    parts = []
    for r in items:
        parts.append(f"### {r.get('title', '')}\n{r.get('url', '')}\n{r.get('content', '')}")
    return "\n\n".join(parts)


def brave_search(query: str, api_key: str, max_results: int = 5) -> dict:
    params = urllib.parse.urlencode({
        "q": query,
        "count": max_results,
        "country": "ru",
        "search_lang": "ru",
        "text_decorations": 0,
    })
    req = urllib.request.Request(
        f"https://api.search.brave.com/res/v1/web/search?{params}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        import gzip
        raw = resp.read()
        if resp.info().get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        data = json.loads(raw)

    items = []
    for r in (data.get("web", {}).get("results") or []):
        items.append({
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "content": r.get("description", ""),
        })
    return {"results": items}


def google_search(query: str, api_key: str, cx: str, max_results: int = 5) -> dict:
    params = urllib.parse.urlencode({
        "key": api_key,
        "cx":  cx,
        "q":   query,
        "num": max_results,
        "lr":  "lang_ru",
        "gl":  "ru",
    })
    req = urllib.request.Request(
        f"https://www.googleapis.com/customsearch/v1?{params}",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google API {e.code}: {body}") from e

    items = []
    for r in (data.get("items") or []):
        items.append({
            "title":   r.get("title", ""),
            "url":     r.get("link", ""),
            "content": r.get("snippet", ""),
        })
    return {"results": items}


def jina_search(query: str, max_results: int = 5) -> dict:
    # Шаг 1: поиск → получаем URL + короткие сниппеты
    encoded = urllib.parse.quote(query, safe="")
    req = urllib.request.Request(
        f"https://s.jina.ai/{encoded}",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"results": [], "error": str(e)}

    items = []
    for r in (data.get("data") or [])[:max_results]:
        items.append({
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "content": r.get("description") or r.get("content", ""),
        })

    # Шаг 2: читаем полный текст топ-2 страниц через r.jina.ai
    for item in items[:2]:
        url = item.get("url", "")
        if not url:
            continue
        try:
            req2 = urllib.request.Request(
                f"https://r.jina.ai/{url}",
                headers={"Accept": "text/plain", "X-Return-Format": "text"},
            )
            with urllib.request.urlopen(req2, timeout=15) as resp:
                full_text = resp.read().decode("utf-8", errors="replace")
            if len(full_text) > 3000:
                full_text = full_text[:3000] + "..."
            item["content"] = full_text
        except Exception as e:
            logger.debug("Jina reader не смог открыть страницу %s: %s", url, e)

    return {"results": items}


def do_search(query: str, provider: str, tavily_client, brave_key: str | None, google_api_key: str | None, google_cx: str | None) -> dict:
    if provider == "brave":
        return brave_search(query, brave_key)
    if provider == "google":
        return google_search(query, google_api_key, google_cx)
    if provider == "jina":
        return jina_search(query)
    return tavily_client.search(query, max_results=5, search_depth="advanced")


def ensure_valuation_columns(db: sqlite3.Connection) -> None:
    existing = {row[1] for row in db.execute("PRAGMA table_info(lots)")}
    cols = {
        "price_min":              "real",
        "price_max":              "real",
        "price_quick_lot_min":    "real",
        "price_quick_lot_max":    "real",
        "price_wholesale_min":    "real",
        "price_wholesale_max":    "real",
        "price_retail_min":       "real",
        "price_retail_max":       "real",
        "valuation_confidence":   "text",
        "valuation_reasoning":    "text",
        "valuation_sources":      "text",
        "valuation_key_factors":  "text",
        "valuated_at":            "text",
    }
    for col, typ in cols.items():
        if col not in existing:
            db.execute(f"ALTER TABLE lots ADD COLUMN {col} {typ}")
    db.commit()


def fetch_lot(lot_id: str) -> dict:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    ensure_valuation_columns(db)
    row = db.execute("SELECT * FROM lots WHERE lot_id = ?", (lot_id,)).fetchone()
    db.close()
    if not row:
        raise SystemExit(f"Лот {lot_id!r} не найден в БД")
    return dict(row)


def save_valuation(lot_id: str, result: dict) -> None:
    import datetime as dt
    db = sqlite3.connect(DB_PATH)
    ensure_valuation_columns(db)
    db.execute("""
        UPDATE lots SET
            price_min               = ?,
            price_max               = ?,
            price_quick_lot_min     = ?,
            price_quick_lot_max     = ?,
            price_wholesale_min     = ?,
            price_wholesale_max     = ?,
            price_retail_min        = ?,
            price_retail_max        = ?,
            valuation_confidence    = ?,
            valuation_reasoning     = ?,
            valuation_sources       = ?,
            valuation_key_factors   = ?,
            valuated_at             = ?
        WHERE lot_id = ?
    """, (
        result.get("auction_price_min") or result.get("market_price_min"),
        result.get("auction_price_max") or result.get("market_price_max"),
        result.get("quick_lot_min"),
        result.get("quick_lot_max"),
        result.get("wholesale_min"),
        result.get("wholesale_max"),
        result.get("retail_min"),
        result.get("retail_max"),
        result.get("confidence"),
        result.get("reasoning"),
        json.dumps(result.get("sources") or [], ensure_ascii=False),
        json.dumps(result.get("key_factors") or [], ensure_ascii=False),
        dt.datetime.now().strftime("%d.%m.%Y %H:%M"),
        lot_id,
    ))
    db.commit()
    db.close()


def _extract_json(text: str) -> dict | None:
    """Извлекает первый JSON-объект из текста (модель может добавлять текст до/после)."""
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        return None


def make_llm_client(gemini_key: str | None, openrouter_key: str | None) -> tuple:
    """Returns (OpenAI client, is_gemini). Gemini key takes priority."""
    if gemini_key:
        return OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        ), True
    return OpenAI(
        api_key=openrouter_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://fedresurs-monitor",
            "X-Title": "Fedresurs Monitor",
        },
    ), False


def valuate(
    lot_id: str,
    model: str,
    openrouter_key: str | None,
    tavily_key: str | None,
    brave_key: str | None,
    google_api_key: str | None,
    google_cx: str | None,
    provider: str,
    gemini_key: str | None = None,
) -> None:
    lot = fetch_lot(lot_id)

    desc_preview = (lot.get("description") or "")[:100]
    print(f"Лот:    {lot_id}")
    print(f"Актив:  {desc_preview}...")
    print(f"Модель: {model}")
    print("─" * 60)

    documents = load_lot_documents(lot_id)
    if documents:
        print(f"Документов загружено: {len(documents)}")

    print(f"Поиск:  {provider}")
    print("─" * 60)
    logger.info("Запуск оценки лота %s, модель=%s, провайдер=%s", lot_id, model, provider)

    ai, is_gemini = make_llm_client(gemini_key, openrouter_key)
    tavily = TavilyClient(api_key=tavily_key) if (_TAVILY_AVAILABLE and tavily_key and provider == "tavily") else None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(lot, documents)},
    ]

    search_count = 0

    # Agentic loop
    while True:
        kwargs: dict = {"model": model, "messages": messages, "tools": TOOLS}
        if not is_gemini:
            kwargs["extra_body"] = {"reasoning": {"effort": "high"}}
        for _attempt in range(5):
            try:
                response = ai.chat.completions.create(**kwargs)
                break
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower() or "quota" in str(e).lower():
                    wait = 35 * (2 ** _attempt)
                    logger.warning("Rate limit (попытка %d/5): жду %dс...", _attempt + 1, wait)
                    print(f"  [rate limit] жду {wait}с...")
                    time.sleep(wait)
                    if _attempt == 4:
                        raise
                else:
                    raise

        choice = response.choices[0]
        msg = choice.message

        # Добавляем ответ модели в историю
        messages.append(msg.model_dump(exclude_unset=True))

        if choice.finish_reason == "tool_calls":
            for tool_call in msg.tool_calls:
                if tool_call.function.name == "web_search":
                    query = json.loads(tool_call.function.arguments)["query"]
                    search_count += 1
                    logger.debug("Поиск [%d]: %s", search_count, query)
                    print(f"  [{search_count}] Поиск: {query}")

                    results = do_search(query, provider, tavily, brave_key, google_api_key, google_cx)
                    content = format_search_results(results)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content,
                    })
        else:
            # Финальный ответ
            final = msg.content or ""
            break

    print(f"\nПоисков выполнено: {search_count}")
    print("─" * 60)
    print("\nОтвет модели:\n")
    print(final)

    # Структурированный вывод
    result = _extract_json(final)
    if result:
        fmt = lambda n: f"{float(n):,.0f}".replace(",", " ") if n else "—"
        print("\n" + "─" * 60)
        print(f"Цена торгов:     {fmt(result.get('auction_price_min'))} — {fmt(result.get('auction_price_max'))} ₽")
        if result.get("quick_lot_min"):
            print(f"Лот перекупу:    {fmt(result.get('quick_lot_min'))} — {fmt(result.get('quick_lot_max'))} ₽")
            print(f"Опт партиями:    {fmt(result.get('wholesale_min'))} — {fmt(result.get('wholesale_max'))} ₽")
            print(f"Розница:         {fmt(result.get('retail_min'))} — {fmt(result.get('retail_max'))} ₽")
        if result.get("price_per_sqm_min"):
            print(f"За кв.м:         {fmt(result['price_per_sqm_min'])} — {fmt(result['price_per_sqm_max'])} ₽/м²")
        print(f"Уверенность:     {result.get('confidence', '—')}")
        print(f"\n{result.get('reasoning', '')}")
        if result.get("key_factors"):
            print()
            for f in result["key_factors"]:
                print(f"  • {f}")
        if result.get("sources"):
            print("\nИсточники:")
            for s in result["sources"]:
                print(f"  — {s}")
        save_valuation(lot_id, result)
        logger.info("Оценка лота %s сохранена в БД (confidence=%s)", lot_id, result.get("confidence"))
        print("\n[сохранено в БД]")
    else:
        logger.error("Не удалось распарсить JSON из ответа модели для лота %s", lot_id)
        print("\n[не удалось распарсить ответ — в БД не сохранено]")


def main() -> None:
    _fix_stdout_encoding()

    if not _OPENAI_AVAILABLE or not _TAVILY_AVAILABLE:
        print("Установи зависимости: pip install -r requirements.txt")
        sys.exit(1)

    p = argparse.ArgumentParser(description="Рыночная оценка лота Федресурса через AI + web search")
    p.add_argument("lot_id", help="ID лота, например: 23595385-6")
    p.add_argument("--model",    default=DEFAULT_MODEL, help=f"Модель (default: {DEFAULT_MODEL})")
    p.add_argument("--provider", default=None, choices=["tavily", "brave", "google", "jina"], help="Поисковый провайдер (default: авто)")
    args = p.parse_args()

    gemini_key     = os.environ.get("GEMINI_API_KEY") or None
    openrouter_key = os.environ.get("OPENROUTER_API_KEY") or None
    tavily_key     = os.environ.get("TAVILY_API_KEY") or None
    brave_key      = os.environ.get("BRAVE_API_KEY") or None
    google_api_key = os.environ.get("GOOGLE_API_KEY") or None
    google_cx      = os.environ.get("GOOGLE_CX") or None

    if not gemini_key and not openrouter_key:
        print("Нужен GEMINI_API_KEY или OPENROUTER_API_KEY в .env")
        sys.exit(1)

    # Авто-выбор провайдера
    provider = args.provider
    if not provider:
        if tavily_key:
            provider = "tavily"
        elif google_api_key and google_cx:
            provider = "google"
        elif brave_key:
            provider = "brave"
        else:
            provider = "jina"

    if provider == "tavily" and not tavily_key:
        print("Нужен TAVILY_API_KEY в .env"); sys.exit(1)
    if provider == "brave" and not brave_key:
        print("Нужен BRAVE_API_KEY в .env"); sys.exit(1)
    if provider == "google" and not (google_api_key and google_cx):
        print("Нужны GOOGLE_API_KEY и GOOGLE_CX в .env"); sys.exit(1)

    valuate(args.lot_id, args.model, openrouter_key, tavily_key, brave_key, google_api_key, google_cx, provider, gemini_key=gemini_key)


if __name__ == "__main__":
    main()
