"""Selection improvements must not weaken source/claim verification."""
import json,os,subprocess,sys
from pathlib import Path
import pytest

from app.knowledge.evidence_selection import SelectionPolicy
from app.knowledge.claim_verifier import quotation_answer,verify_draft
from app.knowledge.grounded_evaluation import corpus_catalog,documents_for,all_quotes_stub
from app.knowledge.evaluation import RETRIEVED_AT

pytestmark=pytest.mark.configuration_only


def test_exact_identifiers_do_not_need_two_extra_query_words():
    c=corpus_catalog()
    # Development source plus a new unseen identifier, not a held-out technique fixture.
    c.ingest_private(record_id="NEW",title="Technique notes",owner_id=101,retrieved_at=RETRIEVED_AT,
        text="T1888.777 describes a fictional controlled interpreter behavior.")
    docs=documents_for(c,[("NEW","Private content")],101)
    r=quotation_answer("What does T1888.777 describe?",docs,c,101,generator=all_quotes_stub,selection_policy=SelectionPolicy())
    assert not r.abstained
    assert r.claims[0].text==docs[0].page_content


def test_generic_inflections_hash_notation_and_named_scope():
    c=corpus_catalog()
    c.ingest_private(record_id="NEW",title="Aurora derivation",owner_id=101,retrieved_at=RETRIEVED_AT,
        text="The Aurora specification derives subkeys with HKDF using SHA-512.")
    docs=documents_for(c,[("NEW","Private content")],101)
    r=quotation_answer("Which derivation hash does the Aurora specification require?",docs,c,101,
                      generator=all_quotes_stub,selection_policy=SelectionPolicy(0.0))
    assert not r.abstained and r.claims[0].text==docs[0].page_content


@pytest.mark.parametrize("policy",[SelectionPolicy(),SelectionPolicy(0.0)])
def test_looser_selection_cannot_drop_qualifiers_or_accept_partial_claims(policy):
    c=corpus_catalog();docs=documents_for(c,[("D-SQL-ID","Names")])
    from app.knowledge.evidence import collect_evidence
    e=collect_evidence(c,docs,202)[0]
    raw=json.dumps({"claims":[{"text":e.excerpt.replace("cannot","can"),"citation_ids":[e.citation_id]}]})
    assert verify_draft("SQL identifiers protected",docs,c,202,raw,selection_policy=policy).abstained


@pytest.mark.parametrize("policy",[SelectionPolicy(),SelectionPolicy(0.0)])
def test_new_selection_preserves_foreign_stale_and_conflicting_refusals(policy):
    c=corpus_catalog()
    foreign=documents_for(c,[("D-PRIVATE","Private content")],101)
    assert quotation_answer("Saffron HSM recovery",foreign,c,202,generator=all_quotes_stub,selection_policy=policy).abstained
    conflict=documents_for(c,[("D-LOG-A","Retention"),("D-LOG-B","Retention")])
    assert quotation_answer("Cedar application audit log retention",conflict,c,202,generator=all_quotes_stub,
                            selection_policy=policy).status=="conflicting_evidence"
    old=c.snapshot(__import__("datetime").datetime(2025,1,1,tzinfo=__import__("datetime").timezone.utc))
    stale=documents_for(old,[("D-ROTATE","Interval")])
    assert quotation_answer("Cedar key rotation interval",stale,c,202,generator=all_quotes_stub,selection_policy=policy).abstained


def test_selection_rejects_heldout_tuning_inputs():
    from app.knowledge.answer_improvement_evaluation import select_on_development
    with pytest.raises(ValueError):
        select_on_development([{"id":"x","split":"heldout"}],{}, {}, {})


def test_improvement_evaluation_is_offline_and_does_not_hide_unjudged_quotes():
    backend=Path(__file__).resolve().parents[1]
    env=os.environ.copy();env.update(PYTHONPATH=str(backend),PYTHONDONTWRITEBYTECODE="1")
    r=json.loads(subprocess.check_output([sys.executable,"-B","-m","app.knowledge.answer_improvement_evaluation"],
                                        cwd=backend,env=env,text=True,timeout=90))
    assert r["isolation"]=={"network_attempts_blocked":0,"forbidden_file_operations_blocked":0}
    for mode in r["modes"].values():
        for split in ("dev","heldout"):
            assert mode[split]["citation_validity"]==1
            assert mode[split]["totals"]["unsupported_excerpts"]==0
            assert "unjudged_claims" in mode[split]["totals"]
            assert mode[split]["semantic_entailment_accuracy"] is None
