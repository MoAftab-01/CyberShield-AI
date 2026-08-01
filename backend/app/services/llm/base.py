from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):

    @abstractmethod
    def chat(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and return the response.
        """
        pass