"""Offline worker benchmark; run: python -B -m app.knowledge.evaluation.

Never import the worker into a serving process: it owns temporary store state.
Importing this module alone does not import application stores or providers.
"""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import math
import os
from pathlib import Path
import socket
import sys
import tempfile

from .ingestion import Catalog, FIXTURE_ROOT

RETRIEVED_AT = datetime(2026, 10, 30, tzinfo=timezone.utc)
MODES = ("bm25", "faiss_hash", "hybrid", "hybrid_mmr")


def fixture_catalog():
    catalog = Catalog()
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["artifacts"]:
        catalog.ingest_artifact(item["artifact_id"], FIXTURE_ROOT/item["filename"], retrieved_at=RETRIEVED_AT)
    catalog.ingest_private(record_id="PRIVATE-ORCHID-71", title="Synthetic incident recovery",
        text="PRIVATE-ORCHID-71 incident recovery requires rotating the synthetic access credential.",
        owner_id=101, retrieved_at=RETRIEVED_AT)
    return catalog


def ranking_metrics(ranked, relevant, k=5):
    """Binary document relevance. Duplicate chunks earn no additional credit."""
    ranked = list(dict.fromkeys(ranked))[:k]
    gold = set(relevant)
    if not gold:
        raise ValueError("Empty-gold abstention cases are scored separately.")
    hits = [int(item in gold) for item in ranked]
    return {
        "recall_at_5": sum(hits)/len(gold),
        "precision_at_5": sum(hits)/k,
        "mrr": next((1/(i+1) for i, hit in enumerate(hits) if hit), 0.0),
        "ndcg_at_5": sum(hit/math.log2(i+2) for i, hit in enumerate(hits)) /
            sum(1/math.log2(i+2) for i in range(min(len(gold), k))),
    }


def _extractive_stub(prompt):
    """Deterministic generator stand-in, not an LLM-quality measurement."""
    evidence = json.loads(prompt.split("\n", 1)[1])["evidence"]
    return json.dumps({"claims": [{"text": evidence[0]["excerpt"],
                                  "citation_ids": [evidence[0]["citation_id"]]}]})


def _rank(mode, question, user_id, documents):
    from app.rag.bm25_store import BM25Store
    from app.rag.faiss_store import FAISSStore
    from app.rag.embeddings import EmbeddingService
    from app.rag.retriever import HybridRetriever

    if mode == "bm25":
        scores = BM25Store.load().get_scores(BM25Store.tokenize(question))
        order = sorted(range(len(documents)), key=lambda i: (-float(scores[i]), documents[i].metadata["chunk_id"]))
        return tuple(documents[i] for i in order[:5])
    if mode == "faiss_hash":
        index, stored = FAISSStore.load()
        distances, indices = index.search(EmbeddingService.embed_query(question), len(stored))
        order = sorted(zip(distances[0], indices[0]), key=lambda pair: (float(pair[0]), stored[int(pair[1])].metadata["chunk_id"]))
        return tuple(stored[int(i)] for _, i in order[:5])
    os.environ["RAG_FUSION"] = "on"
    os.environ["RAG_MMR_LAMBDA"] = "0.85" if mode == "hybrid_mmr" else "1.0"
    found, _ = HybridRetriever.search_with_metrics(question, top_k=5, user_id=user_id, include_uploads=True)
    return tuple(found)


def run_worker():
    """Own a fresh process, deny network, and create only disposable indexes."""
    if any(name in sys.modules for name in ("app.rag.faiss_store", "app.rag.bm25_store", "app.rag.embeddings")):
        raise RuntimeError("Run the benchmark in a fresh dedicated process.")
    sys.dont_write_bytecode = True
    original_connect = socket.socket.connect
    original_create = socket.create_connection
    def deny_network(*args, **kwargs):
        raise RuntimeError("Network is disabled for the offline benchmark.")
    socket.socket.connect = deny_network
    socket.create_connection = deny_network
    try:
        with tempfile.TemporaryDirectory(prefix="cybershield-source-eval-") as temporary:
            previous = dict(os.environ)
            try:
                # Ignore ambient tuning so repeated runs compare the same system.
                for name in tuple(os.environ):
                    if name.startswith("RAG_") or name.startswith("EMBEDDING_"):
                        os.environ.pop(name)
                os.environ["VECTOR_DB_DIR"] = str(Path(temporary)/"indexes")
                os.environ["EMBEDDING_BACKEND"] = "hash"
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                os.environ["HF_HOME"] = str(Path(temporary)/"unused-model-cache")
                with redirect_stdout(io.StringIO()):
                    report = _evaluate()
            finally:
                os.environ.clear()
                os.environ.update(previous)
    finally:
        socket.socket.connect = original_connect
        socket.create_connection = original_create
    return report


