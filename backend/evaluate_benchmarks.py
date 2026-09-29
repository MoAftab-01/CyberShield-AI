"""Evaluate retrieval variants and the local URL-risk heuristic.

Retrieval arms and what each one is for:

===================  =====================================================
``bm25_only``        Lexical baseline. Unchanged formula.
``hashed_vector_only``  Legacy lexical-hash embedding arm. Reproduces the
                     pre-change baseline number and is embedded with
                     :meth:`EmbeddingService.hash_vectors` on purpose, so it
                     stays comparable after the index moved to a semantic
                     encoder.
``dense_vector_only``   Same formula as the arm above, but against the live
                     encoder. The only difference between the two arms is the
                     representation, which is what makes the comparison a
                     measurement of the embedding change rather than of
                     anything else.
``hybrid_rrf``       Unchanged fusion formula over the live index.
``production``       The retriever the application actually calls, so the
                     headline number is the one users experience rather than a
                     harness-only idealisation.
===================  =====================================================
"""

import csv
import json
import math
import pickle
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from app.rag.bm25_store import BM25Store
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import HybridRetriever
from app.utils.url_utils import (
    calculate_url_risk,
    contains_ip,
    count_subdomains,
    detect_keywords,
    extract_domain,
    url_length,
    uses_https,
)


BASE_DIR = Path(__file__).resolve().parent
EVALUATION_DIR = BASE_DIR / "evaluation"
INDEX_DIR = BASE_DIR / "vector_db"

#: Restricts scoring to the public knowledge base. Historically this filter
#: also hid a cross-tenant leak (a user's uploaded CV, indexed into the shared
#: index and readable by everyone). Retrieval now enforces visibility itself,
#: so this should exclude nothing; the harness asserts that rather than
#: assuming it.
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
ALLOWED_SOURCES = {
    path.name
    for path in KNOWLEDGE_BASE_DIR.rglob("*")
    if path.is_file() and path.suffix.lower() in {".pdf", ".txt", ".md"}
}
TOP_K = 5


def page_key(document):
    page = document.metadata.get("page")
    return document.metadata.get("filename"), int(page) + 1


def unique_pages(indices, documents, limit=TOP_K):
    pages = []
    seen = set()
    for index in indices:
        key = page_key(documents[int(index)])
        if key in seen:
            continue
        seen.add(key)
        pages.append(key)
        if len(pages) == limit:
            break
    return pages


def ndcg_at_k(retrieved, relevant, k=TOP_K):
    relevance = [int(page in relevant) for page in retrieved[:k]]
    dcg = sum(score / math.log2(rank + 1) for rank, score in enumerate(relevance, 1))
    ideal_hits = min(len(relevant), k)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / ideal if ideal else 0.0


def query_metrics(retrieved, relevant):
    retrieved = retrieved[:TOP_K]
    relevant = set(relevant)
    hits = [rank for rank, page in enumerate(retrieved, 1) if page in relevant]
    return {
        "recall_at_5": len(hits) / len(relevant) if relevant else 0.0,
        "mrr": 1 / hits[0] if hits else 0.0,
        "ndcg_at_5": ndcg_at_k(retrieved, relevant),
        "source_page_precision_at_5": (
            len(hits) / len(retrieved) if retrieved else 0.0
        ),
        "source_page_recall_at_5": (
            len(hits) / len(relevant) if relevant else 0.0
        ),
    }


