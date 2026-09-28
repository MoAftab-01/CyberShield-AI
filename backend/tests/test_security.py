"""Security regression tests.

Each test here corresponds to a defect that was reachable from the API. They
are written against the public interface rather than internals, so a future
refactor that reintroduces the behaviour fails the test rather than quietly
passing.
"""

import asyncio
import io

import pytest
from fastapi import UploadFile


def run(coroutine):
    """Run a coroutine to completion in a fresh event loop."""

    return asyncio.run(coroutine)


def upload(filename: str, content: bytes = b"hello") -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


class TestUploadPathTraversal:
    """A client-supplied filename must never escape the user's directory."""

    @pytest.mark.parametrize(
        "hostile",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//escape.pdf",
            "/absolute/path/escape.pdf",
            "normal/../../escape.pdf",
        ],
    )
    def test_traversal_is_confined_to_the_user_directory(self, hostile, tmp_path):
        from app.services.document_service import DocumentService

        user_dir = DocumentService._user_directory(999_001)
        stored = DocumentService.safe_filename(hostile, user_dir)

        # No separator survives, so the join cannot move up a level.
        assert "/" not in stored
        assert "\\" not in stored
        assert ".." not in stored

        resolved = DocumentService._resolve_within(user_dir, stored)
        assert resolved is not None
        assert user_dir.resolve() in resolved.parents

    def test_resolve_rejects_an_escape_even_unsanitised(self, tmp_path):
        """Defence in depth: the guard must hold without safe_filename."""

        from app.services.document_service import DocumentService

        user_dir = DocumentService._user_directory(999_002)

        assert DocumentService._resolve_within(user_dir, "../escape.pdf") is None
        assert (
            DocumentService._resolve_within(user_dir, "../../escape.pdf") is None
        )

    def test_delete_cannot_reach_outside_the_user_directory(self, tmp_path):
        from app.services.document_service import DocumentService

        outside = tmp_path / "important.txt"
        outside.write_text("must survive", encoding="utf-8")

        # The service resolves against its own upload root, so an absolute path
        # or a traversal is rejected rather than followed.
        assert (
            DocumentService.delete_file(999_003, f"../../{outside.name}") is False
        )
        assert outside.exists()

    def test_get_file_path_rejects_traversal(self):
        from app.services.document_service import DocumentService

        assert DocumentService.get_file_path(999_004, "../../.env") is None


class TestUploadLimits:

    def test_upload_over_the_limit_is_rejected(self, monkeypatch, tmp_path):
        from app.services.document_service import DocumentService

        monkeypatch.setattr(DocumentService, "MAX_UPLOAD_BYTES", 10)

        with pytest.raises(ValueError, match="upload limit"):
            run(
                DocumentService.save_uploaded_file(
                    file=upload("big.txt", b"x" * 100),
                    user_id=999_005,
                )
            )

    def test_rejected_upload_leaves_no_partial_file(self, monkeypatch):
        from app.services.document_service import DocumentService

        monkeypatch.setattr(DocumentService, "MAX_UPLOAD_BYTES", 10)

        with pytest.raises(ValueError):
            run(
                DocumentService.save_uploaded_file(
                    file=upload("big.txt", b"x" * 100),
                    user_id=999_006,
                )
            )

        # A truncated file left behind would later be indexed as a document.
        assert DocumentService.list_files(999_006) == []

    def test_disallowed_extension_is_rejected(self):
        from app.services.document_service import DocumentService

        with pytest.raises(ValueError, match="PDF, DOCX and TXT"):
            run(
                DocumentService.save_uploaded_file(
                    file=upload("payload.exe", b"MZ"),
                    user_id=999_007,
                )
            )

    def test_same_name_does_not_overwrite(self):
        from app.services.document_service import DocumentService

        first = run(
            DocumentService.save_uploaded_file(
                file=upload("report.txt", b"first"), user_id=999_008
            )
        )
        second = run(
            DocumentService.save_uploaded_file(
                file=upload("report.txt", b"second"), user_id=999_008
            )
        )

        assert first["filename"] != second["filename"]
        assert first["size"] == 5
        assert second["size"] == 6


