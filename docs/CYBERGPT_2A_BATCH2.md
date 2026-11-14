# CyberGPT 2.0 Phase 2A Batch 2: retrieval quality and evaluation hardening

## Scope and isolation

Worktree: E:\placement_personal\Projects\CyberShield-AI-cybergpt-2-source-foundation  
Branch: feature/cybergpt-2-source-foundation  
Base: 2c6bf6879aee47cb6e432c88a1dab8c57fe1de73

Batch 1 was inspected and reused. Its baseline manifest's 15 transferred Phase 1A/1B files were hash-verified in this worktree. The original CyberShield-AI directory was neither used as an interpreter/package source nor accessed for source, environment, data, indexes or model caches in Batch 2. A system Python interpreter and public pretrained-model cache outside both repositories were used instead.

All changes are offline/opt-in. No route, agent, frontend, Docker setting, embedding default, production index, dependency, migration, database or live service was changed. VITE_API_URL=/api and all transferred ownership/fail-closed security source changes remain byte-identical. The ownership migration remains unapplied. No commit, push, deployment, package installation, Docker operation or LangGraph implementation occurred.

The only existing Batch 1 file modified is backend/app/knowledge/ingestion.py. Its new read-only snapshot method is unused by live application routes. All other Batch 1 files and all earlier uncommitted source changes were preserved.

## Exact file changes

Modified:

- backend/app/knowledge/ingestion.py: explicit source-time snapshot views and read-only admission guard; default current-version resolution is unchanged.

Added:

- backend/app/knowledge/quality_dataset.py: separated corpus/label loading, pinned judgments, dataset checks, stripped retrieval requests, opt-in identifier-aware ordering.
- backend/app/knowledge/quality_metrics.py: passage metrics and citation/excerpt/attribution audits.
- backend/app/knowledge/quality_evaluation.py: isolated worker, cached semantic/cross-encoder comparisons, development-only tuning, metrics and resource accounting.
- backend/evaluation/retrieval_quality/corpus.json
- backend/evaluation/retrieval_quality/history.json
- backend/evaluation/retrieval_quality/updates.json
- backend/evaluation/retrieval_quality/queries.json
- backend/evaluation/retrieval_quality/qrels.json
- backend/evaluation/retrieval_quality/manifest.json
- backend/evaluation/retrieval_quality/README.md
- backend/tests/test_retrieval_quality.py
- backend/tests/test_quality_worker.py
- docs/CYBERGPT_2A_BATCH2.md
- docs/CYBERGPT_2A_BATCH2_RESULTS.json

The JSON result document is a deliberately retained compact validation artifact. Full per-query reports and pytest XML remain outside Git in the session artifact directory listed below. No generated vector index or model weights were added to the repository.

## Benchmark design and review limits

The corpus is original synthetic CC0-1.0 material plus Batch 1's unchanged selected-field NVD CVE-2021-44228 fixture. Fictional CVEs, scores and organization-specific policies are not security advice. No third-party prose or model weights are redistributed.

The fixed dataset contains:

- 48 questions, 24 development and 24 held-out, in 24 declared topic families.
- 56 positive passage judgments: 27 development, 29 held-out.
- 16 questions requiring multiple passages, including complementary controls and conflicting reports.
- 33 answerable questions and 15 expected abstentions: 16/8 development, 17/7 held-out.
- 40 questions with labeled relevant evidence; 8 empty-gold cases. Seven nonempty-gold cases deliberately require abstention for malicious/conflicting evidence.
- 49 current record entries: 45 active public records, two private records and two inactive tombstones. There are 50 current public passages and two private passages, with four superseded versions retained (53 total known record versions).
- Two historical questions in each split. Historical cutoffs reduce the visible corpus to four known old records; these are useful correctness checks but relatively easy retrieval cases.

