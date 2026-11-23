from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user
from app.schemas.user_schema import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.user_service import UserService

from app.core.rate_limit import RateLimiter

LOGIN_LIMITER = RateLimiter(30, 60)
REGISTER_LIMITER = RateLimiter(10, 60)

def throttle(request, limiter):
    # Use the connected peer. Forwarded headers do not establish identity.
    limiter.prune()
    allowed, retry = limiter.check(request.client.host if request.client else "unknown")
    if not allowed:
        raise HTTPException(429, "Authentication rate limit exceeded.",
            headers={"Retry-After": str(max(1, int(retry) + 1))})

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):

    throttle(request, REGISTER_LIMITER)
    try:
        return UserService.create_user(db, user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=Token,
)
def login(
    user: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):

    throttle(request, LOGIN_LIMITER)
    authenticated_user = UserService.authenticate_user(
        db,
        user.email,
        user.password,
    )

    if authenticated_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        {
            "sub": authenticated_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user