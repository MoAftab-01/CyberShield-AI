import threading

from fastapi.testclient import TestClient

from app import main


def test_health_is_available_while_knowledge_index_builds(monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def slow_index_build():
        started.set()
        release.wait(timeout=5)

    monkeypatch.setattr(main, "_prepare_knowledge_base", slow_index_build)

    try:
        with TestClient(main.app) as client:
            assert started.wait(timeout=2)
            assert client.get("/health").status_code == 200
    finally:
        release.set()


def test_registration_endpoint_creates_account():
    with TestClient(main.app) as client:
        response = client.post(
            "/users/register",
            json={
                "name": "Registration Test",
                "email": "registration-test@example.com",
                "password": "LocalTestPassword123!",
            },
        )

    assert response.status_code == 201
    assert response.json()["email"] == "registration-test@example.com"