Questions cover exact/overlapping CVEs and ATT&CK identifiers, paraphrases, SQL values versus identifiers, phishing-resistant factors, containment and volatile evidence, browser cookies versus CSRF, TLS identity checks, ransomware backup restoration, misleading titles, conflicting guidance, historical policies, superseded/withdrawn/deleted records, irrelevant material, private owner/other-user counterfactuals, missing facts and source prompt injection.

Corpus, queries and judgments are separate pinned files. Only corpus files enter chunking/indexing. Retrieval accepts ONLY question text, actor and explicit source cutoff: IDs, split, expected abstention, gold labels and tags are removed at the call boundary. They are also absent from generator prompts and reranker inputs. Tests verify this and reject cross-split family/duplicate-query leakage and altered judgment hashes.

Fixtures and labels were authored and checked in a separate source-to-label consistency pass before ranking. Independent human/domain review has NOT occurred. Family groups and entities differ between splits, but security concepts and synthetic authoring patterns are shared; this is not a blind external generalization test. Some unlabeled partial/paraphrased evidence may be useful. Absence of a ranking label is treated as zero relevance under this small closed-world benchmark, while unannotated answer claims remain unjudged rather than being declared semantically false. Independent label-completeness review is needed.

The dataset and tuning grid were frozen before the first held-out run. The manifest SHA256 remained identical in every subsequent run. No data, labels or tuning grid were revised based on held-out scores.

## Retrieval and source-aware behavior

The evaluator reuses existing BM25 tokenization/ranking, FAISSStore, EmbeddingService.hash_vectors, HybridRetriever query expansion, RRF, blended reranking, relevance floors, page deduplication and MMR. The benchmark-only semantic adapter supplies normalized local encoder vectors to the same FAISS/hybrid path. It prohibits silent hash fallback for invalid semantic vectors.

Every mode uses the same question set, corpus snapshot, labels and visibility rules. Catalog authorization filters documents before indexing; separate actor/cutoff contexts and embedding spaces prevent cache mixing. Canonical evidence is checked after retrieval, fusion and reranking. Existing mixed-owner-index tests additionally test the actual hybrid retriever against foreign, legacy and ambiguous metadata.

The identifier-aware variant reorders up to 20 authorized hybrid candidates using exact identifiers from canonical source records. It distinguishes overlapping IDs and does not infer authority from supplied document metadata. It applies no generic trust or recency bonus: an official organization is not proof of truth, and a later retrieval/modification date is not proof of applicability. This variant is opt-in and not wired to runtime.

Current queries still expose only latest active versions. An explicit timezone-aware source cutoff creates a read-only view of the latest KNOWN modification versions at/before that date; withdrawn/deleted versions remain excluded if their tombstone was effective by the cutoff. A record active before later withdrawal can be examined only in an explicit historical view. The view preserves exact ownership, source IDs, versions and dates.

This is source-modification-time selection, not a claim that our system possessed the record then or that its publication date equals its effective date. A current NVD record published in 2021 but only observed in a 2026 revision is not invented as a historical 2024 snapshot. No retroactive facts are inferred. Historical applicability/effective-date modeling and live permission revocation remain future serving concerns.

## Models and selection protocol

Seed: 1729 for Python/NumPy/Torch determinism. Split assignment is fixed by family, not randomized by the seed.

Both real models were already available in the system Hugging Face cache outside the original repository. They are loaded by explicit snapshot path, on CPU, with local_files_only=True, trust_remote_code=False and token=False. Only safetensors snapshots are considered. Network is denied; no download, install or cache write is allowed.

- sentence-transformers/all-MiniLM-L6-v2, revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41, 384 dimensions.
- cross-encoder/ms-marco-MiniLM-L-6-v2, revision 233902d25c440f23af6f7d6e94d2946bac0bee0a, reranking up to 20 authorized semantic-hybrid candidates.

Selected model/config/tokenizer files are SHA256-stamped in the JSON results. These models share a family with the existing MiniLM deployment setup; this is not a comparison against every stronger encoder or a switch of the runtime FastEmbed backend.

