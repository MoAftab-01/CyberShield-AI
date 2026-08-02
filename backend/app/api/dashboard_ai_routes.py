from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.dashboard_ai_service import DashboardAIService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard AI"],
)


@router.get("/ai-summary")
def get_ai_summary(
    db: Session = Depends(get_db),
):
    """
    Generate an AI-powered executive security summary
    for the dashboard.
    """

    # TODO:
    # Replace hardcoded user_id after JWT integration
    user_id = 1

    return DashboardAIService.generate_summary(
        db=db,
        user_id=user_id,
    )