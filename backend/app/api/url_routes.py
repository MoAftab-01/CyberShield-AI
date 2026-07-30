from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user
from app.schemas.url_schema import URLRequest, URLResponse
from app.services.url_service import URLService

router = APIRouter(
    prefix="/url",
    tags=["URL Intelligence"],
)


@router.post(
    "/analyze",
    response_model=URLResponse,
)
async def analyze_url(
    request: URLRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await URLService.analyze(
        db=db,
        current_user=current_user,
        url=request.url,
    )