The fixed development grid is RRF k in [60,10,100] and MMR lambda in [0.85,0.65,1.0], nine configurations per backend. Configuration selection accepts development questions and exactly their judgments; held-out data is rejected. Selection maximizes development nDCG@5, then Recall@5, then MRR, with stable default-first ties. All other retrieval weights/floors remain unchanged in the disposable worker.

Hybrid lambda 1.0 removes the diversity penalty but retains page deduplication. The lambda 0.85 rows retain current MMR behavior. Source-aware and cross-encoder rows use the selected development configuration; neither is tuned on held-out results. They use a top-20 candidate stage, so comparisons measure complete pipeline variants, not an isolated rescaling of five results.

Selected configurations:

- Hash: RRF k=100, lambda=1.0.
- Semantic: RRF k=60, lambda=1.0.

Development selected no diversity penalty in both spaces. No runtime default was changed.

## Scoring definitions

The unit is an authorized source ID + record ID + section in the chosen version, not a whole record or repeated overlapping chunk. Labeled sections are shorter than a single chunk, and exact judgment quotes detect wrong-version labels.

All committed positive labels are grade 2 (required direct evidence); grade 1 support is supported and unit-tested but not used to imply finer human judgments in this fixture set. nDCG supports 2**grade-1 gain; with this dataset it reduces to equally weighted positive relevance. Recall/Precision/MRR use binary relevance. Precision always divides by five, even if fewer results survive. MRR is truncated at five. Empty-gold questions are excluded from retrieval means and remain in abstention metrics. Retrieval means therefore use 19 development and 21 held-out questions.

all_required_at_5 reports complete required passage coverage, including multi-hop cases; it is not answer correctness. Generated evidence coverage is reported both over all labeled cases and over answerable questions only, so required abstentions do not silently lower an unexplained denominator.

## Development results

| Mode | Recall@5 | Precision@5 | MRR | nDCG@5 | All required@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| hash_bm25 | 0.9474 | 0.2632 | 1.0000 | 0.9551 | 0.8947 |
| hash_faiss | 0.8684 | 0.2316 | 0.8789 | 0.8350 | 0.7895 |
| hash_hybrid | 0.8947 | 0.2421 | 0.9474 | 0.8830 | 0.7895 |
| hash_hybrid_mmr | 0.8421 | 0.2211 | 0.9474 | 0.8423 | 0.6842 |
| hash_source_aware | 0.8947 | 0.2421 | 0.9737 | 0.8949 | 0.7895 |
| hash_tuned_hybrid | 0.8947 | 0.2421 | 0.9737 | 0.8949 | 0.7895 |
| hash_tuned_hybrid_mmr | 0.8947 | 0.2421 | 0.9737 | 0.8949 | 0.7895 |
| semantic_cross_encoder | 0.9474 | 0.2632 | 0.9386 | 0.9051 | 0.8947 |
| semantic_faiss | 0.9474 | 0.2737 | 0.8947 | 0.8978 | 0.9474 |
| semantic_hybrid | 0.9474 | 0.2632 | 0.9737 | 0.9249 | 0.8947 |
| semantic_hybrid_mmr | 0.9211 | 0.2526 | 0.9737 | 0.9046 | 0.8421 |
| semantic_source_aware | 0.9474 | 0.2632 | 0.9737 | 0.9249 | 0.8947 |
| semantic_tuned_hybrid | 0.9474 | 0.2632 | 0.9737 | 0.9249 | 0.8947 |
| semantic_tuned_hybrid_mmr | 0.9474 | 0.2632 | 0.9737 | 0.9249 | 0.8947 |

## Held-out results

