"""Phase 2B offline quotation verifier evaluation; no retrieval tuning or live LLM."""
from collections import Counter
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path

from .quality_dataset import (QUALITY_ROOT, corpus_catalog, load_judgments,
                              query_view, retrieval_request, validate_dataset)
from .quality_metrics import audit_answer, judgment_key, passage_key
from .claim_verifier import quotation_answer
from .evidence import collect_evidence, grounded_answer
from .evaluation import RETRIEVED_AT, _extractive_stub

ROOT = QUALITY_ROOT.parent/"grounded_answers"


def load_review():
    manifest = json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
    data = {}
    for name in ("review.json","claim_cases.json"):
        raw = (ROOT/name).read_bytes()
        if sha256(raw).hexdigest()!=manifest[name]:
            raise ValueError("Unapproved Phase 2B evaluation artifact.")
        data[name] = json.loads(raw)
    review = data["review.json"]
    for name,key in (("queries.json","base_queries_sha256"),("qrels.json","base_qrels_sha256")):
        if sha256((QUALITY_ROOT/name).read_bytes()).hexdigest()!=review[key]:
            raise ValueError("Accepted Batch 2 benchmark changed.")
    if sha256((QUALITY_ROOT/"manifest.json").read_bytes()).hexdigest()!=manifest["base_manifest_sha256"]:
        raise ValueError("Accepted corpus approval changed.")
    return review,data["claim_cases.json"]["cases"]


def all_quotes_stub(prompt):
    """No question IDs, judgment labels, expected outcomes or corpus lookups."""
    payload = json.loads(prompt.split("\n",1)[1])
    return json.dumps({"claims":[{"text":e["excerpt"],"citation_ids":[e["citation_id"]]}
                                 for e in payload["evidence"][:5]]})


def documents_for(catalog, selectors, actor=202):
    # Used only by hand-authored controlled verifier scenarios.
    result = []
    for rid,section in selectors:
        result.extend(d for d in catalog.documents(actor)
            if catalog.resolve(d.metadata["chunk_id"],actor)[0].record_id==rid
            and catalog.resolve(d.metadata["chunk_id"],actor)[1].section==section)
    return tuple(result)


def evaluate_controlled(scenarios):
    cases = []
    for case in scenarios:
        catalog = corpus_catalog()
        if case.get("source_as_of"):
            from .ingestion import timestamp
            catalog = catalog.snapshot(timestamp(case["source_as_of"]))
        actor = case["actor"]
        # A foreign result is deliberately fed to the public boundary as an attack.
        source_actor = 101 if case["id"]=="foreign_private" else actor
        documents = documents_for(catalog,case["retrieved"],source_actor)
        canonical = collect_evidence(catalog,documents,source_actor)
        def generate(prompt):
            payload = json.loads(prompt.split("\n",1)[1])
            entries = payload["evidence"]
            claims = [{"text":e["excerpt"],"citation_ids":[e["citation_id"]]} for e in entries]
            mutation = case["mutation"]
            if mutation=="fabricated":
                claims[0]["citation_ids"]=["E-fabricated"]
            elif mutation=="substring":
                claims[0]["text"]="CVSS 8.8 HIGH severity."
            elif mutation=="number":
                claims[0]["text"]=claims[0]["text"].replace("8.8","0.1")
            elif mutation=="prefix":
                claims[0]["text"]="NVD proves: "+claims[0]["text"]
            elif mutation=="negation":
                claims[0]["text"]=claims[0]["text"].replace("do not","do")
            elif mutation=="duplicate_reference":
                claims[0]["citation_ids"]*=2
            elif mutation=="duplicate_claim":
                claims.append(dict(claims[0]))
            elif mutation=="url":
                claims[0]["url"]="https://fabricated.invalid/"
            elif mutation=="tool":
                return json.dumps({"tool_call":"read_secret"})
            elif mutation=="wrong_attribution":
                claims[0]["citation_ids"]=[canonical[-1].citation_id]
            elif mutation=="stale":
                catalog.ingest_private(record_id="D-PRIVATE",title="Saffron replacement",
                    text="New synthetic private content.",owner_id=101,retrieved_at=RETRIEVED_AT+timedelta(days=1))
            return json.dumps({"claims":claims})
        answer = quotation_answer(case["question"],documents,catalog,actor,generator=generate,
                                  retrieval_status=case.get("retrieval_status","ok"))
        accepted = not answer.abstained
        cases.append({"id":case["id"],"expected_accepted":case["expected_accepted"],"accepted":accepted,
                      "status":answer.status,"reason":answer.reason,
                      "verdict_reasons":[v.reason for v in answer.verdicts]})
    positive = sum(c["expected_accepted"] for c in cases)
    negative = len(cases)-positive
    tp = sum(c["accepted"] and c["expected_accepted"] for c in cases)
    fp = sum(c["accepted"] and not c["expected_accepted"] for c in cases)
    return {"cases":cases,"supported_cases":positive,"unsupported_or_unsafe_cases":negative,
            "true_accepts":tp,"false_accepts":fp,"false_rejects":positive-tp,
            "accuracy":sum(c["accepted"]==c["expected_accepted"] for c in cases)/len(cases),
            "quote_support_precision":tp/(tp+fp) if tp+fp else None,
            "false_accept_rate":fp/negative,"false_reject_rate":(positive-tp)/positive}


