from sqlalchemy.orm import Session

from app.database.conversation_crud import ConversationCRUD


class ConversationService:

    @staticmethod
    def start_chat(
        db: Session,
        user_id: int,
        first_question: str,
    ):

        return ConversationCRUD.create_conversation(
            db=db,
            user_id=user_id,
            title=first_question,
        )

    @staticmethod
    def load_history(
        db: Session,
        conversation_id: int,
        user_id: int | None = None,
    ):

        return ConversationCRUD.get_messages(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

    @staticmethod
    def add_user_message(
        db: Session,
        conversation_id: int,
        message: str,
    ):

        return ConversationCRUD.save_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=message,
        )

    @staticmethod
    def add_ai_message(
        db: Session,
        conversation_id: int,
        message: str,
    ):

        return ConversationCRUD.save_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=message,
        )

    @staticmethod
    def list_conversations(
        db: Session,
        user_id: int,
    ):

        return ConversationCRUD.list_user_conversations(
            db=db,
            user_id=user_id,
        )


    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: int,
        user_id: int | None = None,
    ):
        """Load one conversation with its messages.

        Returns ``None`` when the conversation does not exist *or* belongs to
        another user, so the route cannot leak the existence of someone else's
        conversation through a different status code.
        """

        conversation = ConversationCRUD.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            return None

        messages = ConversationCRUD.get_messages(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        return {

            "id": conversation.id,

            "title": conversation.title,

            "messages": messages,

        }


    @staticmethod
    def delete(
        db: Session,
        conversation_id: int,
        user_id: int | None = None,
    ):

        return ConversationCRUD.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

    @staticmethod
    def rename(
        db: Session,
        conversation_id: int,
        title: str,
        user_id: int | None = None,
    ):
        return ConversationCRUD.rename_conversation(
            db=db,
            conversation_id=conversation_id,
            title=title,
            user_id=user_id,
        )