from sqlalchemy.orm import Session

from app.prompts import SECURITY_SYSTEM_PROMPT

from app.rag.retriever import HybridRetriever

from app.services.llm.provider_factory import ProviderFactory
from app.services.conversation_service import ConversationService


class RAGService:

    @staticmethod
    def ask(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        # ---------------------------------------
        # Create Conversation (First Message)
        # ---------------------------------------

        if conversation_id is None:

            conversation = ConversationService.start_chat(
                db=db,
                user_id=user_id,
                first_question=question,
            )

            conversation_id = conversation.id

        # ---------------------------------------
        # Save User Message
        # ---------------------------------------

        ConversationService.add_user_message(
            db=db,
            conversation_id=conversation_id,
            message=question,
        )

        # ---------------------------------------
        # Load Chat History
        # ---------------------------------------

        history = ConversationService.load_history(
            db=db,
            conversation_id=conversation_id,
        )

        conversation_history = ""

        for msg in history:

            role = "User"

            if msg.role == "assistant":
                role = "Assistant"

            conversation_history += (
                f"{role}: {msg.content}\n"
            )

        # ---------------------------------------
        # Hybrid Retrieval
        # ---------------------------------------

        documents = HybridRetriever.search(
            query=question,
            top_k=5,
        )

        knowledge = "\n\n".join(
            doc.page_content
            for doc in documents
        )

        # ---------------------------------------
        # Prompt
        # ---------------------------------------

        prompt = f"""
{SECURITY_SYSTEM_PROMPT}

================================================

Conversation History

================================================

{conversation_history}

================================================

Knowledge Base

================================================

{knowledge}

================================================

Current User Question

================================================

{question}

================================================

Rules

================================================

1. Use conversation history for context.

2. Use the knowledge base for facts.

3. Never invent information.

4. If the answer is unavailable, say so.

5. Always recommend security best practices.
"""

        provider = ProviderFactory.get_provider()

        answer = provider.chat(prompt)

        ConversationService.add_ai_message(
            db=db,
            conversation_id=conversation_id,
            message=answer,
        )

        sources = []
        seen = set()

        for doc in documents:

            key = (
                doc.metadata.get("filename"),
                doc.metadata.get("page"),
            )

            if key in seen:
                continue

            seen.add(key)

            sources.append(
                {
                    "filename": doc.metadata.get("filename"),
                    "page": doc.metadata.get("page") + 1,
                    "folder": doc.metadata.get("source_folder"),
                }
            )

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": sources,
        }

    @staticmethod
    def summarize(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        return RAGService.ask(
            question=f"""
Summarize the uploaded document(s).

User Request:

{question}
""",
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    @staticmethod
    def compare(
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        return RAGService.ask(
            question=f"""
Compare the uploaded document(s).

User Request:

{question}
""",
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    @staticmethod
    def general(
        question: str,
    ):

        provider = ProviderFactory.get_provider()

        answer = provider.chat(
            f"""
You are CyberGPT, an enterprise cybersecurity assistant.

Answer the following question using your cybersecurity knowledge.

Question:
{question}

Rules:
- Be accurate.
- Use markdown.
- Keep the answer concise.
- Include security best practices when appropriate.
"""
        )

        return {
            "conversation_id": None,
            "answer": answer,
            "sources": [],
        }