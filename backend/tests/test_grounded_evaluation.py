"""Review provenance and offline reproducibility; labels never drive drafts."""
from copy import deepcopy
import json,os,subprocess,sys
from pathlib import Path
import pytest
from app.knowledge.grounded_evaluation import load_review,all_quotes_stub

pytestmark=pytest.mark.configuration_only


def test_review_preserves_base_and_flags_known_ambiguities():
    review,_=load_review()
    assert len(review["review"])==48 and not review["tuning_performed"]
    dispositions={x["question_id"]:x for x in review["review"]}
    assert not dispositions["H08-2"]["completion_scored"]
    assert not dispositions["H04-2"]["completion_scored"]
    assert dispositions["H09-1"]["disposition"]=="clarification_required"
    assert len(review["judgments"]["D04-1"]["relevant"])==3


def test_stub_uses_only_passed_source_text_and_citation_ids():
    payload={"question":"ignored","evidence":[{"excerpt":"A complete source paragraph.","citation_id":"E-test"}]}
    assert json.loads(all_quotes_stub("instructions\n"+json.dumps(payload)))=={
        "claims":[{"text":"A complete source paragraph.","citation_ids":["E-test"]}]}


def run():
    backend=Path(__file__).resolve().parents[1]
    env=os.environ.copy()
    env.update(PYTHONPATH=str(backend),PYTHONDONTWRITEBYTECODE="1")
    return json.loads(subprocess.check_output([sys.executable,"-B","-m","app.knowledge.grounded_evaluation"],
                    env=env,cwd=backend,text=True,timeout=90))


def test_grounded_evaluation_reproducible_and_honest_about_failures():
    first,second=run(),run()
    first.pop("costs");second.pop("costs")
    assert first==second
    assert first["isolation"]==dict(network_attempts_blocked=0,forbidden_file_operations_blocked=0)
    assert first["controlled_verifier"]["quote_support_precision"]==1
    assert first["reviewed_labels"]==65
    for split in ("dev","heldout"):
        mode=first["modes"]["verified_quotes"][split]
        assert mode["citation_validity"]==1
        assert mode["totals"]["unsupported_excerpts"]==0
        assert mode["totals"]["correct_abstentions"]==mode["totals"]["expected_abstentions"]
        assert mode["semantic_entailment_accuracy"] is None
        for case in mode["cases"]:
            if case["id"] in {"D10-1","D10-2","H10-2"}:
                assert case["abstained"]


def test_only_flagged_adapter_imports_verifier_and_serving_never_imports_evaluations():
    # Phase 2C explicitly permits one disabled-by-default adapter. The old
    # Phase 2B blanket ban is replaced, not bypassed or skipped.
    import ast
    from app.core.config import Settings
    backend=Path(__file__).resolve().parents[1]
    allowed={"services/grounded_chat_service.py": {"VerifiedAnswer", "quotation_answer", "instruction_like"},
             "schemas/copilot_schema.py": {"VerifiedAnswer"}}
    forbidden={"evaluation", "grounded_evaluation", "quality_evaluation", "answer_improvement_evaluation",
               "quality_dataset", "quality_metrics"}
    found=set()
    for directory in ("api", "agents", "services", "schemas"):
        for file in (backend/"app"/directory).rglob("*.py"):
            relative=file.relative_to(backend/"app").as_posix()
            for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom) and node.module:
                    modules=[node.module, *(node.module+"."+x.name for x in node.names)]
                    if node.module=="app.knowledge.claim_verifier":
                        assert relative in allowed
                        assert {x.name for x in node.names}==allowed[relative]
                        found.add(relative)
                elif isinstance(node, ast.Import):
                    modules=[x.name for x in node.names]
                else:
                    continue
                assert not any(m=="app.knowledge."+bad or m.startswith("app.knowledge."+bad+".")
                               for m in modules for bad in forbidden)
    assert found==set(allowed)
    assert Settings.model_fields["CYBERGPT_V2_ENABLED"].default is False
