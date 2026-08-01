from app.services.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):

    def chat(
        self,
        prompt: str,
    ) -> str:

        raise NotImplementedError(
            "OpenAI provider will be added later."
        )