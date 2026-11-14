"""Offline StateGraph evaluation. Run with --output <external.json>."""
import argparse
from collections import Counter
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import statistics
import sys

import tempfile
_scratch = Path(tempfile.mkdtemp(prefix="cybershield-investigation-eval-"))
(_scratch / "vector_db").mkdir()
os.environ["VECTOR_DB_DIR"] = str(_scratch / "vector_db")
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
def deny(*args, **kwargs):
    raise AssertionError("Evaluation network access forbidden")
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.getaddrinfo = deny
from app.agents.investigation import CVEInvestigator
from evaluation.investigation.scenarios import Scenario

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    options = parser.parse_args()
    cases = json.loads(Path(__file__).with_name("cases.json").read_text())
    results = []
    for case in cases:
        source = Scenario(case["scenario"])
        report = CVEInvestigator(source).run(case["cve"], 7)
        grounding = report["grounding"]
        evidence = {e["citation_id"]: e for e in grounding["evidence"]} if grounding else {}
        links = [(claim["text"], cid) for claim in grounding["claims"]
                 for cid in claim["citation_ids"]] if grounding else []
        exact = sum(cid in evidence and text == evidence[cid]["excerpt"] for text, cid in links)
        counts = Counter(name for name, cve in source.calls if cve == case["cve"])
        correct_tools = (set(counts) == {"nvd", "cisa-kev"}
                         and all(1 <= count <= 2 for count in counts.values())
                         and sum(counts.values()) == len(source.calls))
        covered_sources = {e["source_id"] for e in evidence.values()}
        required_sources = set(case["expected_sources"])
        results.append({"scenario": case["scenario"], "cve": case["cve"],
            "expected": case["expected"], "actual": report["status"],
            "success": report["status"] == case["expected"],
            "correct_tool_calls": correct_tools, "tool_calls": len(source.calls),
            "citation_links": len(links), "exact_citation_links": exact,
            "expected_sources": sorted(required_sources), "covered_sources": sorted(covered_sources),
            "covered_expected_sources": len(covered_sources & required_sources),
            "expected_source_count": len(required_sources), **report["metrics"]})
    links = sum(r["citation_links"] for r in results)
    exact = sum(r["exact_citation_links"] for r in results)
    expected_count = sum(r["expected_source_count"] for r in results)
    covered_count = sum(r["covered_expected_sources"] for r in results)
    latency = sorted(r["latency_ms"] for r in results)
    summary = {"dataset": "20 original synthetic investigation scenarios; CC0-1.0",
        "models": [], "langgraph": importlib.metadata.version("langgraph"),
        "seed": "none; deterministic fixtures, no random retrieval",
        "cases": len(results), "successful": sum(r["success"] for r in results),
        "correct_tool_cases": sum(r["correct_tool_calls"] for r in results),
        "citation_links": links, "exact_citation_links": exact,
        "citation_validity": exact / links if links else None,
        "covered_expected_sources": covered_count, "expected_source_count": expected_count,
        "source_evidence_coverage": covered_count / expected_count if expected_count else None,
        "latency_median_ms": statistics.median(latency),
        "latency_p95_ms": latency[int((len(latency) - 1) * .95)],
        "latency_total_ms": sum(latency), "llm_calls": 0, "input_tokens": 0,
        "output_tokens": 0, "estimated_model_cost_usd": 0.0,
        "limitations": ["Synthetic expected outcomes and source coverage do not measure semantic security correctness.",
            "No live-network latency or model performance measured.",
            "Quotation attribution does not establish factual truth or complete asset assessment.",
            "No held-out tuning; this is a deterministic workflow regression set."],
        "results": results}
    Path(options.output).write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    if not all(r["success"] and r["correct_tool_calls"] for r in results) or exact != links:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
