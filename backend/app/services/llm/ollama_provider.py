import requests

from app.services.llm.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url

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