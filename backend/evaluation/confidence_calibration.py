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

from evaluate_benchmarks import EVALUATION_DIR  # noqa: E402

from app.rag.retriever import HybridRetriever  # noqa: E402

#: Security questions the curated set genuinely does not cover. These are the
#: interesting cases: a keyword matcher would answer them from the documents.
OFF_KB_SECURITY = [
    "What is the difference between AES-128 and AES-256?",
    "How does a Kerberoasting attack work?",
    "How do I configure a NAT rule on a Palo Alto firewall?",
    "What is the difference between SAST and DAST?",
    "How does certificate pinning protect a mobile app?",
    "What is the CVSS score of a vulnerability with high integrity impact only?",
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
    return {
        "question": question,
        "status": metrics.get("status"),
        "returned": len(documents),
        "top_similarity": round(similarities[0], 4) if similarities else 0.0,
        "mean_similarity": (
            round(statistics.fmean(similarities), 4) if similarities else 0.0
        ),
    }


def summarise(label: str, rows: list[dict]) -> dict:
    tops = [row["top_similarity"] for row in rows]
    return {
        "group": label,
        "sample_size": len(rows),
        "min": round(min(tops), 4),
        "median": round(statistics.median(tops), 4),
        "max": round(max(tops), 4),
        "rows": rows,
    }


def main():
    cases = json.loads(
        (EVALUATION_DIR / "rag_cases.json").read_text(encoding="utf-8")
    )

    groups = [
        ("in_knowledge_base", [probe(case["question"]) for case in cases]),
        ("security_not_in_kb", [probe(q) for q in OFF_KB_SECURITY]),
        ("unrelated", [probe(q) for q in UNRELATED]),
    ]

    summary = [summarise(label, rows) for label, rows in groups]

    # A threshold is only defensible if the groups actually separate. Report
    # the overlap explicitly instead of asserting a clean split.
    in_kb = [row["top_similarity"] for row in groups[0][1]]
    off_kb = [row["top_similarity"] for row in groups[1][1]]
    unrelated = [row["top_similarity"] for row in groups[2][1]]

    results = {
        "metric": "top semantic similarity of the best retrieved passage",
        "groups": summary,
        "separation": {
            "in_kb_min": round(min(in_kb), 4),
            "security_not_in_kb_max": round(max(off_kb), 4),
            "unrelated_max": round(max(unrelated), 4),
            "in_kb_vs_security_not_in_kb_overlap": round(
                min(in_kb) <= max(off_kb), 4
            ),
            "note": (
                "Similarity is a ranking signal, not a calibrated probability, "
                "so it separates these groups imperfectly. The value of the "
                "measurement is knowing the size of the overlap, which is why "
                "the gate combines the score with the retrieved count and "
                "labels every non-document answer instead of hiding it."
            ),
        },
    }

    output = EVALUATION_DIR / "confidence_calibration.json"
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    header = f"{'group':22} {'n':>3} {'min':>7} {'median':>7} {'max':>7}"
    print(header)
    print("-" * len(header))
    for row in summary:
        print(
            f"{row['group']:22} {row['sample_size']:3d} {row['min']:7.4f} "
            f"{row['median']:7.4f} {row['max']:7.4f}"
        )

    print(f"\nWrote {output}")


if __name__ == "__main__":
    main()
