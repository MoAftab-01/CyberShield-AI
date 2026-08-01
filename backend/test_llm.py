from app.services.llm_service import LLMService

response = LLMService.generate(
    "Explain SQL Injection in two sentences."
)

print()

print(response)