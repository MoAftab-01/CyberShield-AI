"""Small offline benchmark with fresh-process, temporary-index isolation."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from app.knowledge.evaluation import ranking_metrics, run_worker

pytestmark = pytest.mark.configuration_only


def test_binary_ranking_metrics_and_duplicate_document_credit():
    actual=ranking_metrics(["wrong","right","right","other"],["right","missing"])
    assert actual["recall_at_5"]==0.5
    assert actual["precision_at_5"]==0.2
    assert actual["mrr"]==0.5
    assert 0<actual["ndcg_at_5"]<1


def test_empty_gold_scored_as_abstention_instead_of_fake_recall():
    with pytest.raises(ValueError):
        ranking_metrics([],[])


def test_worker_refuses_serving_process_with_imported_stores(monkeypatch):
    monkeypatch.setitem(sys.modules,"app.rag.faiss_store",object())
    with pytest.raises(RuntimeError,match="dedicated process"):
        run_worker()


def benchmark():
    backend=Path(__file__).resolve().parents[1]
    env=os.environ.copy()
    env["PYTHONPATH"]=str(backend)
    env["PYTHONDONTWRITEBYTECODE"]="1"
    completed=subprocess.run([sys.executable,"-B","-m","app.knowledge.evaluation"],env=env,
                             cwd=backend,capture_output=True,text=True,timeout=60,check=True)
    assert not completed.stderr
    return json.loads(completed.stdout)


def test_offline_benchmark_reproducibility_and_isolation():
    first,second=benchmark(),benchmark()
    assert first==second
    assert first["dataset"]==dict(questions=16,answerable=11,abstention=5,current_public_records=13,private_records=1)
    assert first["embedding"]["backend"]=="hash"
    assert set(first["modes"])=={"bm25","faiss_hash","hybrid","hybrid_mmr"}
    for mode in first["modes"].values():
        assert all(0<=value<=1 for value in mode["retrieval"].values())
        for case in mode["cases"]:
            if case["id"]=="private-other":
                assert "PRIVATE-ORCHID-71" not in case["ranked_record_ids"] and case["abstained"]
            if case["id"]=="private-owner":
                assert "PRIVATE-ORCHID-71" in case["ranked_record_ids"]
            assert "SYN-WITHDRAWN" not in case["ranked_record_ids"]
            assert "SYN-DELETED" not in case["ranked_record_ids"]
        assert mode["generation_contract"]["citation_validity"]==1.0
        assert mode["generation_contract"]["unsupported_excerpt_rate"]==0.0
        assert mode["generation_contract"]["semantic_unsupported_claim_rate"] is None
