"""Synthetic-only contracts, ownership, and adversarial provenance tests."""
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path

from langchain_core.documents import Document
import pytest
from pydantic import ValidationError

from app.knowledge.evaluation import RETRIEVED_AT, fixture_catalog
from app.knowledge.evidence import collect_evidence, grounded_answer, rerank_documents
from app.knowledge.ingestion import Catalog, FIXTURE_ROOT, NvdAdapter, normalize
from app.knowledge.models import SourceDefinition
from app.knowledge.registry import SourceRegistry

pytestmark = pytest.mark.configuration_only


@pytest.fixture
def catalog():
    return fixture_catalog()


def only(catalog, record_id, actor=202):
    return tuple(d for d in catalog.documents(actor) if catalog.resolve(d.metadata["chunk_id"], actor)[0].record_id == record_id)


def approved(tmp_path, payload, artifact_id="custom"):
    path = tmp_path/"artifact.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    manifest = tmp_path/"manifest.json"
    manifest.write_text(json.dumps({"artifacts": [{
        "artifact_id": artifact_id, "sha256": sha256(path.read_bytes()).hexdigest(),
        "source_id": "fixture-reference", "adapter": "reference-fixture", "trust": "synthetic_fixture"}]}))
    return Catalog(manifest), path


def reference(text="First source statement.", modified="2026-01-01T00:00:00Z", **extra):
    return {"records": [{"record_id":"EXAMPLE", "title":"Example", "modified_at":modified,
                         "sections":[{"heading":"Context", "text":text}], **extra}]}


@pytest.mark.parametrize("source", ["nvd","cisa-kev","mitre-attack","mitre-cwe","nist-csrc","owasp"])
def test_official_registry_definitions(source):
    definition = SourceRegistry().get(source)
    assert definition.trust_classification == "authoritative_organization"
    assert definition.canonical_url.startswith("https://")
    assert definition.licensing_notes and definition.licensing_url
    with pytest.raises(ValidationError):
        definition.organization = "Attacker"


@pytest.mark.parametrize("source", ["uploads", "", "attacker-official", None])
def test_unregistered_source_does_not_grant_trust(source):
    with pytest.raises(ValueError):
        SourceRegistry().get(source)


@pytest.mark.parametrize("url", ["http://nist.gov/", "https://user:pass@nist.gov/", "file:///data", "https:///path", "https://nist.gov/#override"])
def test_registry_rejects_unsafe_urls(url):
    with pytest.raises(ValidationError):
        SourceDefinition(source_id="test", organization="Test", canonical_url=url,
            licensing_url="https://example.com/license", licensing_notes="test",
            trust_classification="synthetic_fixture")


def test_pinned_official_snapshot_and_canonical_provenance(catalog):
    docs = only(catalog, "CVE-2021-44228")
    evidence = collect_evidence(catalog, docs, 202)[0]
    assert evidence.canonical_url == "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"
    assert evidence.trust == "official_snapshot"
    assert evidence.section == "CVSS v3.1 assessment"
    assert evidence.source_version.startswith("v-")
    assert evidence.modified_at.year == 2026 and "CRITICAL" in evidence.excerpt


def test_deterministic_documents_chunks_and_dedup(catalog):
    other = fixture_catalog()
    assert catalog.current_records() == other.current_records()
    assert catalog.documents(101) == other.documents(101)
    before = catalog.documents(101)
    catalog.ingest_artifact("synthetic-current", FIXTURE_ROOT/"synthetic-current.json", retrieved_at=RETRIEVED_AT+timedelta(days=1))
    assert catalog.documents(101) == before
    assert len({d.metadata["chunk_id"] for d in before}) == len(before)


def test_synthetic_references_never_get_official_urls(catalog):
    for record in catalog.current_records():
        if record.source_id == "fixture-reference":
            assert record.canonical_url is None and record.trust == "synthetic_fixture"


def test_modified_artifact_cannot_claim_public_trust(tmp_path):
    original = json.loads((FIXTURE_ROOT/"synthetic-current.json").read_text())
    original["scope"] = "knowledge_base"
    original["trust"] = "official_snapshot"
    changed = tmp_path/"changed.json"
    changed.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="integrity"):
        Catalog().ingest_artifact("synthetic-current", changed, retrieved_at=RETRIEVED_AT)


def test_unknown_artifact_is_rejected_before_file_read(tmp_path):
    with pytest.raises(ValueError, match="not approved"):
        Catalog().ingest_artifact("unreviewed", tmp_path/"does-not-exist", retrieved_at=RETRIEVED_AT)


def test_oversized_artifact_rejected(tmp_path):
    path=tmp_path/"large"
    path.write_bytes(b"x"*512001)
    with pytest.raises(ValueError, match="integrity"):
        Catalog().ingest_artifact("synthetic-current", path, retrieved_at=RETRIEVED_AT)


@pytest.mark.parametrize("owner", [None, True, False, 0, -1, "101", 101.0])
def test_private_ingestion_requires_exact_positive_owner(catalog, owner):
    with pytest.raises(ValueError):
        catalog.ingest_private(record_id="x", title="x", text="Private source text.", owner_id=owner, retrieved_at=RETRIEVED_AT)


@pytest.mark.parametrize("actor", [None, True, 101.0, "101", 202, -1])
def test_private_chunks_fail_closed_for_other_or_invalid_principals(catalog, actor):
    assert only(catalog, "PRIVATE-ORCHID-71", actor) == ()


def test_private_owner_can_resolve_without_promotion(catalog):
    documents = only(catalog, "PRIVATE-ORCHID-71", 101)
    assert len(documents) == 1
    evidence = collect_evidence(catalog, documents, 101)[0]
    assert evidence.scope == "private" and evidence.trust == "private_upload"
    assert evidence.canonical_url is None
    with pytest.raises(ValueError):
        collect_evidence(catalog, documents, 202)


def test_stale_versions_are_not_resolvable():
    catalog=Catalog()
    catalog.ingest_artifact("synthetic-old", FIXTURE_ROOT/"synthetic-old.json", retrieved_at=RETRIEVED_AT)
    old_docs=catalog.documents(202)
    catalog.ingest_artifact("synthetic-current", FIXTURE_ROOT/"synthetic-current.json", retrieved_at=RETRIEVED_AT)
    assert all(catalog.resolve(doc.metadata["chunk_id"], 202) is None for doc in old_docs)
    current=only(catalog,"SYN-ROTATION")
    assert "90-day" in current[0].page_content
    for rid in ("SYN-WITHDRAWN","SYN-DELETED"):
        assert only(catalog,rid) == ()


def test_out_of_order_batch_rejected_atomically(catalog):
    before=catalog.current_records()
    with pytest.raises(ValueError,match="Out-of-order"):
        catalog.ingest_artifact("synthetic-old", FIXTURE_ROOT/"synthetic-old.json", retrieved_at=RETRIEVED_AT)
    assert catalog.current_records() == before


def test_equal_timestamp_conflicting_content_requires_review(tmp_path):
    catalog,path=approved(tmp_path,reference())
    catalog.ingest_artifact("custom",path,retrieved_at=RETRIEVED_AT)
    replacement,new_path=approved(tmp_path,reference("Different source statement."))
    catalog._approved=replacement._approved
    with pytest.raises(ValueError,match="conflicting"):
        catalog.ingest_artifact("custom",new_path,retrieved_at=RETRIEVED_AT)


def test_failed_chunking_does_not_partially_admit(tmp_path,monkeypatch):
    payload=reference()
    payload["records"].append({**payload["records"][0],"record_id":"SECOND"})
    catalog,path=approved(tmp_path,payload)
    original=catalog._chunk
    def fail_second(record):
        if record.record_id=="SECOND":
            raise ValueError("Synthetic splitter failure")
        return original(record)
    monkeypatch.setattr(catalog,"_chunk",fail_second)
    with pytest.raises(ValueError,match="splitter"):
        catalog.ingest_artifact("custom",path,retrieved_at=RETRIEVED_AT)
    assert catalog.current_records() == () and catalog.documents(202) == ()


def test_section_boundaries_and_deterministic_chunk_provenance(tmp_path):
    payload=reference(" ".join(["Long synthetic paragraph."]*70))
    payload["records"][0]["sections"].append({"heading":"Mitigation","text":"Separate mitigation example."})
    catalog,path=approved(tmp_path,payload)
    catalog.ingest_artifact("custom",path,retrieved_at=RETRIEVED_AT)
    evidence=collect_evidence(catalog,catalog.documents(202),202)
    assert len(evidence)>2
    assert {item.section for item in evidence}=={"Context","Mitigation"}
    assert all(len(item.excerpt)<=600 for item in evidence)
    assert len({item.chunk_id for item in evidence})==len(evidence)


@pytest.mark.parametrize("value", ["bad\x00text", "bad\x01text"])
def test_control_characters_rejected(value):
    with pytest.raises(ValueError):
        normalize(value)


def test_unicode_and_newline_normalization():
    assert normalize(" e\u0301\r\ntext ")=="\u00e9\ntext"