def build_retrievers():
    documents = pickle.loads((INDEX_DIR / "documents.pkl").read_bytes())
    stored_faiss = faiss.read_index(str(INDEX_DIR / "faiss.index"))
    if stored_faiss.ntotal != len(documents):
        raise ValueError("FAISS vector count does not match document metadata.")

    selected_indices = [
        index
        for index, document in enumerate(documents)
        if document.metadata.get("filename") in ALLOWED_SOURCES
    ]
    safe_documents = [documents[index] for index in selected_indices]
    if not safe_documents:
        raise ValueError("No indexed documents matched the public KB source list.")

    safe_vectors = np.vstack(
        [stored_faiss.reconstruct(index) for index in selected_indices]
    ).astype("float32")
    vector_index = faiss.IndexFlatL2(stored_faiss.d)
    vector_index.add(safe_vectors)

    # The legacy arm needs vectors from the encoder it was measured with, so
    # they are rebuilt here rather than reused from the live index.
    hash_vectors = EmbeddingService.hash_vectors(
        [document.page_content for document in safe_documents]
    )
    hash_index = faiss.IndexFlatL2(hash_vectors.shape[1])
    hash_index.add(hash_vectors)

    bm25 = BM25Okapi(
        [BM25Store.tokenize(document.page_content) for document in safe_documents]
    )

    excluded = [
        document.metadata.get("filename")
        for index, document in enumerate(documents)
        if index not in set(selected_indices)
    ]

    return {
        "documents": safe_documents,
        "vector_index": vector_index,
        "hash_index": hash_index,
        "bm25": bm25,
        "excluded_count": len(excluded),
        "excluded_sources": sorted(set(excluded)),
    }


def retrieve_bm25(question, documents, bm25):
    scores = np.asarray(bm25.get_scores(BM25Store.tokenize(question)))
    return unique_pages(np.argsort(scores)[::-1], documents)


def retrieve_hash_vector(question, documents, vector_index):
    """Legacy arm: hashed query vectors against the stored index vectors.

    Only meaningful when the index was itself built with the hashed encoder.
    :func:`build_retrievers` therefore scores this arm against a hash-built
    index of its own rather than against the live one.
    """

    query = np.asarray(EmbeddingService.hash_vectors([question]), dtype="float32")
    _, indices = vector_index.search(query, len(documents))
    return unique_pages(indices[0], documents)


def retrieve_dense_vector(question, documents, vector_index):
    """Same formula as above, live encoder."""

    query = np.asarray(EmbeddingService.embed_query(question), dtype="float32")
    _, indices = vector_index.search(query, len(documents))
    return unique_pages(indices[0], documents)


def retrieve_hybrid(question, documents, vector_index, bm25):
    candidate_count = min(len(documents), max(TOP_K * 8, 20))
    query = np.asarray(EmbeddingService.embed_query(question), dtype="float32")
    _, vector_indices = vector_index.search(query, candidate_count)
    lexical_scores = np.asarray(bm25.get_scores(BM25Store.tokenize(question)))
    lexical_indices = np.argsort(lexical_scores)[::-1][:candidate_count]
    query_terms = {
        term
        for term in BM25Store.tokenize(question)
        if not term.startswith("phrase:")
    }

    ranks = {}
    coverage = {}
    for rank, index in enumerate(vector_indices[0], 1):
        index = int(index)
        if index >= 0:
            ranks[index] = ranks.get(index, 0.0) + 1 / (60 + rank)
    for rank, index in enumerate(lexical_indices, 1):
        index = int(index)
        ranks[index] = ranks.get(index, 0.0) + 1 / (60 + rank)

    for index in ranks:
        document_terms = {
            term
            for term in BM25Store.tokenize(documents[index].page_content)
            if not term.startswith("phrase:")
        }
        coverage[index] = (
            len(query_terms & document_terms) / len(query_terms)
            if query_terms
            else 0.0
        )
        ranks[index] += coverage[index] * 0.05

    ordered = sorted(ranks, key=lambda index: ranks[index], reverse=True)
    top_coverage = coverage[ordered[0]] if ordered else 0.0
    relevance_floor = max(0.35, top_coverage * 0.5) if top_coverage >= 0.5 else 0
    selected = []
    seen_pages = set()
    for index in ordered:
        if relevance_floor and coverage[index] < relevance_floor:
            continue
        key = page_key(documents[index])
        if key in seen_pages:
            continue
        seen_pages.add(key)
        selected.append(key)
        if len(selected) == TOP_K:
            break
    return selected


