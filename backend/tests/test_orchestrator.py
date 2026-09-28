"""End-to-end orchestration tests.

These exercise the actual entry point the ``/copilot/ask`` route calls, with
retrieval and the model replaced. What they cover is the wiring: that the
decision reaches the right destination, that both turns are persisted whichever
destination it was, and that the user's own secrets are not written to the log.
"""

import asyncio

import pytest

from app.agents.orchestrator import CyberGPTOrchestrator, MAX_QUESTION_LENGTH
from app.services import rag_service


@pytest.fixture
def orchestrator():
    return CyberGPTOrchestrator()


@pytest.fixture
def offline_retrieval(monkeypatch):
    """No index in the test environment; retrieval reports empty."""

    monkeypatch.setattr(
        rag_service.HybridRetriever,
        "search_with_metrics",
        staticmethod(lambda **kwargs: ([], {"status": "empty"})),
    )


def ask(orchestrator, question, db, user, **kwargs):
    return asyncio.run(
        orchestrator.handle(question=question, db=db, user_id=user.id, **kwargs)
    )


def stored_turns(db, conversation_id, user_id):
    from app.services.conversation_service import ConversationService

    history = ConversationService.load_history(
        db=db, conversation_id=conversation_id, user_id=user_id
    )
    return [(message.role, message.content) for message in history]


class TestDispatch:

    def test_a_greeting_takes_the_conversation_path(
        self, orchestrator, db_session, user_factory, offline_retrieval, stub_llm
    ):
        user = user_factory()

        result = ask(orchestrator, "hello", db_session, user)

        assert result["answer_basis"] == "conversation"
        assert result["intent"] == "GENERAL_CONVERSATION"
        assert result["retrieval_metrics"]["status"] == "skipped"
        assert len(stub_llm) == 1

    def test_a_tool_request_takes_the_tool_path(
        self, orchestrator, db_session, user_factory, stub_llm
    ):
        user = user_factory()

        def explode(**kwargs):
            raise AssertionError("a tool request must not run retrieval")

        import app.agents.orchestrator as module

        original = rag_service.HybridRetriever.search_with_metrics
        rag_service.HybridRetriever.search_with_metrics = staticmethod(explode)
        try:
            result = ask(orchestrator, "Generate a strong password", db_session, user)
        finally:
            rag_service.HybridRetriever.search_with_metrics = original

        assert result["answer_basis"] == "tool"
        assert result["tool_used"] == "Password Generator"
        assert result["tool_ok"] is True
        assert result["retrieval_metrics"]["status"] == "skipped"
        assert stub_llm == []

    def test_a_knowledge_question_takes_the_retrieval_path(
        self, orchestrator, db_session, user_factory, offline_retrieval, stub_llm
    ):
        user = user_factory()

        result = ask(orchestrator, "How does zero trust work?", db_session, user)

        assert result["answer_basis"] == "general_knowledge"
        assert result["relevance"] == "irrelevant"
        assert len(stub_llm) == 1

    def test_every_result_carries_its_routing_decision(
        self, orchestrator, db_session, user_factory, offline_retrieval
    ):
        user = user_factory()

        result = ask(orchestrator, "hello", db_session, user)

        assert result["routing"]["source"] in {"rule", "llm", "default"}
        assert 0.0 <= result["routing"]["confidence"] <= 1.0
        assert result["routing"]["reason"]