| Mode | Recall@5 | Precision@5 | MRR | nDCG@5 | All required@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| hash_bm25 | 0.9524 | 0.2571 | 0.9206 | 0.9144 | 0.9048 |
| hash_faiss | 0.9048 | 0.2381 | 0.8452 | 0.8328 | 0.8571 |
| hash_hybrid | 0.9524 | 0.2571 | 0.9444 | 0.9176 | 0.9048 |
| hash_hybrid_mmr | 0.9524 | 0.2571 | 0.9444 | 0.9176 | 0.9048 |
| hash_source_aware | 0.9524 | 0.2571 | 0.9444 | 0.9176 | 0.9048 |
| hash_tuned_hybrid | 0.9524 | 0.2571 | 0.9444 | 0.9176 | 0.9048 |
| hash_tuned_hybrid_mmr | 0.9524 | 0.2571 | 0.9444 | 0.9176 | 0.9048 |
| semantic_cross_encoder | 0.9762 | 0.2667 | 0.9444 | 0.9305 | 0.9524 |
| semantic_faiss | 0.9524 | 0.2667 | 0.7937 | 0.8319 | 0.9524 |
| semantic_hybrid | 0.9762 | 0.2667 | 0.9143 | 0.9161 | 0.9524 |
| semantic_hybrid_mmr | 0.9524 | 0.2571 | 0.9143 | 0.9015 | 0.9048 |
| semantic_source_aware | 0.9762 | 0.2667 | 0.9524 | 0.9453 | 0.9524 |
| semantic_tuned_hybrid | 0.9762 | 0.2667 | 0.9143 | 0.9161 | 0.9524 |
| semantic_tuned_hybrid_mmr | 0.9762 | 0.2667 | 0.9143 | 0.9161 | 0.9524 |

Semantic FAISS improves held-out Recall over hash FAISS but has lower MRR. Default semantic MMR loses recall relative to semantic hybrid without a diversity penalty. Development tuning selects lambda 1.0 and avoids that loss. Identifier-aware semantic ordering has the best nDCG in this small held-out set; cross-encoding also helps ranking but costs much more. None of these differences establishes production accuracy or justifies changing a runtime default.

## Citation, attribution and abstention results

Every citation is resolved against authorized retrieved records. Draft output cannot introduce source URLs or citation IDs. The unchanged Batch 1 exact-excerpt contract rechecks catalog state after generation. A deterministic first-excerpt stub is used; NO real LLM answer quality is measured.

The audit distinguishes:

- Invalid citation references.
- Text not present in cited excerpts (objectively unsupported excerpt).
- An annotated quote assigned to a different authorized source (incorrect attribution).
- An exact source quote not covered by answer judgments (unjudged, not proven false).
- Relevant cited-passage coverage and complete required retrieval coverage.

Tests detect fabricated IDs, foreign private evidence, unsupported text, and a copied exact quotation incorrectly attributed to a private duplicate rather than the judged source. Malicious retrieved instructions never authorize tools; no tool executor is present. Conflicting source passages remain available for inspection, while conflict-resolution answers abstain rather than guessing.

Held-out results (17 answerable questions, seven expected abstentions):

| Mode | Citation validity | Answerable evidence coverage | Unjudged claims | Correct expected abstentions | False abstentions |
| --- | ---: | ---: | ---: | ---: | ---: |
| hash_bm25 | 1.000 | 0.391 | 2 | 7/7 | 6/17 |
| hash_faiss | 1.000 | 0.304 | 0 | 7/7 | 10/17 |
| hash_hybrid_mmr | 1.000 | 0.348 | 0 | 7/7 | 9/17 |
| semantic_faiss | 1.000 | 0.304 | 3 | 7/7 | 7/17 |
| semantic_tuned_hybrid_mmr | 1.000 | 0.348 | 1 | 7/7 | 8/17 |
| semantic_source_aware | 1.000 | 0.348 | 1 | 7/7 | 8/17 |
| semantic_cross_encoder | 1.000 | 0.304 | 1 | 7/7 | 9/17 |

