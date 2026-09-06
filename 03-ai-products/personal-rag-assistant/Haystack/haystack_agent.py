from __future__ import annotations

from collections import defaultdict, deque
import logging
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Deque, Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from haystack import component
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.tools import ComponentTool
from haystack.utils import Secret
from openai import OpenAI
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pinecone_manager import PineconeManager

DEFAULT_USER_MEMORY_NAMESPACE = "user-memory"
DEFAULT_KB_NAMESPACE = "knowledge-base"

_logger = logging.getLogger(__name__)


def _short(text: str, limit: int = 140) -> str:
    """Shorten text for compact logs."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


def _log(event: str, **fields: Any) -> None:
    parts = [f"[ASSISTANT:{event}]"]
    for key, value in fields.items():
        parts.append(f"{key}={value}")
    _logger.debug(" ".join(parts))


def _safe_get_metadata_text(match: Any) -> str:
    """Extract metadata.text from a Pinecone match."""
    metadata = match.get("metadata") if isinstance(match, dict) else getattr(match, "metadata", None)
    if isinstance(metadata, dict):
        return str(metadata.get("text") or "").strip()
    return ""


def _extract_top_memories(search_result: Any, limit: int = 5) -> list[str]:
    matches = search_result.get("matches") if isinstance(search_result, dict) else getattr(search_result, "matches", None)
    matches = matches or []

    memories: list[str] = []
    seen: set[str] = set()
    for match in matches:
        text = _safe_get_metadata_text(match)
        if not text or text in seen:
            continue
        seen.add(text)
        memories.append(text)
        if len(memories) >= limit:
            break
    return memories


def _extract_knowledge_snippets(search_result: Any, limit: int = 3) -> list[str]:
    """Extract retrieved knowledge chunks with optional source labels."""
    matches = search_result.get("matches") if isinstance(search_result, dict) else getattr(search_result, "matches", None)
    matches = matches or []

    snippets: list[str] = []
    seen: set[str] = set()
    for match in matches:
        metadata = match.get("metadata") if isinstance(match, dict) else getattr(match, "metadata", None)
        metadata = metadata if isinstance(metadata, dict) else {}
        text = str(metadata.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        source = str(metadata.get("source_path") or metadata.get("title") or "").strip()
        snippets.append(f"[{source}] {text}" if source else text)
        if len(snippets) >= limit:
            break
    return snippets


def _compact_text(text: str, limit: int = 350) -> str:
    """Compact user/assistant text before storing it in short-term history."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


def _append_tool_handler(tool_name: str):
    """Create a state merge handler that appends a tool name once per invocation."""

    def _handler(current: Any, _: Any) -> list[str]:
        items = list(current or [])
        items.append(tool_name)
        return items

    return _handler


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable `{name}`.")
    return value


def _get_openai_api_key() -> str:
    return os.getenv("PROXYAPI_API_KEY", "").strip() or _require_env("OPENAI_API_KEY")


def _get_openai_base_url() -> str:
    raw = os.getenv("PROXYAPI_BASE_URL", "").strip() or _require_env("OPENAI_BASE_URL")
    if raw.rstrip("/") == "https://api.proxyapi.ru/v1":
        return "https://openai.api.proxyapi.ru/v1"
    return raw


def _get_chat_model() -> str:
    return (
        os.getenv("OPENAI_CHAT_MODEL", "").strip()
        or os.getenv("OPENAI_MODEL", "").strip()
        or "gpt-4o-mini"
    )


def _get_vision_model() -> str:
    return os.getenv("OPENAI_VISION_MODEL", "").strip() or _get_chat_model()


def _get_user_memory_namespace() -> str:
    return os.getenv("PINECONE_USER_MEMORY_NAMESPACE", "").strip() or DEFAULT_USER_MEMORY_NAMESPACE


def _get_knowledge_namespace() -> str:
    return os.getenv("PINECONE_KB_NAMESPACE", "").strip() or DEFAULT_KB_NAMESPACE


