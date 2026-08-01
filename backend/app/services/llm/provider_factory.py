from app.core.config import settings

from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider


class ProviderFactory:

    _provider = None

    @classmethod
    def get_provider(cls):

        if cls._provider is not None:
            return cls._provider

        provider = settings.LLM_PROVIDER.lower()

        if provider == "openai":

            print(
                f"Loading OpenAI: {settings.OPENAI_MODEL}"
            )

            cls._provider = OpenAIProvider()

        elif provider == "ollama":

            print(
                f"Loading Ollama: {settings.OLLAMA_MODEL}"
            )

            cls._provider = OllamaProvider()

        else:

            raise ValueError(
                f"Unsupported provider: {provider}"
            )

        return cls._provider