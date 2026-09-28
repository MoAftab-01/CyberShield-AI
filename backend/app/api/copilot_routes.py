"""CyberGPT endpoint.

Two changes from the previous version, both fixing real defects:

* **Authentication.** The route took no user at all and ran as a hard-coded
  ``user_id = 1``, so it was an unauthenticated endpoint that read and wrote a
  specific account's conversations, with no rate limit between an anonymous
  caller and the Groq quota. It now requires a bearer token and answers as the
  authenticated user.
* **Orchestration.** It called ``RAGService.ask`` directly, which meant one
  behaviour for every question. It now goes through ``CyberGPTOrchestrator``,
  which routes to a deterministic tool, the knowledge base, or a reply.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import CyberGPTOrchestrator

from app.core.rate_limit import RateLimiter
from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user

from app.schemas.copilot_schema import (
    CopilotRequest,
    CopilotResponse,
)

router = APIRouter(
    prefix="/copilot",
    tags=["CyberGPT"],
)

orchestrator = CyberGPTOrchestrator()

#: Every request here can spend a Groq call, and the free tier's quota is
#: shared by all users. 20 questions per minute per account is generous for a
#: person typing and bounded for a script.
ASK_LIMITER = RateLimiter(max_requests=20, window_seconds=60)


@router.post(
    "/ask",
    response_model=CopilotResponse,
)
async def ask_copilot(
    request: CopilotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CyberGPT entry point."""

    allowed, retry_after = ASK_LIMITER.check(f"user:{current_user.id}")

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many questions in a short period. Please wait a moment.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    try:
        return await orchestrator.handle(
            question=request.question,
            db=db,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
        )
    except PermissionError as error:
        # The conversation exists but belongs to another user. Answered as a
        # 404 so the response cannot be used to enumerate other users' ids.
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
