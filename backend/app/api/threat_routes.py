from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user

from app.schemas.threat_schema import ThreatResponse
from app.schemas.history_schema import ThreatHistoryResponse

from app.services.threat_service import ThreatService

router = APIRouter(
    prefix="/threats",
    tags=["Threat Intelligence"]
)


@router.get(
    "/history",
    response_model=List[ThreatHistoryResponse],
)
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ThreatService.get_history(db, user_id=current_user.id)


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "total_searches": ThreatService.total_searches(db, user_id=current_user.id)
    }


@router.get(
    "/{cve_id}",
    response_model=ThreatResponse,
)
def get_cve(
    cve_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ThreatService.get_cve(
        cve_id=cve_id,
        db=db,
        user_id=current_user.id,
    )
