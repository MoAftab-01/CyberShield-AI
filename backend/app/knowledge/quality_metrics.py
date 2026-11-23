"""Passage judgments and answer audits; labels never enter retrieval."""
import math


def passage_key(item):
    return (item.source_id, item.record_id, item.section)


def judgment_key(item):
    source = item.get("source_id", "private-upload" if item["record_id"] in {"D-PRIVATE", "H-PRIVATE"} else "fixture-reference")
    return source, item["record_id"], item["section"]


def passage_metrics(ranked, judgments, k=5):
    grades = {judgment_key(item): item["grade"] for item in judgments}
    if not grades:
        raise ValueError("Empty relevance sets are evaluated as abstention cases.")
    selected = list(dict.fromkeys(ranked[:k]))
    hits = [int(grades.get(key, 0) > 0) for key in selected]
    ideal = sorted(grades.values(), reverse=True)[:k]
    required = {key for key, grade in grades.items() if grade == 2}
    return {
        "recall_at_5": sum(hits)/len(grades),
        "precision_at_5": sum(hits)/k,
        "mrr": next((1/(i+1) for i, hit in enumerate(hits) if hit), 0.0),
        "ndcg_at_5": sum((2**grades.get(key, 0)-1)/math.log2(i+2) for i,key in enumerate(selected)) /
            sum((2**grade-1)/math.log2(i+2) for i,grade in enumerate(ideal)),
        "all_required_at_5": float(required.issubset(selected)),
    }


def audit_answer(evidence, answer, judgments):
    """Closed-world quote/attribution audit, never a semantic LLM judge.

    An unannotated exact excerpt is 'unjudged', not proof of a false claim.
    Invalid references and nonmatching excerpts are objectively unsupported.
    """
    known = {item.citation_id: item for item in evidence}
    valid = total_refs = unsupported = incorrect = unjudged = 0
    covered = set()
    for claim in answer.claims:
        cited = [known.get(cid) for cid in claim.citation_ids]
        total_refs += len(cited)
        valid += sum(item is not None for item in cited)
        if not cited or any(item is None or claim.text not in item.excerpt for item in cited):
            unsupported += 1
            continue
        matches = {judgment_key(item) for item in judgments if item["quote"] == claim.text}
        if not matches:
            unjudged += 1
        elif any(passage_key(item) not in matches for item in cited):
            incorrect += 1
        else:
            covered.update(passage_key(item) for item in cited)
    return {
        "citation_references": total_refs, "valid_references": valid,
        "claims": len(answer.claims), "unsupported_excerpts": unsupported,
        "incorrect_attributions": incorrect, "unjudged_claims": unjudged,
        "covered_passages": len(covered), "relevant_passages": len(judgments),
    }