def _normalize_breed_slug(breed: Optional[str]) -> str:
    if not breed:
        return ""
    slug = breed.strip().lower()
    slug = slug.replace(" ", "/")
    slug = re.sub(r"[^a-z/ -]", "", slug)
    slug = slug.replace("-", "")
    return slug.strip("/")


def estimate_vision_input_tokens(
    *,
    detail: str = "low",
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> int:
    """
    Estimate image input tokens using ProxyAPI/OpenAI vision rules.

    - low: fixed 85 input tokens
    - high: 85 + 170 per 512x512 tile after resizing
    """
    normalized = (detail or "low").strip().lower()
    if normalized in {"low", "auto"}:
        return 85

    if not width or not height or width <= 0 or height <= 0:
        # Safe default for a typical 1024x1024 image in high detail:
        # 85 base + 4 tiles * 170 = 765
        return 765

    scale = min(2048 / width, 2048 / height, 1.0)
    scaled_width = width * scale
    scaled_height = height * scale

    shortest = min(scaled_width, scaled_height)
    if shortest > 0 and shortest != 768:
        scale_to_shortest = 768 / shortest
        scaled_width *= scale_to_shortest
        scaled_height *= scale_to_shortest

    tiles = math.ceil(scaled_width / 512) * math.ceil(scaled_height / 512)
    return 85 + (tiles * 170)


def build_retry_session() -> Session:
    """Build a shared HTTP session with retries for flaky external APIs."""
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "ZeroCoderTelegramAssistant/1.0"})
    return session


class ConversationBuffer:
    """Short-term in-memory chat history for each Telegram user."""

    def __init__(self, max_turns: int = 6) -> None:
        self.max_messages = max(2, max_turns * 2)
        self._messages: dict[int, Deque[ChatMessage]] = defaultdict(lambda: deque(maxlen=self.max_messages))

    def get_messages(self, user_id: int) -> list[ChatMessage]:
        return list(self._messages[user_id])

    def append_turn(self, *, user_id: int, user_text: str, assistant_text: str) -> None:
        history = self._messages[user_id]
        history.append(ChatMessage.from_user(_compact_text(user_text)))
        history.append(ChatMessage.from_assistant(_compact_text(assistant_text)))

    def clear(self, user_id: int) -> None:
        self._messages.pop(user_id, None)


@dataclass
class AssistantResponse:
    mode: str
    text: str
    image_url: Optional[str] = None
    caption: Optional[str] = None
    memories: list[str] = field(default_factory=list)
    vision_input_tokens_estimate: Optional[int] = None
    source_tools: list[str] = field(default_factory=list)
    knowledge_snippets: list[str] = field(default_factory=list)


@component
class CatFactToolComponent:
    """Return a random cat fact from a public API."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @component.output_types(tool_result=str)
    def run(self) -> dict[str, str]:
        response = self.session.get("https://catfact.ninja/fact", timeout=15)
        response.raise_for_status()
        payload = response.json()
        fact = str(payload.get("fact") or "").strip()
        if not fact:
            raise ValueError("Cat API returned an empty fact.")
        return {"tool_result": f"Свежий факт о кошках: {fact}"}


@component
class WeatherToolComponent:
    """Fetch current weather for a city using wttr.in."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @component.output_types(tool_result=str)
    def run(self, location: str) -> dict[str, str]:
        city = (location or "").strip()
        if not city:
            raise ValueError("Weather tool requires a location.")

        response = self.session.get(f"https://wttr.in/{quote(city)}", params={"format": "j1"}, timeout=20)
        response.raise_for_status()
        payload = response.json()

        current = (payload.get("current_condition") or [{}])[0]
        area = (payload.get("nearest_area") or [{}])[0]
        resolved_city = ((area.get("areaName") or [{}])[0] or {}).get("value") or city

        temp_c = current.get("temp_C", "?")
        feels_like = current.get("FeelsLikeC", "?")
        humidity = current.get("humidity", "?")
        wind = current.get("windspeedKmph", "?")
        description = ((current.get("lang_ru") or current.get("weatherDesc") or [{}])[0] or {}).get("value") or "без описания"

        result = (
            f"Погода сейчас в {resolved_city}: {description}. "
            f"Температура {temp_c}°C, ощущается как {feels_like}°C, "
            f"влажность {humidity}%, ветер {wind} км/ч."
        )
        return {"tool_result": result}


