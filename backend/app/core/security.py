from datetime import datetime, timedelta, timezone
from typing import Optional
import math
import time

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """
    if not isinstance(password, str) or "\x00" in password:
        raise ValueError("Password contains an unsupported character.")
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    if not isinstance(password, str) or "\x00" in password:
        return False
    try:
        return pwd_context.verify(password, hashed_password)
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token.
    Returns payload if valid else None.
    """

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )

        subject, expires = payload.get("sub"), payload.get("exp")
        if (not isinstance(subject, str) or not subject or len(subject) > 255
                or subject != subject.strip() or any(ord(c) < 32 for c in subject)
                or type(expires) not in (int, float) or not math.isfinite(expires)
                or expires <= time.time()):
            return None
        return payload

    except (JWTError, ValueError, TypeError, OverflowError):
        return None