from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.conversation_schema import (
    ConversationItem,
    ConversationResponse,
    RenameConversationRequest,
)

from app.services.conversation_service import (
    ConversationService,
)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.get(
    "",
    response_model=list[ConversationItem],
)
def list_conversations(
    db: Session = Depends(get_db),
):

    # Temporary user
    user_id = 1

    return ConversationService.list_conversations(
        db=db,
        user_id=user_id,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):

    conversation = ConversationService.get_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation


@router.patch(
    "/{conversation_id}",
)
def rename_conversation(
    conversation_id: int,
    request: RenameConversationRequest,
    db: Session = Depends(get_db),
):

    conversation = ConversationService.rename(
        db=db,
        conversation_id=conversation_id,
        title=request.title,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return {
        "message": "Conversation renamed."
    }


@router.delete(
    "/{conversation_id}",
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):

    ConversationService.delete(
        db=db,
        conversation_id=conversation_id,
    )

    return {
        "message": "Conversation deleted."
    }