class TestConversationOwnership:
    """Conversations must be readable only by their owner.

    The original routes hard-coded ``user_id = 1``, so every authenticated
    account shared one conversation list and could delete another's threads.
    """

    def test_read_is_scoped_to_the_owner(self, db_session, user_factory):
        from app.services.conversation_service import ConversationService

        owner = user_factory()
        intruder = user_factory()

        conversation = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="secret"
        )

        assert (
            ConversationService.get_conversation(
                db=db_session, conversation_id=conversation.id, user_id=owner.id
            )
            is not None
        )
        assert (
            ConversationService.get_conversation(
                db=db_session,
                conversation_id=conversation.id,
                user_id=intruder.id,
            )
            is None
        )

    def test_rename_is_scoped_to_the_owner(self, db_session, user_factory):
        from app.services.conversation_service import ConversationService

        owner = user_factory()
        intruder = user_factory()

        conversation = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="original title"
        )

        assert (
            ConversationService.rename(
                db=db_session,
                conversation_id=conversation.id,
                title="hijacked",
                user_id=intruder.id,
            )
            is None
        )

        reloaded = ConversationService.get_conversation(
            db=db_session, conversation_id=conversation.id, user_id=owner.id
        )
        assert reloaded["title"] == "original title"

    def test_delete_is_scoped_to_the_owner(self, db_session, user_factory):
        from app.services.conversation_service import ConversationService

        owner = user_factory()
        intruder = user_factory()

        conversation = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="keep me"
        )

        assert (
            ConversationService.delete(
                db=db_session,
                conversation_id=conversation.id,
                user_id=intruder.id,
            )
            is False
        )

        assert (
            ConversationService.get_conversation(
                db=db_session, conversation_id=conversation.id, user_id=owner.id
            )
            is not None
        )

    def test_delete_reports_whether_anything_was_deleted(
        self, db_session, user_factory
    ):
        from app.services.conversation_service import ConversationService

        owner = user_factory()
        conversation = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="temporary"
        )

        assert (
            ConversationService.delete(
                db=db_session, conversation_id=conversation.id, user_id=owner.id
            )
            is True
        )
        # Deleting twice must not report success the second time.
        assert (
            ConversationService.delete(
                db=db_session, conversation_id=conversation.id, user_id=owner.id
            )
            is False
        )

    def test_messages_are_not_readable_cross_tenant(self, db_session, user_factory):
        from app.services.conversation_service import ConversationService

        owner = user_factory()
        intruder = user_factory()

        conversation = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="confidential"
        )
        ConversationService.add_user_message(
            db=db_session,
            conversation_id=conversation.id,
            message="confidential content",
        )

        assert (
            ConversationService.load_history(
                db=db_session,
                conversation_id=conversation.id,
                user_id=intruder.id,
            )
            == []
        )


class TestRateLimiter:

    def test_allows_up_to_the_limit_then_refuses(self):
        from app.core.rate_limit import RateLimiter

        limiter = RateLimiter(max_requests=3, window_seconds=60)

        for _ in range(3):
            allowed, _ = limiter.check("u1")
            assert allowed

        allowed, retry_after = limiter.check("u1")
        assert not allowed
        assert retry_after > 0

    def test_keys_are_independent(self):
        from app.core.rate_limit import RateLimiter

        limiter = RateLimiter(max_requests=1, window_seconds=60)

        assert limiter.check("u1")[0]
        assert not limiter.check("u1")[0]
        # One user's burst must not lock out another.
        assert limiter.check("u2")[0]

    def test_window_expiry_frees_capacity(self):
        """Timing-sensitive by nature, so it waits for the window rather than
        sleeping a fixed amount that a loaded CI machine can overrun."""

        import time

        from app.core.rate_limit import RateLimiter

        limiter = RateLimiter(max_requests=1, window_seconds=0.05)

        assert limiter.check("u1")[0]
        assert not limiter.check("u1")[0]

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if limiter.check("u1")[0]:
                return
            time.sleep(0.01)

        pytest.fail("the rate-limit window never expired")

    def test_prune_drops_idle_keys(self):
        from app.core.rate_limit import RateLimiter

        limiter = RateLimiter(max_requests=1, window_seconds=0.01)
        limiter.check("stale")
        import time

        time.sleep(0.02)
        limiter.prune()

        assert limiter._hits == {}


