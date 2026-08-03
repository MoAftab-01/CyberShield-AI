from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user

from app.services.report_service import ReportService

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get("/passwords")
def get_password_reports(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ReportService.get_password_reports(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get("/urls")
def get_url_reports(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ReportService.get_url_reports(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )