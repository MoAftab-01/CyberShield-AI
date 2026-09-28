"""Shared test configuration.

The application reads settings at import time and ``.env`` points at a
PostgreSQL host that only exists inside the compose network, so the environment
is set before anything from ``app`` is imported. Tests run against a temporary
SQLite file: the models are portable and this keeps the suite runnable without
a database server, which matters because CI has none.

The working directory is also moved into that temporary folder. Several stores
address themselves with relative paths - ``uploads/``, ``vector_db/`` and
``knowledge_base/`` - and without this the suite would write test uploads into
the real uploads directory and, worse, replace the real retrieval index with a
throwaway one built from the hashed embedding backend. Running somewhere empty
also matches a fresh deployment, where no index exists yet.

No test in this suite makes a network call. The LLM provider is replaced with a
stub wherever it is reached, so the suite is fast, deterministic, and does not
consume the Groq quota. A test that needs a real model would be measuring the
provider, not this code.
"""

import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

#: A file-backed SQLite database in a temp directory. An in-memory database
#: would not survive across the connections FastAPI's dependency opens.
_TEMP_DIR = tempfile.mkdtemp(prefix="cybershield-tests-")

#: Must happen before anything under ``app`` is imported: the document service
#: creates its upload directory at import time.
os.chdir(_TEMP_DIR)

os.environ.setdefault("APP_NAME", "CyberShield AI (test)")
os.environ.setdefault("APP_VERSION", "test")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR) / 'test.db'}"
os.environ.setdefault("JWT_SECRET", "test-secret-value-that-is-long-enough-1234")
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("GROQ_API_KEY", "test-key-not-used")
os.environ.setdefault("VT_API_KEY", "")

# Keep the embedding layer on the hashed backend. The semantic model is a
# 90MB download and its behaviour is covered by the evaluation harness, which
# measures it on the labelled set; unit tests must not depend on a download.
os.environ.setdefault("EMBEDDING_BACKEND", "hash")

import pytest  # noqa: E402

#: Shared across the session so generated emails never repeat.
_EMAIL_COUNTER = {"n": 0}


@pytest.fixture(scope="session", autouse=True)
def _database_schema():
    """Create the schema once for the whole session.

    This calls the application's own ``init_db`` rather than importing the
    models here. The models live in three packages and are registered by
    ``init_db``; building the schema any other way would let a new model be
    added without the test database noticing.
    """

    from app.database.init_db import init_db

    init_db()
    yield


@pytest.fixture
def db_session():
    """A session bound to the test database."""

    from app.database.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user_factory(db_session):
    """Create users with unique emails, returning the ORM instance.

    The counter is module-level rather than per-test: the whole session shares
    one SQLite file, so a per-test counter would reuse ``user1@example.test``
    and violate the unique constraint as soon as the first test's rows were
    still present.
    """

    from app.database.models import User
    from app.core.security import hash_password

    created = []

    def make(email: str | None = None):
        _EMAIL_COUNTER["n"] += 1
        user = User(
            name=f"Test User {_EMAIL_COUNTER['n']}",
            email=email or f"user{_EMAIL_COUNTER['n']}@example.test",
            hashed_password=hash_password("CorrectHorse1!"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        created.append(user)
        return user

    yield make

    # Best effort: a test that failed mid-transaction leaves the session
    # unusable, and that must not be reported as a second failure in teardown.
    try:
        for user in created:
            db_session.delete(user)
        db_session.commit()
    except Exception:  # pragma: no cover - cleanup only
        db_session.rollback()


@pytest.fixture
def stub_llm(monkeypatch):
    """Replace the LLM provider with a recorder.

    Returns the list of prompts the code under test produced, so a test can
    assert on *which* prompt path ran, not only on the answer.
    """

    calls = []

    class _StubProvider:
        DEFAULT_SYSTEM_PROMPT = "stub"
        DEFAULT_TEMPERATURE = 0.0

        def chat(self, prompt, **kwargs):
            calls.append({"prompt": prompt, "kwargs": kwargs})
            return "STUB ANSWER"

    from app.services.llm import provider_factory

    monkeypatch.setattr(
        provider_factory.ProviderFactory,
        "get_provider",
        classmethod(lambda cls: _StubProvider()),
    )

    return calls


@pytest.fixture
def failing_llm(monkeypatch):
    """Make every LLM call fail the way a provider outage does."""

    from app.services.llm import provider_factory
    from app.services.llm.base import LLMError

    class _FailingProvider:
        DEFAULT_SYSTEM_PROMPT = "stub"
        DEFAULT_TEMPERATURE = 0.0

        def chat(self, prompt, **kwargs):
            raise LLMError("simulated provider outage")

    monkeypatch.setattr(
        provider_factory.ProviderFactory,
        "get_provider",
        classmethod(lambda cls: _FailingProvider()),
    )
