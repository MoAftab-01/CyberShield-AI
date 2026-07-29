from fastapi import APIRouter, Depends

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
    current_user: User = Depends(get_current_user),
):

    return PasswordService.analyze(
        request.password
    )