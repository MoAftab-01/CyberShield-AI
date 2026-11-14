# CyberGPT 2.0 Phase 2B Batch 1: claim attribution and grounded-answer evaluation

Review date: 2026-11-03 (Asia/Calcutta).

## Outcome and activation boundary

This batch adds an opt-in quotation-based claim verifier and offline evaluation. It establishes that a cited, authorized source section actually contains the complete quoted claim, preserving negation and qualifiers. It DOES NOT establish source truth, general semantic entailment, unrestricted paraphrase support, or answer completeness. Those limits appear explicitly in the response contract.

All 348 pre-existing files were hash-verified unchanged, including the 15 transferred Phase 1A/1B baseline files and the accepted Batch 2 corpus, questions, judgments, settings and documentation. The worktree remains E:\placement_personal\Projects\CyberShield-AI-cybergpt-2-source-foundation on feature/cybergpt-2-source-foundation, base 2c6bf6879aee47cb6e432c88a1dab8c57fe1de73. Branch/head checks read shared Git metadata; no staging or history changes were made.

No live route, orchestrator, provider, frontend, Docker setting, retrieval default, database schema or migration was changed. No original application file, real database, upload, index, running container or model cache was accessed for data or modified. Tests use system Python and temporary synthetic SQLite/vector storage. No installation, download, commit, push or deployment occurred. LangGraph was not implemented.

## Exact changed files

All nine files are NEW; no existing file was modified:

- backend/app/knowledge/claim_verifier.py
- backend/app/knowledge/grounded_evaluation.py
- backend/evaluation/grounded_answers/review.json
- backend/evaluation/grounded_answers/claim_cases.json
- backend/evaluation/grounded_answers/manifest.json
- backend/tests/test_claim_verifier.py
- backend/tests/test_grounded_evaluation.py
- docs/CYBERGPT_2B_BATCH1.md
- docs/CYBERGPT_2B_BATCH1_RESULTS.json

## Benchmark review before evaluation

All 48 questions were reviewed against the corpus, selected versions and visibility rules before the first Phase 2B evaluation. The accepted Batch 2 files are preserved; a separately hash-pinned overlay records the review and checks the original query/qrel/corpus manifest hashes.

- Nine previously omitted supporting/counterexample judgments were added at grade 1: SQL prepared statements, volatile-memory shutdown warnings, certificate-host mismatch examples, backup restoration warnings and ATT&CK parent-technique context. There are now 65 labels, versus 56 originally.
- H04-2 assumes a Windows/object-oriented-shell-to-PowerShell mapping absent from the actual passages.
- H08-2 asks what changed, but its current-only source view supplies no older hash from which to establish a transition.
- These two held-out questions remain evaluated for citation/refusal behavior but are excluded from required-evidence completion and false-abstention denominators. Both legacy baselines and the new path use the SAME reviewed denominators: 16 development and 15 held-out answerable questions.
- H09-1/H09-2 compare staging and production access policies. Different scopes are not a proven same-scope contradiction; clarification is required. Expected abstention is retained, with a more precise reason.
- The other 35 questions were retained. Review entries, rationales and additions are inspectable in review.json.

This is an agent-performed source/label review, not independent human adjudication. The old held-out set has already been observed; Phase 2B results are diagnostic, not a fresh blind test. Some useful evidence may still be unlabeled. No retrieval model, RRF/MMR parameters or production defaults were tuned in this batch.

## Claim-verification contract

The new code reuses Catalog, canonical collect_evidence, immutable Evidence, DraftAnswer/SupportedClaim, and format_citations.

1. Authorize and validate every retrieved document before using it, including owner, scope, version, source/chunk ID, text hash and canonical content.
2. Reject stale, forged, missing and cross-user evidence before generation. Invalid/foreign records produce no claims, excerpts or guessed citation IDs in the response.
3. Quarantine instruction-like passages before prompt construction; an unrelated malicious chunk no longer automatically poisons an otherwise usable context.
4. Select candidate passages through explicit identifiers, user-requested source authority, named-subject and lexical relevance checks. Positive requests cannot qualify from entity names and explicitly negated topic mentions alone.
5. Treat the model draft as untrusted JSON. Duplicate keys, nonfinite constants, unknown fields, fabricated references, duplicate citations/claims, tool structures and oversized output are refused.
6. Require EACH proposed claim to equal the entire canonical source section and the cited retrieved excerpt. Substrings, arbitrary summaries, omitted negation, changed values and incomplete chunks are rejected. Every additional citation must independently support the whole quotation.
7. Recheck source state after generation and before formatting. Titles, URLs, versions and hashes come from the catalog, never the draft.
8. Render server-framed source quotations, not generated conclusions. Every successful result exposes answer_completeness=not_verified and verification_scope=quotation_attribution_only. The model cannot declare its own support verdict.

Only small complete sections fit this first protocol. Longer sections split across chunks are refused until a larger-context verification policy is validated. Honest private copies remain private and cannot masquerade as official NVD sources; a source text copied verbatim does not establish original organizational authority.

The lexical gate and instruction detector are transparent heuristics, not NLI or complete prompt-injection defenses. The callback receives evidence as data and has no tool-execution interface. The pipeline does not read conversation history, write messages, generate passwords or connect automatically to a provider. Tests use source-only stubs.

## Distinct outcomes

| Status | Meaning |
| --- | --- |
| supported_quotes | Every returned quotation is attributed to a complete authorized retrieved section; completeness/truth remain unverified. |
| insufficient_evidence | No usable evidence, unresolved scope/applicability, incomplete context or unsupported relevance. It does not prove the corpus lacks an answer. |
| retrieval_failure | The caller explicitly reported an error or missing index; absence of evidence has not been established. |
| conflicting_evidence | Narrow detector found different retention values for the same subject/scope; it does not choose the newer source. |
| unsupported_claims | Draft references/text/structure failed verification. No partially verified answer is returned. |
| unverified_evidence | Ownership, provenance or source state could not be validated. |
| unsafe_evidence | Only usable candidate content was instruction-like and excluded. |
| generation_failure | The generator failed; exception details are not echoed. |

Conflict detection is deliberately narrow: same-subject retention statements and explicit unresolved conflict requests. Staging versus production is reported as a context insufficiency, not a logically established contradiction. General conflict/applicability detection remains future work.

## Evaluation protocol and results

All 48 questions use the same fixed Batch 2 hash-hybrid retriever (RRF k=60, MMR lambda=1.0). No tuning occurs. Retrieval receives only question text, actor and source cutoff. The reviewed judgments and expected outcomes enter scoring only.

There are three paths: unchanged legacy first-excerpt stub, legacy with the same all-quotation stub as the new path, and the new verifier with that all-quotation stub. Stubs use ONLY passed source excerpts and citation IDs. No live LLM, new model or provider is used.

### Controlled verifier cases

25 hand-authored scenarios include seven valid quotations and 18 unsupported/unsafe/unavailable cases. All 25 expected outcomes matched: seven accepted, zero false accepts and zero false rejects under the quotation-only protocol. Tests include changed scores, missing negation, partial quotes, wrong/fabricated citations, duplicate fields/claims, false authority, unsafe content, version changes, missing retrieval, conflicts and foreign documents.

This is 100% attribution precision on the seven accepted synthetic quotation scenarios, not a general semantic-entailment accuracy claim.

### Reviewed 48-question diagnostic

| Path | Dev false abstentions | Held-out false abstentions | Dev required evidence | Held-out required evidence |
| --- | ---: | ---: | ---: | ---: |
| legacy_first | 7/16 | 8/15 | 9/22 | 7/21 |
| legacy_same_generator | 7/16 | 8/15 | 11/22 | 9/21 |
| verified_quotes | 0/16 | 6/15 | 17/22 | 12/21 |

The new path preserves all expected abstentions (8/8 development, 7/7 held-out). It covers all required labeled passages for 11/16 development and 8/15 scored held-out questions; this is an oracle coverage check, not a system declaration of a complete answer.

