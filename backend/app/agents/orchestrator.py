from sqlalchemy.orm import Session

from app.agents.intent_classifier import IntentClassifier
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.threat_agent import ThreatAgent
from app.agents.url_agent import URLAgent
from app.agents.password_agent import PasswordAgent

from app.services.conversation_service import ConversationService

from app.formatters.threat_formatter import ThreatFormatter
from app.formatters.url_formatter import URLFormatter
from app.formatters.password_formatter import PasswordFormatter


class CyberGPTOrchestrator:

    def __init__(self):
        self.knowledge_agent = KnowledgeAgent()
        self.threat_agent = ThreatAgent()
        self.url_agent = URLAgent()
        self.password_agent = PasswordAgent()

    async def handle(
        self,
        question: str,
        db: Session,
        user_id: int,
        conversation_id: int | None = None,
    ):

        intent = IntentClassifier.classify(question)

        print(f"[CyberGPT] Intent -> {intent}")

        # ---------------------------------------
        # KNOWLEDGE AGENT
        # ---------------------------------------

        if intent == "knowledge":

            return self.knowledge_agent.handle(
                question=question,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        # ---------------------------------------
        # Create Conversation
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
        # THREAT
        # ---------------------------------------

        if intent == "threat":

            result = self.threat_agent.handle(
                question=question,
                db=db,
            )

            answer = ThreatFormatter.format(result)

        # ---------------------------------------
        # URL
        # ---------------------------------------

        elif intent == "url":

            result = await self.url_agent.handle(
                question=question,
                db=db,
                user_id=user_id,
            )

            answer = URLFormatter.format(result)

        # ---------------------------------------
        # PASSWORD
        # ---------------------------------------

        elif intent == "password":

            result = self.password_agent.handle(
                question=question,
                db=db,
                user_id=user_id,
            )

            answer = PasswordFormatter.format(result)

        # ---------------------------------------
        # DEFAULT
        # ---------------------------------------

        else:

            answer = (
                "I couldn't determine which CyberGPT capability "
                "should handle your request."
            )

        # ---------------------------------------
        # Save AI Message
        # ---------------------------------------

        ConversationService.add_ai_message(
            db=db,
            conversation_id=conversation_id,
            message=answer,
        )

        # ---------------------------------------
        # Return
        # ---------------------------------------

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": [],
        }