All returned claims have valid references and exact supporting excerpts; observed unsupported-excerpt and incorrect-attribution counts are zero for the stub. Synthetic adversarial tests separately prove that incorrect references/attributions are detected. Semantic unsupported-claim rate is explicitly null/unmeasured.

False abstentions remain substantial. A malicious passage anywhere in a five-passage context may cause conservative abstention. Lexical sufficiency gates reject paraphrases and the first-excerpt stub cannot synthesize multi-hop answers. A source-supported quotation may still fail to address the question. High retrieval recall and valid citations do not remove these answer-quality gaps.

## Performance and resource costs

These are single-host observations, not controlled throughput measurements. Queries use warm cached vectors for ranking timings; cold text encoding and index construction are recorded separately. Cross-encoder inference is included in its ranking latency. Filesystem/OS caches and concurrent host activity affect timing, and model-import time dominates short runs.

Final run: 44.80s wall, 43.83s process CPU; peak process RSS 851.4 MiB. Earlier same-metric runs took 40.49s and 23.94s. The peak includes both loaded models and interpreter/library overhead, not just model tensors.

| Mode | Held-out mean warm ranking (ms) | p95 (ms) |
| --- | ---: | ---: |
| hash_bm25 | 0.459 | 0.792 |
| hash_faiss | 0.071 | 0.092 |
| hash_hybrid_mmr | 3.751 | 5.051 |
| semantic_faiss | 0.144 | 0.305 |
| semantic_tuned_hybrid_mmr | 4.747 | 7.493 |
| semantic_source_aware | 5.526 | 8.197 |
| semantic_cross_encoder | 251.050 | 490.344 |

Two locally cached model snapshots total approximately 174.4 MiB in the selected stamped files. They were read, not copied or downloaded. The semantic engine encoded 122 distinct texts in 2.520s and scored 547 cross-encoder pairs. Each embedding backend used six authorized actor/source-time contexts. The disposable worker's on-disk temporary footprint at the end totaled 164175 bytes and was removed with the worker's own temporary directory. The JSON field temporary_index_bytes includes any library scratch files and is therefore an upper bound on index storage.

Torch CPU threads are two; FAISS uses its installed library default. An attempted explicit FAISS OpenMP thread override caused an Intel/LLVM OpenMP conflict in this preinstalled environment. That evaluator-only override was removed; no KMP_DUPLICATE_LIB_OK workaround or dependency change was used. Successful repeated runs have identical rankings and audits. Native runtime compatibility and memory use must be reviewed before any serving integration; a roughly 850 MiB evaluation process is not evidence of suitability for a small deployment tier.

## Validation and compatibility

Final focused run: 251 passed, two warnings, 18.92 seconds. This includes 48 new Batch 2 tests, 87 Batch 1 source tests, 36 configuration tests and 80 ownership/visibility/CVE-tool tests. The focused session guard recorded zero outbound/DNS/PostgreSQL attempts. Benchmark subprocess guards also recorded zero network or forbidden file-operation attempts; guard self-tests reject four synthetic external file mutations and one loopback connection attempt without performing them.

The initial offline-test harness misidentified Python 3.10's stdlib asyncio loopback socket pair as outbound traffic: 235 passed, three failed, eight setup errors. Only the temporary harness was corrected to allow exact stdlib socketpair frames on loopback; application assertions and test code were not weakened. The next run passed 246 tests; additional guard/label tests brought the count to 251.

A full-suite checkpoint on system Python 3.10.0 ran 461 tests: 458 passed, three failed, ten warnings, 172.64 seconds. The guard denied 162 attempted outbound operations; zero PostgreSQL attempts. No connection was permitted.

The two existing failures remain:

- test_agent_upgrades.py::TestPasswordSecurityAndPrivacy::test_conversation_title_masks_raw_password_in_new_conversation
- test_orchestrator.py::TestDispatch::test_a_tool_request_takes_the_tool_path

