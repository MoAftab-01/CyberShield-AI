"""Production-source bridge and additive chat behavior; synthetic storage only."""
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest
from langchain_core.documents import Document
from app.knowledge import production_catalog as production
from app.services import grounded_chat_service as service
from app.services.document_service import DocumentService
from app.core.config import settings
from test_grounded_chat_integration import bundle, provider, http

@pytest.fixture(autouse=True)
def enable_local_v2(monkeypatch):
    monkeypatch.setattr(settings, "CYBERGPT_V2_ENABLED", True)


TEXT = "Zero trust does not grant implicit trust based on network location. Each access request requires authentication and authorization."


@pytest.fixture
def source_page(tmp_path, monkeypatch):
    root = tmp_path / "references"
    root.mkdir()
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(fitz.Rect(60, 60, 500, 250), TEXT, fontsize=11)
    path = root / "reference.pdf"
    pdf.save(path)
    pdf.close()
    manifest = tmp_path / "sources.json"
    manifest.write_text(json.dumps({"format_version": 1, "sources": [{"path": path.name,
        "sha256": sha256(path.read_bytes()).hexdigest(), "title": "Synthetic reference",
        "source_id": "nist-csrc", "canonical_url": "https://csrc.nist.gov/publications"}]}))
    monkeypatch.setattr(production, "PUBLIC_ROOT", root)
    monkeypatch.setattr(production, "SOURCE_MANIFEST", manifest)
    document = Document(page_content="Zero trust does not grant implicit trust", metadata={
        "filename": path.name, "page": 0, "scope": "knowledge_base", "source_folder": root.name})
    original = production.HybridRetriever.search_with_metrics
    def retrieve(question, top_k=5, user_id=None, include_uploads=True, *, context=None):
        if context is not None:
            return original(question, top_k, user_id, include_uploads, context=context)
        return [document], {"status": "ok", "retrieved_count": 1, "embedding_backend": "hash"}
    monkeypatch.setattr(production.HybridRetriever, "search_with_metrics", staticmethod(retrieve))
    return SimpleNamespace(document=document, path=path, manifest=manifest, root=root)


def test_production_bridge_admits_complete_verified_page_blocks(source_page):
    catalog, documents, metrics = production.retrieve("Explain zero trust", 1)
    assert documents and metrics["embedding_backend"] == "hash"
    record, chunk = catalog.resolve(documents[0].metadata["chunk_id"], 1)
    assert record.scope == "public" and record.artifact_hash == sha256(source_page.path.read_bytes()).hexdigest()
    assert chunk.excerpt in record.sections[0].text
    assert documents[0].metadata["page"] == 0


@pytest.mark.parametrize("attack", ["bytes", "chunk", "page", "path", "scope"])
def test_forged_or_stale_index_metadata_cannot_become_canonical_evidence(source_page, attack):
    if attack == "bytes": source_page.path.write_bytes(b"modified public source")
    if attack == "chunk": source_page.document.page_content = "Fabricated unrelated source passage"
    if attack == "page": source_page.document.metadata["page"] = 99
    if attack == "path": source_page.document.metadata["filename"] = "../reference.pdf"
    if attack == "scope": source_page.document.metadata["scope"] = "unknown"
    _, documents, _ = production.retrieve("Explain zero trust", 1)
    assert not documents


def test_owned_upload_is_bound_to_authenticated_user_and_actual_bytes(tmp_path, monkeypatch):
    root = tmp_path / "uploads"
    (root / "user_1").mkdir(parents=True)
    (root / "user_2").mkdir()
    (root / "user_1" / "private.txt").write_text(TEXT)
    (root / "user_2" / "private.txt").write_text("Foreign tenant confidential recovery records must never be returned.")
    monkeypatch.setattr(DocumentService, "UPLOAD_DIR", root)
    document = Document(page_content=TEXT, metadata={"filename": "private.txt", "page": 0,
        "scope": "user_upload", "source_folder": "uploads", "user_id": 1})
    monkeypatch.setattr(production.HybridRetriever, "search_with_metrics", staticmethod(lambda *a, **k: ([document], {"status": "ok", "retrieved_count": 1})))
    catalog, documents, _ = production.retrieve("Explain zero trust in my document", 1)
    assert documents and catalog.current_records()[0].scope == "private"
    assert all(catalog.resolve(d.metadata["chunk_id"], 2) is None for d in documents)
    _, foreign, _ = production.retrieve("Explain zero trust in my document", 2)
    assert not foreign
    document.metadata["user_id"] = 2
    _, forged, _ = production.retrieve("Explain zero trust in my document", 2)
    assert not forged  # User 2's file bytes do not contain user 1's indexed text.


def test_default_runtime_catalog_supports_real_source_path_without_fixture_manifest(http, provider, source_page, monkeypatch):
    monkeypatch.setattr(settings, "CYBERGPT_V2_CATALOG_MANIFEST", None)
    result = http.post("Explain zero trust network location authentication").json()
    assert result["grounding"]["status"] == "supported_quotes"
    assert result["grounding"]["evidence"][0]["source_id"] == "nist-csrc"
    assert result["sources"][0]["page"] == 1
    assert len(provider["calls"]) == 1


def test_greeting_does_not_disable_knowledge_questions_with_default_router_intent(http, bundle, provider):
    bundle()
    greeting = http.post("hello").json()
    assert greeting["answer_basis"] == "conversation" and greeting["grounding"] is None
    assert not provider["calls"]
    result = http.post().json()
    assert result["grounding"]["status"] == "supported_quotes"


