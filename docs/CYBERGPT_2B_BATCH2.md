# CyberGPT 2.0 — Phase 2B Batch 2

Validation date: 2026-11-04. Isolated worktree: E:/placement_personal/Projects/CyberShield-AI-cybergpt-2-source-foundation. Branch: feature/cybergpt-2-source-foundation. HEAD remains 2c6bf6879aee47cb6e432c88a1dab8c57fe1de73. No commits or staged changes.

## Scope and result

Part A passed its privacy/compatibility gate before Part B. Final complete offline suite: 558 passed, zero failures/errors/skips. The three previously failing tests now pass without changing their assertions. The new answer selector is opt-in and offline; production retrieval defaults, answer-pipeline integration, source fixtures and relevance labels are unchanged. Requested privacy protections change transcript handling, as described below.

No original application files, running containers, real databases, uploads, existing indexes or model caches were used or changed. No migration, dependency installation, download, secret rotation, database rewrite or deployment was performed.

## Part A: privacy boundaries

- Password generation still uses the existing local cryptographic generator and returns the value in the immediate authorized tool answer and UI metadata. It requires a positive authenticated user ID. The orchestrator verifies conversation ownership before dispatch and stores a constant value-free summary through ToolResult.history_answer.
- A single deterministic helper recognizes explicit credential values, quotes, strength questions and generator-shaped pasted values. Unicode normalization and format-character removal apply only to detection; analysis receives the original value. Supplied credentials preempt unrelated CVE/URL tools and model classification. All detected values are redacted from titles and stored user questions. Generation verbs are stopwords, fixing the capitalized-generation routing bug.
- Title routing explicitly disables model classification. Tool input receives the sanitized question; the analysis decision retains its value only for local scoring. Existing logging records routing enums/confidence, not content. Password-bearing schema/dataclass representations hide values; response JSON remains compatible.
- New assistant persistence replaces generated-password formats and password-topic model replies with value-free summaries. Standalone explanations redact submitted values; findings prompts include counts instead of matched dictionary/pattern strings, whitelist enums/numbers, and use fixed fallback advice.
- Legacy database rows are neither deleted nor rewritten. Both RAG prompt-history construction and follow-up query augmentation use ONLY a finite set of fixed topic labels. If any message in the conversation is credential-related, both omit historical context, including when that message is older than the last-eight window. Arbitrary historic text and embedded instructions never enter these two outbound paths.

Compatibility tradeoff: detailed conversational recall is reduced to coarse topic labels, and credential conversations lose history context entirely. The authenticated history UI still displays unchanged legacy rows. This is a conservative boundary because deterministic regexes cannot reliably identify every arbitrary secret in prose. New input recognition is heuristic and can over-redact technical tokens; it is not universal DLP. This work does not remediate historical disclosures to external systems or control external reverse-proxy/body logging. No such systems were accessed.

Authentication hashes, account password-length rules, SQL schema, frontend response format and Docker settings are unchanged. No account/data migration is required for these edits. The prior unapplied threat-search ownership migration remains a separate local-integration prerequisite; it was not applied.

## Part A: Python compatibility

index_meta.expected_stamp now streams files through hashlib.sha256().update() in 1 MiB blocks instead of hashlib.file_digest (introduced in Python 3.11). Empty, binary and multi-block fixtures match the original digest contract on Python 3.10 without that API. Schema version stays 4; no indexing algorithm or rebuild policy changes.

Previously failing nodes, all now passing:

1. test_agent_upgrades.py::TestPasswordSecurityAndPrivacy::test_conversation_title_masks_raw_password_in_new_conversation
2. test_orchestrator.py::TestDispatch::test_a_tool_request_takes_the_tool_path
3. test_evaluation_cases.py::test_index_stamp_tracks_pdf_content_not_timestamp

Privacy regressions cover authorized immediate generation, repeated requests, upper/fullwidth/zero-width generation wording, spaces and Unicode in submitted values, punctuation, no-keyword strength questions, misleading legacy titles, old messages outside the history window, adversarial URL/CVE requests, prompt instructions, multiple values, cross-user rejection, repr/log output, and derived findings. Only synthetic secrets are used.

## Part B: diagnosis and development-only selection

The same 48 questions, reviewed 65-label overlay, 49 current records and 50 public passages are reused. There are 24 development and 24 held-out questions. Completion scoring still excludes the two ambiguous held-out cases, leaving 16 development and 15 held-out answerable cases. No qrels/corpus edits were made; labels stay outside retrieval_request inputs.

Inspection of the six old held-out abstentions found relevant passages already present in the retrieved candidate lists:

| Case | Diagnosis | Result with locked selector |
| --- | --- | --- |
| H04-1 | Exact T1059.001 found; baseline still required two extra lexical matches | Accepted complete technique quote |
| H06-1 | Long extortion/recovery paraphrase has sparse lexical overlap despite H-RESTORE/Test retrieval | Still abstains; not fixed using held-out-specific rules |
| H06-2 | Backup isolation and restoration wording differs from offline/immutable/test phrasing | Still abstains; no topic-specific synonym mapping added |
| H07-1 | Derivation/derives and SHA/hash notation mismatch | Quotes historical section |
| H07-2 | Same superficial mismatch in an as-of question | Quotes historical section |
| H08-1 | SHA notation lacks the literal token hash | Quotes current section |

These are principally evidence-selection failures, not an absent-candidate retrieval failure or a reason to alter judgments. Existing H04-2/H08-2 ambiguity exclusions and H09 historical deployment qualification remain unchanged.

The explicit SelectionPolicy recognizes SHA notation and five-character inflection prefixes. Non-CVE exact identifier matches can pass without additional generic words. The original identifier, named scope, year, owner, provenance/version, negation, conflict and complete-section quote checks still run. Neither normalized tokens nor labels become answer facts. The selector can choose topically imperfect quotes; literal quotation is not proof of semantic relevance or correctness.

Candidate overlap fractions 0.25 and 0.0 are evaluated on development only. Both satisfy development safety/coverage equally; the predeclared tie rule selects stricter 0.25. Policy selection completes before held-out retrieval/scoring. No held-out-specific tuning or thresholds were added. The two remaining backup paraphrases are retained as limitations. Topic-specific synonym mappings considered during diagnostics were removed before the final run; the final policy was frozen before re-evaluation.

## Grounded-answer results

| Split | Required coverage, baseline → opt-in | False abstentions, baseline → opt-in | Complete required evidence, baseline → opt-in | Valid citations, opt-in |
| --- | --- | --- | --- | --- |
| Development | 17/22 (77.3%) → 18/22 (81.8%) | 0/16 → 0/16 | 11/16 → 12/16 | 20/20 |
| Held-out | 12/21 (57.1%) → 16/21 (76.2%) | 6/15 (40.0%) → 2/15 (13.3%) | 8/15 → 12/15 | 19/19 |

Expected safe abstentions remain 8/8 development and 7/7 held-out. Zero unsupported literal excerpts or incorrect attributions were observed. Two development and one held-out returned quotes remain unjudged for question relevance; semantic entailment accuracy remains null. Citation validity means authorized resolution plus exact attributed text, not a claim of 100% answer correctness. Missing qualifiers, fabricated IDs, conflicting sources, stale versions, wrong ownership/attribution, unsupported claims and malicious source instructions are covered by new and existing verifier tests.

This is a small synthetic diagnostic set reviewed by the same agent, with previously inspected held-out examples. It is not a fresh blind or independent human evaluation. Exact quotations remain the baseline; no unrestricted paraphrasing or live model generation was introduced.

## Retrieval benchmark regression

All seven hash-based modes exactly reproduce accepted Phase 2A Batch 2 ranking/evidence/abstention metrics: BM25, FAISS/hash, hybrid, hybrid+MMR, source-aware hybrid, tuned hybrid and tuned hybrid+MMR. Timing is excluded from equality checks. The original 16-question benchmark also ran; Recall@5 remains 1.0 in all four modes (hybrid MRR 0.954545, nDCG@5 0.966448). These retrieval outputs use their original qrels, distinct from the reviewed answer-completion overlay.

48-question held-out retrieval metrics, unchanged:

| Mode | Recall@5 | Precision@5 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.952381 | 0.257143 | 0.920635 | 0.914361 |
| FAISS/hash | 0.904762 | 0.238095 | 0.845238 | 0.832832 |
| Hybrid / hybrid+MMR / source-aware / tuned variants | 0.952381 | 0.257143 | 0.944444 | 0.917622 |

No semantic model/cross-encoder or model cache was accessed. Hash dimensions and retrieval defaults remain unchanged. Two answer-evaluation runs produced identical non-cost JSON, including per-question results.

## Validation and reproducibility

System CPython 3.10.0; faiss-cpu 1.9.0.post1, NumPy 1.26.4, Pydantic 2.12.5, rank-bm25 0.2.2. No installs. Hash-only CPU evaluation, seed 1729 inherited from the existing benchmark. Answer evaluation: 1.282 s wall / 0.969 s CPU. Retrieval benchmark: 2.317 s wall / 2.031 s CPU, peak process RSS 84,209,664 bytes, temporary index 164,175 bytes. These are local synthetic costs, not production latency.

| Executed group | Passed | Failed/errors/skipped | Time |
| --- | ---: | --- | --- |
| Final Part A privacy/routing/compatibility gate | 94 | 0/0/0 | 10.49 s pytest (10.743 s JUnit) |
| Part B citation/evidence/security/foundation group | 307 | 0/0/0 | 16.34 s pytest (16.592 s JUnit), 2 warnings |
| Complete backend suite, final guarded run | 558 | 0/0/0 | 45.72 s pytest (45.970 s JUnit), 11 warnings |

