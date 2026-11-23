"""Readiness probes disclose no credentials and never mutate schema."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes import router
from app.database.database import get_db

def test_ready_with_isolated_database(db_session):
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready", "database": "available", "ownership_schema": "available"}

def test_readiness_failure_is_fixed_and_redacted():
    class DB:
        def execute(self, *args): raise RuntimeError("SYNTHETIC_PRIVATE_DIAGNOSTIC")
        def rollback(self): pass
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_db] = lambda: DB()
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database or required ownership schema unavailable."}
        assert "SYNTHETIC_PRIVATE_DIAGNOSTIC" not in response.text
