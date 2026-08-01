import requests

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):

    def __init__(self):

        self.model = settings.OLLAMA_MODEL

        self.base_url = "http://localhost:11434"

    def chat(
        self,
        prompt: str,
    ) -> str:

        response = requests.post(

            f"{self.base_url}/api/generate",

            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },

            timeout=180,

        )

        response.raise_for_status()

        data = response.json()

        return data["response"].strip()