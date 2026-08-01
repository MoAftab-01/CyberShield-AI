from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.copilot_schema import (
    CopilotRequest,
    CopilotResponse,
)

from app.services.rag_service import (
    RAGService,
)

router = APIRouter(
    prefix="/copilot",
    tags=["Security Copilot"],
)


@router.post(
    "/ask",
    response_model=CopilotResponse,
)
def ask_copilot(
    request: CopilotRequest,
    db: Session = Depends(get_db),
):

    # Temporary user
    # Later this comes from JWT

    user_id = 1

    return RAGService.ask(

        question=request.question,

        db=db,

        user_id=user_id,

        conversation_id=request.conversation_id,

    )