"""Answering-path tests for :class:`RAGService`.

The behaviour under test is the one the assistant previously did not have: it
now decides *what kind of question* it is answering and labels the result. The
thresholds asserted here are the measured ones from
``evaluation/confidence_calibration.json``, so if retrieval or the embedding
model changes enough to invalidate them, these tests are where it surfaces.
"""

import pytest
from langchain_core.documents import Document

from app.services import rag_service
from app.services.rag_service import (
    DOCUMENT_AT_LEAST,
    IRRELEVANT_BELOW,
    RAGService,
)


def passage(similarity: float, filename: str = "nist-sp-800-53.pdf", page: int = 0):
    """A retrieved chunk carrying the metadata retrieval attaches."""

    return Document(
        page_content="Access control policy excerpt.",
        metadata={
            "filename": filename,
            "page": page,
            "source_folder": "knowledge_base",
            "semantic_similarity": similarity,
        },
    )


def ok_metrics(top: float):
    return {
        "status": "ok",
        "retrieved_count": 1,
        "top_semantic_similarity": top,
    }


def lexical_passage(
    text: str,
    lexical_rank: int,
    term_coverage: float,
    filename: str = "nist.pdf",
    page: int = 0,
):
    return Document(
        page_content=text,
        metadata={
            "filename": filename,
            "page": page,
            "source_folder": "knowledge_base",
            "semantic_similarity": 0.1,
            "lexical_rank": lexical_rank,
            "query_term_coverage": term_coverage,
        },
    )


class TestRelevanceGate:
    """The gate separates three measured groups of questions."""

    def test_a_well_matched_passage_is_document(self):
        assert (
            RAGService._relevance([passage(0.72)], ok_metrics(0.72))
            == "document"
        )

    def test_a_near_miss_is_related_not_document(self):
        """Measured overlap: a security question the corpus does not cover can
        score 0.61, inside the knowledge-base range."""

        top = (IRRELEVANT_BELOW + DOCUMENT_AT_LEAST) / 2
        assert RAGService._relevance([passage(top)], ok_metrics(top)) == "related"

    def test_an_unrelated_question_is_irrelevant(self):
        """Measured: unrelated questions peak at 0.2046."""

        assert (
            RAGService._relevance([passage(0.20)], ok_metrics(0.20))
            == "irrelevant"
        )

    def test_the_boundaries_are_inclusive_where_they_should_be(self):
        assert (
            RAGService._relevance(
                [passage(DOCUMENT_AT_LEAST)], ok_metrics(DOCUMENT_AT_LEAST)
            )
            == "document"
        )
        assert (
            RAGService._relevance(
                [passage(IRRELEVANT_BELOW)], ok_metrics(IRRELEVANT_BELOW)
            )
            == "related"
        )

    def test_no_documents_is_irrelevant(self):
        assert RAGService._relevance([], ok_metrics(0.0)) == "irrelevant"

    def test_a_degraded_retrieval_is_irrelevant(self):
        """``empty``/``no_match`` mean the index could not answer, which must
        not be reported as a low-confidence document match."""

        for status in ("empty", "no_match"):
            assert (
                RAGService._relevance([], {"status": status}) == "irrelevant"
            )

    def test_the_highest_scoring_passage_decides(self):
        documents = [passage(0.31, page=0), passage(0.80, page=1)]

        assert RAGService._relevance(documents, ok_metrics(0.80)) == "document"

    def test_a_missing_similarity_is_treated_as_zero(self):
        bare = Document(page_content="x", metadata={"filename": "a.pdf"})

        assert RAGService._relevance([bare], ok_metrics(0.0)) == "irrelevant"

    def test_hash_mode_uses_exact_phrase_and_lexical_evidence(self):
        document = lexical_passage(
            "Use parameterized queries to prevent SQL injection attacks.",
            lexical_rank=1,
            term_coverage=0.75,
        )

        assert RAGService._relevance(
            [document],
            {"status": "ok", "embedding_backend": "hash"},
            "How can developers prevent SQL injection?",
        ) == "document"

    def test_hash_mode_recognizes_an_exact_standard_control_id(self):
        document = lexical_passage(
            "PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks.",
            lexical_rank=4,
            term_coverage=0.583,
            filename="NIST-SP-800-218.pdf",
            page=19,
        )

        assert RAGService._relevance(
            [document],
            {"status": "ok", "embedding_backend": "hash"},
            "What does NIST SSDF practice PW.1 require teams to consider during software design?",
        ) == "document"

    def test_hash_mode_promotes_a_supported_aes_strength_comparison(self):
        document = lexical_passage(
            "AES-128 provides 128 bits of security strength, while AES-256 provides 256 bits.",
            lexical_rank=1,
            term_coverage=0.429,
            filename="OWASP-ASVS-5.0.0.pdf",
            page=104,
        )

        assert RAGService._relevance(
            [document],
            {"status": "ok", "embedding_backend": "hash"},
            "What is the security-strength difference between AES-128 and AES-256?",
        ) == "document"

    def test_hash_mode_does_not_promote_generic_token_overlap(self):
        document = lexical_passage(
            "Adversaries must overcome multiple layers of security safeguards.",
            lexical_rank=1,
            term_coverage=0.75,
        )

        assert RAGService._relevance(
            [document],
            {"status": "ok", "embedding_backend": "hash"},
            "How does a Kerberoasting attack work?",
        ) == "irrelevant"

    def test_hash_mode_never_treats_hash_cosine_as_semantic_evidence(self):
        document = passage(0.95)

        assert RAGService._relevance(
            [document],
            {"status": "ok", "embedding_backend": "hash"},
            "Explain this topic",
        ) == "irrelevant"


