"""LLM provider abstraction using OpenRouter."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

# Default models for different tasks
DEFAULT_CHECK_MODEL = "anthropic/claude-sonnet-4"
DEFAULT_CHAT_MODEL = "anthropic/claude-opus-4.5"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    """Base exception for LLM errors."""


class NoAPIKeyError(LLMError):
    """Raised when OPENROUTER_API_KEY is not set."""


class APIError(LLMError):
    """Raised when the API returns an error."""


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float


def get_api_key() -> str:
    """Get the OpenRouter API key from environment.

    Raises:
        NoAPIKeyError: If OPENROUTER_API_KEY is not set.
    """
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise NoAPIKeyError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Get an API key at https://openrouter.ai/keys"
        )
    return key


def get_model(task: str = "check") -> str:
    """Get the model to use for a task.

    Args:
        task: The task type ("check" or "chat").

    Returns:
        Model identifier string.
    """
    # Check for task-specific override first, then general override
    env_model = os.environ.get("CERTO_MODEL")
    if env_model:
        return env_model

    # Fall back to defaults
    if task == "chat":
        return DEFAULT_CHAT_MODEL
    return DEFAULT_CHECK_MODEL


def call_llm(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    task: str = "check",
    json_response: bool = False,
) -> LLMResponse:
    """Call the LLM via OpenRouter.

    Args:
        prompt: The user prompt.
        system: Optional system prompt.
        model: Model to use (overrides env/defaults).
        task: Task type for default model selection.
        json_response: Whether to request JSON output.

    Returns:
        LLMResponse with content and token usage.

    Raises:
        NoAPIKeyError: If API key is not set.
        APIError: If the API call fails.
    """
    api_key = get_api_key()
    model = model or get_model(task)

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if json_response:
        payload["response_format"] = {"type": "json_object"}

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OPENROUTER_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/metaist/certo",
            "X-Title": "certo",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise APIError(f"OpenRouter API error {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise APIError(f"Network error: {e.reason}") from e

    # Extract response
    choice = result.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "")
    usage = result.get("usage", {})

    # Cost can be in usage.cost or usage.cost_details.upstream_inference_cost (BYOK)
    cost = usage.get("cost", 0)
    if cost == 0:
        cost_details = usage.get("cost_details", {})
        cost = cost_details.get("upstream_inference_cost", 0)

    return LLMResponse(
        content=content,
        model=result.get("model", model),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        cost=cost,
    )
