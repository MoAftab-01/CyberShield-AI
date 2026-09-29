"""Knowledge-base answering.

This is where the assistant decides what kind of question it is answering and
says so. Three behaviours, each labelled in the response:

* **document** - retrieval found passages that answer the question; the model
  writes from them and cites them.
* **general_knowledge** - retrieval found nothing relevant; the model answers
  from its own knowledge, cites nothing, and the response says the answer does
  not come from the documents.
* **conversation** - a greeting or a "what can you do" message; no retrieval,
  no long answer.

The previous implementation had only the first path, with a prompt that
forbade using anything but the supplied context and prescribed a six-section
report format. Every question was therefore forced through the knowledge base:
a greeting, a CVE lookup and a question about a topic the corpus does not cover
all got the same treatment, which is why the assistant behaved like a search
box over a handful of PDFs.

The confidence gate is calibrated rather than guessed. ``confidence_calibration
.json`` measures the top semantic similarity of the best retrieved passage
across three question groups:

=========================  ======  =======  ========  =======
group                      n       min      median    max
=========================  ======  =======  ========  =======
in the knowledge base      18      0.5644   0.6917    0.7878
security, not in the KB    6       0.3082   0.3603    0.6109
unrelated to security      6       0.1033   0.1311    0.2046
=========================  ======  =======  ========  =======

:data:`IRRELEVANT_BELOW` sits in the wide, empty gap between the unrelated
group and the other two. :data:`DOCUMENT_AT_LEAST` separates the two security
groups imperfectly - a security question the corpus does not cover can score
above a covered one - so the fallback is designed to be safe under that
overlap: it never claims document support it does not have, and the passages
retrieved are still returned to the user as related reading.
"""

import os
import re

from sqlalchemy.orm import Session

from app.rag.bm25_store import BM25Store
from app.prompts import (
    ASSISTANT_PERSONA,
    COMPARE_PROMPT,
    CONVERSATION_PROMPT,
    DOCUMENT_ANSWER_PROMPT,
    GENERAL_ANSWER_PROMPT,
    SUMMARIZE_PROMPT,
)

from app.rag.retriever import HybridRetriever

from app.agents.intents import (
    BASIS_CONVERSATION,
    BASIS_DOCUMENT,
    BASIS_GENERAL,
    DOCUMENT_BOUND_INTENTS,
)

from app.services.llm.base import LLMError
from app.services.llm.provider_factory import ProviderFactory
from app.services.conversation_service import ConversationService

#: Below this top similarity the knowledge base has nothing to do with the
#: question. Measured: unrelated questions peak at 0.2046, security questions
#: start at 0.3082.
IRRELEVANT_BELOW = 0.30

#: At or above this, the retrieved passages are treated as answering the
#: question. Measured: knowledge-base questions start at 0.5644.
DOCUMENT_AT_LEAST = 0.55

#: How much of the answer the fallback paths may produce.
GENERAL_MAX_TOKENS = 900
CONVERSATION_MAX_TOKENS = 200
DOCUMENT_MAX_TOKENS = 900

HASH_DOCUMENT_MIN_COVERAGE = 0.60
HASH_DOCUMENT_MAX_LEXICAL_RANK = 5
HASH_CONTROL_MIN_COVERAGE = 0.50
HASH_RELATED_MIN_COVERAGE = 0.25
HASH_RELATED_MAX_LEXICAL_RANK = 20

CONTROL_IDENTIFIER_PATTERN = re.compile(
    r"\b(?:AC|AU|CA|CM|CP|IA|IR|MA|MP|PE|PL|PM|PS|RA|SA|SC|SI|SR)-"
    r"\d{1,2}(?:\(\d+\))?\b|\b(?:PO|PS|PW|RV)\.\d+\b",
    re.IGNORECASE,
)
VERSIONED_REFERENCE_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9]*)[-\u2010-\u2015](\d+(?:\.\d+)*)\b",
    re.IGNORECASE,
)
STANDARD_REFERENCE_PATTERN = re.compile(
    r"\bNIST\s+(?:(?:SP)\s*)?800[- ]\d+[A-Z0-9.-]*\b"
    r"|\bNIST\s+(?:CSF|Cybersecurity Framework)(?:\s*2\.0)?\b"
    r"|\bOWASP\s+(?:ASVS|Top\s+10|API\s+Security|API\s+Top\s+10)\b"
    r"|\bCIS\s+Controls?(?:\s+v?\d+)?\b"
    r"|\bISO(?:/IEC)?\s*2700[12]\b"
    r"|\bPCI\s+DSS\b|\bMITRE\s+ATT&CK\b"
    r"|\bCVSS(?:\s+v?3(?:\.\d)?)?\b",
    re.IGNORECASE,
)