@component
class WikipediaToolComponent:
    """Fetch a short Wikipedia summary for a requested topic."""

    SEARCH_URL = "https://ru.wikipedia.org/w/api.php"
    SUMMARY_URL = "https://ru.wikipedia.org/api/rest_v1/page/summary/{}"
    FALLBACK_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
    FALLBACK_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
    REQUEST_HEADERS = {
        "User-Agent": "ZeroCoderTelegramAssistant/1.0 (educational bot; contact: local-app)",
        "Accept": "application/json",
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    @component.output_types(tool_result=str)
    def run(self, topic: str) -> dict[str, str]:
        query = (topic or "").strip()
        if not query:
            raise ValueError("Wikipedia tool requires a topic.")

        title, extract, page_url = self._search_and_fetch(
            query=query,
            search_url=self.SEARCH_URL,
            summary_url=self.SUMMARY_URL,
        )

        if not title:
            title, extract, page_url = self._search_and_fetch(
                query=query,
                search_url=self.FALLBACK_SEARCH_URL,
                summary_url=self.FALLBACK_SUMMARY_URL,
            )

        if not title:
            return {"tool_result": f"В Wikipedia не нашлось статьи по запросу: {query}"}

        if not extract:
            return {
                "tool_result": (
                    f"Нашел статью Wikipedia: {title}, но краткое описание недоступно. "
                    f"Ссылка: {page_url or 'нет ссылки'}"
                )
            }

        result = f"{title}: {extract}"
        if page_url:
            result += f"\nИсточник: {page_url}"
        return {"tool_result": result}

    def _search_and_fetch(self, *, query: str, search_url: str, summary_url: str) -> tuple[str, str, str]:
        search_response = self.session.get(
            search_url,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "utf8": 1,
                "format": "json",
                "srlimit": 1,
            },
            headers=self.REQUEST_HEADERS,
            timeout=20,
        )
        search_response.raise_for_status()
        search_payload = search_response.json()
        search_items = (((search_payload.get("query") or {}).get("search")) or [])
        if not search_items:
            return "", "", ""

        title = str(search_items[0].get("title") or "").strip()
        if not title:
            return "", "", ""

        summary_response = self.session.get(
            summary_url.format(quote(title)),
            headers=self.REQUEST_HEADERS,
            timeout=20,
        )
        summary_response.raise_for_status()
        summary_payload = summary_response.json()

        extract = str(summary_payload.get("extract") or "").strip()
        page_url = (((summary_payload.get("content_urls") or {}).get("desktop") or {}).get("page")) or ""
        return title, extract, page_url


