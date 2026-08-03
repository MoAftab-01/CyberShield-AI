from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user

from app.services.dashboard_ai_service import DashboardAIService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard AI"],
)


@router.get("/ai-summary")
def get_ai_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI-powered executive security summary
    for the logged-in user.
    """

    return DashboardAIService.generate_summary(
        db=db,
        current_user=current_user,
    )

@router.get("/ai-summary")
def get_ai_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print("AI SUMMARY ROUTE HIT")
    print(current_user)

    return DashboardAIService.generate_summary(
        db=db,
        current_user=current_user,
    )