Returned quotation citations are all authorized and valid: 19/19 development and 14/14 held-out. No returned claim fails literal excerpt support, and no incorrect attribution is observed. Two development quotes and one held-out quote remain unjudged for question relevance. They must not be counted as semantically correct answers. General semantic entailment accuracy is explicitly null.

The prototype initially returned irrelevant public plant/crop decoy quotations for two unavailable private-document requests. No private content was returned, but the answers were misleading. A generic relevance correction stopped names and negated topic words from supplying affirmative evidence; an unseen Azure counterexample test protects that behavior. This was a verifier bug fix after observing failures, not evidence of blind generalization. No retrieval tuning or label adjustment hid the failures.

The first focused run also exposed three refusal-taxonomy mistakes: all-unsafe sources were refused but labeled insufficient rather than unsafe. The new code was corrected; no existing test assertion was weakened.

The final evaluation repeats exactly after excluding timing/cost fields. It took approximately 1.27 seconds with zero provider calls, model downloads, network attempts or forbidden file-operation attempts. Different generators or real-model outputs have not been validated.

## Tests and isolation

- Final focused run: 299 passed, two warnings, 19.09 seconds; includes 48 new Phase 2B tests and 251 preserved focused tests.
- Complete backend suite: 507 passed, three failed, zero skipped/errors, ten warnings, 179.61 seconds.
- Full-suite guard denied 162 attempted outbound/DNS operations and recorded zero PostgreSQL attempts. No outbound request was permitted.
- Focused guard recorded zero outbound/PostgreSQL attempts. Existing dedicated guard self-tests intentionally exercise denied operations on synthetic temporary paths.
- The actual mixed-owner hybrid-index tests, configuration tests and threat ownership tests remain unchanged and passed.
- All 348 pre-existing files remain byte-identical. New modules are not imported by live routes/services/agents.

The three failures are unchanged from the accepted Batch 2 environment:

1. test_agent_upgrades.py::TestPasswordSecurityAndPrivacy::test_conversation_title_masks_raw_password_in_new_conversation
2. test_orchestrator.py::TestDispatch::test_a_tool_request_takes_the_tool_path
3. test_evaluation_cases.py::test_index_stamp_tracks_pdf_content_not_timestamp (system Python 3.10 lacks hashlib.file_digest).

The full suite remains red. No failure was hidden, skipped, xfailed or fixed by changing unrelated runtime behavior.

## Python compatibility investigation and minimal proposal (NOT applied)

Existing backend/app/rag/index_meta.py:expected_stamp, line 51, calls hashlib.file_digest. The API was introduced in Python 3.11. The Dockerfile already uses Python 3.12; the dependency-complete system test interpreter is 3.10. A separate installed Python 3.12 lacks backend dependencies. No dependency installation or original virtual-environment access was performed.

Small proposed source change, for a separate approved batch:

    hasher = hashlib.sha256()
    for block in iter(lambda: source.read(1024 * 1024), b""):
        hasher.update(block)
    digest = hasher.hexdigest()

This preserves SHA256 over the same binary bytes with bounded memory, leaves index-stamp schema/version and values unchanged, and should not trigger a rebuild merely for compatibility. Do not bump SCHEMA_VERSION or delete/rebuild any real index. Verify empty, binary, large and mtime-only-change fixtures under Python 3.10 and an approved Python 3.12 environment. Affected files: app/rag/index_meta.py and focused test_evaluation_cases.py additions only.

Primary reference: https://docs.python.org/3/library/hashlib.html#hashlib.file_digest

## Password-routing and generated-secret investigation (HIGH priority, NOT fixed here)

A separate synthetic-only probe used temporary SQLite, a fixed noncredential marker, fake provider callbacks and no production connections. It printed only booleans/counts, never generated values, prompts or tokens. The results confirm:

- Immediate password-generator output contains its value, as intended.
- The same value is persisted in assistant conversation history.
- A later document-answer prompt includes that stored value.
- The capitalized generation verb is falsely extracted as a password.
- Masking that verb produces a title request which triggers one redundant model classification.
- A strength question lacking the literal word password can leave an actual credential-like token unextracted and unmasked.

Affected paths and causes:

| File/function | Finding |
| --- | --- |
| app/agents/router.py:extract_password | Topic-gated fallback misses no-keyword strength questions; mixed-case fallback mistakes a capitalized generation verb for a credential. |
| app/agents/tools.py:redact_secrets | Depends on that extractor; missing candidates remain unmasked. |
| app/services/rag_service.py:_resolve_conversation | Reclassifies an already sanitized title with LLM fallback enabled. |
| app/agents/tools.py:password_generate | Both display answer and metadata contain the generated value. Immediate authorized display is intentional. |
| app/agents/orchestrator.py:_tool | Persists result.answer verbatim, including the generated password. |
| app/services/rag_service.py:_history / _document_answer | Loads saved assistant content and places it in the next model prompt. |

The title-mask failure and unexpected-classifier-call failure are therefore confirmed code-path defects, not failures introduced by this verifier.

Proposed minimal next SECURITY batch:

1. Add a safe history representation to ToolResult (for example history_answer). password_generate supplies a constant value-free summary. _tool stores only that summary for sensitive outputs while preserving the immediate authorized display and existing response format.
2. Never use provider classification for title sanitization: use deterministic secret detection and/or allow_llm=False in _resolve_conversation. Keep intent dispatch based on the original request.
3. Separate candidate-secret recognition from intent routing. Exclude ordinary generation verbs; cover explicit credential/strength contexts before any provider call, including no-password-keyword cases. Add adversarial privacy tests rather than only adding one stopword.
4. Add a read-time safeguard for legacy generated-password messages before history enters any model prompt. This does not erase old database values; reliable legacy handling and any cleanup/rotation need separate user-approved policy.
5. Add synthetic tests asserting immediate display, absence from stored user/assistant turns and titles, absence from future classifier/RAG prompts, no redundant generation classification, and cross-user denial.

No account password policy, hashing scheme, authentication route, schema or user record was changed. Existing generated values may already be stored or previously sent to providers; the new quotation pipeline does not remedy that. No real history was inspected or deleted. No secret was generated/rotated for an actual account. This confirmed exposure is a blocker for live integration and should take priority over further retrieval tuning.

## Reproduction and review artifacts

From the isolated backend:

    python -B -m app.knowledge.grounded_evaluation

Focused tests:

    python -B -m pytest -p no:cacheprovider tests/test_claim_verifier.py tests/test_grounded_evaluation.py tests/test_retrieval_quality.py tests/test_quality_worker.py tests/test_source_foundation.py tests/test_source_benchmark.py tests/test_configuration.py tests/test_rag_visibility.py tests/test_threat_ownership.py tests/test_tools.py::TestCveLookup -q

For full-suite validation use the offline guard, not an unguarded invocation: existing tests attempt network operations. This session used C:\Users\moham\AppData\Local\Temp\cybershield-2b-batch1-_payhsbq\isolated_tests.py. The same directory holds all-source before hashes, focused/full XML, initial/final evaluation JSON, the synthetic security probe and its boolean-only result.

The repository JSON results are deliberately compact; raw per-question results stay in the artifact directory. The reviewed data are original synthetic CC0 fixtures plus the unchanged selected-field official NVD sample from Batch 1.

## Remaining risks and next review

- Free-form paraphrases, cross-passage deductions, factual truth and general contradiction detection are not verified. Complete-section quotations provide a bounded attribution guarantee only.
- Relevance filtering and injection detection are heuristic. Some quoted evidence is still unjudged or may not answer the full request. Long-section/context validation remains deferred.
- The existing held-out set is reused and now reviewed; independent adjudication and a fresh blinded set are still needed.
- The in-memory catalog is not a concurrent serving permission-revocation system. A trusted authenticated actor must be provided by any future integration.
- The generated-password history/prompt exposure remains unresolved and high priority; the full suite and local ownership-migration prerequisites remain unresolved.
- Production integration, defaults, migrations and LangGraph remain disabled/unmodified.

Stop after this batch. Recommended next approval: the minimal generated-password privacy/routing remediation and compatibility patch, then independently validate a stronger claim-entailment policy before any live answer-pipeline integration.
