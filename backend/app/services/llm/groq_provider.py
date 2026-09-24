from openai import OpenAI

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider


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

    def chat(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are CyberGPT, an expert cybersecurity assistant."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Groq returned an empty response")

        return content.strip()