def test_explicit_general_knowledge_is_labelled_and_has_no_document_citations(http, monkeypatch):
    captured = []
    class General:
        def chat_bounded(self, prompt, **options):
            captured.append((prompt, options))
            return "Use layered controls and review their limitations."
    monkeypatch.setattr(service.ProviderFactory, "get_provider", classmethod(lambda cls: General()))
    result = http.post("From general knowledge explain defense in depth").json()
    assert result["answer_basis"] == "general_knowledge"
    assert result["grounding"] is None and result["sources"] == []
    assert "not verified against documents" in result["answer"]
    assert len(captured) == 1 and captured[0][1]["max_attempts"] == 1


def test_general_provider_failure_returns_controlled_labelled_reply(http, monkeypatch):
    class Failed:
        def chat_bounded(self, *args, **kwargs): raise TimeoutError("synthetic timeout")
    monkeypatch.setattr(service.ProviderFactory, "get_provider", classmethod(lambda cls: Failed()))
    result = http.post("From general knowledge explain defense in depth").json()
    assert result["answer_basis"] == "general_knowledge" and result["sources"] == []
    assert "unavailable" in result["answer"] and "synthetic timeout" not in result["answer"]


def test_followup_uses_only_safe_owned_topic_labels(http, bundle, provider, db_session, monkeypatch):
    bundle()
    from app.services.conversation_service import ConversationService
    conversation = ConversationService.start_chat(db_session, http.user.id, "Zero trust")
    ConversationService.add_user_message(db_session, conversation.id, "Explain zero trust")
    observed = []
    async def answer(question, user_id):
        observed.append((question, user_id))
        return {"answer": "Synthetic followup", "history_answer": "Synthetic followup", "sources": [],
            "answer_basis": "document", "grounding": None, "retrieval_metrics": {"status": "empty", "retrieved_count": 0}}
    monkeypatch.setattr(service.GroundedChatService, "answer", staticmethod(answer))
    http.post("What about its implementation?", conversation_id=conversation.id)
    assert observed and "zero trust" in observed[0][0]
    assert "context topic" in observed[0][0]


@pytest.mark.parametrize("model,bounded,expected", [("openai/gpt-oss-20b", True, "low"), ("openai/gpt-oss-120b", True, "low"), ("llama-3.1-8b-instant", True, None), ("openai/gpt-oss-20b", False, None)])
def test_reasoning_budget_fix_is_bounded_and_model_specific(monkeypatch, model, bounded, expected):
    from app.services.llm.groq_provider import GroqProvider
    monkeypatch.setattr(settings, "GROQ_MODEL", model)
    requests, retries = [], []
    class Client:
        def __init__(self): self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def with_options(self, **options): retries.append(options); return self
        def create(self, **options):
            requests.append(options)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Synthetic response"))])
    provider = GroqProvider.__new__(GroqProvider)
    provider.client = Client()
    provider.chat("Synthetic public prompt", max_attempts=1 if bounded else None, max_tokens=900)
    assert requests[0].get("reasoning_effort") == expected
    assert requests[0]["max_tokens"] == 900
    assert retries == ([{"max_retries": 0}] if bounded else [])


def test_model_selects_ids_and_server_copies_canonical_complete_text(monkeypatch):
    captured = []
    class Selector:
        def chat_bounded(self, prompt, **options):
            captured.append(prompt)
            return json.dumps({"citation_ids": ["E-allowed"]})
    monkeypatch.setattr(service.ProviderFactory, "get_provider", classmethod(lambda cls: Selector()))
    text = "Synthetic complete evidence must retain its qualifier."
    payload = {"question": "What must be retained?", "evidence": [{"citation_id": "E-allowed", "excerpt": text}]}
    result = json.loads(service.generate("Instructions\n" + json.dumps(payload)))
    assert result == {"claims": [{"text": text, "citation_ids": ["E-allowed"]}]}
    assert "untrusted data" in captured[0]


@pytest.mark.parametrize("selected", [["E-fabricated"], ["E-allowed", "E-allowed"], [None]])
def test_fabricated_or_duplicate_model_selections_fail_closed(monkeypatch, selected):
    class Selector:
        def chat_bounded(self, *args, **kwargs): return json.dumps({"citation_ids": selected})
    monkeypatch.setattr(service.ProviderFactory, "get_provider", classmethod(lambda cls: Selector()))
    payload = {"question": "Question", "evidence": [{"citation_id": "E-allowed", "excerpt": "Synthetic complete evidence."}]}
    with pytest.raises(ValueError): service.generate("Instructions\n" + json.dumps(payload))


def test_admission_rechecks_bytes_even_if_hash_cache_claims_success(source_page, monkeypatch):
    monkeypatch.setattr(production, "_checked_hash", lambda *args: source_page.manifest)
    source_page.path.write_bytes(b"changed during admission")
    _, documents, _ = production.retrieve("Explain zero trust", 1)
    assert not documents


def test_opt_in_readiness_details_do_not_change_default_contract_or_enable_flag(db_session, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.routes import router
    from app.database.database import get_db
    monkeypatch.setattr(settings, "CYBERGPT_V2_ENABLED", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_MODEL", "synthetic-model")
    monkeypatch.setattr(production, "availability", lambda: {"bundled_sources_expected": 10, "bundled_sources_available": 10, "shared_index_available": True})
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        assert client.get("/ready").json() == {"status": "ready", "database": "available", "ownership_schema": "available"}
        data = client.get("/ready?details=true&CYBERGPT_V2_ENABLED=true").json()
    assert data["cybergpt_v2"] == {"enabled": False, "provider": "groq", "model": "synthetic-model", "bundled_sources_expected": 10, "bundled_sources_available": 10, "shared_index_available": True}
    assert settings.CYBERGPT_V2_ENABLED is False
    assert "JWT_SECRET" not in json.dumps(data) and "API_KEY" not in json.dumps(data)
