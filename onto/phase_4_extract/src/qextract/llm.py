"""Chat client for the llama-server that serves Qwen (OpenAI-compatible endpoint)."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, Final, Literal, override

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

DEFAULT_URL: Final = "http://127.0.0.1:18013"


@dataclass(frozen=True, slots=True)
class LlmUnavailableError(Exception):
    """The model server did not give a usable answer (network, status, or malformed body)."""

    url: str
    reason: str

    @override
    def __str__(self) -> str:
        return f"model server {self.url}: {self.reason}"


@dataclass(frozen=True, slots=True)
class Message:
    """One chat turn."""

    role: Literal["system", "user", "assistant"]
    content: str


class _Reply(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")
    content: str


class _Choice(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")
    message: _Reply


class _Response(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")
    choices: tuple[_Choice, ...]


def chat(base_url: str, messages: Sequence[Message], *, max_tokens: int = 9000, timeout: float = 3600.0) -> str:
    """Return the assistant text for the conversation; raise LlmUnavailableError on transport or format problems."""
    body = {
        "model": "local",
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    try:
        response = httpx.post(f"{base_url}/v1/chat/completions", json=body, timeout=timeout)
        response.raise_for_status()
        parsed = _Response.model_validate_json(response.content)
    except httpx.HTTPError as e:
        raise LlmUnavailableError(url=base_url, reason=f"{type(e).__name__}: {e}") from e
    except ValidationError as e:
        raise LlmUnavailableError(url=base_url, reason=f"unexpected response body: {e.error_count()} errors") from e
    if not parsed.choices:
        raise LlmUnavailableError(url=base_url, reason="no choices in response")
    return parsed.choices[0].message.content
