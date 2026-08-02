from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.services.rag_service import RAGService


class KnowledgeAgent(BaseAgent):

    def handle(
        self,
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        return RAGService.ask(
            question=question,
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )