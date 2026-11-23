"""Fresh subprocess benchmark regressions; models are not loaded in unit tests."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from app.knowledge.quality_evaluation import run_worker

pytestmark=pytest.mark.configuration_only


def deterministic_report(value):
    if isinstance(value,dict):
        return {key:deterministic_report(item) for key,item in value.items()
                if key not in {"timing","costs","load_seconds","import_and_load_seconds"}}
    if isinstance(value,list):
        return [deterministic_report(item) for item in value]
    return value


def worker():
    root=Path(__file__).resolve().parents[1]
    env=os.environ.copy()
    env.update(PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE="1")
    completed=subprocess.run([sys.executable,"-B","-m","app.knowledge.quality_evaluation"],
        cwd=root,env=env,capture_output=True,text=True,timeout=120,check=True)
    return json.loads(completed.stdout)


def test_quality_benchmark_hash_reproducibility_and_security():
    first,second=worker(),worker()
    assert deterministic_report(first)==deterministic_report(second)
    assert first["isolation"]==dict(network_attempts_blocked=0,forbidden_file_operations_blocked=0)
    assert first["seed"]==1729 and first["dataset"]["questions"]==48
    dev=set(first["tuning"]["hash"]["dev_query_ids"])
    assert len(dev)==24 and all(identifier.startswith("D") for identifier in dev)
    for mode in first["modes"].values():
        for split in ("dev","heldout"):
            for case in mode[split]["cases"]:
                if case["id"] in {"D10-1","D10-2","H10-2"}:
                    assert not any(item[0]=="private-upload" for item in case["ranked"])
                    assert case["abstained"]
                if not case["id"].startswith(("D06-", "H07-")):
                    assert not any(item[1] in {"D-RETRACT","D-DELETED"} for item in case["ranked"])
            assert mode[split]["evidence"]["citation_validity"] in {1,None}
            assert mode[split]["evidence"]["unsupported_excerpts"]==0
            assert mode[split]["evidence"]["semantic_unsupported_claim_rate"] is None
            assert all(0<=number<=1 for number in mode[split]["retrieval"].values())


def test_worker_cannot_reuse_application_store_state(monkeypatch):
    monkeypatch.setitem(sys.modules,"app.rag.embeddings",object())
    with pytest.raises(RuntimeError,match="dedicated"):
        run_worker()


def test_worker_denies_external_filesystem_mutations_and_network(tmp_path):
    root=Path(__file__).resolve().parents[1]
    env=os.environ.copy()
    env.update(PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE="1")
    source = """
from pathlib import Path
import json,os,socket,sys,tempfile
import app.knowledge.quality_evaluation as worker
folder=Path(sys.argv[1])
protected=folder/'synthetic-protected.txt'
protected.write_text('synthetic original',encoding='utf-8')
def evaluate(*args):
    operations=[
        lambda:protected.write_text('changed',encoding='utf-8'),
        lambda:(folder/'forbidden').mkdir(),
        lambda:protected.unlink(),
        lambda:protected.rename(folder/'moved'),
        lambda:socket.create_connection(('127.0.0.1',9),timeout=0.1),
    ]
    rejected=0
    for operation in operations:
        try: operation()
        except RuntimeError: rejected+=1
        else: raise AssertionError('Guard allowed an operation')
    assert protected.read_text(encoding='utf-8')=='synthetic original'
    return {'costs':{},'verified_rejections':rejected}
worker._evaluate=evaluate
report=worker.run_worker()
assert report['verified_rejections']==5
assert report['isolation']=={'network_attempts_blocked':1,'forbidden_file_operations_blocked':4}
print('guards verified')
"""
    result=subprocess.run([sys.executable,"-B","-c",source,str(tmp_path)],env=env,cwd=root,
                          capture_output=True,text=True,check=True,timeout=30)
    assert result.stdout.strip()=="guards verified"
    assert (tmp_path/"synthetic-protected.txt").read_text(encoding="utf-8")=="synthetic original"


@pytest.mark.parametrize("relative,blocked", [
    ("backend/app/rag/embeddings.py", False),
    ("backend/app/rag/__pycache__/embeddings.cpython-312.pyc", False),
    ("backend/evaluation/retrieval_quality/corpus.json", False),
    ("backend/evaluation/grounded_answers/review.json", False),
    ("backend/.env", True),
    ("backend/uploads/private.pdf", True),
    ("backend/vector_db/faiss.index", True),
    ("backend/vector_db/documents.pkl", True),
    ("backend/.model_cache/weights.onnx", True),
    ("backend/application.db", True),
])
def test_same_named_checkout_only_allows_source_and_reviewed_fixtures(tmp_path, relative, blocked):
    from app.knowledge.quality_evaluation import _protected_repository_read
    checkout = tmp_path / "CyberShield-AI"
    assert _protected_repository_read(checkout / relative, checkout, checkout) is blocked


def test_separate_original_still_denies_even_source_reads(tmp_path):
    from app.knowledge.quality_evaluation import _protected_repository_read
    original = tmp_path / "CyberShield-AI"
    feature = tmp_path / "CyberShield-AI-cybergpt-2-source-foundation"
    assert _protected_repository_read(original / "backend/app/rag/embeddings.py", feature, original)
    assert _protected_repository_read(original / "backend/evaluation/retrieval_quality/corpus.json", feature, original)
    assert not _protected_repository_read(feature / "backend/app/rag/embeddings.py", feature, original)
