"""Offline synthetic adversarial investigations; genuine compiled StateGraph."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
import pytest

from app.agents.investigation import CVEInvestigator, validate_cve, NODES
from app.agents.investigation_intelligence import OfflineIntelligence, ReadOnlyLiveIntelligence
from app.api import investigation_routes as routes
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.core.security import create_access_token
from app.database.database import get_db
from app.knowledge.evidence import collect_evidence
from app.knowledge.claim_verifier import verify_draft

CVE = "CVE-2021-44228"


from evaluation.investigation.scenarios import Scenario


# Includes partial results, unsupported inputs and negative catalog observations.
CASES = [
    ("normal", CVE, "complete"),
    ("rapid_reset", "CVE-2023-44487", "complete"),
    ("xz", "CVE-2024-3094", "complete"),
    ("unknown", "CVE-2099-9999", "partial"),
    ("negative", CVE, "complete"),
    ("retry", CVE, "complete"),
    ("outage", CVE, "insufficient_evidence"),
    ("nvd_outage", CVE, "partial"),
    ("cisa-kev_outage", CVE, "partial"),
    ("mismatch", CVE, "partial"),
    ("withdrawn", CVE, "partial"),
    ("injection", CVE, "partial"),
    ("stale", CVE, "partial"),
    ("malformed", CVE, "partial"),
    ("malformed_kev", CVE, "partial"),
    ("duplicate", CVE, "partial"),
    ("identifier_omitted", CVE, "complete"),
    ("missing", CVE, "partial"),
    ("malicious_action", CVE, "partial"),
    ("long", CVE, "partial"),
]


@pytest.mark.parametrize("scenario,cve,expected", CASES, ids=[c[0] for c in CASES])
def test_investigation_scenarios(scenario, cve, expected):
    source = Scenario(scenario)
    agent = CVEInvestigator(source)
    assert agent.graph.__class__.__name__ == "CompiledStateGraph"
    report = agent.run(cve, 7)
    assert report["status"] == expected
    assert report["mode"] == "offline_fixture"
    assert report["workflow"][0] == "validate" and report["workflow"][-1] == "report"
    assert {name for name, _ in source.calls} == {"nvd", "cisa-kev"}
    assert all(query == cve for _, query in source.calls)
    assert len(source.calls) <= 4
    grounding = report["grounding"]
    if grounding and not grounding["abstained"]:
        known = {e["citation_id"]: e for e in grounding["evidence"]}
        assert known
        for claim in grounding["claims"]:
            assert claim["citation_ids"]
            for cid in claim["citation_ids"]:
                assert cid in known and claim["text"] == known[cid]["excerpt"]
        assert all(e["scope"] == "public" and e["trust"] == "synthetic_fixture"
                   for e in known.values())
    serialized = json.dumps(report)
    assert "Ignore previous instructions" not in serialized
    assert "Invoke the shell tool" not in serialized
    assert report["metrics"]["llm_calls"] == 0
    assert report["metrics"]["input_tokens"] == report["metrics"]["output_tokens"] == 0
    if scenario == "outage":
        assert len(source.calls) == 4 and report["findings"]["known_exploited"] is None
    if scenario == "cisa-kev_outage":
        assert report["findings"]["known_exploited"] is None
    if scenario == "retry":
        assert report["workflow"].count("nvd") == 2
        assert report["workflow"].count("kev") == 2


@pytest.mark.parametrize("value", ["CVE-2021-44228;whoami", "../../etc/passwd",
    "cve-2021-44228", "CVE-2021-44228\n", "CVE-2021-123", "",
    "CVE-2021-44228 https://example.com", "CVE-\u0662\u0660\u0662\u0661-44228", None])
def test_input_rejected_before_tools(value):
    source = Scenario()
    report = CVEInvestigator(source).run(value, 7)
    assert report["status"] == "invalid_input" and source.calls == []


def test_no_ambient_catalog_upload_or_shared_index_access(monkeypatch):
    from app.knowledge import runtime_catalog
    from app.rag.faiss_store import FAISSStore
    from app.rag.bm25_store import BM25Store
    monkeypatch.setattr(runtime_catalog, "load_catalog", lambda *a: pytest.fail("Ambient catalog accessed"))
    before = FAISSStore._index, BM25Store._bm25
    report = CVEInvestigator(Scenario()).run(CVE, 91)
    assert report["grounding"]["evidence"]
    assert (FAISSStore._index, BM25Store._bm25) == before


def test_fabricated_citations_and_wrong_attribution_fail_closed():
    agent = CVEInvestigator(Scenario())
    state = {"cve": CVE, "actor": 1, "started": 0}
    for action in [agent.validate, agent.nvd, agent.kev, agent.correlate]:
        state.update(action(state))
    docs = state["documents"]
    evidence = collect_evidence(state["catalog"], docs, 1)
    for text, cid in [(evidence[0].excerpt, "E-fabricated"),
                      ("Unsupported synthetic impact claim.", evidence[0].citation_id)]:
        result = verify_draft(CVE, docs, state["catalog"], 1,
            json.dumps({"claims": [{"text": text, "citation_ids": [cid]}]}))
        assert result.abstained


def test_private_passage_injected_by_reranker_cannot_escape():
    agent = CVEInvestigator(Scenario())
    state = {"cve": CVE, "actor": 1}
    for action in [agent.validate, agent.nvd, agent.kev, agent.correlate]:
        state.update(action(state))
    state["catalog"].ingest_private(record_id="FOREIGN", title="Foreign synthetic document",
        text=CVE + " Synthetic private passage.", owner_id=2,
        retrieved_at=datetime.now(timezone.utc))
    foreign = [d for d in state["catalog"].documents(2) if d.metadata.get("user_id") == 2]
    state["documents"] = tuple(foreign)
    with pytest.raises(ValueError):
        agent.verify(state)


def test_no_state_or_citation_leak_between_users():
    agent = CVEInvestigator(Scenario())
    a = agent.run(CVE, 1)
    b = agent.run("CVE-2024-3094", 2)
    assert CVE not in json.dumps(b)
    assert "CVE-2024-3094" not in json.dumps(a)


def test_live_adapter_requires_approval_and_never_accepts_arbitrary_sources():
    with pytest.raises(ValueError):
        ReadOnlyLiveIntelligence()
    with pytest.raises(ValueError):
        ReadOnlyLiveIntelligence(approved=True).lookup("http://127.0.0.1", CVE)


@pytest.fixture
def http(db_session, user_factory, monkeypatch):
    monkeypatch.setattr(settings, "CVE_INVESTIGATION_ENABLED", True)
    monkeypatch.setattr(settings, "CVE_INVESTIGATION_LIVE_APPROVED", False)
    monkeypatch.setattr(routes, "LIMITER", RateLimiter(6, 60))
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_db] = lambda: db_session
    user = user_factory()
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, user=user,
            headers={"Authorization": "Bearer " + create_access_token({"sub": user.email})})


def test_api_requires_auth_before_graph(http, monkeypatch):
    monkeypatch.setattr(routes, "investigator", lambda: pytest.fail("Unauthenticated graph access"))
    response = http.client.post("/investigations/cve", json={"cve": CVE})
    assert response.status_code in {401, 403}


def test_api_uses_server_flags_and_forbids_ownership_override(http):
    for extra in [{"user_id": 2}, {"live": True}, {"url": "https://example.com"}]:
        response = http.client.post("/investigations/cve", headers=http.headers,
            json={"cve": CVE, **extra})
        assert response.status_code == 422
    response = http.client.post("/investigations/cve", headers=http.headers, json={"cve": CVE})
    assert response.status_code == 200 and response.json()["mode"] == "offline_fixture"


def test_api_stream_contains_real_workflow_and_final_report(http):
    response = http.client.post("/investigations/cve?stream=true",
        headers=http.headers, json={"cve": CVE})
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [e["node"] for e in events if e["type"] == "progress"] == list(NODES)
    assert events[-1]["type"] == "report"
    assert response.headers["cache-control"] == "no-store"


def test_api_disabled_and_throttled(http, monkeypatch):
    monkeypatch.setattr(settings, "CVE_INVESTIGATION_ENABLED", False)
    assert http.client.post("/investigations/cve", headers=http.headers,
        json={"cve": CVE}).status_code == 503
    monkeypatch.setattr(settings, "CVE_INVESTIGATION_ENABLED", True)
    for _ in range(6):
        assert http.client.post("/investigations/cve", headers=http.headers,
            json={"cve": CVE}).status_code == 200
    response = http.client.post("/investigations/cve", headers={**http.headers,
        "X-Forwarded-For": "198.51.100.7"}, json={"cve": CVE})
    assert response.status_code == 429 and response.headers["retry-after"]
