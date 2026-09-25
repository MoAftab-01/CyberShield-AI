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

        documents, retrieval_metrics = HybridRetriever.search_with_metrics(
            query=question,
            top_k=5,
        )

        knowledge = "\n\n".join(
            f"[Source {index}: {doc.metadata.get('filename', 'unknown')} "
            f"page {int(doc.metadata.get('page', 0)) + 1}]\n{doc.page_content}"
            for index, doc in enumerate(documents, start=1)
        )
        if not knowledge:
            knowledge = "[No matching knowledge-base passages were found.]"

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

1. Use conversation history only to resolve references such as "it" or "that document".
   Do not treat previous assistant messages as evidence.

2. Use only facts supported by the Knowledge Base. If the passages do not answer
   the question, explicitly say that the uploaded documents do not contain enough
   information and explain what information is missing. Do not guess.

3. Never invent information, document content, or citations.

4. Cite every document-derived claim inline as [Source N]. Do not cite a source
   that does not support the claim.

5. Answer the user's actual question directly. Do not invoke, imitate, or redirect
   to the password analyzer, URL scanner, CVE tools, or any other application feature.

6. If the question is unrelated to cybersecurity or the uploaded documents, say so
   briefly instead of fabricating a document-based answer.

7. Separate "From the documents" from "Additional general guidance". Only include
   additional guidance when it is clearly labeled as general guidance.
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
                    "page": int(doc.metadata.get("page", 0)) + 1,
                    "folder": doc.metadata.get("source_folder"),
                }
            )

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": sources,
            "retrieval_metrics": retrieval_metrics,
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