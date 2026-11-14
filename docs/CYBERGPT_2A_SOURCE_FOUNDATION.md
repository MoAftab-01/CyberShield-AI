# CyberGPT 2.0 Phase 2A Batch 1

## Review status and activation boundary

This batch is an **opt-in offline foundation**, not a replacement chat pipeline. No existing application source, frontend, Docker configuration, migration, or dependency was edited for Phase 2A. Nothing imports the new package from live routes or agents. No online fetcher, LangGraph agent, database, persistent catalog, cross-encoder model, or service was added.

Development worktree: E:\placement_personal\Projects\CyberShield-AI-cybergpt-2-source-foundation  
Branch: feature/cybergpt-2-source-foundation  
Base: 2c6bf6879aee47cb6e432c88a1dab8c57fe1de73

The original main working tree was inventoried before copying: ten modified tracked files, zero staged files, five reviewed untracked source/test/migration files, and 24 excluded local/model-cache files. All 15 reviewed files were copied byte-for-byte and SHA256 checked. The transfer manifest is CYBERGPT_2A_BASELINE.json. No environment files, credentials, uploads, indexes, databases, cache, virtual environment, or local settings were transferred. The existing interpreter/dependencies were reused read-only from the original virtual environment.

The preserved security baseline includes fail-closed RAG scopes, authenticated threat-search ownership, Phase 1A settings hardening, the unapplied ownership migration, and frontend Docker VITE_API_URL=/api. The original PostgreSQL database still needs the ownership migration before using that modified backend. This batch does not apply it or start any application service.

## Reused architecture

- Existing FastAPI routes and CyberGPT orchestration remain the live entry points.
- Existing DocumentChunker provides 600-character / 100-character overlap splitting within each explicit section; sections never share a chunk.
- Existing BM25Store tokenization and ranking, FAISSStore normalized dense vectors, HybridRetriever query expansion, RRF, blended reranking, relevance floors, page deduplication, and MMR are reused.
- Existing EmbeddingService is selected as hash/384 only inside offline benchmark workers. Runtime model selection and embeddings remain configurable and unchanged.
- Existing RAGService._generate is called lazily only when a developer explicitly invokes grounded_answer without a generator stub. Tests and benchmarks always use a stub.
- Existing ownership/security tests are preserved unchanged. New catalog resolution adds a separate authorization/version check before citation output.
- Existing evaluation datasets and sweeps are untouched. This corpus is a new, small diagnostic set.

## Files added

Application library:

- backend/app/knowledge/__init__.py: inert package boundary.
- backend/app/knowledge/models.py: immutable, extra-field-forbidding source, record, chunk, evidence, claim, and answer contracts.
- backend/app/knowledge/registry.py: application-controlled official source definitions and a distinctly synthetic fixture source.
- backend/app/knowledge/ingestion.py: bounded offline adapters, pinned approval manifest, normalization, hashing, deduplication, version history, structured chunks, and private ownership.
- backend/app/knowledge/evidence.py: canonical evidence resolution, authorized reranker hook, citation formatter, conservative exact-excerpt answer boundary.
- backend/app/knowledge/evaluation.py: dedicated offline worker, temporary indexes, existing retrieval comparisons and separate answer-contract scoring.

Fixtures: backend/evaluation/source_foundation/{manifest.json,nvd-selected-fields.json,synthetic-old.json,synthetic-current.json,questions.json,README.md}.

Tests: backend/tests/test_source_foundation.py and backend/tests/test_source_benchmark.py.

Documentation: this file and CYBERGPT_2A_BASELINE.json. Prior security-baseline files are transferred, not newly changed by Phase 2A.

## Source registry and admission

