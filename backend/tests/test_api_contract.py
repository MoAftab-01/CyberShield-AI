"""API contract tests.

These go through FastAPI's real routing, dependency injection and response
serialisation, which the service-level tests deliberately bypass. What they
protect is the part a unit test cannot see: who is allowed to call an endpoint,
what status code comes back, and whether the response still matches the schema
the frontend was written against.

The schema assertions matter here because the copilot response gained fields.
Additive changes are safe, but a field being *removed* or renamed would break
the deployed frontend silently, and these tests fail loudly instead.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(user_factory):
    """A real bearer token for a real user."""

    from app.core.security import create_access_token

    user = user_factory()

    token = create_access_token(
        data={"sub": user.email},
    )

    return user, {"Authorization": f"Bearer {token}"}


class TestCopilotRequiresAuthentication:
    """The endpoint previously ran as a hard-coded ``user_id = 1`` with no
    authentication at all, so anyone could read and write that account."""

    def test_no_token_is_rejected(self, client):
        response = client.post("/copilot/ask", json={"question": "hello"})

        assert response.status_code == 403

    def test_a_malformed_token_is_rejected(self, client):
        response = client.post(
            "/copilot/ask",
            json={"question": "hello"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )

        assert response.status_code == 401

    def test_a_token_for_a_deleted_user_is_rejected(self, client, db_session):
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": "ghost@example.test"})

        response = client.post(
            "/copilot/ask",
            json={"question": "hello"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401


class TestCopilotResponseContract:

    def test_a_conversation_reply_matches_the_schema(
        self, client, auth_headers, monkeypatch
    ):
        from app.api import copilot_routes

        monkeypatch.setattr(
            copilot_routes.orchestrator, "handle", _fake_handle
        )

        _, headers = auth_headers
        response = client.post(
            "/copilot/ask", json={"question": "hello"}, headers=headers
        )

        assert response.status_code == 200
        body = response.json()

        # Fields the frontend has always read.
        for field in ("answer", "sources", "conversation_id", "retrieval_metrics"):
            assert field in body, field

        # Fields added by the orchestration work.
        for field in (
            "answer_basis",
            "relevance",
            "suggestions",
            "related_sources",
            "intent",
            "routing",
        ):
            assert field in body, field

        assert body["routing"]["source"] in {"rule", "llm", "default"}

    def test_a_conversation_id_is_optional(self, client, auth_headers, monkeypatch):
        """It used to be required, which made the general path a 500."""

        from app.api import copilot_routes

        monkeypatch.setattr(
            copilot_routes.orchestrator, "handle", _fake_handle
        )

        _, headers = auth_headers
        response = client.post(
            "/copilot/ask", json={"question": "hello"}, headers=headers
        )

        assert response.status_code == 200

    def test_an_empty_question_is_a_validation_error(self, client, auth_headers):
        _, headers = auth_headers

        response = client.post(
            "/copilot/ask", json={"question": ""}, headers=headers
        )

        assert response.status_code == 422

    def test_a_missing_question_is_a_validation_error(self, client, auth_headers):
        _, headers = auth_headers

        response = client.post("/copilot/ask", json={}, headers=headers)

        assert response.status_code == 422


class TestCopilotErrorMapping:

    def test_a_foreign_conversation_is_a_404_not_a_403(
        self, client, auth_headers, monkeypatch
    ):
        """A 403 would confirm the conversation exists, which is enough to
        enumerate other users' threads."""

        from app.api import copilot_routes

        async def refuse(**kwargs):
            raise PermissionError("That conversation does not belong to you.")

        monkeypatch.setattr(copilot_routes.orchestrator, "handle", refuse)

        _, headers = auth_headers
        response = client.post(
            "/copilot/ask",
            json={"question": "hello", "conversation_id": 1},
            headers=headers,
        )

        assert response.status_code == 404
        assert "does not belong to you" in response.json()["detail"]

    def test_an_invalid_question_length_is_a_422(
        self, client, auth_headers, monkeypatch
    ):
        from app.api import copilot_routes

        async def too_long(**kwargs):
            raise ValueError("The question must be under 4000 characters.")

        monkeypatch.setattr(copilot_routes.orchestrator, "handle", too_long)

        _, headers = auth_headers
        response = client.post(
            "/copilot/ask", json={"question": "hello"}, headers=headers
        )

        assert response.status_code == 422