def _evaluate():
    from app.rag.bm25_store import BM25Store
    from app.rag.faiss_store import FAISSStore
    from app.rag.embeddings import EmbeddingService
    from .evidence import collect_evidence, grounded_answer

    storage = Path(os.environ["VECTOR_DB_DIR"]).resolve()
    assert FAISSStore.INDEX_PATH.resolve().is_relative_to(storage)
    assert BM25Store.INDEX_PATH.resolve().is_relative_to(storage)
    catalog = fixture_catalog()
    questions = json.loads((FIXTURE_ROOT/"questions.json").read_text(encoding="utf-8"))["questions"]
    report = {
        "dataset": {"questions": len(questions),
                    "answerable": sum(bool(q["gold"]) for q in questions),
                    "abstention": sum(q["abstain"] for q in questions),
                    "current_public_records": sum(r.scope == "public" and r.state == "active" for r in catalog.current_records()),
                    "private_records": 1},
        "embedding": {"backend": EmbeddingService.backend_name(), "dimension": EmbeddingService.dimension(),
                      "semantic_model_compared": False},
        "scoring": {"k": 5, "unit": "current document; binary relevance",
                    "precision_denominator": 5, "empty_gold": "excluded from ranking aggregates; abstention scored separately",
                    "generation": "deterministic first-excerpt stub, not model accuracy",
                    "cross_encoder": "optional authorized reranker contract; no model configured",
                    "hybrid": "existing RRF + blended rerank + page dedup; lambda=1.0",
                    "hybrid_mmr": "same existing pipeline with lambda=0.85"},
        "modes": {},
    }
    for mode in MODES:
        cases, measured = [], []
        accepted = valid_citations = total_citations = supported = total_claims = 0
        correct_abstentions = abstention_cases = gold_covered = gold_total = 0
        active_user = None
        for question in questions:
            actor = question["user_id"]
            if actor != active_user:
                documents = sorted(catalog.documents(actor), key=lambda d: d.metadata["chunk_id"])
                FAISSStore._index = FAISSStore._documents = None
                BM25Store._bm25 = BM25Store._documents = None
                FAISSStore.build_index(EmbeddingService.embed_documents([d.page_content for d in documents]), documents)
                BM25Store.build_index(documents)
                active_user = actor
            retrieved = _rank(mode, question["question"], actor, documents)
            evidence = collect_evidence(catalog, retrieved, actor)
            ranked = list(dict.fromkeys(item.record_id for item in evidence))
            metric = ranking_metrics(ranked, question["gold"]) if question["gold"] else None
            if metric:
                measured.append(metric)
            answer = grounded_answer(question["question"], retrieved, catalog, actor, generator=_extractive_stub)
            if question["abstain"]:
                abstention_cases += 1
                correct_abstentions += answer.abstained
            if not answer.abstained:
                accepted += 1
            resolved = {item.citation_id:item for item in evidence}
            for claim in answer.claims:
                total_claims += 1
                supported += all(cid in resolved and claim.text in resolved[cid].excerpt for cid in claim.citation_ids)
                for cid in claim.citation_ids:
                    total_citations += 1
                    valid_citations += cid in resolved
            gold_total += len(question["gold"])
            gold_covered += len(set(question["gold"]) & {item.record_id for item in answer.evidence})
            cases.append({"id": question["id"], "ranked_record_ids": ranked,
                          "ranking": metric, "abstained": answer.abstained, "reason": answer.reason})
        report["modes"][mode] = {
            "retrieval": {key: round(sum(m[key] for m in measured)/len(measured), 6) for key in measured[0]},
            "generation_contract": {
                "accepted_answers": accepted, "claims": total_claims,
                "citation_validity": valid_citations/total_citations if total_citations else None,
                "evidence_coverage": gold_covered/gold_total,
                "unsupported_excerpt_rate": 1-supported/total_claims if total_claims else None,
                "semantic_unsupported_claim_rate": None,
                "correct_abstentions": correct_abstentions, "abstention_cases": abstention_cases,
            },
            "cases": cases,
        }
    return report


if __name__ == "__main__":
    print(json.dumps(run_worker(), indent=2, sort_keys=True))