class TestPersistence:

    def test_a_new_conversation_is_created_and_reported(
        self, orchestrator, db_session, user_factory, offline_retrieval
    ):
        user = user_factory()

        result = ask(orchestrator, "hello", db_session, user)

        assert isinstance(result["conversation_id"], int)

    def test_both_turns_are_stored_for_a_conversation_reply(
        self, orchestrator, db_session, user_factory, offline_retrieval
    ):
        user = user_factory()

        result = ask(orchestrator, "hello", db_session, user)
        turns = stored_turns(db_session, result["conversation_id"], user.id)

        assert [role for role, _ in turns] == ["user", "assistant"]
        assert turns[0][1] == "hello"

    def test_both_turns_are_stored_for_a_tool_call(
        self, orchestrator, db_session, user_factory
    ):
        """The original bug: a tool answer had nowhere to be recorded."""

        user = user_factory()

        result = ask(orchestrator, "Generate a strong password", db_session, user)
        turns = stored_turns(db_session, result["conversation_id"], user.id)

        assert [role for role, _ in turns] == ["user", "assistant"]
        assert "Generated Password" in turns[1][1]

    def test_a_follow_up_continues_the_same_conversation(
        self, orchestrator, db_session, user_factory, offline_retrieval
    ):
        user = user_factory()

        first = ask(orchestrator, "hello", db_session, user)
        second = ask(
            orchestrator,
            "what can you do?",
            db_session,
            user,
            conversation_id=first["conversation_id"],
        )

        assert second["conversation_id"] == first["conversation_id"]

        turns = stored_turns(db_session, first["conversation_id"], user.id)
        assert len(turns) == 4

    def test_a_pasted_password_is_not_written_to_the_log(
        self, orchestrator, db_session, user_factory
    ):
        user = user_factory()

        result = ask(
            orchestrator, "analyze password: Tr0ub4dor&3", db_session, user
        )
        turns = stored_turns(db_session, result["conversation_id"], user.id)

        stored_user_message = turns[0][1]

        assert "Tr0ub4dor&3" not in stored_user_message
        assert "analyze password:" in stored_user_message

    def test_the_scored_password_is_not_in_the_stored_answer(
        self, orchestrator, db_session, user_factory
    ):
        user = user_factory()

        result = ask(
            orchestrator, "analyze password: Tr0ub4dor&3", db_session, user
        )
        turns = stored_turns(db_session, result["conversation_id"], user.id)

        assert "Tr0ub4dor&3" not in turns[1][1]


class TestValidation:

    def test_an_empty_question_is_rejected(
        self, orchestrator, db_session, user_factory
    ):
        user = user_factory()

        with pytest.raises(ValueError):
            ask(orchestrator, "   ", db_session, user)

    def test_an_overlong_question_is_rejected(
        self, orchestrator, db_session, user_factory
    ):
        """Every extra character is prompt tokens on a metered quota."""

        user = user_factory()

        with pytest.raises(ValueError):
            ask(orchestrator, "x" * (MAX_QUESTION_LENGTH + 1), db_session, user)

    def test_a_question_at_the_limit_is_accepted(
        self, orchestrator, db_session, user_factory, offline_retrieval
    ):
        user = user_factory()

        result = ask(orchestrator, "x" * MAX_QUESTION_LENGTH, db_session, user)

        assert result["answer"]


class TestTenantIsolation:

    def test_answering_into_another_users_conversation_is_refused(
        self, orchestrator, db_session, user_factory, offline_retrieval
    ):
        from app.services.conversation_service import ConversationService

        owner = user_factory()
        intruder = user_factory()

        record = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="private"
        )

        with pytest.raises(PermissionError):
            ask(
                orchestrator,
                "hello",
                db_session,
                intruder,
                conversation_id=record.id,
            )

    def test_a_refused_question_is_not_recorded_anywhere(
        self, orchestrator, db_session, user_factory, offline_retrieval
    ):
        """Ownership is checked before the user's message is written, so a
        rejected request leaves no trace in the target thread."""

        from app.services.conversation_service import ConversationService

        owner = user_factory()
        intruder = user_factory()

        record = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="private"
        )

        with pytest.raises(PermissionError):
            ask(
                orchestrator,
                "let me in",
                db_session,
                intruder,
                conversation_id=record.id,
            )

        contents = [
            content for _, content in stored_turns(db_session, record.id, owner.id)
        ]
        assert not any("let me in" in content for content in contents)

        # And the intruder got no thread of their own out of the attempt.
        assert (
            ConversationService.get_conversation(
                db=db_session, conversation_id=record.id, user_id=intruder.id
            )
            is None
        )


class TestProviderOutage:

    def test_a_total_model_outage_still_returns_a_response(
        self, orchestrator, db_session, user_factory, offline_retrieval, failing_llm
    ):
        """A 500 here would be indistinguishable from a bug in the route."""

        user = user_factory()

        result = ask(orchestrator, "How does zero trust work?", db_session, user)

        assert "temporarily unavailable" in result["answer"]
        assert result["conversation_id"]

    def test_a_tool_still_works_when_the_model_is_down(
        self, orchestrator, db_session, user_factory, failing_llm
    ):
        """Tools are deterministic; they do not depend on the provider."""

        user = user_factory()

        result = ask(orchestrator, "Generate a strong password", db_session, user)

        assert result["tool_ok"] is True
        assert "Generated Password" in result["answer"]
