"""Fail-closed metadata checks and real hybrid retrieval on temporary indexes."""

from pathlib import Path
from types import SimpleNamespace

from langchain_core.documents import Document
import pytest

from app.rag.bm25_store import BM25Store
from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore
from app.rag.retriever import HybridRetriever


def document(metadata, text="Ransomware containment incident response evidence"):
    return Document(page_content=text, metadata=metadata)


@pytest.mark.parametrize("actor", [101, 202, None])
def test_explicit_public_references_remain_visible(actor):
    reference = document({"scope": "knowledge_base", "source_folder": "Governance"})
    assert HybridRetriever._is_visible(reference, actor)


@pytest.mark.parametrize("folder", [
    "uploads", "user_upload", "Uploads", "uploads/user_101",
    "uploads\\user_101", " / UPLOADS / user_101 ",
])
def test_legacy_upload_markers_require_the_actual_owner(folder):
    private = document({"source_folder": folder, "user_id": 101})
    assert HybridRetriever._is_visible(private, 101)
    assert not HybridRetriever._is_visible(private, 202)
    assert not HybridRetriever._is_visible(private, None)
    assert not HybridRetriever._is_visible(document({"source_folder": folder}), 101)


@pytest.mark.parametrize("metadata", [
    {},
    {"source_folder": "Governance"},
    {"user_id": 101},
    {"scope": "unknown", "user_id": 101},
    {"scope": "public"},
    {"scope": ["knowledge_base"]},
    {"scope": {"value": "knowledge_base"}},
    {"scope": True},
    {"scope": "knowledge_base", "source_folder": "uploads"},
    {"scope": "knowledge_base", "source_folder": " USER_UPLOAD "},
    {"scope": "knowledge_base", "source_folder": "uploads/user_101"},
    {"scope": "knowledge_base", "user_id": 101},
    {"scope": "knowledge_base", "user_id": None},
    {"scope": "knowledge_base", "source_folder": ["uploads"]},
    {"scope": "user_upload"},
    {"scope": "user_upload", "user_id": None},
    {"scope": "user_upload", "user_id": True},
    {"scope": "user_upload", "user_id": 0},
    {"scope": "user_upload", "user_id": -1},
    {"scope": "user_upload", "user_id": "101"},
    {"scope": "user_upload", "user_id": 101.0},
])
def test_ambiguous_or_invalid_metadata_is_never_public(metadata):
    candidate = document(metadata)
    for actor in (101, 202, None):
        assert not HybridRetriever._is_visible(candidate, actor)


@pytest.mark.parametrize("metadata", [None, [], "not-metadata"])
def test_malformed_metadata_fails_closed(metadata):
    assert not HybridRetriever._is_visible(SimpleNamespace(metadata=metadata), 101)


@pytest.mark.parametrize("actor", [None, True, 0, -1, "1", 1.0])
def test_invalid_calling_identity_cannot_match_upload_owner(actor):
    private = document({"scope": "user_upload", "user_id": 1})
    assert not HybridRetriever._is_visible(private, actor)


@pytest.fixture
def hybrid_index(tmp_path, monkeypatch):
    directory = tmp_path / "vector_db"
    assert not directory.resolve().is_relative_to(Path(__file__).resolve().parents[1])
    monkeypatch.setattr(FAISSStore, "INDEX_PATH", directory / "faiss.index")
    monkeypatch.setattr(FAISSStore, "META_PATH", directory / "documents.pkl")
    monkeypatch.setattr(FAISSStore, "_index", None)
    monkeypatch.setattr(FAISSStore, "_documents", None)
    monkeypatch.setattr(BM25Store, "INDEX_PATH", directory / "bm25.pkl")
    monkeypatch.setattr(BM25Store, "DOCS_PATH", directory / "bm25_documents.pkl")
    monkeypatch.setattr(BM25Store, "_bm25", None)
    monkeypatch.setattr(BM25Store, "_documents", None)
    monkeypatch.setattr(EmbeddingService, "_backend", "hash")
    monkeypatch.setattr(EmbeddingService, "_model", None)
    monkeypatch.setattr(EmbeddingService, "_dimension", 384)
    monkeypatch.setenv("RAG_FUSION", "on")

    rows = [
        {"filename": "public.txt", "scope": "knowledge_base"},
        {"filename": "alpha.txt", "scope": "user_upload", "user_id": 101},
        {"filename": "beta.txt", "scope": "user_upload", "user_id": 202},
        {"filename": "legacy-alpha.txt", "source_folder": "uploads", "user_id": 101},
        {"filename": "ownerless.txt", "source_folder": "uploads"},
        {"filename": "unknown.txt", "scope": "unknown", "user_id": 101},
        {"filename": "conflicting.txt", "scope": "knowledge_base", "user_id": 202},
        {"filename": "missing-scope.txt", "user_id": 101},
    ]
    documents = [document({**metadata, "page": 0}) for metadata in rows]
    # Unrelated public documents keep the query terms selective for BM25.
    documents.extend(
        document({"filename": f"unrelated-{number}.txt", "page": 0,
                  "scope": "knowledge_base"},
                 f"Astronomy telescope observations orbital mechanics sample {number}")
        for number in range(12)
    )
    vectors = EmbeddingService.embed_documents(doc.page_content for doc in documents)
    FAISSStore.build_index(vectors, documents)
    BM25Store.build_index(documents)

    # Exercise on-disk load paths too, with every file confined to tmp_path.
    FAISSStore._index = None
    FAISSStore._documents = None
    BM25Store._bm25 = None
    BM25Store._documents = None


@pytest.mark.parametrize("actor,include_uploads,expected", [
    (101, True, {"public.txt", "alpha.txt", "legacy-alpha.txt"}),
    (202, True, {"public.txt", "beta.txt"}),
    (None, True, {"public.txt"}),
    (101, False, {"public.txt"}),
])
def test_real_hybrid_search_never_returns_foreign_or_ambiguous_chunks(
    hybrid_index, actor, include_uploads, expected
):
    results, metrics = HybridRetriever.search_with_metrics(
        "ransomware containment incident response evidence", top_k=20,
        user_id=actor, include_uploads=include_uploads,
    )
    assert {item.metadata["filename"] for item in results} == expected
    assert metrics["fusion"] == "reciprocal_rank_fusion+rerank+mmr"
    assert metrics["embedding_backend"] == "hash"
    assert metrics["lexical_candidates"] > 0
    assert metrics["vector_candidates"] > 0
