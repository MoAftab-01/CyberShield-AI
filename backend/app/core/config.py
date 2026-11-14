from pathlib import Path

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

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

#: Normal runtime must fail before serving requests with a weak signing secret.
#: Explicit test settings retain the warning for existing synthetic fixtures.
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    # ==========================
    # Application
    # ==========================
    APP_NAME: str = "CyberShield"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    # Server-only opt-in; no default catalog or benchmark data admission.
    CYBERGPT_V2_ENABLED: bool = False
    CYBERGPT_V2_CATALOG_MANIFEST: Path | None = None

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
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

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
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("CYBERGPT_V2_ENABLED", mode="before")
    @classmethod
    def _validate_cybergpt_v2_enabled(cls, value):
        if type(value) is bool:
            return value
        if isinstance(value, str) and value.strip().casefold() in {"true", "false"}:
            return value.strip().casefold() == "true"
        raise ValueError("CYBERGPT_V2_ENABLED accepts only true or false.")

    @field_validator("CYBERGPT_V2_CATALOG_MANIFEST")
    @classmethod
    def _validate_cybergpt_v2_manifest(cls, value):
        if value is not None and not value.is_absolute():
            raise ValueError("CYBERGPT_V2_CATALOG_MANIFEST requires an absolute path.")
        return value

    @field_validator("ENVIRONMENT")
    @classmethod
    def _normalize_environment(cls, value: str) -> str:
        environment = value.strip().lower()
        if not environment:
            raise ValueError("ENVIRONMENT must not be empty.")
        return environment

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, value: str, info: ValidationInfo) -> str:
        try:
            url = make_url(value)
        except (ArgumentError, ValueError):
            raise ValueError("DATABASE_URL must be a valid database URL.") from None

        backend = url.get_backend_name()
        if backend == "sqlite":
            if info.data.get("ENVIRONMENT") != "test":
                raise ValueError("SQLite is allowed only with ENVIRONMENT=test.")
        elif backend != "postgresql":
            raise ValueError("DATABASE_URL must use PostgreSQL outside SQLite tests.")
        elif not url.host or not url.database or not url.database.strip():
            raise ValueError("PostgreSQL DATABASE_URL requires a host and database name.")

        return value

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
    def _check_jwt_secret_strength(cls, value: str, info: ValidationInfo) -> str:
        if not value.strip():
            raise ValueError("JWT_SECRET must not be empty.")
        if len(value.strip()) < MIN_JWT_SECRET_LENGTH:
            if info.data.get("ENVIRONMENT") != "test":
                raise ValueError(
                    f"JWT_SECRET must contain at least {MIN_JWT_SECRET_LENGTH} "
                    "characters outside tests; configure a randomly generated secret."
                )
            print(
                "[security] JWT_SECRET is shorter than "
                f"{MIN_JWT_SECRET_LENGTH} characters. An HMAC secret this "
                "short can be brute-forced offline from a single token; "
                "rotate it to a long random value."
            )
        return value


settings = Settings()
