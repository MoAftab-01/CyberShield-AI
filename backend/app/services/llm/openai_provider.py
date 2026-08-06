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