The complete suite includes all old assertions and all new tests; nothing was skipped or xfailed. Guards block outbound DNS/sockets and PostgreSQL and restrict SQLite to synthetic temporary storage outside the worktree. Existing conftest supplies test settings, hash embeddings and isolated upload/vector paths. Every successful final test run reports zero outbound/PostgreSQL attempts. The quality workers independently report zero network/forbidden-file operations.

Some legacy unit tests implicitly invoked a configured provider without requesting their existing stub fixture. The temporary runner supplies that fixture only to test_orchestrator.py, test_rag_service.py and test_agent_upgrades.py, except explicit failing_llm tests; the Part A gate supplies it throughout. Tests already requesting stub_llm receive the same instance and retain call-count assertions. This is offline unit validation, not live-provider or PostgreSQL integration validation.

Artifacts and exact runner are retained outside the repository at C:/Users/moham/AppData/Local/Temp/cybershield-2b-batch2-lry_qxnj. Run from the isolated worktree using system python (not the original virtualenv):

    python -B <artifact-dir>/isolated_tests.py <worktree> part-a-gate-offline test_password_privacy.py test_hash_compatibility.py test_router.py test_orchestrator.py::TestDispatch test_orchestrator.py::TestPersistence test_agent_upgrades.py::TestPasswordSecurityAndPrivacy test_evaluation_cases.py::test_index_stamp_tracks_pdf_content_not_timestamp

    python -B <artifact-dir>/isolated_tests.py <worktree> part-b test_answer_selection.py test_claim_verifier.py test_grounded_evaluation.py test_configuration.py test_quality_worker.py test_rag_visibility.py test_retrieval_quality.py test_source_benchmark.py test_source_foundation.py test_threat_ownership.py test_tools.py::TestCveLookup

    python -B <artifact-dir>/isolated_tests.py <worktree> full-offline .

From backend with PYTHONPATH set to that backend, the existing self-isolating workers were executed:

    python -B -m app.knowledge.evaluation
    python -B -m app.knowledge.quality_evaluation
    python -B -m app.knowledge.answer_improvement_evaluation

Initial diagnostics were not clean: missing provider stubs caused blocked network attempts; automatically generated multi-megabyte hash-fixture IDs caused three setup errors; an attempted fixture-setup hook caused lifecycle errors. The temporary harness was corrected and explicit small parameter IDs added; no old test assertion was weakened. Final clean results above supersede those diagnostic runs. Final boundary review also found a comma/period detection gap. Seven punctuation cases were added; a resulting Unicode-substring precedence regression was caught by an unchanged existing assertion and fixed by prioritizing explicit original values. The final privacy gate and complete suite both pass. Existing deprecation warnings remain.

## Exact files changed in this batch

Compared against the 357-file pre-batch SHA256 inventory, 11 existing files changed:

- backend/app/agents/orchestrator.py
- backend/app/agents/router.py
- backend/app/agents/tools.py
- backend/app/knowledge/claim_verifier.py
- backend/app/knowledge/grounded_evaluation.py
- backend/app/rag/index_meta.py
- backend/app/schemas/copilot_schema.py
- backend/app/schemas/password_schema.py
- backend/app/services/conversation_service.py
- backend/app/services/password_service.py
- backend/app/services/rag_service.py

Eight new files:

- backend/app/core/credential_privacy.py
- backend/app/knowledge/evidence_selection.py
- backend/app/knowledge/answer_improvement_evaluation.py
- backend/tests/test_password_privacy.py
- backend/tests/test_hash_compatibility.py
- backend/tests/test_answer_selection.py
- docs/CYBERGPT_2B_BATCH2.md
- docs/CYBERGPT_2B_BATCH2_RESULTS.json

All other inventoried files remain byte-identical, including previous tests, reviewed fixtures, source registry, owner-scoped threat routes/CRUD and fail-closed retrieval implementation. The machine-readable report includes pre/post hashes for modified files and complete benchmark/answer results. Git diff against HEAD also includes accepted uncommitted earlier batches; that is not the delta for this batch.

## Review boundary

Part A observed privacy regressions are closed in isolated tests. Historical stored secrets remain in the authenticated history UI by explicit non-rewrite policy; any cleanup or rotation requires separate approval. Part B remains an offline opt-in prototype with lexical relevance limitations, incomplete judgments and two false abstentions. No live answer-pipeline integration is recommended yet. Stop for review; no LangGraph work started.

Community context: Nicholas Flemmer's DEV article, Keeping secrets out of an AI chat log: what I do and where it falls short (https://dev.to/nicholasflemmer/keeping-secrets-out-of-an-ai-chat-log-what-i-do-and-where-it-falls-short-982), reinforces that pattern scrubbing has limits. The conservative fixed-label history boundary above is verified by repository tests; the article is context, not validation.