| ID | Organization / canonical source | Machine-readable entry | Rights / status |
| --- | --- | --- | --- |
| nvd | NIST NVD, https://nvd.nist.gov/ | CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0 | Attribute NVD/CVE contributors; review third-party rights. |
| cisa-kev | CISA, https://www.cisa.gov/known-exploited-vulnerabilities-catalog | Official KEV JSON feed linked in registry | Review website policies and third-party material. |
| mitre-attack | MITRE, https://attack.mitre.org/ | Official attack-stix-data repository | Retain applicable terms, notices and attribution. |
| mitre-cwe | MITRE, https://cwe.mitre.org/ | Official CWE downloads | MITRE copyright designation and license must accompany redistribution. |
| nist-csrc | NIST CSRC, https://csrc.nist.gov/publications | Publication-specific adapters deferred | Check final/draft/withdrawn status and publication notices. |
| owasp | OWASP, https://owasp.org/ | Official CheatSheetSeries repository | Project-specific license/attribution review required. |
| fixture-reference | CyberShield original offline test text | Bundled JSON | CC0-1.0 synthetic material; never official authority. |

Definitions include official URLs, licensing references/notes and organizational trust. Record contracts carry record ID/title/type, publication/modification/retrieval timestamps, source version, artifact and content hashes, lifecycle state, scope, owner, identifiers and sections. This separates organizational authority from snapshot provenance and currency.

Public admission requires a digest in the **operator-controlled** manifest and a registered adapter/source binding. The manifest is privileged application configuration, not upload metadata. Byte integrity is not an organizational digital signature: provenance depends on the operator reviewing the source and snapshot. Only the NVD adapter is implemented for official input in this batch; registration of the other five sources does not claim their content was ingested.

The curated NVD fixture contains selected factual fields for CVE-2021-44228, reviewed against the official API on 2026-10-30: ID, dates, NVD primary CVSS v3.1 score and severity. It omits third-party description text. It is not a complete API response. The adapter can also preserve an English description and CVSS v3.1 assessment from approved NVD-shaped input; other CVSS versions and full reference/affected-product modeling remain future work. Canonical document URLs are generated from validated CVE IDs, never from payload URL claims.

All fictional records remain synthetic_fixture and have no external document URL. They must not be represented as MITRE, OWASP, NIST, or CISA recommendations. No source definition alone makes an upload public.

## Ingestion and lifecycle behavior

- Artifact reads are bounded to 512 KB and adapters to 100 records per batch.
- Text is Unicode NFC normalized; CRLF/CR becomes LF; invalid control characters are rejected.
- Document IDs hash source, source record identifier, scope and exact owner identity.
- Content hashes cover normalized headings/text; versions additionally cover title, source dates, state, identifiers, trust, canonical URL, type and licensing notes.
- Retrieval time is separate from source modification time; it does not establish that a policy is current.
- Duplicate versions keep the original admitted snapshot/retrieval metadata and do not create new chunks. Multiple retrieval observations are not persisted as a separate audit log.
- Changes require a strictly newer source modification time. Equal-time conflicting records or older snapshots require operator review.
- Entire batches are validated and chunked before catalog mutation. Histories remain in memory; only the latest active version resolves.
- NVD Rejected records become withdrawn. Synthetic fixtures exercise superseded, withdrawn and deleted states. Old chunks remain in memory but cannot resolve after supersession/withdrawal/deletion.
- Private ingestion requires an exact positive integer owner. Boolean, float, string, missing and nonpositive identities fail closed. Private IDs include ownership; uploads cannot be promoted through payload metadata.
- Logs contain source ID and record count only, never source text, questions, private file paths or credentials.

The catalog is process-local and intended for offline evaluation or explicit developer calls. It is not a durable, concurrent serving catalog. Persistence, access-controlled lifecycle APIs and cache invalidation require a later design.

## Evidence and citation contract

collect_evidence resolves every chunk ID against the catalog for the current actor and checks canonical text and identity metadata. It accepts existing retriever diagnostic score keys but derives no trust from them. Unknown URL/trust keys, changed owners/scopes/versions/hashes/content, stale records, and foreign chunks are rejected.

rerank_documents lets a configured reranker reorder/drop immutable authorized evidence. Added/modified/duplicated evidence is rejected, and authorization is checked again after the callback. No cross-encoder is installed or downloaded. Any future reranker implementation must be operator-controlled; this callback is not an untrusted plugin sandbox.

The public format_citations function re-resolves the original retrieved documents and rejects citation IDs outside that authorized result. The generator cannot supply source URLs, titles, section labels or final citation identifiers.

A real offline example:

- record_id: CVE-2021-44228
- source_id: nvd
- section: CVSS v3.1 assessment
- excerpt: "CVE-2021-44228 has CVSS v3.1 base score 10 (CRITICAL)."
- citation_id: E-a94dfaf58dec46546509
- source_version: v-93827f5cdebb8c89e49d7ef12533b7a1a2bb64fd744584a2ce4601db991409a5
- canonical_url: https://nvd.nist.gov/vuln/detail/CVE-2021-44228
- retrieved_at: 2026-10-30T00:00:00Z
- mapping: claim-1 -> E-a94dfaf58dec46546509
- verification: exact_excerpt
- answer verification_level: extractive-reference-integrity-only

grounded_answer serializes authorized evidence as untrusted data for the existing answer generator. It has no tool executor. Draft JSON forbids extra fields and must map each claim to retrieved citations. Every accepted claim must be an exact substring of every cited excerpt; unsupported paraphrases, invented references, URLs in extra fields, and tool-call structures are refused. Source state is checked again after generation and before formatting.

Insufficient lexical coverage, missing exact CVE/CWE/ATT&CK identifiers, unavailable/foreign/stale evidence, malformed model output, and obvious instruction-like content produce an abstention with no evidence. Explicit conflict-resolution questions abstain in this batch. Prompt-injection marker detection is a conservative heuristic, not a complete prompt-injection defense.

Exact excerpt validation is **not** semantic claim verification. An exact quotation may still be irrelevant, misleading, outdated, inapplicable, or contradicted by another source. Automatic conflict detection, effective-date/applicability reasoning, richer question relevance and full claim entailment are deferred. The live CyberGPT route has not acquired these protections until separately integrated and approved.

## Reproducing the offline benchmark

From this worktree's backend directory with existing dependencies:

    python -B -m app.knowledge.evaluation

The worker refuses to start if embedding/index stores were already imported. It sets VECTOR_DB_DIR to a fresh TemporaryDirectory before imports, pins hash embeddings, ignores ambient RAG/embedding tuning, denies socket connections, suppresses index-build console noise, and cleans only its own disposable directory. No application settings, database session, HTTP client, upload index or environment file is loaded. Do not call the worker from a server.

The benchmark prepares authorized actor-specific corpora before ranking and checks catalog authorization again on output. The preserved Phase 1B tests additionally exercise mixed-owner indexes and ambiguous/legacy metadata against the actual hybrid retriever.

Dataset: 16 questions; 11 answerable; 5 expected abstentions; 13 active public records, one private synthetic record, and retained superseded/withdrawn/deleted history. One official selected-field record; all other text/questions are original CC0 synthetic fixtures. Questions include overlapping identifiers, KEV, ATT&CK, CWE, OWASP, NIST controls, conflicting/stale versions, missing/deleted evidence, private owner/other-user access and prompt injection.

Binary relevance is measured at current document level, not repeated overlapping chunks. Recall denominator is gold documents; Precision@5 always divides by five, even when fewer results survive filtering. MRR is truncated to the returned top five. nDCG uses binary gain. Empty-gold questions are excluded from ranking aggregates and evaluated as abstention cases.

| Mode | Recall@5 | Precision@5 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 1.000000 | 0.218182 | 1.000000 | 1.000000 |
| FAISS / hash | 1.000000 | 0.218182 | 1.000000 | 1.000000 |
| Existing hybrid, MMR lambda 1.0 | 1.000000 | 0.218182 | 0.954545 | 0.966448 |
| Existing hybrid, MMR lambda 0.85 | 1.000000 | 0.218182 | 0.954545 | 0.966448 |

Hybrid includes existing query expansion, RRF, blended reranking, relevance floors and page deduplication; lambda 1.0 removes the diversity penalty but still deduplicates pages. No runtime tuning was changed. There is no measurable MMR gain on this tiny corpus. This result does not establish a production ranking winner.

Generation-contract metrics use a deterministic first-excerpt stub, **not a real model**:

| Mode | Accepted / 16 | Citation validity | Gold evidence coverage | Unsupported excerpt rate | Correct expected abstentions |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 | 6 | 1.0 | 0.50 | 0.0 | 5 / 5 |
| FAISS / hash | 6 | 1.0 | 0.50 | 0.0 | 5 / 5 |
| Hybrid | 10 | 1.0 | 0.75 | 0.0 | 5 / 5 |
| Hybrid + MMR | 10 | 1.0 | 0.75 | 0.0 | 5 / 5 |

