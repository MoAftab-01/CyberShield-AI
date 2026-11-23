"""Pinned synthetic corpus admission, separated from benchmark query labels."""
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from .evaluation import RETRIEVED_AT
from .ingestion import Catalog, timestamp
from .quality_metrics import judgment_key

QUALITY_ROOT = Path(__file__).resolve().parents[2]/"evaluation/retrieval_quality"
SEED = 1729


def corpus_catalog():
    """Only corpus artifacts and fixed synthetic private data enter the index."""
    manifest = json.loads((QUALITY_ROOT/"manifest.json").read_text(encoding="utf-8"))
    catalog = Catalog(QUALITY_ROOT/"manifest.json")
    for item in manifest["artifacts"]:
        catalog.ingest_artifact(item["artifact_id"], QUALITY_ROOT/item["filename"], retrieved_at=RETRIEVED_AT)
    for owner, identifier, title, text in (
        (101, "D-PRIVATE", "Saffron recovery runbook",
         "Project Saffron recovery requires two custodians to unlock the cold standby HSM."),
        (203, "H-PRIVATE", "Violet signing runbook",
         "Project Violet emergency signing recovery requires two offline recovery shares and an incident commander approval."),
    ):
        catalog.ingest_private(record_id=identifier, title=title, text=text, owner_id=owner, retrieved_at=RETRIEVED_AT)
    return catalog


def load_judgments():
    manifest = json.loads((QUALITY_ROOT/"manifest.json").read_text(encoding="utf-8"))
    decoded = {}
    for name in ("queries.json", "qrels.json"):
        raw = (QUALITY_ROOT/name).read_bytes()
        if sha256(raw).hexdigest() != manifest[name]:
            raise ValueError("Benchmark questions or judgments changed after approval.")
        decoded[name] = json.loads(raw)
    return decoded["queries.json"]["questions"], decoded["qrels.json"]["judgments"]


def retrieval_request(question):
    """Strip ALL evaluation annotations before crossing the retrieval boundary."""
    return {name:question[name] for name in ("question","user_id","source_as_of")}


def query_view(catalog, question):
    cutoff = question["source_as_of"]
    return catalog.snapshot(timestamp(cutoff)) if cutoff else catalog


def validate_dataset(catalog, questions, judgments):
    """A separate consistency pass: IDs/quotes/scopes/split groups, not ranking."""
    ids = [item["id"] for item in questions]
    if len(set(ids)) != len(ids) or set(ids) != set(judgments):
        raise ValueError("Question IDs and judgments must have a one-to-one mapping.")
    groups, normalized_queries = {}, {}
    counts = {"questions": len(questions), "dev": 0, "heldout": 0, "labels": 0,
              "multi_passage_questions": 0, "expected_abstentions": 0}
    for item in questions:
        if item["split"] not in {"dev", "heldout"}:
            raise ValueError("Unknown benchmark split.")
        family = item["family"]
        if family in groups and groups[family] != item["split"]:
            raise ValueError("Paraphrase families cannot cross splits.")
        groups[family] = item["split"]
        query = item["question"].strip().casefold()
        if query in normalized_queries and normalized_queries[query] != item["split"]:
            raise ValueError("A duplicate question crossed splits.")
        normalized_queries[query] = item["split"]
        view = query_view(catalog, item)
        available = {(record.source_id, record.record_id, chunk.section): chunk
                     for chunk in view.authorized_chunks(item["user_id"])
                     for record, _ in [view.resolve(chunk.chunk_id, item["user_id"])]}
        labels = judgments[item["id"]]["relevant"]
        seen = set()
        for label in labels:
            key = judgment_key(label)
            if key in seen or key not in available or label["grade"] not in {1, 2}:
                raise ValueError("Invalid, foreign, duplicate, or stale relevance judgment.")
            seen.add(key)
            if label["quote"] != available[key].excerpt:
                raise ValueError("Judgment quote does not match the selected source version.")
        if not labels and not item["expected_abstain"]:
            raise ValueError("An answerable question needs reviewed evidence.")
        counts[item["split"]] += 1
        counts["labels"] += len(labels)
        counts["multi_passage_questions"] += len(labels)>1
        counts["expected_abstentions"] += item["expected_abstain"]
    counts["families"] = len(groups)
    counts["current_records"] = len(catalog.current_records())
    counts["current_public_passages"] = len(catalog.documents(None))
    return counts


def source_aware_order(question, documents, catalog, actor):
    """Opt-in exact-identifier preference; no authority or recency boost."""
    from .evidence import IDENTIFIER, collect_evidence
    evidence = collect_evidence(catalog, documents, actor)
    wanted = {value.upper() for value in IDENTIFIER.findall(question)}
    if not wanted:
        return tuple(documents)
    matches = {}
    for item in evidence:
        record, _ = catalog.resolve(item.chunk_id, actor)
        identifiers = {value.upper() for _, value in record.identifiers}
        matches[item.chunk_id] = bool(wanted & identifiers)
    ordered = tuple(sorted(documents, key=lambda d: not matches[d.metadata["chunk_id"]]))
    collect_evidence(catalog, ordered, actor)
    return ordered
