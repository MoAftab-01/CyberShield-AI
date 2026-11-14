"""Only synthetic hosts/files; no database or external service is contacted."""
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.demo_host import create_demo_app, validate_demo_database

pytestmark = pytest.mark.configuration_only


def test_same_origin_routes_preserve_api_lifespan_and_authorization(tmp_path):
    events = []

    @asynccontextmanager
    async def lifespan(api):
        events.append("start")
        yield
        events.append("stop")

    api = FastAPI(lifespan=lifespan)

    @api.get("/ready")
    def ready():
        return {"status": "ready"}

    @api.get("/private")
    def private():
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})

    (tmp_path / "index.html").write_text("<html>Synthetic demo shell</html>", encoding="utf-8")
    (tmp_path / "asset.js").write_text("void 0", encoding="utf-8")
    with TestClient(create_demo_app(api, tmp_path)) as client:
        assert events == ["start"]
        for path in ["/", "/investigate", "/login", "/register", "/copilot"]:
            response = client.get(path)
            assert response.status_code == 200 and "Synthetic demo shell" in response.text
        assert client.get("/asset.js").text == "void 0"
        assert client.get("/api/ready").json() == {"status": "ready"}
        response = client.get("/api/private")
        assert response.status_code == 401 and response.headers["WWW-Authenticate"] == "Bearer"
        for path in ["/api/missing", "/missing.js", "/.env", "/not-a-route"]:
            assert client.get(path).status_code == 404
    assert events == ["start", "stop"]


@pytest.mark.parametrize("scheme", ["postgresql", "postgres"])
def test_demo_database_binding_is_explicit(scheme):
    value = validate_demo_database(
        scheme + "://demo_user@dpg-synthetic-a/demo_db",
        host_prefix="dpg-synthetic-a", database="demo_db", user="demo_user",
    )
    assert value.startswith("postgresql://")


@pytest.mark.parametrize("url", [
    "postgresql://demo_user@unapproved-host/demo_db",
    "postgresql://demo_user@dpg-synthetic-a.attacker.test/demo_db",
    "postgresql://demo_user@dpg-synthetic-a/wrong_db",
    "postgresql://wrong_user@dpg-synthetic-a/demo_db",
    "sqlite:///synthetic.db",
    "not a database URL",
])
def test_unintended_database_is_rejected_before_initialization(url):
    with pytest.raises(ValueError, match="Demo database identity"):
        validate_demo_database(url, host_prefix="dpg-synthetic-a", database="demo_db", user="demo_user")
