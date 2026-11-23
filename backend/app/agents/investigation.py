"""Bounded, request-local CVE investigation using a compiled LangGraph.

No LLM, checkpoint, shell, upload, conversation, or arbitrary URL tool is used.
Source text is data. Quotation attribution does not establish factual truth.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.knowledge.claim_verifier import instruction_like, verify_draft, terms
from app.knowledge.evidence import collect_evidence
from app.knowledge.ingestion import Catalog, NvdAdapter, normalize, timestamp
from app.knowledge.models import Section
from app.knowledge.registry import SourceRegistry
from app.rag.retrieval_context import RetrievalContext
from app.rag.retriever import HybridRetriever

from app.agents.cve_input import validate_cve

NODES = ("validate", "nvd", "kev", "correlate", "assess", "verify", "report")


class InvestigationState(TypedDict, total=False):
    cve: str
    actor: int
    started: float
    attempts: dict
    results: dict
    errors: dict
    catalog: object
    documents: tuple
    evidence: tuple
    grounding: dict
    warnings: list
    progress: list
    findings: dict
    report: dict


def empty_catalog():
    # No default evaluation manifest, persistent files, or shared index access.
    catalog = Catalog.__new__(Catalog)
    catalog.registry = SourceRegistry()
    catalog._approved = {}
    catalog._records = {}
    catalog._current = {}
    catalog._chunks = {}
    return catalog


def _admit(catalog, source_id, record, payload, retrieved_at, fixture):
    definition = catalog.registry.get(source_id)
    return catalog._admit(catalog._record(
        source_id=source_id, trust="synthetic_fixture" if fixture else "official_snapshot",
        scope="public", owner_id=None,
        canonical_url=None if fixture else (
            "https://nvd.nist.gov/vuln/detail/" + record["record_id"]
            if source_id == "nvd" else definition.canonical_url),
        artifact_hash=sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        retrieved_at=retrieved_at, licensing_notes=definition.licensing_notes, **record))


class CVEInvestigator:
    def __init__(self, intelligence):
        self.intelligence = intelligence
        graph = StateGraph(InvestigationState)
        for name, action in (
            ("validate", self.validate), ("nvd", self.nvd), ("kev", self.kev),
            ("correlate", self.correlate), ("assess", self.assess),
            ("verify", self.verify), ("report", self.report)):
            graph.add_node(name, action)
        graph.add_edge(START, "validate")
        graph.add_conditional_edges("validate",
            lambda state: "report" if state.get("errors", {}).get("input") else "nvd")
        graph.add_conditional_edges("nvd", lambda state:
            "nvd" if self._retry(state, "nvd") else "kev")
        graph.add_conditional_edges("kev", lambda state:
            "kev" if self._retry(state, "cisa-kev") else (
                "correlate" if any(r.get("status") == "ok" for r in state["results"].values()) else "assess"))
        graph.add_edge("correlate", "assess")
        graph.add_conditional_edges("assess", lambda state: "verify" if state.get("documents") else "report")
        graph.add_edge("verify", "report")
        graph.add_edge("report", END)
        self.graph = graph.compile()

    @staticmethod
    def _retry(state, source):
        return (state["results"][source]["status"] == "unavailable"
                and state["attempts"].get(source, 0) < 2)

    def validate(self, state):
        try:
            validate_cve(state["cve"])
            if type(state["actor"]) is not int or state["actor"] <= 0:
                raise ValueError("Invalid actor.")
        except (KeyError, ValueError):
            return {"errors": {"input": "invalid_input"}, "progress": ["validate"]}
        return {"catalog": empty_catalog(), "attempts": {}, "results": {},
                "errors": {}, "progress": ["validate"], "warnings": []}

    def _lookup(self, state, source):
        attempts = dict(state["attempts"])
        attempts[source] = attempts.get(source, 0) + 1
        try:
            payload = self.intelligence.lookup(source, state["cve"])
            # Adapters return bounded JSON, never URLs or executable instructions.
            if not isinstance(payload, dict):
                raise ValueError("Invalid source payload.")
            result = {"status": "ok", "payload": payload,
                      "retrieved_at": datetime.now(timezone.utc)}
        except (TimeoutError, ConnectionError):
            result = {"status": "unavailable"}
        except Exception:
            # Fixed diagnostic: no upstream bodies, credentials, or request headers.
            result = {"status": "invalid"}
        results = {**state["results"], source: result}
        return {"attempts": attempts, "results": results,
                "progress": state["progress"] + ["kev" if source == "cisa-kev" else source]}

    def nvd(self, state):
        return self._lookup(state, "nvd")

    def kev(self, state):
        return self._lookup(state, "cisa-kev")

    def correlate(self, state):
        catalog, cve = state["catalog"], state["cve"]
        findings = {"nvd_status": "unavailable", "kev_status": "unknown",
                    "known_exploited": None}
        warnings = []
        fixture = self.intelligence.fixture
        for source, result in state["results"].items():
            if result["status"] != "ok":
                warnings.append(source + "_" + result["status"])
                continue
            payload, at = result["payload"], result["retrieved_at"]
            try:
                if source == "nvd":
                    records = NvdAdapter().parse(payload)
                    if not records:
                        findings["nvd_status"] = "not_found"
                        continue
                    if len(records) != 1 or records[0]["record_id"] != cve:
                        raise ValueError("Mismatched CVE.")
                    record = records[0]
                    findings["nvd_status"] = record["state"]
                    if record["state"] != "active":
                        warnings.append("nvd_record_withdrawn")
                    if sum(len(section.text) for section in record["sections"]) > 128000:
                        raise ValueError("Source text exceeds investigation bounds.")
                    _admit(catalog, source, record, payload, at, fixture)
                else:
                    entries = payload.get("vulnerabilities")
                    if (not isinstance(entries, list) or not isinstance(payload.get("catalogVersion"), str)
                            or not isinstance(payload.get("dateReleased"), str)):
                        raise ValueError("Incomplete catalog.")
                    released = timestamp(payload["dateReleased"])
                    if released is None or released > at:
                        raise ValueError("Invalid catalog date.")
                    if (at - released).total_seconds() > 7 * 86400:
                        warnings.append("kev_snapshot_outdated")
                    matches = [entry for entry in entries if entry.get("cveID") == cve]
                    if len(matches) > 1 or any(not isinstance(e, dict) for e in entries):
                        raise ValueError("Ambiguous catalog.")
                    findings["kev_status"] = "listed" if matches else "not_listed_in_snapshot"
                    findings["known_exploited"] = bool(matches)
                    # A negative is explicitly limited to this complete catalog snapshot.
                    text = (normalize(matches[0]["shortDescription"]) if matches else
                        cve + " is not listed in CISA KEV catalog snapshot " + payload["catalogVersion"]
                        + ". This does not establish absence of exploitation.")
                    sections = [Section(heading="KEV catalog observation", text=text)]
                    if matches and matches[0].get("requiredAction"):
                        sections.append(Section(heading="CISA required action",
                            text=normalize(matches[0]["requiredAction"])))
                    _admit(catalog, source, dict(record_id=cve, title=cve + " KEV catalog observation",
                        document_type="KEV snapshot", published_at=None, modified_at=released,
                        identifiers=(("cve", cve),), state="active", sections=tuple(sections)),
                        payload, at, fixture)
            except Exception:
                findings["nvd_status" if source == "nvd" else "kev_status"] = "invalid"
                if source == "cisa-kev":
                    findings["known_exploited"] = None
                warnings.append(source + "_invalid_evidence")
        documents = tuple(catalog.documents(state["actor"]))
        # Canonical identity and visibility revalidation before any ranking/output.
        collect_evidence(catalog, documents, state["actor"])
        if documents:
            safe = tuple(d for d in documents if not instruction_like(d.page_content))
            if len(safe) != len(documents):
                warnings.append("instruction_like_source_withheld")
            if safe and len(safe) <= 256:
                context = RetrievalContext.build(safe)
                ranked, _ = HybridRetriever.search_with_metrics(cve, top_k=5,
                    user_id=state["actor"], include_uploads=False, context=context)
                collect_evidence(catalog, ranked, state["actor"])
                selected_ids = {d.metadata["chunk_id"] for d in ranked}
                # Exact record identity complements text retrieval: source
                # descriptions may omit their own CVE. Never use foreign IDs.
                exact = [d for d in safe if d.metadata["chunk_id"] not in selected_ids
                    and catalog.resolve(d.metadata["chunk_id"], state["actor"])[0].record_id == cve]
                documents = tuple(list(ranked) + exact)[:20]
            else:
                documents = ()
            collect_evidence(catalog, documents, state["actor"])
        return {"documents": documents, "findings": findings, "warnings": warnings,
                "progress": state["progress"] + ["correlate"]}

    def assess(self, state):
        warnings = list(state.get("warnings", []))
        warnings.append("Asset exposure, affected installed versions, and business impact are not established.")
        findings = dict(state.get("findings", {}))
        findings.setdefault("known_exploited", None)
        findings.setdefault("kev_status", "unknown")
        findings.setdefault("nvd_status", "unavailable")
        if findings.get("nvd_status") == "withdrawn" and findings.get("known_exploited"):
            warnings.append("Conflicting status: withdrawn NVD record and positive KEV observation require human review.")
        return {"warnings": warnings, "findings": findings,
                "progress": state["progress"] + ["assess"]}

    def verify(self, state):
        catalog, actor = state["catalog"], state["actor"]
        evidence = collect_evidence(catalog, state["documents"], actor)
        accepted, claims, warnings = [], [], list(state["warnings"])
        documents = {d.metadata["chunk_id"]: d for d in state["documents"]}
        for item in evidence:
            if instruction_like(item.title + " " + item.excerpt):
                warnings.append("instruction_like_source_withheld")
                continue
            # One complete section per check; the existing verifier still enforces
            # canonical identity, exact attribution, ownership and source state.
            query = "What does this source state about " + state["cve"] + "?"
            # CVE anchoring is checked by canonical record_id above. A description
            # may omit the identifier; do not prepend invented text to quotations.
            if state["cve"] not in item.excerpt:
                query = "What about " + " ".join(sorted(terms(item.excerpt))[:8]) + "?"
            draft = json.dumps({"claims": [{"text": item.excerpt,
                                           "citation_ids": [item.citation_id]}]})
            verified = verify_draft(query, [documents[item.chunk_id]], catalog, actor, draft)
            if verified.abstained:
                warnings.append("quotation_not_verified")
                continue
            accepted.append(item)
            quote = verified.claims[0].model_copy(update={"claim_id": "claim-" + str(len(claims) + 1)})
            claims.append(quote)
        grounding = {
            "status": "supported_quotes" if claims else "insufficient_evidence",
            "answer": "Complete source quotations; factual truth and completeness are not verified.",
            "abstained": not bool(claims), "reason": "exact_source_quotations",
            "claims": [c.model_dump(mode="json") for c in claims],
            "evidence": [e.model_dump(mode="json") for e in accepted],
            "verdicts": [], "quarantined_count": len(evidence) - len(accepted),
            "answer_completeness": "not_verified", "verification_scope": "quotation_attribution_only"}
        return {"grounding": grounding, "warnings": warnings,
                "progress": state["progress"] + ["verify"]}

    def report(self, state):
        grounding = state.get("grounding")
        findings = state.get("findings", {})
        status = ("invalid_input" if state.get("errors", {}).get("input") else
                  "complete" if grounding and not grounding["abstained"]
                  and findings.get("nvd_status") == "active"
                  and findings.get("kev_status") in {"listed", "not_listed_in_snapshot"}
                  and not any("outdated" in w or "withheld" in w or "not_verified" in w
                              for w in state.get("warnings", [])) else
                  "partial" if grounding and not grounding["abstained"] else "insufficient_evidence")
        progress = state.get("progress", []) + ["report"]
        report = {"schema_version": 1, "cve": state.get("cve", ""), "status": status,
            "mode": "offline_fixture" if self.intelligence.fixture else "read_only_live",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "findings": findings, "grounding": grounding,
            "uncertainty": state.get("warnings", []), "workflow": progress,
            "tools": [{"name": name, "attempts": count,
                       "status": state["results"][name]["status"]}
                      for name, count in state.get("attempts", {}).items()],
            "metrics": {"latency_ms": round((time.perf_counter() - state["started"]) * 1000, 3),
                        "llm_calls": 0, "input_tokens": 0, "output_tokens": 0,
                        "estimated_model_cost_usd": 0.0}}
        return {"report": report, "progress": progress}

    def stream(self, cve, actor):
        # No caller-supplied graph config, checkpoint namespace or tracing callbacks.
        for update in self.graph.stream(
            {"cve": cve, "actor": actor, "started": time.perf_counter()},
            config={"recursion_limit": 20, "callbacks": []}, stream_mode="updates"):
            for node, value in update.items():
                yield {"type": "progress", "node": node}
                if node == "report":
                    yield {"type": "report", "report": value["report"]}

    def run(self, cve, actor):
        return next(event["report"] for event in self.stream(cve, actor) if event["type"] == "report")