class TestAnsweringPaths:
    """Each path returns the labels the route publishes."""

    @pytest.fixture
    def conversation(self, db_session, user_factory):
        from app.services.conversation_service import ConversationService

        user = user_factory()
        record = ConversationService.start_chat(
            db=db_session, user_id=user.id, first_question="hello"
        )
        return user, record.id

    def _with_retrieval(self, monkeypatch, documents, metrics):
        monkeypatch.setattr(
            rag_service.HybridRetriever,
            "search_with_metrics",
            staticmethod(lambda **kwargs: (documents, metrics)),
        )

    def test_a_covered_question_is_answered_from_the_documents(
        self, db_session, conversation, monkeypatch, stub_llm
    ):
        user, conversation_id = conversation
        self._with_retrieval(monkeypatch, [passage(0.78)], ok_metrics(0.78))

        result = RAGService.answer(
            question="What does NIST say about access control?",
            db=db_session,
            user_id=user.id,
            conversation_id=conversation_id,
        )

        assert result["answer_basis"] == "document"
        assert result["relevance"] == "document"
        assert len(result["sources"]) == 1
        assert result["related_sources"] == []
        # The retrieved passage must be in the prompt, or the answer is not
        # grounded in it whatever the label says.
        assert "Access control policy excerpt." in stub_llm[0]["prompt"]

    def test_an_uncovered_question_is_labelled_and_cites_nothing(
        self, db_session, conversation, monkeypatch, stub_llm
    ):
        user, conversation_id = conversation
        self._with_retrieval(monkeypatch, [passage(0.15)], ok_metrics(0.15))

        result = RAGService.answer(
            question="What is the capital of France?",
            db=db_session,
            user_id=user.id,
            conversation_id=conversation_id,
        )

        assert result["answer_basis"] == "general_knowledge"
        assert result["sources"] == []
        assert "Not from the knowledge base" in result["answer"]
        # The near-miss passages still travel back, as related reading.
        assert len(result["related_sources"]) == 1

    def test_a_document_request_the_documents_do_not_cover_says_so(
        self, db_session, conversation, monkeypatch
    ):
        from app.agents.intents import Intent

        user, conversation_id = conversation
        self._with_retrieval(monkeypatch, [], {"status": "empty"})

        result = RAGService.answer(
            question="Search my documents for the MFA rollout plan",
            db=db_session,
            user_id=user.id,
            conversation_id=conversation_id,
            intent=Intent.DOCUMENT_SEARCH,
        )

        assert "Not from your documents" in result["answer"]

    def test_unsupported_standard_reference_does_not_call_the_model(
        self, stub_llm
    ):
        result = RAGService._general_answer(
            question="What does NIST SP 800-999 control AC-99 require?",
            db=None,
            conversation_id=1,
            documents=[],
            metrics={"status": "no_match", "embedding_backend": "hash"},
            persist=False,
        )

        assert "Specific reference not verified" in result["answer"]
        assert "AC-99" in result["answer"]
        assert result["sources"] == []
        assert stub_llm == []

    def test_the_general_answer_is_stored_with_its_label(
        self, db_session, conversation, monkeypatch
    ):
        """The stored turn must carry the label too, or reopening the thread
        shows a general answer with no indication that it is one."""

        from app.services.conversation_service import ConversationService

        user, conversation_id = conversation
        self._with_retrieval(monkeypatch, [], {"status": "empty"})

        RAGService.answer(
            question="Explain the CIA triad.",
            db=db_session,
            user_id=user.id,
            conversation_id=conversation_id,
        )

        history = ConversationService.load_history(
            db=db_session, conversation_id=conversation_id, user_id=user.id
        )
        stored = [message.content for message in history if message.role == "assistant"]

        assert stored
        assert "Not from the knowledge base" in stored[-1]

    def test_retrieval_is_scoped_to_the_calling_user(
        self, db_session, conversation, monkeypatch
    ):
        """``include_uploads`` without a ``user_id`` would search every user's
        documents."""

        user, conversation_id = conversation
        seen = {}

        def capture(**kwargs):
            seen.update(kwargs)
            return [], {"status": "empty"}

        monkeypatch.setattr(
            rag_service.HybridRetriever, "search_with_metrics", staticmethod(capture)
        )

        RAGService.answer(
            question="What is in my documents?",
            db=db_session,
            user_id=user.id,
            conversation_id=conversation_id,
        )

        assert seen["user_id"] == user.id
        assert seen.get("include_uploads") is True


