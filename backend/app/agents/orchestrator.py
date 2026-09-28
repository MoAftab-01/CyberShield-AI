"""CyberGPT orchestration.

One entry point that decides how a question should be answered, then answers
it. The decision is made by :class:`IntentRouter`, which is deterministic
first: pattern rules run without any model call, and the model is consulted
only when they produce nothing, and only for a question long enough to carry
signal. That ordering is what keeps the common cases free of LLM calls.

Three destinations, because the three kinds of request need different
machinery:

* **Tools** - "generate a password", "scan this URL", "what is CVE-2021-44228".
  These are actions with deterministic answers. Running them through retrieval
  and a language model would be slower, cost a call, and let a model invent a
  password requirement or a CVSS score.
* **Knowledge** - "how does zero trust work". Retrieval first, with a labelled
  general-knowledge fallback when the corpus does not cover it.
* **Conversation** - "hello". No retrieval, no report.

What this replaces
------------------

The previous ``orchestrator.py`` imported ``IntentClassifier`` and four agent
classes and was *never called* - nothing in the codebase imported it. The live
route went straight to ``RAGService.ask``, so the agent package was dead code
and the assistant had exactly one behaviour: search the knowledge base. The
files it depended on have been removed and their useful parts (the password,
URL and threat services) are reached through the tool registry instead.

Persistence happens here rather than inside each path, so a tool answer, a
document answer and a general answer all land in the conversation history the
same way, and the user's own secrets are redacted before they are stored.
"""

from sqlalchemy.orm import Session

from app.agents.intents import (
    BASIS_TOOL,
    CONVERSATION_INTENTS,
    Intent,
    TOOL_INTENTS,
)
from app.agents.router import IntentRouter, RoutingDecision
from app.agents.tools import ToolContext, redact_secrets, run_tool

from app.services.conversation_service import ConversationService
from app.services.rag_service import RAGService

MAX_QUESTION_LENGTH = 4000


class CyberGPTOrchestrator:
    """Routes a question to a tool, the knowledge base, or a reply."""

    async def handle(
        self,
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ) -> dict:
        """Answer one question and persist both turns.

        Returns the same keys the route has always returned (``answer``,
        ``sources``, ``conversation_id``, ``retrieval_metrics``) plus additive
        ones describing how the answer was produced.
        """

        question = (question or "").strip()

        if not question:
            raise ValueError("The question must not be empty.")

        if len(question) > MAX_QUESTION_LENGTH:
            raise ValueError(
                f"The question must be under {MAX_QUESTION_LENGTH} characters."
            )

        decision = IntentRouter.classify(question)

        print(
            f"[cybergpt] intent={decision.intent.value} "
            f"source={decision.source} confidence={decision.confidence:.2f}"
        )

        # The conversation is resolved before dispatch so every path,
        # including a pure tool call, has somewhere to record itself.
        conversation_id = self._conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
        )

        ConversationService.add_user_message(
            db=db,
            conversation_id=conversation_id,
            message=redact_secrets(question, decision),
        )

        if decision.intent in TOOL_INTENTS:
            result = await self._tool(
                decision=decision,
                question=question,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        elif decision.intent in CONVERSATION_INTENTS:
            result = RAGService.converse(
                question=question,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        else:
            result = RAGService.answer(
                question=question,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
                intent=decision.intent,
            )

        result["conversation_id"] = conversation_id
        result["intent"] = decision.intent.value
        result["routing"] = {
            "source": decision.source,
            "confidence": decision.confidence,
            "reason": decision.reason,
        }

        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _conversation(
        db: Session,
        user_id: int,
        conversation_id: int | None,
        question: str,
    ) -> int:
        """Resolve the conversation to write to, verifying ownership."""

        return RAGService._resolve_conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
        )

    @staticmethod
    async def _tool(
        decision: RoutingDecision,
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int,
    ) -> dict:
        """Run a deterministic tool and record its output."""

        user = CyberGPTOrchestrator._load_user(db, user_id)

        context = ToolContext(
            db=db,
            user=user,
            question=question,
            decision=decision,
            conversation_id=conversation_id,
        )

        result = await run_tool(decision, context)

        ConversationService.add_ai_message(
            db=db,
            conversation_id=conversation_id,
            message=result.answer,
        )

        return {
            "answer": result.answer,
            "sources": result.sources,
            "retrieval_metrics": {
                "status": "skipped",
                "retrieved_count": 0,
                "reason": (
                    "Handled by a deterministic tool; retrieval was not "
                    "attempted."
                ),
            },
            "answer_basis": result.basis or BASIS_TOOL,
            "relevance": "not_applicable",
            "tool_used": result.tool_used,
            "tool_ok": result.ok,
            "tool_metadata": result.metadata,
            "related_sources": [],
            "suggestions": result.suggestions,
        }

    @staticmethod
    def _load_user(db: Session, user_id: int):
        """Fetch the ORM user the tools expect.

        ``password_analyze`` writes an audit row keyed on the user, so it needs
        the mapped instance rather than just an id.
        """

        from app.database.models import User

        return db.query(User).filter(User.id == user_id).first()


#: Shared instance. The orchestrator is stateless; it exists so the route has
#: one obvious thing to call.
orchestrator = CyberGPTOrchestrator()


async def handle_question(
    question: str,
    db: Session,
    user_id: int,
    conversation_id: int | None = None,
) -> dict:
    return await orchestrator.handle(
        question=question,
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
    )
