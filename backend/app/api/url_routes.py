from fastapi import APIRouter, Depends

from app.database.models import User
from app.dependencies.auth import get_current_user
from app.schemas.url_schema import URLRequest, URLResponse
from app.services.url_service import URLService

router = APIRouter(
    prefix="/url",
    tags=["URL Scanner"],
)


@router.post(
    "/analyze",
    response_model=URLResponse,
)
async def analyze_url(
    request: URLRequest,
    current_user: User = Depends(get_current_user),
):

    return await URLService.analyze(request.url)