@pytest.mark.parametrize("payload", [{}, {"vulnerabilities":None}, {"vulnerabilities":[{"cve":{"id":"CVE-1"}}]}])
def test_nvd_malformed_inputs_rejected(payload):
    with pytest.raises(ValueError):
        NvdAdapter().parse(payload)


def test_nvd_rejected_record_has_no_active_chunks(tmp_path):
    payload={"vulnerabilities":[{"cve":{"id":"CVE-2099-40000","vulnStatus":"Rejected"}}]}
    path=tmp_path/"nvd.json"
    path.write_text(json.dumps(payload))
    manifest=tmp_path/"manifest.json"
    manifest.write_text(json.dumps({"artifacts":[dict(artifact_id="rejected",source_id="nvd",
        adapter="nvd",trust="synthetic_fixture",sha256=sha256(path.read_bytes()).hexdigest())]}))
    catalog=Catalog(manifest)
    record=catalog.ingest_artifact("rejected",path,retrieved_at=RETRIEVED_AT)[0]
    assert record.state=="withdrawn" and catalog.documents(202)==()


@pytest.mark.parametrize("key,value", [
    ("source_id","nvd"),("scope","knowledge_base"),("user_id",202),("source_version","v-forged"),
    ("content_hash","fake"),("text_hash","fake"),("canonical_url","https://attacker.example/"),
    ("document_id","fake"),("chunk_id","missing"),("page",False),
])
def test_retrieval_metadata_forgery_denied(catalog,key,value):
    doc=only(catalog,"PRIVATE-ORCHID-71",101)[0].model_copy(deep=True)
    doc.metadata[key]=value
    with pytest.raises(ValueError):
        collect_evidence(catalog,[doc],101)


def test_retrieved_text_substitution_denied(catalog):
    doc=only(catalog,"SYN-CWE")[0].model_copy(deep=True)
    doc.page_content="Invented text"
    with pytest.raises(ValueError):
        collect_evidence(catalog,[doc],202)


def test_existing_retriever_diagnostics_allowed_without_granting_trust(catalog):
    doc=only(catalog,"SYN-CWE")[0].model_copy(deep=True)
    doc.metadata.update(retrieval_score=1.0,vector_rank=1,lexical_rank=1,
                        semantic_similarity=1.0,query_term_coverage=1.0)
    assert collect_evidence(catalog,[doc],202)


def test_reranker_can_only_reorder_authorized_evidence(catalog):
    docs=only(catalog,"SYN-CWE")+only(catalog,"SYN-OWASP")
    assert rerank_documents(catalog,docs,202,lambda evidence:reversed(evidence)) == tuple(reversed(docs))
    private=collect_evidence(catalog,only(catalog,"PRIVATE-ORCHID-71",101),101)
    with pytest.raises(ValueError):
        rerank_documents(catalog,docs,202,lambda evidence:private)
    with pytest.raises(ValueError):
        rerank_documents(catalog,docs,202,lambda evidence:(evidence[0],evidence[0]))
    with pytest.raises(ValueError):
        rerank_documents(catalog,docs,202,lambda evidence:(evidence[0].model_copy(update={"scope":"private"}),))


def draft_for(catalog,docs,actor=202,**updates):
    item=collect_evidence(catalog,docs,actor)[0]
    return json.dumps({"claims":[{"text":item.excerpt,"citation_ids":[item.citation_id],**updates}]})


def test_grounded_excerpt_contract_and_deterministic_citation(catalog):
    docs=only(catalog,"CVE-2021-44228")
    answer=grounded_answer("CVE-2021-44228 severity",docs,catalog,202,generator=lambda prompt:draft_for(catalog,docs))
    assert not answer.abstained
    assert answer.claims[0].citation_ids==(answer.evidence[0].citation_id,)
    assert answer.claims[0].verification=="exact_excerpt"
    assert "https://nvd.nist.gov/vuln/detail/CVE-2021-44228" in answer.answer
    assert answer.evidence[0].source_version in answer.answer


@pytest.mark.parametrize("update", [
    {"citation_ids":["E-invented"]}, {"text":"Unsupported invented answer."},
    {"url":"https://attacker.example/"}, {"tools":["read_secrets"]},
    {"citation_ids":[]}, {"text":""}, {"text":"CRITICAL"},
])
def test_invalid_generated_claims_abstain(catalog,update):
    docs=only(catalog,"SYN-CWE")
    answer=grounded_answer("CWE-89 SQL injection",docs,catalog,202,
                           generator=lambda prompt:draft_for(catalog,docs,**update))
    assert answer.abstained and answer.evidence==() and answer.claims==()