The additional failure is:

- test_evaluation_cases.py::test_index_stamp_tracks_pdf_content_not_timestamp: existing app/rag/index_meta.py uses hashlib.file_digest, introduced in Python 3.11; the available dependency-complete system environment is Python 3.10.

The existing backend Dockerfile already uses Python 3.12-slim. A system Python 3.12.10 interpreter is installed, but it lacks pytest/FastAPI/SQLAlchemy/FAISS and other backend dependencies. Nothing was installed, no original virtual environment was accessed, and existing index code/tests were not patched to conceal the mismatch. A complete suite in an approved dependency-complete Python 3.12 environment remains an integration prerequisite.

Final full-suite rerun after retrieval-input boundary hardening: 459 passed, 3 failed, 0 errors, 0 skipped, 168.53s. It retained the same three failed nodes; none was hidden or weakened. The final guard again denied 162 outbound operations and recorded zero PostgreSQL attempts.

Full failures are reported, not skipped or xfailed. The full suite remains red. Existing source-hash evidence shows the index-stamp and password-routing code were not changed by this batch.

## Reproduction and retained evidence

From the isolated worktree backend directory, with existing dependencies:

    python -B -m app.knowledge.quality_evaluation
    python -B -m app.knowledge.quality_evaluation --local-models

The first command uses only hash embeddings and does not import Torch/models. The second loads only complete cached snapshots of the two named models; missing models are reported rather than downloaded or silently compared as hashes.

Focused tests:

    python -B -m pytest -p no:cacheprovider tests/test_retrieval_quality.py tests/test_quality_worker.py tests/test_source_foundation.py tests/test_source_benchmark.py tests/test_configuration.py tests/test_rag_visibility.py tests/test_threat_ownership.py tests/test_tools.py::TestCveLookup -q

This session used an additional isolated runner under C:\Users\moham\AppData\Local\Temp\cybershield-2a-batch2-cwnpm5ii\isolated_tests.py. It disables bytecode and pytest cache writes and external plugin auto-loading, denies DNS/connections/PostgreSQL, restricts SQLite to temporary test storage and asserts vector-path isolation. Run the full suite through this guard rather than unguarded: existing tests still attempt outbound requests. XML reports, before/after source inventory, full per-query benchmark JSON and the previous ingestion.py are retained in that same temporary artifact directory.

The compact JSON result report records exact model revisions, selected file hashes, package versions, configurations, both development and held-out aggregates, abstention metrics, resource costs and test outcomes. Raw repeated reports were compared after excluding timings/costs: rankings, versions, configurations, citation audits and metrics match exactly. The final retrieval-input hardening run matches earlier runs as well.

## Limitations and recommended Phase 2B

- Independent domain review and completeness checks of judgments are pending. Synthetic fixed-template cases, shared concepts and small historical corpora limit generalization. No confidence interval or production-grade accuracy claim is warranted.
- The benchmark uses a stub generator and conservative existing gates. Claim relevance, semantic entailment, applicability/effective dates and robust conflict detection remain unresolved; excerpt integrity is not truth.
- Snapshot views are process-local evaluation constructs, not a concurrent serving catalog or user-permission revocation mechanism.
- An identifier-aware ranking benefit in one small held-out set does not justify a universal source-authority or freshness boost.
- Memory and native OpenMP compatibility require review before serving real models. No deployment change is proposed from these latency numbers.
- Two password-routing/security failures remain, the local ownership migration remains unapplied, and a compatible full-suite environment is still required.

Recommended next step: independent passage-label review and a fresh locked test set, then targeted claim relevance/attribution/applicability checks in the opt-in grounded path. Validate in an approved Python 3.12 environment and resolve outstanding authentication/password-history security blockers before proposing live retrieval integration. Keep the current runtime defaults until larger evidence and resource measurements support a change. LangGraph remains a later separately approved stage.
