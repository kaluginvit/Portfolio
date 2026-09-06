import logging
import os

from fastapi import HTTPException
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
)
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Ты финансовый аналитик. Отвечай строго на основе предоставленных данных таблицы.
Всегда называй конкретные числа и суммы из данных. Отвечай по-русски, кратко и по существу."""


def get_summary(table_data: str) -> str:
    logger.info("get_summary: model=%s, table_data_len=%d", MODEL, len(table_data))
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "system",
                    "content": f"{SYSTEM_PROMPT}\n\nДанные таблицы:\n\n{table_data}",
                },
                {
                    "role": "user",
                    "content": (
                        "Проанализируй эти финансовые данные и дай краткое саммари: "
                        "топ-3 ключевых инсайта. Выдели самые важные цифры и тренды. "
                        "Формат: три пункта, каждый начинается с эмодзи."
                    ),
                },
            ],
        )
        result = response.choices[0].message.content
        logger.info("get_summary: response_len=%d", len(result) if result else 0)
        return result
    except OpenAIError as e:
        logger.error("get_summary API error: %s", e)
        raise HTTPException(status_code=502, detail=f"Ошибка AI-сервиса при генерации саммари: {e}")
    except Exception as e:
        logger.error("get_summary unexpected error: %s", e)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка при генерации саммари.")


def chat(message: str, history: list, table_data: str) -> str:
    messages = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nДанные таблицы:\n\n{table_data}",
        }
    ]
    for item in history:
        messages.append({"role": "user", "content": item["user"]})
        messages.append({"role": "assistant", "content": item["assistant"]})
    messages.append({"role": "user", "content": message})

    logger.info("chat: model=%s, messages=%d, message_len=%d", MODEL, len(messages), len(message))
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=messages,
        )
        result = response.choices[0].message.content
        logger.info("chat: response_len=%d", len(result) if result else 0)
        return result
    except OpenAIError as e:
        logger.error("chat API error: %s", e)
        raise HTTPException(status_code=502, detail=f"Ошибка AI-сервиса в чате: {e}")
    except Exception as e:
        logger.error("chat unexpected error: %s", e)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка в чате.")
