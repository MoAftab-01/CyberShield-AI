from app.core.config import settings

from app.services.llm.groq_provider import GroqProvider
from app.services.llm.openai_provider import OpenAIProvider


class ProviderFactory:

    _provider = None

    @classmethod
    def get_provider(cls):

        if cls._provider is not None:
            return cls._provider

        provider = settings.LLM_PROVIDER.lower()

        if provider == "groq":
            print(f"Loading Groq: {settings.GROQ_MODEL}")
            cls._provider = GroqProvider()

        elif provider == "openai":

            print(
                f"Loading OpenAI: {settings.OPENAI_MODEL}"
            )

            cls._provider = OpenAIProvider()

        else:

            raise ValueError(
                f"Unsupported provider: {provider}"
            )

        return cls._provider