@pytest.mark.parametrize("raw", ["not JSON","{}",'{"claims":[]}',"x"*20001])
def test_malformed_generated_contract_abstains(catalog,raw):
    answer=grounded_answer("CWE-89 SQL injection",only(catalog,"SYN-CWE"),catalog,202,generator=lambda _:raw)
    assert answer.abstained


@pytest.mark.parametrize("question", ["CVE-2099-99999 severity","CVE-2099-100010 severity",""])
def test_missing_exact_identifier_abstains_before_generation(catalog,question):
    def forbidden(_):
        pytest.fail("Generator must not receive insufficient evidence")
    assert grounded_answer(question,only(catalog,"SYN-CVE-10001"),catalog,202,generator=forbidden).abstained


def test_private_cross_user_answer_never_reaches_generator(catalog):
    def forbidden(_):
        pytest.fail("Generator must not receive foreign private evidence")
    answer=grounded_answer("PRIVATE-ORCHID-71 recovery",only(catalog,"PRIVATE-ORCHID-71",101),
                           catalog,202,generator=forbidden)
    assert answer.abstained and answer.evidence==()


def test_prompt_injection_cannot_call_generator_or_tools(catalog):
    def forbidden(_):
        pytest.fail("Injection must not reach the generator")
    answer=grounded_answer("CVE-2099-66666 remediation",only(catalog,"SYN-INJECTION"),
                           catalog,202,generator=forbidden)
    assert answer.abstained and answer.reason=="instruction_like_content"


def test_conflict_resolution_deferred_explicitly(catalog):
    answer=grounded_answer("Conflicting AC-2 review intervals",only(catalog,"SYN-ROTATION")+only(catalog,"SYN-CONFLICT"),
                           catalog,202,generator=lambda _:pytest.fail("Do not guess between conflicting sources"))
    assert answer.abstained and answer.reason=="conflict_resolution_deferred"


def test_evidence_revalidated_after_generation(catalog):
    docs=only(catalog,"PRIVATE-ORCHID-71",101)
    raw=draft_for(catalog,docs,101)
    def generator(_):
        catalog.ingest_private(record_id="PRIVATE-ORCHID-71", title="Updated incident",
            text="A new private source version.",owner_id=101,retrieved_at=RETRIEVED_AT+timedelta(days=1))
        return raw
    answer=grounded_answer("PRIVATE-ORCHID-71 incident recovery",docs,catalog,101,generator=generator)
    assert answer.abstained and answer.evidence==()


def test_existing_generator_is_reused_only_when_explicitly_invoked(catalog,monkeypatch):
    from app.services.rag_service import RAGService
    docs=only(catalog,"SYN-CWE")
    calls=[]
    def generate(prompt,max_tokens):
        calls.append((prompt,max_tokens))
        return draft_for(catalog,docs)
    monkeypatch.setattr(RAGService,"_generate",generate)
    answer=grounded_answer("CWE-89 SQL injection",docs,catalog,202)
    assert not answer.abstained and len(calls)==1
    assert "untrusted DATA" in calls[0][0] and calls[0][1]==700

def test_formatter_cannot_resolve_fabricated_or_foreign_ids(catalog):
    from app.knowledge.evidence import format_citations
    docs=only(catalog,"SYN-CWE")
    valid=collect_evidence(catalog,docs,202)[0].citation_id
    assert valid in format_citations(catalog,docs,202,[valid])
    for identifiers in ([valid,"E-forged"],[valid,valid]):
        with pytest.raises(ValueError):
            format_citations(catalog,docs,202,identifiers)
    private_docs=only(catalog,"PRIVATE-ORCHID-71",101)
    private=collect_evidence(catalog,private_docs,101)[0].citation_id
    with pytest.raises(ValueError):
        format_citations(catalog,private_docs,202,[private])


def test_supplied_scope_authority_and_url_are_ignored_at_ingestion(tmp_path):
    payload=reference()
    payload.update(scope="knowledge_base",trust="official_snapshot")
    payload["records"][0].update(scope="public",source_id="nvd",
        owner_id=None,canonical_url="https://attacker.example/",trust="official_snapshot")
    catalog,path=approved(tmp_path,payload)
    record=catalog.ingest_artifact("custom",path,retrieved_at=RETRIEVED_AT)[0]
    assert record.source_id=="fixture-reference"
    assert record.trust=="synthetic_fixture" and record.canonical_url is None


def test_nvd_numeric_score_serializations_produce_same_content():
    def parse(score):
        return NvdAdapter().parse({"vulnerabilities":[{"cve":{"id":"CVE-2099-10000",
            "metrics":{"cvssMetricV31":[{"cvssData":{"baseScore":score,"baseSeverity":"CRITICAL"}}]}}}]})
    assert parse(10)==parse(10.0)