Citation validity counts returned claim-to-citation references that resolve to authorized retrieved evidence. Gold evidence coverage counts labeled relevant document IDs present among the answer's cited evidence, divided by total gold documents. Unsupported excerpt rate measures only nonmatching accepted excerpts; a zero rate is enforced by the contract. **Semantic unsupported-claim rate is null/unmeasured.** Low coverage and extra conservative abstentions are visible rather than hidden. Prompt-injection contamination anywhere in the supplied top-five context can cause an otherwise answerable question to abstain.

Two independent subprocess runs produce exactly equal JSON reports. Hash embeddings are a deterministic lexical proxy, not semantic embeddings. No stronger encoder comparison was performed: no model/cache transfer or download was authorized. A reviewed, locally available semantic model comparison and larger independent labels are required before changing a default. The deliberately simple set is a correctness diagnostic, not production-grade accuracy evidence.

## Validation commands and results

Focused command (from backend; conftest sets isolated synthetic settings before application imports):

    python -B -m pytest -p no:cacheprovider tests/test_source_foundation.py tests/test_source_benchmark.py tests/test_configuration.py tests/test_rag_visibility.py tests/test_threat_ownership.py tests/test_tools.py::TestCveLookup -q

This session additionally wrapped pytest with socket/PostgreSQL denial, restricted SQLite storage, disabled external plugin auto-loading and bytecode/cache writes, and asserted temporary vector storage. Guard runner and XML reports are preserved outside both worktrees under C:\Users\moham\AppData\Local\Temp\cybershield-2a-baseline-9nu0iupm.

Final focused result: **203 passed**, 52 warnings; 87 new source-foundation tests, 36 existing configuration tests, and 80 preserved ownership/visibility/CVE-tool tests. Zero outbound or PostgreSQL attempts. Synthetic benchmark subprocesses also deny network and use disposable indexes.

Transferred-baseline full suite: **325 passed, 2 failed**, 257 warnings. The guard blocked 162 outbound attempts; zero PostgreSQL attempts. No connection was permitted. Known failures were not changed or weakened:

- test_agent_upgrades.py::TestPasswordSecurityAndPrivacy::test_conversation_title_masks_raw_password_in_new_conversation
- test_orchestrator.py::TestDispatch::test_a_tool_request_takes_the_tool_path

These concern password routing/title masking and are outside this source-foundation batch. Full-suite tests that attempt network access still need stronger stubbing; offline guards remain necessary. Expanded full-suite checkpoint: **409 passed, 2 failed**, 257 warnings, 160.93 seconds; the same two failures and 162 denied outbound attempts, zero PostgreSQL attempts. This checkpoint collected the initial 84 new tests. The final formatter/adversarial refinements and three added tests were subsequently validated by the final 203-test focused run (87 new tests); no existing runtime source changed.

No migration, Docker restart/build, database connection, installation, commit or deployment was performed.

## Remaining risks and next review step

1. Existing authentication/password-history security remediation is not completed by this batch; retain the known regression failures and Phase 1B follow-up work.
2. Existing local PostgreSQL ownership migration remains unapplied; do not start the transferred backend against it before a separately approved migration.
3. Operator-approved hashes establish the reviewed artifact boundary, not automatic authenticity/current applicability. License review and source-specific adapters must precede expansion.
4. Catalog memory, version retention and identifier checks are deliberately small/offline. No persistent catalog, source deletion synchronization, multi-worker cache invalidation or live-route cutover is implemented.
5. Complete prompt-injection resistance, semantic entailment, conflict detection and answer relevance are not demonstrated by excerpt matching.
6. No semantic encoder or cross-encoder model has been compared. Existing runtime model configuration/indexes remain untouched.
7. Small fixture metrics are not deployment evidence. No production accuracy claim is made.

Proposed Phase 2B, only after approval: finish outstanding security blockers; expand reviewed source/version/applicability fixtures; compare an approved locally available semantic encoder and optional authorized reranker; add claim relevance/entailment and conflict tests; then propose an explicit live retrieval/citation integration. LangGraph agent architecture remains a separate later decision.
