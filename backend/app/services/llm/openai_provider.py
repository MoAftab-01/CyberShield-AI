from openai import OpenAI

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    def chat(
        self,
        prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are CyberGPT, an expert cybersecurity assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content.strip()

    def chat_bounded(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_attempts: int | None = None,
    ) -> str:

        options = {}
        if max_tokens is not None:
            options["max_tokens"] = max_tokens
        if timeout is not None:
            options["timeout"] = timeout
        if max_attempts is not None and (type(max_attempts) is not int or max_attempts != 1):
            raise ValueError("OpenAI bounded calls require one attempt.")
        client = self.client if max_attempts is None else self.client.with_options(max_retries=0)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt or self.DEFAULT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2 if temperature is None else temperature,
            **options,
        )

        return response.choices[0].message.content.strip()