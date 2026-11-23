"""LLM provider interface.

Every provider implements one method. ``chat`` gained optional parameters
rather than gaining new methods, so all existing call sites - which pass a
prompt positionally - keep working unchanged.

The additions exist for three concrete reasons:

* ``system_prompt`` - routers and summarisers need a different instruction than
  the CyberGPT persona. Without it they have to smuggle instructions into the
  user prompt, which is the same channel as untrusted content.
* ``max_tokens`` - an unbounded completion on a free-tier quota is both a cost
  and a latency risk. A caller that only needs a one-word label can now say so.
* ``temperature`` - classification must be deterministic; prose should not be.
"""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):

    #: Applied when a caller does not override it.
    DEFAULT_SYSTEM_PROMPT = "You are CyberGPT, an expert cybersecurity assistant."
    DEFAULT_TEMPERATURE = 0.2

    @abstractmethod
    def chat(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
    ) -> str:
        """Send a prompt to the LLM and return the response text.

        Raises ``LLMError`` when the provider cannot produce a usable answer,
        so callers can degrade to a non-LLM path instead of returning a 500.
        """
        raise NotImplementedError


    def chat_bounded(
        self, prompt: str, *, timeout: float, system_prompt: str | None = None,
        max_tokens: int | None = None, temperature: float | None = None,
        max_attempts: int = 1,
    ) -> str:
        """Explicit opt-in: legacy chat signatures/defaults remain unchanged."""
        if type(max_attempts) is not int or max_attempts != 1:
            raise ValueError("Bounded generation requires one attempt.")
        return self.chat(prompt, timeout=timeout, system_prompt=system_prompt,
                         max_tokens=max_tokens, temperature=temperature, max_attempts=1)


class LLMError(RuntimeError):
    """Raised when an LLM call fails after retries.

    A distinct type because every caller of ``chat`` wants to catch *this* and
    fall back, rather than catch ``Exception`` and accidentally swallow real
    bugs alongside provider outages.
    """