def retrieve_production(question):
    """The retriever the API serves, scored through its own public method.

    Run with ``user_id=None`` to measure the anonymous/public view, which is
    the stricter case: scoped visibility must still surface the public
    knowledge base in full.
    """

    results, _metrics = HybridRetriever.search_with_metrics(
        query=question,
        top_k=TOP_K,
        user_id=None,
        include_uploads=False,
    )
    pages = []
    for document in results:
        pages.append(
            (
                document.metadata.get("filename"),
                int(document.metadata.get("page", 0)) + 1,
            )
        )
    return pages


def load_rag_cases():
    """Load the base benchmark plus any expanded cases contributed later.

    A file named ``rag_cases_expanded.json`` is treated as additive. That keeps
    the current benchmark stable while making it easy to grow the gold set with
    more curated pages without editing the original minimal baseline by hand.
    """
    base_path = EVALUATION_DIR / "rag_cases.json"
    expanded_path = EVALUATION_DIR / "rag_cases_expanded.json"

    cases = json.loads(base_path.read_text(encoding="utf-8"))

    if expanded_path.exists():
        expanded = json.loads(expanded_path.read_text(encoding="utf-8"))
        cases.extend(expanded)

    identifiers = [case["id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("RAG benchmark case IDs must be unique across both files.")

    return cases


def validate_gold_pages(cases, indexed_pages):
    """Reject benchmark labels that cannot be retrieved from this KB index."""
    missing = sorted(
        {
            (item["source"], int(item["page"]))
            for case in cases
            for item in case["relevant_pages"]
            if (item["source"], int(item["page"])) not in indexed_pages
        }
    )
    if missing:
        raise ValueError(
            "Gold labels reference pages absent from the indexed knowledge base: "
            + ", ".join(f"{source} p.{page}" for source, page in missing)
        )


def evaluate_retrieval():
    cases = load_rag_cases()
    bundle = build_retrievers()
    documents = bundle["documents"]
    indexed_pages = {
        (document.metadata.get("filename"), int(document.metadata.get("page", 0)) + 1)
        for document in documents
    }
    validate_gold_pages(cases, indexed_pages)
    vector_index = bundle["vector_index"]
    hash_index = bundle["hash_index"]
    bm25 = bundle["bm25"]

    methods = {
        "bm25_only": lambda question: retrieve_bm25(question, documents, bm25),
        "hashed_vector_only": lambda question: retrieve_hash_vector(
            question, documents, hash_index
        ),
        "dense_vector_only": lambda question: retrieve_dense_vector(
            question, documents, vector_index
        ),
        "hybrid_rrf": lambda question: retrieve_hybrid(
            question, documents, vector_index, bm25
        ),
        "production": retrieve_production,
    }
    per_question = []
    metric_values = {method: [] for method in methods}

    for case in cases:
        relevant = {
            (item["source"], int(item["page"]))
            for item in case["relevant_pages"]
        }
        method_results = {}
        for method, retrieve in methods.items():
            retrieved = retrieve(case["question"])
            scores = query_metrics(retrieved, relevant)
            metric_values[method].append(scores)
            method_results[method] = {
                "metrics": scores,
                "retrieved_pages": [
                    {"source": source, "page": page}
                    for source, page in retrieved
                ],
            }
        per_question.append(
            {
                "id": case["id"],
                "question": case["question"],
                "gold_pages": [
                    {"source": source, "page": page}
                    for source, page in sorted(relevant)
                ],
                "methods": method_results,
            }
        )

    summary = {
        method: {
            metric: round(
                sum(row[metric] for row in rows) / len(rows), 4
            )
            for metric in rows[0]
        }
        for method, rows in metric_values.items()
    }
    return {
        "sample_size": len(cases),
        "top_k": TOP_K,
        "embedding_backend": EmbeddingService.backend_name(),
        "embedding_model": EmbeddingService.model_name(),
        "embedding_dimension": EmbeddingService.dimension(),
        "included_public_sources": sorted(ALLOWED_SOURCES),
        "safe_index_chunks": len(documents),
        "excluded_non_kb_index_chunks": bundle["excluded_count"],
        "excluded_non_kb_sources": bundle["excluded_sources"],
        "metrics": summary,
        "per_question": per_question,
    }


def classification_metrics(cases, predictions):
    true_positive = sum(
        case["suspicious"] == 1 and predictions[case["id"]] == 1
        for case in cases
    )
    false_positive = sum(
        case["suspicious"] == 0 and predictions[case["id"]] == 1
        for case in cases
    )
    true_negative = sum(
        case["suspicious"] == 0 and predictions[case["id"]] == 0
        for case in cases
    )
    false_negative = sum(
        case["suspicious"] == 1 and predictions[case["id"]] == 0
        for case in cases
    )
    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    return {
        "accuracy": (true_positive + true_negative) / len(cases),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0,
        "specificity": (
            true_negative / (true_negative + false_positive)
            if true_negative + false_positive
            else 0.0
        ),
        "confusion_matrix": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
        },
    }


def evaluate_url_detection():
    cases = json.loads((EVALUATION_DIR / "url_cases.json").read_text(encoding="utf-8"))
    predictions = {}
    details = []
    for case in cases:
        url = case["url"]
        domain = extract_domain(url)
        score, level, _ = calculate_url_risk(
            https=uses_https(url),
            contains_ip_address=contains_ip(url),
            keywords=detect_keywords(url),
            length=url_length(url),
            subdomains=count_subdomains(domain),
        )
        prediction = int(level in {"High", "Critical"})
        predictions[case["id"]] = prediction
        details.append(
            {
                "id": case["id"],
                "expected_suspicious": case["suspicious"],
                "predicted_suspicious": prediction,
                "risk_score": score,
                "risk_level": level,
            }
        )
    return {
        "sample_size": len(cases),
        "positive_decision_threshold": ["High", "Critical"],
        "scope": "Local URL heuristic only; VirusTotal is not queried.",
        "dataset_note": "Synthetic, hand-labeled fixtures; not a real-world phishing corpus.",
        "metrics": {
            key: round(value, 4) if isinstance(value, float) else value
            for key, value in classification_metrics(cases, predictions).items()
        },
        "per_case": details,
    }


def evaluate_answer_annotations():
    path = EVALUATION_DIR / "answer_annotations.csv"
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    reviewed = [
        row
        for row in rows
        if row.get("generated_answer", "").strip()
        and row.get("citations_correct", "") in {"0", "1"}
        and row.get("all_factual_claims_supported", "") in {"0", "1"}
    ]
    if not reviewed:
        return {
            "status": "pending_manual_review",
            "sample_size": 0,
            "citation_correctness": None,
            "faithfulness": None,
        }
    return {
        "status": "manually_reviewed",
        "sample_size": len(reviewed),
        "citation_correctness": round(
            sum(int(row["citations_correct"]) for row in reviewed) / len(reviewed), 4
        ),
        "faithfulness": round(
            sum(int(row["all_factual_claims_supported"]) for row in reviewed)
            / len(reviewed),
            4,
        ),
    }


def main():
    results = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "retrieval": evaluate_retrieval(),
        "url_detection": evaluate_url_detection(),
        "answer_review": evaluate_answer_annotations(),
        "methodology": {
            "retrieval_relevance": "A result is relevant only when its source filename and 1-based PDF page match a curated gold page.",
            "retrieval_averaging": "Macro average across benchmark questions; page-level binary relevance.",
            "url_decision": "High/Critical local risk is suspicious; Low/Medium is not suspicious.",
            "answer_review": "Claim support and citation correctness require manual review of generated answers; retrieval source-page alignment alone is not answer faithfulness.",
        },
    }
    output = EVALUATION_DIR / "results.json"
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote evaluation results to {output}")
    print(json.dumps({
        "retrieval": results["retrieval"]["metrics"],
        "url_detection": results["url_detection"]["metrics"],
        "answer_review": results["answer_review"],
    }, indent=2))


if __name__ == "__main__":
    main()