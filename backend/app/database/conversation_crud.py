from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.chat_message import ChatMessage


class ConversationCRUD:

    @staticmethod
    def create_conversation(
        db: Session,
        user_id: int,
        title: str,
    ):

        conversation = Conversation(
            user_id=user_id,
            title=title[:80],
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: int,
    ):

        return (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: int,
    ):

        return (
            db.query(ChatMessage)
            .filter(
                ChatMessage.conversation_id == conversation_id
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    @staticmethod
    def save_message(
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
    ):

        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def list_user_conversations(
        db: Session,
        user_id: int,
    ):

        return (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id
            )
            .order_by(
                Conversation.updated_at.desc()
            )
            .all()
        )

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: int,
    ):

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

        if conversation:

            db.delete(conversation)
            db.commit()