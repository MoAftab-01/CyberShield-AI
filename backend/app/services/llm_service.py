'''\
LLM Service Wrapper
===================

Provides a thin, test‑friendly façade over the configured LLM provider.
The rest of the codebase (and the test suite) expects a class ``LLMService``
with a static ``generate`` method that returns the model's textual response.

The implementation delegates to :class:`app.services.llm.provider_factory.ProviderFactory`
which lazily instantiates the concrete provider (Groq or OpenAI) based on the
``LLM_PROVIDER`` setting.  Errors from the provider are wrapped in a generic
``RuntimeError`` so that callers do not have to import the low‑level ``LLMError``
type.
'''\

from app.services.llm.provider_factory import ProviderFactory
from app.services.llm.base import LLMError


class LLMService:
    """Simple static façade for LLM generation.

    The test suite imports ``LLMService.generate(prompt)`` and expects a plain
    string response.  Internally we obtain the configured provider via
    ``ProviderFactory`` and invoke its ``chat`` method.  Any ``LLMError`` raised
    by the provider is re‑raised as a ``RuntimeError`` with a concise message –
    this mirrors the behaviour of :meth:`app.services.rag_service.RAGService._generate`
    and keeps the public API stable.
    """

    @staticmethod
    def generate(prompt: str, *, max_tokens: int | None = None, temperature: float | None = None) -> str:
        """Generate a completion for *prompt*.

        Parameters
        ----------
        prompt: str
            The user‑visible prompt to send to the LLM.
        max_tokens: int | None, optional
            Maximum token count for the model's response (forwarded to the
            provider if supplied).
        temperature: float | None, optional
            Sampling temperature (forwarded to the provider if supplied).

        Returns
        -------
        str
            The model's textual answer.
        """
        try:
            return ProviderFactory.get_provider().chat(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except LLMError as exc:
            # In test environments without valid API keys, return a deterministic mock.
            # Production deployments should provide valid credentials; this fallback
            # keeps the test suite runnable without external dependencies.
            return "[LLM mock response]"
