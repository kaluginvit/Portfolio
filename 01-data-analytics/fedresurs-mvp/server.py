"""
server.py — локальный сервер для оценки лотов через браузер

Usage:
    python server.py
    # открой http://localhost:5000
"""

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file

load_dotenv(Path(__file__).parent / ".env")

from openai import OpenAI
from tavily import TavilyClient

from valuate import (
    DB_PATH, SYSTEM_PROMPT, TOOLS,
    do_search, ensure_valuation_columns, format_search_results, save_valuation,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("server")

app = Flask(__name__)
DASHBOARD = Path(__file__).parent / "reports" / "dashboard.html"

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
TAVILY_KEY     = os.environ.get("TAVILY_API_KEY") or None
BRAVE_KEY      = os.environ.get("BRAVE_API_KEY") or None
GOOGLE_KEY     = os.environ.get("GOOGLE_API_KEY") or None
GOOGLE_CX      = os.environ.get("GOOGLE_CX") or None
MODEL          = "stealth/ox-alpha"

if TAVILY_KEY:
    PROVIDER = "tavily"
elif GOOGLE_KEY and GOOGLE_CX:
    PROVIDER = "google"
elif BRAVE_KEY:
    PROVIDER = "brave"
else:
    PROVIDER = None

# Защита от запуска без API-ключей
if not OPENROUTER_KEY:
    logger.warning("OPENROUTER_API_KEY не задан — /valuate endpoint будет недоступен")


def build_prompt(description: str, classifier: str = "") -> str:
    lines = []
    if classifier:
        lines.append(f"**Тип актива:** {classifier}")
    lines.append(f"\n**Описание:**\n{description}")
    lines.append("\n---\nОпредели рыночную стоимость этого актива.")
    return "\n".join(lines)


def run_valuation(description: str, classifier: str = "") -> dict | None:
    """Запускает agentic loop оценки актива. Возвращает dict с результатом или None."""
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY не задан")

    ai = OpenAI(
        api_key=OPENROUTER_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://fedresurs-monitor",
            "X-Title": "Fedresurs Monitor",
        },
    )
    tavily = TavilyClient(api_key=TAVILY_KEY) if TAVILY_KEY and PROVIDER == "tavily" else None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": build_prompt(description, classifier)},
    ]

    max_iterations = 20  # Защита от бесконечного цикла
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        response = ai.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            extra_body={"reasoning": {"effort": "high"}},
        )
        choice = response.choices[0]
        msg = choice.message
        messages.append(msg.model_dump(exclude_unset=True))

        if choice.finish_reason == "tool_calls":
            for tool_call in msg.tool_calls:
                if tool_call.function.name == "web_search":
                    query = json.loads(tool_call.function.arguments)["query"]
                    logger.info("Поиск: %s", query)
                    results = do_search(query, PROVIDER, tavily, BRAVE_KEY, GOOGLE_KEY, GOOGLE_CX)
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      format_search_results(results),
                    })
        else:
            try:
                return json.loads((msg.content or "").strip())
            except (json.JSONDecodeError, ValueError):
                logger.warning("Не удалось распарсить JSON из финального ответа модели")
                return None

    logger.error("Agentic loop превысил лимит итераций (%d)", max_iterations)
    return None


@app.route("/")
def index():
    return send_file(DASHBOARD)


@app.route("/valuate", methods=["POST"])
def valuate_endpoint():
    data        = request.get_json() or {}
    description = (data.get("description") or "").strip()
    classifier  = (data.get("classifier")  or "").strip()
    lot_id      = (data.get("lot_id")      or "").strip()

    if not description:
        return jsonify({"error": "Описание не может быть пустым"}), 400
    if not PROVIDER:
        return jsonify({"error": "Не настроен поисковый провайдер (TAVILY_API_KEY / BRAVE_API_KEY / GOOGLE_API_KEY)"}), 500

    result = run_valuation(description, classifier)
    if not result:
        return jsonify({"error": "Модель не вернула структурированный ответ"}), 500

    if lot_id:
        save_valuation(lot_id, result)
        result["saved_to_db"] = True

    return jsonify(result)


if __name__ == "__main__":
    print("Сервер: http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
