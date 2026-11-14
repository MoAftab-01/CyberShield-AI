"""Synthetic authentication regressions; no real credentials or database."""
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
import pytest
from app.core.config import settings
from app.core.security import decode_access_token, hash_password, verify_password, create_access_token
from app.api import user_routes
from app.database.database import get_db
from app.core.rate_limit import RateLimiter

@pytest.mark.parametrize("claims", [
    {"sub": "alpha@example.com"}, {"exp": 4102444800},
    {"sub": "", "exp": 4102444800}, {"sub": ["alpha@example.com"], "exp": 4102444800},
    {"sub": " alpha@example.com", "exp": 4102444800},
    {"sub": "alpha@example.com", "exp": "4102444800"},
    {"sub": "alpha@example.com", "exp": True},
    {"sub": "alpha@example.com", "exp": time.time() - 100},
])
def test_jwt_requires_valid_expiration_and_subject(claims):
    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    assert decode_access_token(token) is None

def test_valid_jwt_still_works():
    assert decode_access_token(create_access_token({"sub": "alpha@example.com"}))["sub"] == "alpha@example.com"

def test_nul_and_invalid_hash_are_contained():
    assert verify_password("synthetic\x00input", hash_password("SyntheticOnly!923")) is False
    assert verify_password("SyntheticOnly!923", "not-a-valid-hash") is False
    with pytest.raises(ValueError, match="unsupported character"):
        hash_password("synthetic\x00input")

def test_bcrypt_legacy_long_password_compatibility_is_preserved():
    # Preserve existing bcrypt's first-72-byte compatibility; no account lockout.
    prefix = "Synthetic!" * 8
    encoded = hash_password(prefix + "suffix-one")
    assert verify_password(prefix + "suffix-two", encoded)

def test_concurrent_duplicate_registration_rolls_back(monkeypatch):
    from app.services.user_service import UserService
    from app.schemas.user_schema import UserCreate
    from sqlalchemy.exc import IntegrityError
    events = []
    class Query:
        def filter(self, *args): return self
        def first(self): return None
    class DB:
        def query(self, *args): return Query()
        def add(self, value): events.append("add")
        def commit(self): raise IntegrityError("synthetic", {}, Exception())
        def rollback(self): events.append("rollback")
    monkeypatch.setattr(UserService, "get_user_by_email", staticmethod(lambda *a: object()))
    with pytest.raises(ValueError, match="Email already exists"):
        UserService.create_user(DB(), UserCreate(name="Alpha", email="alpha@example.com", password="SyntheticOnly!923"))
    assert events == ["add", "rollback"]

def test_throttle_ignores_forwarded_identity(db_session, monkeypatch):
    app = FastAPI(); app.include_router(user_routes.router)
    app.dependency_overrides[get_db] = lambda: db_session
    monkeypatch.setattr(user_routes, "LOGIN_LIMITER", RateLimiter(1, 60))
    with TestClient(app) as client:
        for index, status in enumerate([401, 429]):
            result = client.post("/users/login", headers={"X-Forwarded-For": "198.51.100." + str(index)},
                json={"email": "not-a-user@example.com", "password": "SyntheticOnly!923"})
            assert result.status_code == status

def test_missing_bearer_is_consistently_unauthorized(db_session):
    app = FastAPI(); app.include_router(user_routes.router)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        response = client.get("/users/me")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
