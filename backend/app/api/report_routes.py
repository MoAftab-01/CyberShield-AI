from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
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
):
    return ReportService.get_password_reports(
        db,
        page,
        page_size,
    )


@router.get("/urls")
def get_url_reports(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
):
    return ReportService.get_url_reports(
        db,
        page,
        page_size,
    )