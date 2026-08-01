from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==========================
    # Application
    # ==========================
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str

    # ==========================
    # Database
    # ==========================
    DATABASE_URL: str

    # ==========================
    # JWT Authentication
    # ==========================
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # ==========================
    # AI APIs
    # ==========================
    OPENAI_API_KEY: str = ""
    # ==========================
# LLM Configuration
# ==========================

    LLM_PROVIDER: str = "ollama"

    OLLAMA_MODEL: str = "llama3:latest"

    OPENAI_MODEL: str = "gpt-4o-mini"

    # Ollama
    AI_PROVIDER: str = "ollama"
    OLLAMA_MODEL: str = "llama3:latest"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ==========================
    # VirusTotal
    # ==========================
    VT_API_KEY: str = ""

    # ==========================
    # Logging
    # ==========================
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()