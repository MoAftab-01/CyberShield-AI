"""Conversation endpoints.

Every route is scoped to the authenticated user. Previously they ran as a
hard-coded ``user_id = 1``, which meant any logged-in account could list, read,
rename and delete the same account's conversations - a textbook IDOR. Ownership
is enforced in :class:`ConversationCRUD`, so a conversation belonging to
someone else answers exactly as a missing one does and the routes cannot leak
its existence.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user

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

NOT_FOUND = "Conversation not found"


@router.get(
    "",
    response_model=list[ConversationItem],
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ConversationService.list_conversations(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    conversation = ConversationService.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=NOT_FOUND,
        )

    return conversation


@router.patch(
    "/{conversation_id}",
)
def rename_conversation(
    conversation_id: int,
    request: RenameConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    conversation = ConversationService.rename(
        db=db,
        conversation_id=conversation_id,
        title=request.title,
        user_id=current_user.id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=NOT_FOUND,
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
    current_user: User = Depends(get_current_user),
):

    deleted = ConversationService.delete(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    # Deleting someone else's conversation must not report success, and must
    # not report 403 either - that would confirm the id exists.
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=NOT_FOUND,
        )

    return {
        "message": "Conversation deleted."
    }
