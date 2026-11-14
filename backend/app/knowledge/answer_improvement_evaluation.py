"""Development-only selection, then locked held-out quotation diagnostics."""
from dataclasses import asdict
import json

from .quality_dataset import corpus_catalog,load_judgments,retrieval_request,validate_dataset
from .grounded_evaluation import load_review,_score
from .evidence_selection import SelectionPolicy


def select_on_development(questions,judgments,decisions,retrievals):
    ids={q["id"] for q in questions}
    if not questions or any(q["split"]!="dev" for q in questions) or set(judgments)!=ids or set(retrievals)!=ids:
        raise ValueError("Selection accepts development questions and labels only.")
    rows=[]
    for fraction in (0.25,0.0):
        policy=SelectionPolicy(fraction)
        report=_score("improved",questions,judgments,decisions,retrievals,policy)
        t=report["totals"]
        eligible=(t["correct_abstentions"]==t["expected_abstentions"] and
                  not t["unsupported_excerpts"] and not t["incorrect_attributions"])
        rows.append({"policy":asdict(policy),"eligible":eligible,"dev":report})
    eligible=[row for row in rows if row["eligible"]]
    if not eligible:
        raise ValueError("No development policy preserved the safety gate.")
    # Penalize returning unjudged quotes; prefer the stricter initial candidate on ties.
    winner=max(eligible,key=lambda row:(
        row["dev"]["totals"]["answerable_required_covered"]-row["dev"]["totals"]["unjudged_claims"],
        -row["dev"]["totals"]["false_abstentions"]))
    return SelectionPolicy(**winner["policy"]),rows


def _evaluate(local_models,scratch):
    from unittest.mock import patch
    from app.rag.embeddings import EmbeddingService
    from .quality_evaluation import Engine
    catalog=corpus_catalog()
    questions,_=load_judgments()
    review,_=load_review()
    judgments=review["judgments"]
    decisions={r["question_id"]:r for r in review["review"]}
    stats=validate_dataset(catalog,questions,judgments)
    engine=Engine(catalog)
    retrievals={}
    with patch.object(EmbeddingService,"embed_documents",classmethod(lambda cls,texts:engine.embed(texts))), \
         patch.object(EmbeddingService,"embed_query",classmethod(lambda cls,text:engine.embed([text]))), \
         patch.object(EmbeddingService,"backend_name",classmethod(lambda cls:"hash")):
        dev=[q for q in questions if q["split"]=="dev"]
        for q in dev:
            view,docs,evidence,_=engine.rank(retrieval_request(q),"hybrid",rrf=60,mmr=1.0)
            retrievals[q["id"]]=view,docs,evidence
        policy,rows=select_on_development(dev,{q["id"]:judgments[q["id"]] for q in dev},
            {q["id"]:decisions[q["id"]] for q in dev},dict(retrievals))
        # Policy is locked before any held-out retrieval/scoring is performed.
        for q in questions:
            if q["split"]=="heldout":
                view,docs,evidence,_=engine.rank(retrieval_request(q),"hybrid",rrf=60,mmr=1.0)
                retrievals[q["id"]]=view,docs,evidence
    modes={}
    for name,selected in (("baseline",None),("improved",policy)):
        modes[name]={split:_score("improved",[q for q in questions if q["split"]==split],
            judgments,decisions,retrievals,selected) for split in ("dev","heldout")}
    return {"dataset":stats,"selected_policy":asdict(policy),"development_candidates":rows,
            "protocol":{"retrieval":"unchanged fixed hash hybrid RRF60/lambda1",
                        "policy_selection":"development safety gate then covered-required minus unjudged",
                        "generator":"same source-only all-quotes stub",
                        "quotes":"complete canonical sections; no paraphrasing",
                        "heldout_use":"scoring only after policy lock; reused diagnostic set"},
            "modes":modes,"costs":{"provider_calls":0,"model_downloads":0}}


def run_worker():
    from . import quality_evaluation
    previous=quality_evaluation._evaluate
    try:
        quality_evaluation._evaluate=_evaluate
        return quality_evaluation.run_worker(local_models=False)
    finally:
        quality_evaluation._evaluate=previous


if __name__=="__main__":
    print(json.dumps(run_worker(),indent=2,sort_keys=True))
