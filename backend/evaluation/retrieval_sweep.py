"""Retrieval configuration sweep.

The audit found the retrieval pipeline had never been measured end to end: the
chunk size, the fusion weights and the relevance floor were all inherited
choices. This script varies them against the labelled question set and reports
retrieval metrics, so each claim about the pipeline is backed by a number
rather than by intuition.

Two design choices make the numbers trustworthy:

* **One code path.** Every configuration is scored through
  :meth:`HybridRetriever.search_with_metrics`, the method the API serves. A
  reimplementation inside the harness could pass while the real retriever
  failed.
* **Both axes together.** Chunk size and fusion interact. Measuring them one at
  a time produced a confident, wrong conclusion during development - dense-only
  looked clearly better at 800/150 and clearly worse at 600/100 - so the sweep
  runs the cross product and the shipped configuration is read off the grid.

This script rebuilds the on-disk index for each chunk setting and restores the
shipped configuration when it finishes. Run it from ``backend/``:

    python evaluation/retrieval_sweep.py
"""

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from evaluate_benchmarks import EVALUATION_DIR, TOP_K, query_metrics  # noqa: E402

from app.rag.retriever import HybridRetriever  # noqa: E402
from app.services.knowledge_base_service import KnowledgeBaseService  # noqa: E402

#: (label, environment overrides) for the ranking stage, scored at every chunk
#: setting. Labels describe the configuration, never the expectation.
FUSION_CONFIGURATIONS = [
    ("dense + mmr", {"RAG_FUSION": "off"}),
    ("dense, no mmr", {"RAG_FUSION": "off", "RAG_MMR_LAMBDA": "1.0"}),
    ("fused + mmr, tuned dense weight", {"RAG_FUSION": "on"}),
    (
        "fused + mmr, inherited weights",
        {
            "RAG_FUSION": "on",
            "RAG_RERANK_RRF_WEIGHT": "0.55",
            "RAG_RERANK_SEMANTIC_WEIGHT": "0.30",
            "RAG_RERANK_COVERAGE_WEIGHT": "0.15",
        },
    ),
    (
        "fused + mmr, relevance floor off",
        {"RAG_FUSION": "on", "RAG_FLOOR_TRIGGER_COVERAGE": "2.0"},
    ),
]

CHUNK_SETTINGS = [(600, 100), (800, 150), (1000, 200), (1200, 250)]

SHIPPED_CHUNK_SIZE = 600
SHIPPED_CHUNK_OVERLAP = 100

TUNED_KEYS = [
    "RAG_FUSION",
    "RAG_MMR_LAMBDA",
    "RAG_FLOOR_TRIGGER_COVERAGE",
    "RAG_FLOOR_MINIMUM",
    "RAG_FLOOR_FRACTION",
    "RAG_POOL_MULTIPLIER_PLAIN",
    "RAG_POOL_MULTIPLIER_FILTERED",
    "RAG_RERANK_POOL",
    "RAG_RERANK_RRF_WEIGHT",
    "RAG_RERANK_SEMANTIC_WEIGHT",
    "RAG_RERANK_COVERAGE_WEIGHT",
    "RAG_COVERAGE_WEIGHT",
    "RAG_RRF_K",
]


def clear_tuning() -> None:
    for key in TUNED_KEYS:
        os.environ.pop(key, None)


def score(cases) -> dict:
    """Score the live retriever over every labelled question."""

    rows = []
    for case in cases:
        relevant = {
            (item["source"], int(item["page"]))
            for item in case["relevant_pages"]
        }
        documents, metrics = HybridRetriever.search_with_metrics(
            query=case["question"],
            top_k=TOP_K,
            user_id=None,
            include_uploads=False,
        )
        retrieved = [
            (
                document.metadata.get("filename"),
                int(document.metadata.get("page", 0)) + 1,
            )
            for document in documents
        ]
        row = query_metrics(retrieved, relevant)
        row["returned_result"] = metrics.get("status") == "ok"
        rows.append(row)

    return {
        metric: round(sum(row[metric] for row in rows) / len(rows), 4)
        for metric in (
            "recall_at_5",
            "mrr",
            "ndcg_at_5",
            "source_page_precision_at_5",
        )
    } | {
        "queries_with_no_result": sum(
            1 for row in rows if not row["returned_result"]
        ),
    }


def main():
    cases = json.loads(
        (EVALUATION_DIR / "rag_cases.json").read_text(encoding="utf-8")
    )

    grid: dict[str, dict] = {}

    for size, overlap in CHUNK_SETTINGS:

        clear_tuning()
        os.environ["RAG_CHUNK_SIZE"] = str(size)
        os.environ["RAG_CHUNK_OVERLAP"] = str(overlap)
        build = KnowledgeBaseService.ensure_index()

        setting = f"{size}/{overlap}"
        grid[setting] = {"index": build, "configurations": {}}

        for label, overrides in FUSION_CONFIGURATIONS:
            clear_tuning()
            os.environ.update(overrides)
            grid[setting]["configurations"][label] = score(cases)

        print(f"measured {setting}: {build}")

    # Restore the shipped configuration and leave the index built for it, so
    # running the sweep does not change what the application serves.
    clear_tuning()
    os.environ["RAG_CHUNK_SIZE"] = str(SHIPPED_CHUNK_SIZE)
    os.environ["RAG_CHUNK_OVERLAP"] = str(SHIPPED_CHUNK_OVERLAP)
    restored = KnowledgeBaseService.ensure_index()
    clear_tuning()

    results = {
        "sample_size": len(cases),
        "top_k": TOP_K,
        "note": (
            "Every configuration is scored through HybridRetriever."
            "search_with_metrics with user_id=None, the same path the API "
            "serves, so these numbers describe what a user would receive. "
            "Relevance is binary page-level: a result counts only when its "
            f"source filename and 1-based PDF page match a gold page. With "
            f"{len(cases)} questions one question is worth "
            f"{round(100 / len(cases), 1)} points of Recall@5, so differences "
            "smaller than about two questions are not decisive."
        ),
        "shipped_configuration": {
            "chunk_size": SHIPPED_CHUNK_SIZE,
            "chunk_overlap": SHIPPED_CHUNK_OVERLAP,
            "fusion": "on",
            "mmr_lambda": 0.72,
            "rerank_weights": {"rrf": 0.30, "semantic": 0.55, "coverage": 0.15},
        },
        "restored_after_sweep": restored,
        "grid": grid,
    }

    output = EVALUATION_DIR / "retrieval_sweep.json"
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    # A compact table is more useful than the JSON when reading a terminal.
    print()
    header = f"{'chunking':>10}  {'configuration':34} {'R@5':>7} {'MRR':>7} {'nDCG@5':>7}"
    print(header)
    print("-" * len(header))
    for setting, payload in grid.items():
        for label, metrics in payload["configurations"].items():
            print(
                f"{setting:>10}  {label:34} "
                f"{metrics['recall_at_5']:7.4f} {metrics['mrr']:7.4f} "
                f"{metrics['ndcg_at_5']:7.4f}"
            )
    print(f"\nWrote {output}")


if __name__ == "__main__":
    main()