class TestCopilotRateLimit:

    def test_a_burst_is_cut_off_with_a_retry_hint(
        self, client, auth_headers, monkeypatch
    ):
        """Each request can spend a Groq call from a shared quota."""

        from app.api import copilot_routes

        monkeypatch.setattr(
            copilot_routes.orchestrator, "handle", _fake_handle
        )
        monkeypatch.setattr(
            copilot_routes,
            "ASK_LIMITER",
            copilot_routes.RateLimiter(max_requests=3, window_seconds=60),
        )

        _, headers = auth_headers

        codes = [
            client.post(
                "/copilot/ask", json={"question": "hello"}, headers=headers
            ).status_code
            for _ in range(5)
        ]

        assert codes[:3] == [200, 200, 200]
        assert codes[3] == 429
        assert codes[4] == 429

    def test_the_retry_after_header_is_present_and_positive(
        self, client, auth_headers, monkeypatch
    ):
        from app.api import copilot_routes

        monkeypatch.setattr(
            copilot_routes.orchestrator, "handle", _fake_handle
        )
        monkeypatch.setattr(
            copilot_routes,
            "ASK_LIMITER",
            copilot_routes.RateLimiter(max_requests=1, window_seconds=60),
        )

        _, headers = auth_headers

        first = client.post(
            "/copilot/ask", json={"question": "hello"}, headers=headers
        )
        second = client.post(
            "/copilot/ask", json={"question": "hello"}, headers=headers
        )

        assert first.status_code == 200
        assert second.status_code == 429
        assert int(second.headers["Retry-After"]) >= 1

    def test_one_users_burst_does_not_block_another(
        self, client, auth_headers, monkeypatch
    ):
        from app.api import copilot_routes
        from app.core.security import create_access_token

        monkeypatch.setattr(
            copilot_routes.orchestrator, "handle", _fake_handle
        )
        monkeypatch.setattr(
            copilot_routes,
            "ASK_LIMITER",
            copilot_routes.RateLimiter(max_requests=1, window_seconds=60),
        )

        first_user, first_headers = auth_headers

        # A second, distinct account.
        from app.database.database import SessionLocal
        from app.database.models import User
        from app.core.security import hash_password

        session = SessionLocal()
        try:
            other = User(
                name="Other User",
                email="rate-limit-other@example.test",
                hashed_password=hash_password("CorrectHorse1!"),
            )
            session.add(other)
            session.commit()
            session.refresh(other)
            other_token = create_access_token(data={"sub": other.email})
        finally:
            session.close()

        other_headers = {"Authorization": f"Bearer {other_token}"}

        assert (
            client.post(
                "/copilot/ask", json={"question": "a"}, headers=first_headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/copilot/ask", json={"question": "b"}, headers=first_headers
            ).status_code
            == 429
        )
        assert (
            client.post(
                "/copilot/ask", json={"question": "c"}, headers=other_headers
            ).status_code
            == 200
        )


class TestConversationRoutesRequireAuthentication:

    @pytest.mark.parametrize(
        "method,path",
        [
            ("get", "/conversations"),
            ("get", "/conversations/1"),
            ("delete", "/conversations/1"),
            ("patch", "/conversations/1"),
        ],
    )
    def test_anonymous_access_is_refused(self, client, method, path):
        response = getattr(client, method)(path)

        assert response.status_code in {401, 403}

    def test_a_user_cannot_read_another_users_conversation(
        self, client, auth_headers, db_session
    ):
        from app.services.conversation_service import ConversationService

        owner, _ = auth_headers

        record = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="private"
        )

        from app.core.security import create_access_token, hash_password
        from app.database.database import SessionLocal
        from app.database.models import User

        session = SessionLocal()
        try:
            other = User(
                name="Intruder",
                email="idor-intruder@example.test",
                hashed_password=hash_password("CorrectHorse1!"),
            )
            session.add(other)
            session.commit()
            session.refresh(other)
            token = create_access_token(data={"sub": other.email})
        finally:
            session.close()

        headers = {"Authorization": f"Bearer {token}"}

        assert (
            client.get(f"/conversations/{record.id}", headers=headers).status_code
            == 404
        )
        assert (
            client.delete(f"/conversations/{record.id}", headers=headers).status_code
            == 404
        )


class TestUploadRoutesRequireAuthentication:

    def test_anonymous_upload_is_refused(self, client):
        response = client.post(
            "/upload",
            files={"file": ("a.txt", b"hello", "text/plain")},
        )

        assert response.status_code in {401, 403, 404}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fake_handle(question, db, user_id, conversation_id=None):
    """A standing orchestrator response, so route tests do not retrieve."""

    return {
        "answer": "STUB ANSWER",
        "sources": [],
        "retrieval_metrics": {"status": "skipped", "retrieved_count": 0},
        "answer_basis": "conversation",
        "relevance": "not_applicable",
        "related_sources": [],
        "suggestions": [],
        "intent": "GENERAL_CONVERSATION",
        "routing": {"source": "rule", "confidence": 0.9, "reason": "greeting"},
        "conversation_id": conversation_id or 1,
    }
