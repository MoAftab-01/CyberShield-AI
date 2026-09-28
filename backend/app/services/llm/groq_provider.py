"""Groq provider.

Groq is the production LLM. On the free tier it rate-limits aggressively and
occasionally returns 5xx or times out, and the original implementation let
those surface as 500s to the user: an exception from ``create`` propagated all
the way up the request. Three things changed, all of them bounded so the
free tier stays viable:

* an explicit request timeout, so a hung connection cannot pin a Render worker
  for the full 60s the frontend waits;
* a small retry with exponential backoff, but only for failures that can
  actually succeed on retry (rate limits, timeouts, connection errors, 5xx) -
  retrying an invalid API key just burns quota;
* a typed ``LLMError`` at the boundary so callers fall back deliberately.
"""

import time

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider, LLMError

DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1.0


class GroqProvider(BaseLLMProvider):
    """OpenAI-compatible client for Groq's hosted inference API."""

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is required when LLM_PROVIDER=groq"
            )

        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
        )

    def chat(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
    ) -> str:

        request = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or self.DEFAULT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": (
                self.DEFAULT_TEMPERATURE if temperature is None else temperature
            ),
            "timeout": DEFAULT_TIMEOUT_SECONDS if timeout is None else timeout,
        }

        if max_tokens is not None:
            request["max_tokens"] = max_tokens

        last_error: Exception | None = None

        for attempt in range(MAX_ATTEMPTS):

            try:
                response = self.client.chat.completions.create(**request)
            except (RateLimitError, APITimeoutError, APIConnectionError) as error:
                last_error = error
            except APIStatusError as error:
                # 4xx other than 429 will not fix itself; 5xx might.
                if error.status_code < 500:
                    raise LLMError(
                        f"Groq rejected the request: {error}"
                    ) from error
                last_error = error
            except Exception as error:  # pragma: no cover - defensive
                raise LLMError(f"Groq request failed: {error}") from error
            else:
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
                last_error = LLMError("Groq returned an empty response")

            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))

        raise LLMError(f"Groq unavailable after {MAX_ATTEMPTS} attempts: {last_error}")
