import os

from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider


class ProviderFactory:

    @staticmethod
    def get_provider():

        provider = os.getenv(
            "AI_PROVIDER",
            "ollama",
        ).lower()

        if provider == "openai":
            return OpenAIProvider()

        return OllamaProvider()