"""Threat authorization with real routes/ORM and synthetic, isolated storage."""

from pathlib import Path
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.threat_routes import router
from app.core.security import create_access_token, hash_password
from app.database.database import engine, get_db
from app.database.models import User
from app.database.threat_crud import ThreatCRUD
from app.models.threat_search import ThreatSearch
from app.services import threat_service
from app.services.threat_service import ThreatService


def search_data(cve="CVE-2024-10001"):
    return {
        "cve": cve,
        "severity": "HIGH",
        "risk_level": "High",
        "cvss": 7.5,
        "known_exploited": False,
        "product": "Synthetic fixture",
    }


@pytest.fixture(scope="module")
def fixture_hash():
    return hash_password("Synthetic test account password")


@pytest.fixture
def owned_session(fixture_hash):
    assert engine.url.get_backend_name() == "sqlite"
    root = Path(os.environ["VECTOR_DB_DIR"]).resolve().parent
    assert Path(engine.url.database).resolve().parent == root
    assert not root.is_relative_to(Path(__file__).resolve().parents[1])

    # Explicit BEGIN keeps SQLite savepoints inside a real outer transaction.
    # Service commits release savepoints; teardown rolls back all fixture data.
    with engine.connect() as connection:
        transaction = connection.begin()
        connection.exec_driver_sql("BEGIN")
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            users = [
                User(name="Synthetic Alpha", email="alpha@example.com", hashed_password=fixture_hash),
                User(name="Synthetic Beta", email="beta@example.com", hashed_password=fixture_hash),
            ]
            session.add_all(users)
            session.commit()
            yield session, users
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture(autouse=True)
def offline_lookups(monkeypatch):
    calls = []

    def nvd(cve_id):
        calls.append(cve_id)
        return {"vulnerabilities": [{"cve": {
            "id": cve_id,
            "published": "2024-01-01T00:00:00Z",
            "lastModified": "2024-01-01T00:00:00Z",
            "metrics": {"cvssMetricV31": [{"cvssData": {
                "baseSeverity": "HIGH", "baseScore": 7.5,
            }}]},
            "descriptions": [{"lang": "en", "value": "Synthetic vulnerability"}],
        }}]}

    monkeypatch.setattr(threat_service.NVDClient, "get_cve", staticmethod(nvd))
    monkeypatch.setattr(
        threat_service.CISAClient, "get_kev",
        staticmethod(lambda _: {"known_exploited": False, "product": "Synthetic fixture"}),
    )
    monkeypatch.setattr(
        threat_service.EPSSClient, "get_epss",
        staticmethod(lambda _: {"epss": "0.1", "percentile": "0.2"}),
    )
    monkeypatch.setattr(threat_service.GitHubClient, "get_advisory", staticmethod(lambda _: []))
    return calls


@pytest.fixture
def client(owned_session):
    session, _ = owned_session
    application = FastAPI()
    application.include_router(router)

    def isolated_db():
        yield session

    application.dependency_overrides[get_db] = isolated_db
    # Deliberately omit app.main: no background indexing or real app startup.
    with TestClient(application) as test_client:
        yield test_client


def auth_headers(user):
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("path", ["/threats/history", "/threats/stats", "/threats/CVE-2024-10001"])
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid-fixture"}],
                         ids=["anonymous", "invalid-bearer"])
def test_threat_routes_require_authentication(client, offline_lookups, path, headers):
    assert client.get(path, headers=headers).status_code in {401, 403}
    assert offline_lookups == []


def test_history_and_counts_exclude_other_users_and_preserve_ownerless_rows(
    client, owned_session
):
    session, (alpha, beta) = owned_session
    ThreatCRUD.save_search(session, search_data("CVE-2024-10001"), user_id=alpha.id)
    ThreatCRUD.save_search(session, search_data("CVE-2024-10002"), user_id=beta.id)
    legacy = ThreatSearch(**search_data("CVE-2024-10003"))
    session.add(legacy)
    session.commit()
    legacy_id = legacy.id

    for user, expected in [(alpha, "CVE-2024-10001"), (beta, "CVE-2024-10002")]:
        history = client.get("/threats/history", headers=auth_headers(user))
        assert history.status_code == 200
        assert [item["cve"] for item in history.json()] == [expected]
        stats = client.get("/threats/stats", headers=auth_headers(user))
        assert stats.status_code == 200
        assert stats.json() == {"total_searches": 1}

    retained = session.get(ThreatSearch, legacy_id)
    assert retained is not None
    assert retained.user_id is None
    assert retained.cve == "CVE-2024-10003"


def test_lookup_uses_authenticated_owner_and_ignores_forged_owner_query(client, owned_session):
    session, (alpha, beta) = owned_session
    response = client.get(
        f"/threats/CVE-2024-10004?user_id={beta.id}", headers=auth_headers(alpha)
    )
    assert response.status_code == 200
    row = session.query(ThreatSearch).filter(ThreatSearch.cve == "CVE-2024-10004").one()
    assert row.user_id == alpha.id
    assert client.get("/threats/stats", headers=auth_headers(beta)).json() == {"total_searches": 0}
    assert client.get(
        f"/threats/history?user_id={alpha.id}", headers=auth_headers(beta)
    ).json() == []


def test_persistence_does_not_trust_owner_in_lookup_data(owned_session):
    session, (alpha, beta) = owned_session
    data = {**search_data(), "user_id": beta.id}
    row = ThreatCRUD.save_search(session, data, user_id=alpha.id)
    assert row.user_id == alpha.id


def test_crud_applies_owner_filter_before_history_limit(owned_session):
    session, (alpha, beta) = owned_session
    ThreatCRUD.save_search(session, search_data(), user_id=alpha.id)
    for number in range(12):
        ThreatCRUD.save_search(session, search_data(f"CVE-2024-{20000 + number}"), user_id=beta.id)
    records = ThreatCRUD.get_recent_searches(session, user_id=alpha.id, limit=1)
    assert len(records) == 1
    assert records[0].user_id == alpha.id
    assert ThreatCRUD.get_total_searches(session, user_id=alpha.id) == 1


@pytest.mark.parametrize("owner", [None, True, 0, -1, "1", 1.0])
@pytest.mark.parametrize("operation", ["save", "history", "count", "lookup"])
def test_missing_or_invalid_owner_fails_before_io(owner, operation, offline_lookups):
    # No usable DB object: validation must happen before a query or lookup.
    with pytest.raises(ValueError, match="authenticated user ID"):
        if operation == "save":
            ThreatCRUD.save_search(object(), search_data(), user_id=owner)
        elif operation == "history":
            ThreatService.get_history(object(), user_id=owner)
        elif operation == "count":
            ThreatService.total_searches(object(), user_id=owner)
        else:
            ThreatService.get_cve("CVE-2024-10001", object(), user_id=owner)
    assert offline_lookups == []
