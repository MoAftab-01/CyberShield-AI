from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -----------------------------
    # Application Settings
    # -----------------------------
    APP_NAME: str = "CyberShield AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # -----------------------------
    # Database Settings
    # -----------------------------
    DATABASE_URL: str

    # -----------------------------
    # JWT Authentication
    # -----------------------------
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # -----------------------------
    # OpenAI
    # -----------------------------
    OPENAI_API_KEY: str = ""

    # -----------------------------
    # Logging
    # -----------------------------
    LOG_LEVEL: str = "INFO"

    VT_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()