@component
class DogImageToolComponent:
    """Fetch a dog image URL from Dog CEO API."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @component.output_types(tool_result=str, image_url=str)
    def run(self, breed: Optional[str] = None) -> dict[str, str]:
        breed_slug = _normalize_breed_slug(breed)
        if breed_slug:
            url = f"https://dog.ceo/api/breed/{breed_slug}/images/random"
        else:
            url = "https://dog.ceo/api/breeds/image/random"

        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        payload = response.json()

        if payload.get("status") != "success":
            if breed_slug:
                fallback = self.session.get("https://dog.ceo/api/breeds/image/random", timeout=20)
                fallback.raise_for_status()
                payload = fallback.json()
            else:
                raise ValueError(f"Dog API failed: {payload}")

        image_url = str(payload.get("message") or "").strip()
        if not image_url:
            raise ValueError("Dog API returned an empty image URL.")

        breed_text = breed.strip() if breed else "случайной собаки"
        return {
            "tool_result": f"Получено фото {breed_text}. Если нужен разбор породы и краткая история, вызови анализатор.",
            "image_url": image_url,
        }


@component
class DogImageAnalyzerToolComponent:
    """Analyze a dog image with a vision-capable OpenAI-compatible model."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        detail: str = "low",
        max_output_tokens: int = 350,
    ) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.detail = detail if detail in {"low", "high", "auto"} else "low"
        self.max_output_tokens = max_output_tokens

    @component.output_types(
        tool_result=str,
        image_url=str,
        caption=str,
        response_mode=str,
        vision_input_tokens_estimate=int,
    )
    def run(self, user_request: str, image_url: str) -> dict[str, Any]:
        image = (image_url or "").strip()
        if not image:
            raise ValueError("Dog image analyzer requires image_url from state.")

        prompt = (
            "Ты анализируешь фото собаки для Telegram-бота. "
            "Определи вероятную породу или тип собаки, опиши заметные признаки, "
            "а затем дай короткую справку: происхождение породы, характер и интересный факт. "
            "Если породу нельзя определить уверенно, честно так и скажи. "
            "Отвечай по-русски, компактно, чтобы текст хорошо помещался в caption Telegram. "
            f"Запрос пользователя: {user_request}"
        )

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image, "detail": self.detail},
                    ],
                }
            ],
            max_output_tokens=self.max_output_tokens,
        )

        caption = (getattr(response, "output_text", None) or "").strip()
        if not caption:
            caption = "Не удалось получить подробный анализ изображения, но фото собаки найдено."

        estimate = estimate_vision_input_tokens(detail=self.detail)
        return {
            "tool_result": f"Анализ изображения собаки готов. Используй этот текст как основу ответа: {caption}",
            "image_url": image,
            "caption": caption,
            "response_mode": "photo",
            "vision_input_tokens_estimate": estimate,
        }