NONINFORMATIVE_PHRASE_TERMS = BM25Store.STOP_WORDS | {
    "about", "according", "between", "consider", "difference", "describe",
    "developer", "developers", "during", "example", "explain", "handle",
    "organization", "organizations", "prevent", "provide", "require",
    "requirements", "requires", "team", "teams", "tell", "use", "using",
    "work", "nist", "sp",
}


def _threshold(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class RAGService:

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @staticmethod
    def ask(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
        template=None,
    ):
        """Answer a question, creating or continuing a conversation.

        Kept with its original signature and response shape so existing callers
        keep working; the orchestrator uses :meth:`answer` directly because it
        has already resolved the conversation.
        """

        conversation_id = RAGService._resolve_conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
        )

        ConversationService.add_user_message(
            db=db,
            conversation_id=conversation_id,
            message=question,
        )

        return RAGService.answer(
            question=question,
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            persist=True,
            template=template,
        )

    # ------------------------------------------------------------------
    # Conversation handling
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_conversation(
        db: Session,
        user_id: int,
        conversation_id: int | None,
        question: str,
    ) -> int:
        """Return a usable conversation id owned by ``user_id``.

        A supplied id is verified against the caller before it is written to.
        Without that check, knowing a conversation id would be enough to append
        messages to another user's thread.
        """

        if conversation_id is not None:

            owned = ConversationService.get_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            if owned is None:
                raise PermissionError(
                    "That conversation does not belong to you."
                )

            return conversation_id

        conversation = ConversationService.start_chat(
            db=db,
            user_id=user_id,
            first_question=question,
        )

        return conversation.id

    @staticmethod
    def _history(db: Session, conversation_id: int, user_id: int) -> str:
        """Render recent turns for pronoun resolution.

        Bounded in length: the whole thread would grow the prompt without
        bound, and on a free-tier quota an unbounded prompt is a cost and a
        latency problem.
        """

        history = ConversationService.load_history(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        lines = []

        for message in history[-8:]:
            role = "Assistant" if message.role == "assistant" else "User"
            lines.append(f"{role}: {message.content[:600]}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Answering
    # ------------------------------------------------------------------

    @staticmethod
    def answer(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int,
        intent=None,
        persist: bool = True,
        template=None,
    ) -> dict:
        """Route one question to the right answering path.

        The decision is driven by what retrieval actually found, not by what
        the question looked like. A question the corpus answers is answered
        from the corpus; one it does not is answered from general knowledge and
        says so. A question the user aimed at their own documents, which the
        documents do not cover, is told exactly that.
        """

        documents, metrics = HybridRetriever.search_with_metrics(
            query=question,
            top_k=5,
            user_id=user_id,
            include_uploads=True,
        )

        relevance = RAGService._relevance(documents, metrics, question)

        if relevance == "document":
            return RAGService._document_answer(
                question=question,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
                documents=documents,
                metrics=metrics,
                relevance=relevance,
                persist=persist,
                template=template,
            )

        document_scoped = intent in DOCUMENT_BOUND_INTENTS

        return RAGService._general_answer(
            question=question,
            db=db,
            conversation_id=conversation_id,
            documents=documents,
            metrics=metrics,
            persist=persist,
            relevance=relevance,
            document_scoped=document_scoped,
            template=template,
        )

    @staticmethod
    def _relevance(documents, metrics, question: str = "") -> str:
        """Classify retrieval with a signal appropriate to its embedding space."""

        if not documents or metrics.get("status") != "ok":
            return "irrelevant"

        if metrics.get("embedding_backend") == "hash":
            return RAGService._hash_relevance(question, documents)

        top = max(
            (
                float(document.metadata.get("semantic_similarity") or 0.0)
                for document in documents
            ),
            default=0.0,
        )

        if top < _threshold("RAG_IRRELEVANT_BELOW", IRRELEVANT_BELOW):
            return "irrelevant"

        if top >= _threshold("RAG_DOCUMENT_AT_LEAST", DOCUMENT_AT_LEAST):
            return "document"

        # Between the two: the corpus has something adjacent, but not an
        # answer. Treated as general knowledge so the assistant never presents
        # a near-miss as document support, while the passages still travel back
        # to the user as related reading.
        return "related"

    @staticmethod
    def _hash_relevance(question: str, documents) -> str:
        """Use lexical evidence; hash-vector cosine is not semantic confidence."""

        query_phrases = {
            token
            for token in BM25Store.tokenize(question)
            if token.startswith("phrase:")
            and not any(
                term in NONINFORMATIVE_PHRASE_TERMS
                for term in token[len("phrase:"):].split("_")
            )
        }
        control_identifiers = CONTROL_IDENTIFIER_PATTERN.findall(question)
        versioned_references = RAGService._versioned_references(question)
        related_evidence = False

        for document in documents:
            metadata = document.metadata
            try:
                lexical_rank = int(metadata.get("lexical_rank"))
                term_coverage = float(metadata.get("query_term_coverage") or 0.0)
            except (TypeError, ValueError):
                continue

            document_tokens = set(BM25Store.tokenize(document.page_content))
            phrase_match = bool(query_phrases & document_tokens)
            control_match = any(
                phrase in document_tokens
                for identifier in control_identifiers
                for phrase in BM25Store.tokenize(identifier)
                if phrase.startswith("phrase:")
            )
            versioned_match = (
                len(versioned_references) >= 2
                and versioned_references.issubset(
                    RAGService._versioned_references(document.page_content)
                )
            )

            if lexical_rank <= HASH_DOCUMENT_MAX_LEXICAL_RANK:
                if (
                    term_coverage >= HASH_DOCUMENT_MIN_COVERAGE
                    and phrase_match
                ) or (
                    term_coverage >= HASH_CONTROL_MIN_COVERAGE
                    and control_match
                ) or (
                    term_coverage >= 0.40
                    and versioned_match
                ):
                    return "document"

            if (
                lexical_rank <= HASH_RELATED_MAX_LEXICAL_RANK
                and term_coverage >= HASH_RELATED_MIN_COVERAGE
                and (phrase_match or control_match)
            ):
                related_evidence = True

        return "related" if related_evidence else "irrelevant"

    @staticmethod
    def _versioned_references(text: str) -> set[tuple[str, str]]:
        return {
            (prefix.upper(), number)
            for prefix, number in VERSIONED_REFERENCE_PATTERN.findall(text)
        }

    @staticmethod
    def _specific_reference(question: str) -> str | None:
        """Return a named standard/control whose exact requirements need proof."""
        match = CONTROL_IDENTIFIER_PATTERN.search(question)
        if match:
            return match.group(0)

        match = STANDARD_REFERENCE_PATTERN.search(question)
        return match.group(0) if match else None

    # -- document path ---------------------------------------------------

    @staticmethod
    def _document_answer(
        question,
        db,
        user_id,
        conversation_id,
        documents,
        metrics,
        relevance,
        persist,
        template=None,
    ) -> dict:

        context = RAGService._render_context(documents)
        history = RAGService._history(db, conversation_id, user_id)

        prompt = (template or DOCUMENT_ANSWER_PROMPT).format(
            persona=ASSISTANT_PERSONA,
            context=context,
            question=question,
        )

        if history:
            prompt = (
                f"Conversation so far (use only to resolve references such as "
                f"'it' or 'that document'; it is not evidence):\n{history}\n\n"
                f"{prompt}"
            )

        answer = RAGService._generate(prompt, DOCUMENT_MAX_TOKENS)

        if persist:
            RAGService._persist(db, conversation_id, answer)

        return {
            "answer": answer,
            "sources": RAGService._sources(documents),
            "retrieval_metrics": metrics,
            "answer_basis": BASIS_DOCUMENT,
            "relevance": relevance,
            "conversation_id": conversation_id,
            "related_sources": [],
            "suggestions": RAGService._suggestions(question),
        }

    # -- general path ----------------------------------------------------

    @staticmethod
    def _general_answer(
        question,
        db,
        conversation_id,
        documents,
        metrics,
        persist,
        relevance="irrelevant",
        document_scoped=False,
        template=None,
    ) -> dict:
        """Answer from model knowledge, labelled as such.

        The label is the point. The user is told, in the response itself, that
        the answer did not come from the indexed documents - so a general
        answer can never be mistaken for a sourced one.
        """

        if document_scoped:
            notice = (
                "> **Not from your documents.** Nothing in the indexed "
                "documents answers this question, so the answer below comes "
                "from general cybersecurity knowledge and carries no document "
                "citations.\n\n"
            )
        else:
            notice = (
                "> **Not from the knowledge base.** No passage in the indexed "
                "documents answers this question, so the answer below comes "
                "from general cybersecurity knowledge and carries no document "
                "citations.\n\n"
            )

        related = RAGService._sources(documents) if documents else []
        specific_reference = RAGService._specific_reference(question)

        if specific_reference:
            source_scope = "your documents" if document_scoped else "the knowledge base"
            answer = (
                f"> **Specific reference not verified.** I couldn't retrieve a "
                f"passage from {source_scope} that supports an exact answer about "
                f"`{specific_reference}`. I won't guess its requirements or scoring."
            )
            if related:
                answer += " Potentially related passages are listed separately; they are not evidence for this answer."
            else:
                answer += " Provide the relevant passage or ask a broader question."

            if persist:
                RAGService._persist(db, conversation_id, answer)

            return {
                "answer": answer,
                "sources": [],
                "retrieval_metrics": metrics,
                "answer_basis": BASIS_GENERAL,
                "relevance": relevance,
                "conversation_id": conversation_id,
                "related_sources": related,
                "suggestions": RAGService._suggestions(question),
            }

        if template is not None and documents:
            # Summarise/compare requests keep their document grounding even
            # when the similarity gate is unsure, because the user named their
            # own material; the notice still says the coverage is partial.
            prompt = template.format(
                persona=ASSISTANT_PERSONA,
                context=RAGService._render_context(documents),
                question=question,
            )
            notice = (
                "> **Partial document coverage.** The indexed documents only "
                "partly cover this request; the answer below is grounded in "
                "the passages that were found and says what is missing.\n\n"
            )
        else:
            prompt = (
                f"{GENERAL_ANSWER_PROMPT.format(persona=ASSISTANT_PERSONA)}"
                f"\n\nQuestion: {question}"
            )

        answer = RAGService._generate(prompt, GENERAL_MAX_TOKENS)

        if persist:
            RAGService._persist(db, conversation_id, notice + answer)

        # This is the honesty case the calibration measured: a security
        # question the corpus does not cover can score close to one it does.
        # Returning the passages as *related reading* gives the user the
        # benefit of the near-miss without attaching it to the answer.
        return {
            "answer": notice + answer,
            "sources": [],
            "retrieval_metrics": metrics,
            "answer_basis": BASIS_GENERAL,
            "relevance": relevance,
            "conversation_id": conversation_id,
            "related_sources": related,
            "suggestions": RAGService._suggestions(question),
        }

    # -- conversation path -----------------------------------------------

    @staticmethod
    def converse(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int,
        persist: bool = True,
    ) -> dict:
        """Reply to a greeting or a capability question."""

        prompt = CONVERSATION_PROMPT.format(
            persona=ASSISTANT_PERSONA,
            question=question,
        )

        answer = RAGService._generate(prompt, CONVERSATION_MAX_TOKENS)

        if persist:
            RAGService._persist(db, conversation_id, answer)

        return {
            "answer": answer,
            "sources": [],
            "retrieval_metrics": {
                "status": "skipped",
                "retrieved_count": 0,
                "reason": "Conversational message; retrieval not attempted.",
            },
            "answer_basis": BASIS_CONVERSATION,
            "relevance": "not_applicable",
            "conversation_id": conversation_id,
            "related_sources": [],
            "suggestions": RAGService._suggestions(question),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate(prompt: str, max_tokens: int) -> str:
        """Call the model, degrading to an explanation rather than a 500."""

        try:
            return ProviderFactory.get_provider().chat(
                prompt,
                max_tokens=max_tokens,
            )
        except LLMError as error:
            return (
                "The language model is temporarily unavailable, so this "
                "answer could not be generated. Retrieval itself succeeded - "
                "the sources listed with this message are the passages that "
                "matched your question.\n\n"
                f"_(provider error: {error})_"
            )

    @staticmethod
    def _render_context(documents) -> str:
        return "\n\n".join(
            f"[Source {index}: {document.metadata.get('filename', 'unknown')} "
            f"page {int(document.metadata.get('page', 0)) + 1}]\n"
            f"{document.page_content}"
            for index, document in enumerate(documents, start=1)
        ) or "[No matching knowledge-base passages were found.]"

    @staticmethod
    def _sources(documents) -> list[dict]:
        sources = []
        seen = set()

        for document in documents:

            key = (
                document.metadata.get("filename"),
                document.metadata.get("page"),
            )

            if key in seen:
                continue

            seen.add(key)

            sources.append(
                {
                    "filename": document.metadata.get("filename"),
                    "page": int(document.metadata.get("page", 0)) + 1,
                    "folder": document.metadata.get("source_folder"),
                }
            )

        return sources

    @staticmethod
    def _persist(db: Session, conversation_id: int, answer: str) -> None:
        ConversationService.add_ai_message(
            db=db,
            conversation_id=conversation_id,
            message=answer,
        )

    #: Follow-up prompts, chosen by what the question was about. Static text
    #: rather than a generated list, because generating them costs an extra
    #: model call per turn for something the user rarely acts on.
    SUGGESTION_SETS = (
        (
            ("password", "passphrase", "credential", "mfa", "2fa"),
            [
                "How should I store these credentials?",
                "What makes a password resistant to cracking?",
            ],
        ),
        (
            ("url", "link", "phishing", "domain"),
            [
                "What are the signs of a phishing domain?",
                "How does a homograph attack work?",
            ],
        ),
        (
            ("cve", "vulnerability", "exploit", "patch"),
            [
                "Which of these are being exploited in the wild?",
                "What is the recommended mitigation?",
            ],
        ),
        (
            ("incident", "breach", "response", "containment"),
            [
                "What should the first hour of response look like?",
                "How do we preserve evidence while containing?",
            ],
        ),
    )

    @staticmethod
    def _suggestions(question: str) -> list[str]:
        lowered = question.lower()

        for keywords, suggestions in RAGService.SUGGESTION_SETS:
            if any(keyword in lowered for keyword in keywords):
                return suggestions

        return [
            "Which NIST control covers this?",
            "What does OWASP recommend here?",
        ]

    # ------------------------------------------------------------------
    # Document-scoped requests
    # ------------------------------------------------------------------

    @staticmethod
    def summarize(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        return RAGService.ask(
            question=question or "Summarise the uploaded documents.",
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            template=SUMMARIZE_PROMPT,
        )

    @staticmethod
    def compare(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        return RAGService.ask(
            question=question or "Compare the uploaded documents.",
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            template=COMPARE_PROMPT,
        )

    @staticmethod
    def general(
        question: str,
    ):
        """Answer without a conversation. Retained for backwards compatibility.

        The orchestrator does not use this: it always has a conversation to
        persist to, which is why the original ``general`` path - which returned
        ``conversation_id: None`` and stored nothing - is no longer reachable
        from the API.
        """

        try:
            answer = ProviderFactory.get_provider().chat(
                f"{GENERAL_ANSWER_PROMPT.format(persona=ASSISTANT_PERSONA)}"
                f"\n\nQuestion: {question}",
                max_tokens=GENERAL_MAX_TOKENS,
            )
        except LLMError as error:
            answer = f"The language model is temporarily unavailable. _{error}_"

        return {
            "conversation_id": None,
            "answer": answer,
            "sources": [],
        }