class TestJwtAlgorithmPinning:
    """``JWT_ALGORITHM`` is environment-driven and the decoder trusts it.

    Setting it to ``none`` is the classic JWT confusion attack: the token's own
    header is believed about how it was signed, and an unsigned token verifies.
    """

    def test_hmac_algorithms_are_the_only_accepted_set(self):
        from app.core.config import ALLOWED_JWT_ALGORITHMS

        assert ALLOWED_JWT_ALGORITHMS == {"HS256", "HS384", "HS512"}

    def _settings_with(self, algorithm: str):
        from app.core.config import Settings

        return Settings(
            APP_NAME="t",
            APP_VERSION="t",
            ENVIRONMENT="test",
            DATABASE_URL="sqlite://",
            JWT_SECRET="x" * 40,
            JWT_ALGORITHM=algorithm,
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
        )

    @pytest.mark.parametrize("algorithm", ["none", "NONE", "RS256", "ES256", ""])
    def test_dangerous_algorithms_refuse_to_load(self, algorithm):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="JWT_ALGORITHM must be one"):
            self._settings_with(algorithm)

    @pytest.mark.parametrize("algorithm", ["HS256", "hs256", " hs512 "])
    def test_hmac_algorithms_load_and_are_normalised(self, algorithm):
        assert self._settings_with(algorithm).JWT_ALGORITHM in {
            "HS256",
            "HS512",
        }

    def test_a_short_secret_warns_but_does_not_block_startup(self, capsys):
        """A hard failure here would take down a healthy deployment."""

        from app.core.config import Settings

        settings = Settings(
            APP_NAME="t",
            APP_VERSION="t",
            ENVIRONMENT="test",
            DATABASE_URL="sqlite://",
            JWT_SECRET="short",
            JWT_ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
        )

        assert settings.JWT_SECRET == "short"
        assert "JWT_SECRET is shorter than" in capsys.readouterr().out


class TestVirusTotalFailureTolerance:
    """A third-party outage must not take the scanner down with it."""

    def test_missing_key_is_reported_not_raised(self, monkeypatch):
        from app.integrations import virustotal
        from app.integrations.virustotal import VirusTotalClient
        from app.core.config import settings

        monkeypatch.setattr(settings, "VT_API_KEY", "")

        result = run(VirusTotalClient.analyze_url("https://example.com"))

        assert result["available"] is False
        assert result["found"] is False
        assert "reason" in result

    def test_http_error_is_reported_not_raised(self, monkeypatch):
        import httpx

        from app.core.config import settings
        from app.integrations.virustotal import VirusTotalClient

        monkeypatch.setattr(settings, "VT_API_KEY", "test-key")

        class _BoomClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def get(self, *args, **kwargs):
                raise httpx.ConnectError("network down")

        monkeypatch.setattr(httpx, "AsyncClient", _BoomClient)

        result = run(VirusTotalClient.analyze_url("https://example.com"))

        assert result["available"] is False
        assert result["malicious"] == 0

    def test_unknown_url_is_available_but_not_found(self, monkeypatch):
        from app.core.config import settings
        from app.integrations.virustotal import VirusTotalClient
        import httpx

        monkeypatch.setattr(settings, "VT_API_KEY", "test-key")

        class _Response:
            status_code = 404

        class _Client:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def get(self, *args, **kwargs):
                return _Response()

        monkeypatch.setattr(httpx, "AsyncClient", _Client)

        result = run(VirusTotalClient.analyze_url("https://never-seen.test"))

        assert result["available"] is True
        assert result["found"] is False


class TestThreatAggregatorHonesty:
    """An unchecked URL must not be reported as having no detections."""

    def test_unavailable_intelligence_is_stated_and_lowers_confidence(self):
        from app.intelligence.threat_aggregator import ThreatAggregator

        result = ThreatAggregator.aggregate(
            local_score=95,
            vt_result={
                "available": False,
                "malicious": 0,
                "suspicious": 0,
                "reason": "VirusTotal rate limit reached for this API key.",
            },
        )

        assert any("rate limit" in reason for reason in result["reasons"])
        assert not any(
            "No known threat intelligence detections" in reason
            for reason in result["reasons"]
        )
        assert result["confidence"] < 60

    def test_clean_reputation_still_reports_no_detections(self):
        from app.intelligence.threat_aggregator import ThreatAggregator

        result = ThreatAggregator.aggregate(
            local_score=95,
            vt_result={"available": True, "malicious": 0, "suspicious": 0},
        )

        assert any(
            "No known threat intelligence detections" in reason
            for reason in result["reasons"]
        )

    def test_known_malicious_still_penalises(self):
        from app.intelligence.threat_aggregator import ThreatAggregator

        result = ThreatAggregator.aggregate(
            local_score=95,
            vt_result={"available": True, "malicious": 10, "suspicious": 0},
        )

        assert result["final_score"] < 95
        assert any("malicious vendors" in reason for reason in result["reasons"])
