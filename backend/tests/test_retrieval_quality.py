"""Synthetic passage judgments, temporal views, citations and split guards."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest
from app.knowledge.evaluation import RETRIEVED_AT
from app.knowledge.evidence import collect_evidence, grounded_answer
from app.knowledge.ingestion import timestamp
from app.knowledge.models import GroundedAnswer, SupportedClaim
from app.knowledge.quality_dataset import (corpus_catalog, load_judgments, query_view,
    source_aware_order, validate_dataset)
from app.knowledge.quality_evaluation import select_configuration
from app.knowledge.quality_metrics import audit_answer, judgment_key, passage_key, passage_metrics

pytestmark = pytest.mark.configuration_only


@pytest.fixture
def dataset():
    catalog=corpus_catalog()
    questions,judgments=load_judgments()
    return catalog,questions,judgments


def selected(catalog,record_id,actor=202):
    return tuple(d for d in catalog.documents(actor)
                 if catalog.resolve(d.metadata["chunk_id"],actor)[0].record_id==record_id)


def test_separate_pinned_labels_are_valid_for_every_visible_snapshot(dataset):
    catalog,questions,judgments=dataset
    stats=validate_dataset(catalog,questions,judgments)
    assert stats["questions"]==48 and stats["dev"]==stats["heldout"]==24
    assert stats["labels"]==56 and stats["multi_passage_questions"]==16
    assert stats["families"]==24 and stats["expected_abstentions"]==15


def test_corpus_admission_never_loads_questions_or_judgments(monkeypatch):
    from app.knowledge import quality_dataset
    monkeypatch.setattr(quality_dataset,"load_judgments",lambda:pytest.fail("Labels leaked into corpus admission"))
    catalog=quality_dataset.corpus_catalog()
    documents=catalog.documents(101)
    assert documents
    assert all(not ({"gold","question","expected_abstain","split","grade"} & doc.metadata.keys()) for doc in documents)


def test_full_query_strings_are_absent_from_corpus(dataset):
    catalog,questions,_=dataset
    text="\n".join(doc.page_content for doc in catalog.documents(101)+catalog.documents(203)).casefold()
    assert all(q["question"].casefold() not in text for q in questions)


@pytest.mark.parametrize("change",["family","duplicate-query","unknown-split"])
def test_split_leakage_is_rejected(dataset,change):
    catalog,questions,judgments=dataset
    questions=deepcopy(questions)
    if change=="family":
        questions[-1]["family"]=questions[0]["family"]
    elif change=="duplicate-query":
        questions[-1]["question"]=questions[0]["question"]
    else:
        questions[-1]["split"]="train-on-test"
    with pytest.raises(ValueError):
        validate_dataset(catalog,questions,judgments)


@pytest.mark.parametrize("change",["quote","foreign","duplicate","grade"])
def test_invalid_or_foreign_passage_labels_fail_closed(dataset,change):
    catalog,questions,judgments=dataset
    judgments=deepcopy(judgments)
    label=judgments["D01-1"]["relevant"][0]
    if change=="quote":
        label["quote"]="An unsupported label quote."
    elif change=="foreign":
        label.update(record_id="H-PRIVATE",section="Private content")
    elif change=="duplicate":
        judgments["D01-1"]["relevant"].append(dict(label))
    else:
        label["grade"]=5
    with pytest.raises(ValueError):
        validate_dataset(catalog,questions,judgments)


@pytest.mark.parametrize("cutoff",[None,"2025-01-01",datetime(2025,1,1)])
def test_historical_views_require_explicit_aware_cutoff(dataset,cutoff):
    with pytest.raises(ValueError):
        dataset[0].snapshot(cutoff)


def test_explicit_history_preserves_old_evidence_and_does_not_mutate_current(dataset):
    catalog,questions,_=dataset
    prior=tuple(catalog.current_records())
    view=catalog.snapshot(timestamp("2025-01-01T00:00:00Z"))
    old=selected(view,"D-ROTATE")
    new=selected(catalog,"D-ROTATE")
    assert "twelve-month" in old[0].page_content and "six-month" in new[0].page_content
    assert old[0].metadata["source_version"]!=new[0].metadata["source_version"]
    assert catalog.resolve(old[0].metadata["chunk_id"],202) is None
    assert view.resolve(new[0].metadata["chunk_id"],202) is None
    evidence=collect_evidence(view,old,202)[0]
    assert evidence.modified_at.year==2024 and evidence.retrieved_at==RETRIEVED_AT
    assert tuple(catalog.current_records())==prior


def test_source_time_view_does_not_infer_history_from_recent_nvd_snapshot(dataset):
    catalog=dataset[0]
    # Published in 2021, but only its reviewed 2026 revision is available.
    assert selected(catalog,"CVE-2021-44228")
    assert not selected(catalog.snapshot(timestamp("2025-01-01T00:00:00Z")),"CVE-2021-44228")


@pytest.mark.parametrize("actor",[None,True,101.0,"101",202,-1])
def test_historical_view_keeps_private_owner_validation(dataset,actor):
    view=dataset[0].snapshot(timestamp("2027-01-01T00:00:00Z"))
    assert not selected(view,"D-PRIVATE",actor)


def test_historical_snapshot_rejects_new_admission(dataset):
    view=dataset[0].snapshot(timestamp("2027-01-01T00:00:00Z"))
    with pytest.raises(ValueError,match="read-only"):
        view.ingest_private(record_id="x",title="x",text="Synthetic content.",owner_id=101,retrieved_at=RETRIEVED_AT)


@pytest.mark.parametrize("identifier",["D-RETRACT","D-DELETED"])
def test_withdrawn_or_deleted_current_records_never_resolve(dataset,identifier):
    catalog=dataset[0]
    assert not selected(catalog,identifier)
    historical=catalog.snapshot(timestamp("2025-01-01T00:00:00Z"))
    assert selected(historical,identifier)  # explicitly historical, before removal


def test_source_aware_identifier_ranking_uses_canonical_record_ids(dataset):
    catalog=dataset[0]
    wrong=selected(catalog,"D-CVE-B")
    right=selected(catalog,"D-CVE-A")
    result=source_aware_order("CVE-2099-51001 severity",wrong+right,catalog,202)
    assert result[:len(right)]==right
    before=collect_evidence(catalog,right,202)
    after=collect_evidence(catalog,result,202)
    assert tuple(e for e in after if e.record_id=="D-CVE-A")==before


def test_source_aware_stage_does_not_sort_unrelated_sources_by_recency_or_trust(dataset):
    catalog=dataset[0]
    older=selected(catalog,"D-LOG-A")
    newer=selected(catalog,"D-LOG-B")
    authoritative=selected(catalog,"CVE-2021-44228")
    docs=older+newer+authoritative
    assert source_aware_order("audit retention",docs,catalog,202)==docs


@pytest.mark.parametrize("tamper",["foreign","owner","scope","version"])
def test_source_aware_stage_rechecks_cross_user_and_forged_metadata(dataset,tamper):
    catalog=dataset[0]
    private=selected(catalog,"D-PRIVATE",101)[0].model_copy(deep=True)
    if tamper=="owner":
        private.metadata["user_id"]=202
    elif tamper=="scope":
        private.metadata["scope"]="knowledge_base"
    elif tamper=="version":
        private.metadata["source_version"]="fake"
    with pytest.raises(ValueError):
        source_aware_order("Project Saffron", [private],catalog,202)


def test_graded_passage_metrics_multiple_required_and_supporting_evidence():
    labels=[dict(record_id="A",section="x",grade=2),dict(record_id="B",section="x",grade=1)]
    rank=[("fixture-reference","B","x"),("fixture-reference","A","x")]
    metrics=passage_metrics(rank,labels)
    assert metrics["recall_at_5"]==1 and metrics["precision_at_5"]==0.4
    assert metrics["mrr"]==1 and 0<metrics["ndcg_at_5"]<1
    assert metrics["all_required_at_5"]==1


def test_duplicate_passages_do_not_earn_multiple_credits():
    labels=[dict(record_id="A",section="x",grade=2)]
    key=("fixture-reference","A","x")
    metrics=passage_metrics([key]*5,labels)
    assert metrics["recall_at_5"]==1 and metrics["precision_at_5"]==0.2


def test_incomplete_multihop_evidence_is_visible_in_metrics():
    labels=[dict(record_id="A",section="x",grade=2),dict(record_id="B",section="x",grade=2)]
    metrics=passage_metrics([("fixture-reference","A","x")],labels)
    assert metrics["recall_at_5"]==0.5 and metrics["all_required_at_5"]==0


def test_selection_rejects_heldout_queries_and_labels(dataset):
    _,questions,judgments=dataset
    forbidden=lambda *a,**k:pytest.fail("Held-out data must not reach tuning")
    with pytest.raises(ValueError):
        select_configuration(questions,judgments,forbidden)
    dev=[q for q in questions if q["split"]=="dev"]
    with pytest.raises(ValueError):
        select_configuration(dev,judgments,forbidden)


def test_tuning_visits_only_development_queries_with_fixed_grid(dataset):
    catalog,questions,judgments=dataset
    dev=[q for q in questions if q["split"]=="dev"]
    labels={q["id"]:judgments[q["id"]] for q in dev}
    visited=[]
    allowed_queries={q["question"] for q in dev}
    def rank(question,*args,**kwargs):
        assert set(question)=={"question","user_id","source_as_of"}
        assert question["question"] in allowed_queries
        visited.append(("dev",kwargs["rrf"],kwargs["mmr"]))
        return None,(),(),0
    result=select_configuration(dev,labels,rank)
    assert len(visited)==24*9
    assert {item[0] for item in visited}=={"dev"}
    assert {item[1] for item in visited}=={10,60,100}
    assert result["hybrid_mmr"]["rrf"]==60 and result["hybrid_mmr"]["mmr"]==0.85
    assert result["hybrid"]["mmr"]==1


def test_audit_distinguishes_fabrication_unsupported_text_and_unjudged_quotes(dataset):
    catalog,_,judgments=dataset
    evidence=collect_evidence(catalog,selected(catalog,"D-CVE-A"),202)
    item=evidence[0]
    labels=judgments["D01-1"]["relevant"]
    claims=(
        SupportedClaim(claim_id="1",text=item.excerpt,citation_ids=("E-fabricated",)),
        SupportedClaim(claim_id="2",text="CVE-2099-51001 is definitely harmless.",citation_ids=(item.citation_id,)),
        SupportedClaim(claim_id="3",text="A short excerpt",citation_ids=(item.citation_id,)),
    )
    audit=audit_answer(evidence,GroundedAnswer(answer="synthetic",claims=claims,abstained=False),labels)
    assert audit["citation_references"]==3 and audit["valid_references"]==2
    assert audit["unsupported_excerpts"]==3


def test_exact_quote_from_wrong_source_is_incorrect_attribution(dataset):
    catalog,_,judgments=dataset
    labels=judgments["D01-1"]["relevant"]
    quote=labels[0]["quote"]
    catalog.ingest_private(record_id="COPY",title="Private copy",text=quote,owner_id=202,retrieved_at=RETRIEVED_AT)
    evidence=collect_evidence(catalog,selected(catalog,"COPY",202),202)
    answer=GroundedAnswer(answer=quote,abstained=False,claims=(
        SupportedClaim(claim_id="1",text=quote,citation_ids=(evidence[0].citation_id,)),))
    audit=audit_answer(evidence,answer,labels)
    assert audit["valid_references"]==1 and audit["unsupported_excerpts"]==0
    assert audit["incorrect_attributions"]==1 and audit["covered_passages"]==0


def test_unannotated_excerpt_is_not_falsely_called_a_semantic_error(dataset):
    catalog,_,judgments=dataset
    evidence=collect_evidence(catalog,selected(catalog,"D-SQL"),202)
    answer=GroundedAnswer(answer=evidence[0].excerpt,abstained=False,claims=(
        SupportedClaim(claim_id="1",text=evidence[0].excerpt,citation_ids=(evidence[0].citation_id,)),))
    audit=audit_answer(evidence,answer,judgments["D01-1"]["relevant"])
    assert audit["unjudged_claims"]==1 and audit["unsupported_excerpts"]==0


@pytest.mark.parametrize("record,question",[("D-INJECT","CVE-2099-53333 remediation"),("H-INJECT","CVE-2099-64444 remediation")])
def test_malicious_sources_are_evidence_not_tool_authorization(dataset,record,question):
    catalog=dataset[0]
    answer=grounded_answer(question,selected(catalog,record),catalog,202,
                           generator=lambda _:pytest.fail("Malicious instruction reached generation"))
    assert answer.abstained and answer.reason=="instruction_like_content"


def test_conflicting_sources_preserved_without_guessing_a_winner(dataset):
    catalog=dataset[0]
    docs=selected(catalog,"D-LOG-A")+selected(catalog,"D-LOG-B")
    assert len(collect_evidence(catalog,docs,202))==2
    answer=grounded_answer("conflicting Cedar audit retention",docs,catalog,202,
                           generator=lambda _:pytest.fail("Do not guess between conflicting evidence"))
    assert answer.abstained


@pytest.mark.parametrize("filename",["queries.json","qrels.json"])
def test_question_and_judgment_hash_tampering_is_rejected(tmp_path,monkeypatch,filename):
    from hashlib import sha256
    from app.knowledge import quality_dataset
    manifest={}
    for name in ("queries.json","qrels.json"):
        data=b"{}"
        (tmp_path/name).write_bytes(data)
        manifest[name]=sha256(data).hexdigest()
    (tmp_path/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    (tmp_path/filename).write_text('{"tampered":true}',encoding="utf-8")
    monkeypatch.setattr(quality_dataset,"QUALITY_ROOT",tmp_path)
    with pytest.raises(ValueError,match="after approval"):
        quality_dataset.load_judgments()


def test_local_model_discovery_requires_complete_safetensors_snapshot(tmp_path,monkeypatch):
    from app.knowledge.quality_evaluation import local_snapshot,SEMANTIC_MODEL
    monkeypatch.setattr("pathlib.Path.home",lambda:tmp_path)
    folder=tmp_path/".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/reviewed"
    folder.mkdir(parents=True)
    for name in ("config.json","tokenizer.json"):
        (folder/name).write_text("{}",encoding="utf-8")
    assert local_snapshot(SEMANTIC_MODEL) is None
    (folder/"model.safetensors").write_bytes(b"synthetic-placeholder-not-loaded")
    assert local_snapshot(SEMANTIC_MODEL)==folder


def test_retrieval_requests_are_independent_of_gold_and_abstention_labels(dataset):
    from app.knowledge.quality_dataset import retrieval_request
    question=dataset[1][0]
    changed={**question,"expected_abstain":not question["expected_abstain"],
             "gold":["fabricated"],"split":"heldout","family":"fake","id":"fake"}
    assert retrieval_request(changed)==retrieval_request(question)
    assert set(retrieval_request(question))=={"question","user_id","source_as_of"}