def _score(name,questions,judgments,decisions,retrievals,selection_policy=None):
    statuses = Counter()
    totals = Counter()
    cases = []
    for question in questions:
        key = question["id"]
        view,docs,evidence = retrievals[key]
        answer = (grounded_answer(question["question"],docs,view,question["user_id"],generator=_extractive_stub)
                  if name=="legacy_first" else
                  grounded_answer(question["question"],docs,view,question["user_id"],generator=all_quotes_stub)
                  if name=="legacy_same_generator" else
                  quotation_answer(question["question"],docs,view,question["user_id"],generator=all_quotes_stub,selection_policy=selection_policy))
        labels = judgments[key]["relevant"]
        audit = audit_answer(evidence,answer,labels)
        totals.update(audit)
        statuses[getattr(answer,"status","abstained" if answer.abstained else "returned_excerpts")] += 1
        expected = question["expected_abstain"]
        scored = decisions[key]["completion_scored"]
        totals["expected_abstentions"] += expected
        totals["correct_abstentions"] += expected and answer.abstained
        # Coverage of known required facts; never assert actual semantic completeness.
        required = {judgment_key(label) for label in labels if label["grade"]==2}
        cited = {passage_key(e) for e in answer.evidence}
        matched = {judgment_key(label) for label in labels
                   if any(claim.text==label["quote"] and any(cid==e.citation_id and
                       passage_key(e)==judgment_key(label) for cid in claim.citation_ids
                       for e in answer.evidence) for claim in answer.claims)}
        if scored and not expected:
            totals["answerable_scored"] += 1
            totals["false_abstentions"] += answer.abstained
            totals["required_evidence_complete"] += bool(required) and required.issubset(matched)
            totals["no_relevant_evidence_returned"] += not bool(matched)
            totals["answerable_required_passages"] += len(required)
            totals["answerable_required_covered"] += len(required & matched)
        cases.append({"id":key,"abstained":answer.abstained,"status":getattr(answer,"status",None),
                      "reason":answer.reason,"audit":audit,"required_passages":len(required),
                      "required_matched":len(required & matched),"completion_scored":scored})
    return {"totals":dict(totals),"statuses":dict(statuses),
        "citation_validity":totals["valid_references"]/totals["citation_references"] if totals["citation_references"] else None,
        "false_abstention_rate":totals["false_abstentions"]/totals["answerable_scored"],
        "required_evidence_coverage":totals["answerable_required_covered"]/totals["answerable_required_passages"],
        "semantic_entailment_accuracy":None,"cases":cases}


def _evaluate(local_models,scratch):
    from unittest.mock import patch
    from app.rag.embeddings import EmbeddingService
    from .quality_evaluation import Engine
    catalog = corpus_catalog()
    questions,_ = load_judgments()
    review,scenarios = load_review()
    judgments = review["judgments"]
    stats = validate_dataset(catalog,questions,judgments)
    decisions = {item["question_id"]:item for item in review["review"]}
    engine = Engine(catalog)
    retrievals = {}
    with patch.object(EmbeddingService,"embed_documents",classmethod(lambda cls,texts:engine.embed(texts))), \
         patch.object(EmbeddingService,"embed_query",classmethod(lambda cls,text:engine.embed([text]))), \
         patch.object(EmbeddingService,"backend_name",classmethod(lambda cls:"hash")):
        for question in questions:
            view,docs,evidence,_ = engine.rank(retrieval_request(question),"hybrid",rrf=60,mmr=1.0)
            retrievals[question["id"]] = view,docs,evidence
    return {
        "dataset":stats,"reviewed_labels":sum(len(j["relevant"]) for j in judgments.values()),
        "review_dispositions":dict(Counter(d["disposition"] for d in review["review"])),
        "protocol":{"retrieval":"fixed existing hash hybrid: RRF 60, MMR lambda 1; no tuning",
                    "generation":"deterministic source-only stubs, not an LLM-quality test",
                    "verification":"complete section quotation attribution; no general semantic entailment",
                    "review_manifest_sha256":sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
                    "completion":"oracle required-evidence coverage only; pipeline completeness remains unverified"},
        "controlled_verifier":evaluate_controlled(scenarios),
        "modes":{name:{split:_score(name,[q for q in questions if q["split"]==split],
                     judgments,decisions,retrievals) for split in ("dev","heldout")}
                 for name in ("legacy_first","legacy_same_generator","verified_quotes")},
        "costs":{"model_downloads":0,"provider_calls":0},
    }


def run_worker():
    from . import quality_evaluation
    previous = quality_evaluation._evaluate
    try:
        quality_evaluation._evaluate = _evaluate
        return quality_evaluation.run_worker(local_models=False)
    finally:
        quality_evaluation._evaluate = previous


if __name__=="__main__":
    print(json.dumps(run_worker(),indent=2,sort_keys=True))
