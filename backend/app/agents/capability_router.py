from app.services.llm.provider_factory import ProviderFactory


class CapabilityRouter:

    @staticmethod
    def route(
        agent: str,
        capabilities: list[str],
        question: str,
    ) -> str:

        provider = ProviderFactory.get_provider()

        prompt = f"""
You are an AI routing engine.

Agent:
{agent}

Available capabilities:
{", ".join(capabilities)}

User Question:
{question}

Rules:
- Return ONLY one capability.
- It MUST be one of the available capabilities.
- No explanation.
- No punctuation.
"""

        response = provider.chat(prompt)
        print("\n========== CAPABILITY ROUTER ==========")
        print("Agent:", agent)
        print("Question:", question)
        print("LLM Raw Response:", response)
        print("=======================================\n")

        capability = response.strip().lower()

        if capability not in capabilities:
            return capabilities[0]

        return capability