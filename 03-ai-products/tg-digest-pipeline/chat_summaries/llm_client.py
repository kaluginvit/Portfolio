"""
Общий клиент для OpenRouter через openai SDK.
Ротация: для каждой модели перебирает все ключи, затем следующая модель.
"""

from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI, RateLimitError, APIError

_clients: dict[str, OpenAI] = {}


def _find_env(start: Path) -> Path | None:
    for parent in [start, *start.parents]:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return None


def _load_env(env_path: Path) -> None:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def _get_client(api_key: str, base_url: str) -> OpenAI:
    cache_key = f"{api_key}:{base_url}"
    if cache_key not in _clients:
        _clients[cache_key] = OpenAI(api_key=api_key, base_url=base_url)
    return _clients[cache_key]


def call_llm(
    messages: list[dict],
    models: list[str] | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.2,
    env_path: Path | None = None,
) -> tuple[str, str, dict]:
    """Вызывает LLM через OpenRouter с ротацией моделей и ключей.

    Args:
        messages: Список сообщений в формате [{"role": "user", "content": "..."}].
        models: Список моделей. Если None — берёт из OPENROUTER_MODELS.
        max_tokens: Максимальное число токенов в ответе.
        temperature: Температура генерации.
        env_path: Путь до .env. Если None — ищет вверх по дереву от cwd.

    Returns:
        Кортеж (content, model_used, usage_dict).

    Raises:
        RuntimeError: Если все комбинации модель/ключ вернули ошибку.
    """
    if env_path is not None:
        _load_env(env_path)
    else:
        found = _find_env(Path.cwd())
        if found:
            _load_env(found)

    keys_raw = os.environ.get("OPENROUTER_API_KEYS") or os.environ.get("OPENROUTER_API_KEY") or ""
    api_keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    if not api_keys:
        raise RuntimeError("Нет OpenRouter API-ключей (OPENROUTER_API_KEYS или OPENROUTER_API_KEY в .env)")

    if models is None:
        models_raw = os.environ.get("OPENROUTER_MODELS") or "minimax/minimax-m3:free"
        models = [m.strip() for m in models_raw.split(",") if m.strip()]

    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    errors: list[str] = []
    for model in models:
        for i, api_key in enumerate(api_keys, 1):
            label = f"[{model}/key-{i}]"
            try:
                response = _get_client(api_key, base_url).chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                content = response.choices[0].message.content or ""
                usage = response.usage
                print(f"{label} OK", flush=True)
                return content, model, {
                    "tokens_input": getattr(usage, "prompt_tokens", None),
                    "tokens_output": getattr(usage, "completion_tokens", None),
                }
            except RateLimitError as exc:
                print(f"{label} rate limit", flush=True)
                errors.append(f"{label}: rate limit — {exc}")
            except APIError as exc:
                print(f"{label} API error: {exc}", flush=True)
                errors.append(f"{label}: {exc}")
            except Exception as exc:
                print(f"{label} error: {exc}", flush=True)
                errors.append(f"{label}: {exc}")

    raise RuntimeError("Все OpenRouter-модели/ключи недоступны:\n" + "\n".join(errors))
