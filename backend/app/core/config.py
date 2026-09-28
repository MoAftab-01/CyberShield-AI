from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: JWT signing algorithms this application will accept.
#:
#: ``JWT_ALGORITHM`` is read from the environment, and the decoder trusts it
#: when verifying tokens. Without an allow-list, setting it to ``none`` - the
#: classic JWT confusion attack - or to a value the library treats loosely
#: would make forged tokens verifiable. Only HMAC algorithms are listed because
#: the application signs with a shared secret; an asymmetric algorithm here
#: would need a key pair that does not exist in this deployment.
ALLOWED_JWT_ALGORITHMS = frozenset(
    {"HS256", "HS384", "HS512"}
)

#: Below this length an HMAC secret is brute-forceable offline. Warned about
#: rather than enforced, because a hard failure at import would take down a
#: running deployment that is otherwise healthy - and a warning the operator
#: can see is more useful than an outage.
MIN_JWT_SECRET_LENGTH = 32


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

    # Comma-separated browser origins allowed to call the API.
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "https://cybershieldai-security.vercel.app"
    )

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
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    # Kept in step with the deployed value and with .env.example. A code
    # default that disagrees with production is a trap: anything run without
    # the environment variable silently answers with a different model.
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Retained for users who explicitly select the OpenAI provider.
    OPENAI_MODEL: str = "gpt-4o-mini"

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

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def _validate_jwt_algorithm(cls, value: str) -> str:
        algorithm = (value or "").strip().upper()

        if algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise ValueError(
                f"JWT_ALGORITHM must be one of "
                f"{sorted(ALLOWED_JWT_ALGORITHMS)}; got {value!r}. "
                "An unrestricted algorithm lets a forged token verify."
            )

        return algorithm

    @field_validator("JWT_SECRET")
    @classmethod
    def _check_jwt_secret_strength(cls, value: str) -> str:
        if len(value or "") < MIN_JWT_SECRET_LENGTH:
            print(
                "[security] JWT_SECRET is shorter than "
                f"{MIN_JWT_SECRET_LENGTH} characters. An HMAC secret this "
                "short can be brute-forced offline from a single token; "
                "rotate it to a long random value."
            )
        return value


settings = Settings()