"""Conversation persistence.

Ownership is filtered here rather than in the route handlers. Every read and
write takes an optional ``user_id``; when it is supplied the query is scoped to
that owner, so a conversation belonging to someone else is indistinguishable
from one that does not exist. Filtering at this layer means a future endpoint
cannot forget the check, which is how the original IDOR arose: the routes
hard-coded ``user_id = 1``, so every authenticated user read and deleted the
same account's conversations.
"""

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
        user_id: int | None = None,
    ):

        query = db.query(Conversation).filter(
            Conversation.id == conversation_id
        )

        if user_id is not None:
            query = query.filter(Conversation.user_id == user_id)

        return query.first()

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: int,
        user_id: int | None = None,
    ):

        query = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        )

        # Messages carry no owner of their own; ownership is inherited from the
        # conversation, so it is enforced with an EXISTS subquery rather than a
        # column filter.
        if user_id is not None:
            query = query.filter(
                db.query(Conversation.id)
                .filter(
                    Conversation.id == ChatMessage.conversation_id,
                    Conversation.user_id == user_id,
                )
                .exists()
            )

        return query.order_by(ChatMessage.created_at.asc()).all()

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
    def rename_conversation(
        db: Session,
        conversation_id: int,
        title: str,
        user_id: int | None = None,
    ):

        conversation = ConversationCRUD.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            return None

        conversation.title = title[:80]

        db.commit()
        db.refresh(conversation)

        return conversation

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: int,
        user_id: int | None = None,
    ) -> bool:
        """Delete a conversation. Returns whether anything was deleted.

        The original returned nothing, so the route reported success even when
        the id did not exist or belonged to another user. The caller now has a
        real answer to act on.
        """

        conversation = ConversationCRUD.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            return False

        db.delete(conversation)
        db.commit()

        return True