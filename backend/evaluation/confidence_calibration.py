"""Calibrate the retrieval confidence gate.

The assistant needs to decide, per question, whether the knowledge base can
answer it. Get this wrong in one direction and it claims a document says
something it does not; wrong in the other and it refuses a question the
documents answer. Both failures were present before this work, in the form of a
prompt instruction ("use ONLY the supplied context") that was never backed by
a measurement.

This script measures the signal the gate would use - the top cosine similarity
returned by the live retriever - across three groups of questions:

* **in the knowledge base** - the labelled benchmark questions, which should
  pass the gate;
* **security, but not in the knowledge base** - real questions the curated
  documents do not cover, which should fall back to general knowledge;
* **unrelated to security** - which should be declined outright.

The output is the separation between the groups, which is what justifies a
threshold rather than a guess. Run from ``backend/``:

    python evaluation/confidence_calibration.py
"""

import json
import statistics
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from evaluate_benchmarks import EVALUATION_DIR, load_rag_cases  # noqa: E402

from app.rag.embeddings import EmbeddingService  # noqa: E402
from app.rag.retriever import HybridRetriever  # noqa: E402
from app.services.rag_service import RAGService  # noqa: E402

#: Security questions the curated set genuinely does not cover. These are the
#: interesting cases: a keyword matcher would answer them from the documents.
OFF_KB_SECURITY = [
    "How does a Kerberoasting attack work?",
    "How do I configure a NAT rule on a Palo Alto firewall?",
    "What is the difference between SAST and DAST?",
    "How does certificate pinning protect a mobile app?",
    "What is the CVSS score of a vulnerability with high integrity impact only?",
    "How can I configure an EDR exclusion policy in Microsoft Defender for Endpoint?",
]

#: Nothing to do with security or the knowledge base.
UNRELATED = [
    "What is the capital of France?",
    "Write a poem about the ocean.",
    "How do I bake sourdough bread?",
    "Who won the 2018 FIFA World Cup?",
    "Convert 15 US dollars into euros.",
    "What is the weather in Tokyo tomorrow?",
]

TOP_K = 5


def probe(question: str) -> dict:
    documents, metrics = HybridRetriever.search_with_metrics(
        query=question,
        top_k=TOP_K,
        user_id=None,
        include_uploads=False,
    )
    similarities = [
        float(document.metadata.get("semantic_similarity") or 0.0)
        for document in documents
    ]
    coverages = [
        float(document.metadata.get("query_term_coverage") or 0.0)
        for document in documents
    ]
    lexical_ranks = [
        int(document.metadata["lexical_rank"])
        for document in documents
        if document.metadata.get("lexical_rank") is not None
    ]
    backend = metrics.get("embedding_backend", EmbeddingService.backend_name())
    return {
        "question": question,
        "status": metrics.get("status"),
        "returned": len(documents),
        "embedding_backend": backend,
        "top_semantic_similarity": (
            round(similarities[0], 4)
            if similarities and backend == "fastembed"
            else None
        ),
        "top_term_coverage": round(max(coverages), 4) if coverages else 0.0,
        "best_lexical_rank": min(lexical_ranks) if lexical_ranks else None,
        "relevance": RAGService._relevance(documents, metrics, question),
    }


def summarise(label: str, rows: list[dict], score_field: str) -> dict:
    scores = [row[score_field] for row in rows if row[score_field] is not None]
    return {
        "group": label,
        "sample_size": len(rows),
        "score_field": score_field,
        "min": round(min(scores), 4) if scores else None,
        "median": round(statistics.median(scores), 4) if scores else None,
        "max": round(max(scores), 4) if scores else None,
        "gate_results": {
            decision: sum(row["relevance"] == decision for row in rows)
            for decision in ("document", "related", "irrelevant")
        },
        "rows": rows,
    }


def main():
    cases = load_rag_cases()

    groups = [
        ("in_knowledge_base", [probe(case["question"]) for case in cases]),
        ("security_not_in_kb", [probe(q) for q in OFF_KB_SECURITY]),
        ("unrelated", [probe(q) for q in UNRELATED]),
    ]

    backend = EmbeddingService.backend_name()
    score_field = (
        "top_semantic_similarity"
        if backend == "fastembed"
        else "top_term_coverage"
    )
    summary = [
        summarise(label, rows, score_field)
        for label, rows in groups
    ]

    if backend == "fastembed":
        in_kb = [row[score_field] for row in groups[0][1]]
        off_kb = [row[score_field] for row in groups[1][1]]
        unrelated = [row[score_field] for row in groups[2][1]]
        separation = {
            "in_kb_min": round(min(in_kb), 4),
            "security_not_in_kb_max": round(max(off_kb), 4),
            "unrelated_max": round(max(unrelated), 4),
            "in_kb_vs_security_not_in_kb_overlap": min(in_kb) <= max(off_kb),
        }
    else:
        separation = {
            "metric": "gate classification counts",
            "false_document_classifications": {
                label: sum(row["relevance"] == "document" for row in rows)
                for label, rows in groups[1:]
            },
            "knowledge_base_questions_classified_document": sum(
                row["relevance"] == "document" for row in groups[0][1]
            ),
        }

    results = {
        "metric": score_field,
        "embedding_backend": backend,
        "groups": summary,
        "separation": separation,
    }

    output = EVALUATION_DIR / "confidence_calibration.json"
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    header = f"{'group':22} {'n':>3} {'min':>7} {'median':>7} {'max':>7}"
    print(header)
    print("-" * len(header))
    for row in summary:
        print(
            f"{row['group']:22} {row['sample_size']:3d} "
            f"{str(row['min']):>7} {str(row['median']):>7} "
            f"{str(row['max']):>7} {row['gate_results']}"
        )

    print(f"\nWrote {output}")


if __name__ == "__main__":
    main()
