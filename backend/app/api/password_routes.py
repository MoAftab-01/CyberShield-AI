from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.database.models import User
from app.schemas.password_schema import (
    PasswordRequest,
    PasswordResponse,
)
from app.services.password_service import PasswordService

router = APIRouter(
    prefix="/password",
    tags=["Password Intelligence"],
)


@router.post(
    "/analyze",
    response_model=PasswordResponse,
)
def analyze_password(
    request: PasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return PasswordService.analyze(
        db=db,
        current_user=current_user,
        password=request.password,
    )