class HaystackTelegramAssistant:
    DEFAULT_MEMORY_TOP_K = 4
    DEFAULT_KNOWLEDGE_TOP_K = 3

    def __init__(self, memory_manager: Optional[PineconeManager] = None) -> None:
        load_dotenv()

        self.memory_manager = memory_manager or PineconeManager()
        self.http_session = build_retry_session()
        self.history = ConversationBuffer(max_turns=int(os.getenv("SHORT_TERM_HISTORY_TURNS", "6")))
        self.memory_namespace = _get_user_memory_namespace()
        self.knowledge_namespace = _get_knowledge_namespace()
        self.knowledge_top_k = int(os.getenv("KNOWLEDGE_TOP_K", str(self.DEFAULT_KNOWLEDGE_TOP_K)))
        self.api_key = _get_openai_api_key()
        self.api_base_url = _get_openai_base_url()
        self.chat_model = _get_chat_model()
        self.vision_model = _get_vision_model()
        self.vision_detail = os.getenv("OPENAI_VISION_DETAIL", "low").strip().lower() or "low"
        if self.vision_detail not in {"low", "high", "auto"}:
            self.vision_detail = "low"
        self.max_completion_tokens = int(os.getenv("OPENAI_MAX_COMPLETION_TOKENS", "500"))

        self.agent = Agent(
            chat_generator=OpenAIChatGenerator(
                api_key=Secret.from_token(self.api_key),
                api_base_url=self.api_base_url,
                model=self.chat_model,
                generation_kwargs={"max_completion_tokens": self.max_completion_tokens},
            ),
            tools=self._build_tools(),
            system_prompt=self._build_system_prompt([], []),
            exit_conditions=["text"],
            max_agent_steps=8,
            raise_on_tool_invocation_failure=False,
            state_schema={
                "dog_image_url": {"type": str},
                "photo_caption": {"type": str},
                "response_mode": {"type": str},
                "vision_input_tokens_estimate": {"type": int},
                "used_tools": {"type": list[str]},
            },
        )

    def _build_tools(self) -> list[ComponentTool]:
        cat_fact_tool = ComponentTool(
            component=CatFactToolComponent(session=self.http_session),
            name="cat_fact_tool",
            description="Используй, когда пользователь просит факт о кошках.",
            outputs_to_string={"source": "tool_result"},
            outputs_to_state={"used_tools": {"handler": _append_tool_handler("cat_fact_tool")}},
        )

        wikipedia_tool = ComponentTool(
            component=WikipediaToolComponent(session=self.http_session),
            name="wikipedia_tool",
            description=(
                "Используй, когда пользователь просит краткую справку, определение или информацию "
                "о человеке, технологии, термине, стране, событии или другом известном объекте."
            ),
            outputs_to_string={"source": "tool_result"},
            outputs_to_state={"used_tools": {"handler": _append_tool_handler("wikipedia_tool")}},
        )

        dog_image_tool = ComponentTool(
            component=DogImageToolComponent(session=self.http_session),
            name="dog_image_tool",
            description=(
                "Используй, когда пользователь просит фото собаки или хочет получить картинку собаки. "
                "Можно передать breed, если порода известна на английском."
            ),
            outputs_to_string={"source": "tool_result"},
            outputs_to_state={
                "dog_image_url": {"source": "image_url"},
                "used_tools": {"handler": _append_tool_handler("dog_image_tool")},
            },
        )

        dog_image_analyzer_tool = ComponentTool(
            component=DogImageAnalyzerToolComponent(
                api_key=self.api_key,
                base_url=self.api_base_url,
                model=self.vision_model,
                detail=self.vision_detail,
            ),
            name="dog_image_analyzer_tool",
            description=(
                "Используй после dog_image_tool, когда нужно описать уже найденную картинку собаки. "
                "Инструмент подготовит caption для Telegram и сохранит его в state."
            ),
            outputs_to_string={"source": "tool_result"},
            inputs_from_state={"dog_image_url": "image_url"},
            outputs_to_state={
                "dog_image_url": {"source": "image_url"},
                "photo_caption": {"source": "caption"},
                "response_mode": {"source": "response_mode"},
                "vision_input_tokens_estimate": {"source": "vision_input_tokens_estimate"},
                "used_tools": {"handler": _append_tool_handler("dog_image_analyzer_tool")},
            },
        )

        weather_tool = ComponentTool(
            component=WeatherToolComponent(session=self.http_session),
            name="weather_tool",
            description=(
                "Используй, когда пользователь спрашивает про текущую погоду в городе или населенном пункте."
            ),
            outputs_to_string={"source": "tool_result"},
            outputs_to_state={"used_tools": {"handler": _append_tool_handler("weather_tool")}},
        )

        return [cat_fact_tool, wikipedia_tool, dog_image_tool, dog_image_analyzer_tool, weather_tool]

    def _build_system_prompt(self, memories: list[str], knowledge_snippets: list[str]) -> str:
        if memories:
            memory_block = "\n".join(f"- {memory}" for memory in memories)
        else:
            memory_block = "- Сохраненной памяти по этой теме пока нет."

        if knowledge_snippets:
            knowledge_block = "\n".join(f"- {snippet}" for snippet in knowledge_snippets)
        else:
            knowledge_block = "- База знаний пока не дала релевантных фрагментов."

        return f"""
Ты персональный Telegram-ассистент на Haystack.

Твои правила:
1. Отвечай по-русски, дружелюбно и по делу.
2. Учитывай сохраненный контекст пользователя из Pinecone, но не выдумывай факты, если памяти нет.
3. Если в базе знаний есть полезные фрагменты, используй их как приоритетный источник фактов.
4. Если пользователь просит факт о кошках, используй `cat_fact_tool`.
5. Если пользователь просит кратко объяснить тему, рассказать о человеке, термине, технологии или событии, используй `wikipedia_tool`.
6. Если пользователь просит погоду, используй `weather_tool`. Если города нет, сначала уточни город.
7. Если пользователь просит показать собаку или прислать картинку собаки:
   - сначала используй `dog_image_tool`
   - затем используй `dog_image_analyzer_tool`, чтобы подготовить подпись к фото
8. Если инструменты дали данные, опирайся на них, а не на догадки.
9. Когда подготовлено фото собаки, пиши короткий сопроводительный текст. Само фото и caption бот отправит отдельно.

Доступная память пользователя:
{memory_block}

Релевантные фрагменты базы знаний:
{knowledge_block}
""".strip()

    def _build_messages(self, user_id: int, user_text: str) -> list[ChatMessage]:
        messages = self.history.get_messages(user_id)
        messages.append(ChatMessage.from_user(user_text))
        return messages

    def _remember_turn(self, *, user_id: int, user_text: str, response: AssistantResponse) -> None:
        assistant_text = response.caption or response.text
        if assistant_text:
            self.history.append_turn(user_id=user_id, user_text=user_text, assistant_text=assistant_text)

    def _load_memories(self, user_id: int, message_text: str) -> list[str]:
        try:
            result = self.memory_manager.query_by_text(
                text=message_text,
                top_k=self.DEFAULT_MEMORY_TOP_K,
                namespace=self.memory_namespace,
                filter={"user_id": user_id},
                include_metadata=True,
                include_values=False,
            )
        except Exception as exc:
            _log("MEMORY_ERR", user_id=user_id, error=repr(exc))
            return []

        memories = _extract_top_memories(result, limit=self.DEFAULT_MEMORY_TOP_K)
        _log("MEMORY", user_id=user_id, found=len(memories), items=repr([_short(item, 60) for item in memories]))
        return memories

    def _load_knowledge_context(self, message_text: str) -> list[str]:
        try:
            result = self.memory_manager.query_by_text(
                text=message_text,
                top_k=self.knowledge_top_k,
                namespace=self.knowledge_namespace,
                filter={"doc_type": "knowledge"},
                include_metadata=True,
                include_values=False,
            )
        except Exception as exc:
            _log("KNOWLEDGE_ERR", error=repr(exc))
            return []

        snippets = _extract_knowledge_snippets(result, limit=self.knowledge_top_k)
        _log("KNOWLEDGE", found=len(snippets), items=repr([_short(item, 70) for item in snippets]))
        return snippets

    def run(self, *, user_id: int, message_text: str) -> AssistantResponse:
        text = (message_text or "").strip()
        if not text:
            raise ValueError("Assistant requires a non-empty message_text.")

        memories = self._load_memories(user_id=user_id, message_text=text)
        knowledge_snippets = self._load_knowledge_context(text)
        system_prompt = self._build_system_prompt(memories, knowledge_snippets)
        messages = self._build_messages(user_id=user_id, user_text=text)

        _log("RUN", user_id=user_id, text=repr(_short(text)), model=self.chat_model)
        result = self.agent.run(
            messages=messages,
            system_prompt=system_prompt,
            used_tools=[],
        )

        last_message = result.get("last_message")
        answer_text = (getattr(last_message, "text", None) or "").strip()
        response_mode = str(result.get("response_mode") or "text").strip()
        image_url = str(result.get("dog_image_url") or "").strip() or None
        caption = str(result.get("photo_caption") or "").strip() or None
        vision_estimate = result.get("vision_input_tokens_estimate")
        vision_estimate = int(vision_estimate) if isinstance(vision_estimate, int) else None
        source_tools = [tool for tool in result.get("used_tools", []) if isinstance(tool, str)]
        source_tools = list(dict.fromkeys(source_tools))

        if response_mode == "photo" and image_url:
            final_caption = caption or answer_text or "Вот фото собаки."
            final_text = answer_text or "Подготовил фото собаки и подпись к нему."
            response = AssistantResponse(
                mode="photo",
                text=final_text,
                image_url=image_url,
                caption=final_caption,
                memories=memories,
                knowledge_snippets=knowledge_snippets,
                vision_input_tokens_estimate=vision_estimate,
                source_tools=source_tools,
            )
            self._remember_turn(user_id=user_id, user_text=text, response=response)
            return response

        response = AssistantResponse(
            mode="text",
            text=answer_text or "Не удалось сформировать ответ.",
            memories=memories,
            knowledge_snippets=knowledge_snippets,
            vision_input_tokens_estimate=vision_estimate,
            source_tools=source_tools,
        )
        self._remember_turn(user_id=user_id, user_text=text, response=response)
        return response

    def estimate_current_vision_tokens(self) -> int:
        return estimate_vision_input_tokens(detail=self.vision_detail)

    def clear_user_context(self, user_id: int) -> Any:
        self.history.clear(user_id)
        return self.memory_manager.delete_by_filter({"user_id": user_id}, namespace=self.memory_namespace)
