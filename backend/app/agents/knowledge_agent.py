from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.agents.capability_router import CapabilityRouter

from app.services.rag_service import RAGService


class KnowledgeAgent(BaseAgent):

    CAPABILITIES = [
        "rag",
        "summarize",
        "compare",
        "general",
    ]

    def handle(
        self,
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        capability = CapabilityRouter.route(
            agent="Knowledge Agent",
            capabilities=self.CAPABILITIES,
            question=question,
        )

        print(f"[KnowledgeAgent] {capability}")

        if capability == "general":

            return RAGService.general(
                question
            )

        elif capability == "summarize":

            return RAGService.summarize(
                question=question,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        elif capability == "compare":

            return RAGService.compare(
                question=question,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        return RAGService.ask(
            question=question,
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )   