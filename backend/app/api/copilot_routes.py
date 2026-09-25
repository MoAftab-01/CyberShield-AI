from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.copilot_schema import (
    CopilotRequest,
    CopilotResponse,
)

from app.services.rag_service import RAGService


router = APIRouter(
    prefix="/copilot",
    tags=["CyberGPT"],
)

@router.post(
    "/ask",
    response_model=CopilotResponse,
)
async def ask_copilot(
    request: CopilotRequest,
    db: Session = Depends(get_db),
):
    """
    CyberGPT entry point.
    """

    # TODO: Replace with authenticated user later
    user_id = 1

    return RAGService.ask(
        question=request.question,
        db=db,
        user_id=user_id,
        conversation_id=request.conversation_id,
    )