class TestConversationPath:

    def test_a_greeting_skips_retrieval_entirely(
        self, db_session, user_factory, monkeypatch
    ):
        from app.services.conversation_service import ConversationService

        user = user_factory()
        record = ConversationService.start_chat(
            db=db_session, user_id=user.id, first_question="hi"
        )

        def explode(**kwargs):
            raise AssertionError("retrieval must not run for a greeting")

        monkeypatch.setattr(
            rag_service.HybridRetriever, "search_with_metrics", staticmethod(explode)
        )

        result = RAGService.converse(
            question="hello",
            db=db_session,
            user_id=user.id,
            conversation_id=record.id,
        )

        assert result["answer_basis"] == "conversation"
        assert result["retrieval_metrics"]["status"] == "skipped"
        assert result["sources"] == []


class TestProviderOutage:

    def test_a_document_answer_degrades_instead_of_raising(
        self, db_session, user_factory, monkeypatch, failing_llm
    ):
        from app.services.conversation_service import ConversationService

        user = user_factory()
        record = ConversationService.start_chat(
            db=db_session, user_id=user.id, first_question="q"
        )

        monkeypatch.setattr(
            rag_service.HybridRetriever,
            "search_with_metrics",
            staticmethod(lambda **kwargs: ([passage(0.78)], ok_metrics(0.78))),
        )

        result = RAGService.answer(
            question="What does NIST say?",
            db=db_session,
            user_id=user.id,
            conversation_id=record.id,
        )

        assert "temporarily unavailable" in result["answer"]
        # Retrieval worked, so the sources are still returned - the user can
        # read the passages even though the summary failed.
        assert len(result["sources"]) == 1
        assert result["answer_basis"] == "document"

    def test_a_conversation_reply_degrades_instead_of_raising(
        self, db_session, user_factory, failing_llm
    ):
        from app.services.conversation_service import ConversationService

        user = user_factory()
        record = ConversationService.start_chat(
            db=db_session, user_id=user.id, first_question="hi"
        )

        result = RAGService.converse(
            question="hello",
            db=db_session,
            user_id=user.id,
            conversation_id=record.id,
        )

        assert "temporarily unavailable" in result["answer"]
        assert result["conversation_id"] == record.id


class TestConversationOwnership:

    def test_answering_into_another_users_thread_is_refused(
        self, db_session, user_factory
    ):
        from app.services.conversation_service import ConversationService

        owner = user_factory()
        intruder = user_factory()

        record = ConversationService.start_chat(
            db=db_session, user_id=owner.id, first_question="private"
        )

        with pytest.raises(PermissionError):
            RAGService.ask(
                question="append to someone else's thread",
                db=db_session,
                user_id=intruder.id,
                conversation_id=record.id,
            )

    def test_a_new_conversation_is_created_when_none_is_given(
        self, db_session, user_factory, monkeypatch
    ):
        user = user_factory()

        monkeypatch.setattr(
            rag_service.HybridRetriever,
            "search_with_metrics",
            staticmethod(lambda **kwargs: ([], {"status": "empty"})),
        )

        result = RAGService.ask(
            question="Explain defence in depth.",
            db=db_session,
            user_id=user.id,
        )

        assert isinstance(result["conversation_id"], int)
        assert result["conversation_id"] > 0


class TestHelpers:

    def test_sources_deduplicate_by_file_and_page(self):
        documents = [passage(0.8, page=3), passage(0.7, page=3)]

        sources = RAGService._sources(documents)

        assert len(sources) == 1
        # Pages are 1-based in the response and 0-based in storage.
        assert sources[0]["page"] == 4

    def test_sources_survive_a_missing_folder(self):
        document = Document(
            page_content="x", metadata={"filename": "a.pdf", "page": 0}
        )

        sources = RAGService._sources([document])

        assert sources[0]["filename"] == "a.pdf"
        assert sources[0]["folder"] is None

    def test_rendered_context_labels_every_passage_with_its_source(self):
        rendered = RAGService._render_context([passage(0.8, page=2)])

        assert "nist-sp-800-53.pdf" in rendered
        assert "page 3" in rendered

    def test_an_empty_context_says_so_rather_than_rendering_nothing(self):
        assert "No matching knowledge-base passages" in RAGService._render_context([])

    def test_suggestions_are_chosen_by_topic(self):
        password = RAGService._suggestions("How do I store passwords?")
        phishing = RAGService._suggestions("How do I spot a phishing domain?")
        other = RAGService._suggestions("Explain the OSI model.")

        assert password != phishing
        assert "credential" in " ".join(password).lower() or "password" in " ".join(
            password
        ).lower()
        assert other
