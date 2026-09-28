# CyberShield AI — Baseline Evaluation Report

**Captured:** 2026-09-29 (re-run of the pre-existing harness, unmodified)
**Harness:** `backend/evaluate_benchmarks.py`
**Raw output:** `backend/evaluation/baseline_results.json`
**Reproducibility:** Deterministic. The harness measures retrieval + the local URL
heuristic only — it makes **no LLM calls**, so numbers are byte-stable across runs.

To reproduce:

```powershell
.\.venv\Scripts\python.exe backend\evaluate_benchmarks.py
```

---

## 1. What the harness actually measures

| Metric family | Status |
| --- | --- |
| Retrieval: Recall@5, MRR, nDCG@5, source-page Precision@5 / Recall@5 | **Measured** |
| URL detection: accuracy, precision, recall, F1, specificity, confusion matrix | **Measured** |
| Answer faithfulness / citation correctness | **Not measured** — harness returns `pending_manual_review`, `sample_size: 0`, values `null` |
| Context relevance | **Not measured** |
| Hallucination rate | **Not measured** |
| Latency | **Not measured** |
| Token usage | **Not measured** |
| Intent classification accuracy | **Not measured** |
| Tool selection accuracy | **Not measured** |
| Unnecessary tool / RAG call rate | **Not measured** |

The harness deliberately reports unmeasured things as `null` rather than zero. That
honesty is a strength and is preserved.

---

## 2. Retrieval baseline — 18 curated cases, K = 5

Gold labels are page-level: a retrieved chunk counts as relevant only if its
**filename + 1-based page** matches a hand-curated gold page.
Index scope: 3,662 chunks from the 6 public KB PDFs (7 non-KB chunks excluded).

| Method | Recall@5 | MRR | nDCG@5 | Precision@5 | Recall@5 (page) |
| --- | --- | --- | --- | --- | --- |
| `bm25_only` | 0.6667 | 0.4648 | 0.5155 | 0.1333 | 0.6667 |
| `hashed_vector_only` | 0.3889 | 0.1963 | 0.2433 | 0.0778 | 0.3889 |
| **`hybrid_rrf` (production)** | **0.7222** | **0.4713** | **0.5314** | **0.1444** | **0.7222** |

### Observations

- **Hybrid RRF is the best configuration** and beats BM25-only on every metric —
  the fusion layer is doing real work and should be kept.
- **The "vector" half contributes almost nothing.** `hashed_vector_only` scores
  0.3889 Recall@5, *worse than pure lexical BM25* at 0.6667. This is expected once
  you read `app/rag/embeddings.py`: the "embedding" is a **blake2b hashing
  bag-of-words** (tokens hashed into 384 buckets, L2-normalised), not a semantic
  encoder. FAISS therefore indexes a lexical hashed vector, so the system has
  **no semantic retrieval capability at all** — that is why it gains only +0.055
  Recall@5 over BM25 and why the vector-only arm actively loses to BM25.
- **Retrieval recall is not the main quality problem.** At 0.72 Recall@5, the
  gold page usually *is* in the top 5. The user-visible failures come from what
  happens *after* retrieval (see §4–5), not only from ranking.
- **Precision@5 is very low (0.14)** — only ~0.7 of 5 slots are gold. One cause is
  visible in the corpus: **2,656 of 3,662 chunks (72.5%) are a single document**
  (`NIST-SP-800-53r5.pdf`, a 500-page control catalog), which crowds out
  better-matched sources. Page-level gold also caps precision mechanically.
- Cases that fail for **all** methods: `RAG-07` (PDP/PEP responsibilities),
  `RAG-08` (six CSF functions — BM25 and vector both 0.0, RRF recovers to 1.0),
  `RAG-10` (coordinating CSF functions — BM25 1.0 but RRF 0.0).

---

## 3. URL detection baseline — 24 synthetic fixtures

Local heuristic only; **VirusTotal is not queried** in this measurement.

| Metric | Value |
| --- | --- |
| Accuracy | 0.8750 |
| Precision | 1.0000 |
| Recall | 0.7500 |
| F1 | 0.8571 |
| Specificity | 1.0000 |

Confusion matrix: TP 9, FP 0, TN 12, FN 3.

No false positives; the 3 misses are false negatives. The dataset is
**synthetic and hand-labelled**, so this is a smoke test of the scoring rules,
not real-world phishing accuracy — the harness README says the same.

---

## 4. Answer quality — not measured at baseline

`answer_annotations.csv` exists with the right columns
(`generated_answer`, `citations_correct`, `all_factual_claims_supported`) but is
**empty of reviewed rows**, so `answer_review` is
`{"status": "pending_manual_review", "sample_size": 0}`.

There is therefore **no baseline number for faithfulness, groundedness or
hallucination rate.** Any figure quoted for these would be fabricated. They are
listed as *not measured* in the before/after report.

---

## 5. Qualitative baseline — observed behaviour (from code inspection)

These are reproducible by inspection of the request path, not scored by the
harness. They are recorded here because the harness cannot see them.

| Behaviour | Baseline reality |
| --- | --- |
| Chat entry point | Frontend `POST /copilot/ask` → `RAGService.ask` **directly** |
| Agent/orchestrator layer | **Never invoked** by the chat path — `app/agents/*` is unreachable dead code from the UI |
| Auth on chat | **None** — `copilot_routes.py` hardcodes `user_id = 1` |
| "Generate a strong password" | Routed to RAG; the KB-only prompt forbids answering → *"documents do not contain enough information"* |
| "Hello" | Routed to RAG → same KB-only refusal |
| "Analyze this password: X" | `PasswordAgent` passes the **entire sentence** as the password |
| Multi-user isolation of uploads | **None** — uploaded docs enter the one shared index and are retrievable by any user |
| Latency / token accounting | Not recorded anywhere |

Evidence for the upload-isolation finding: the current index contains 7 chunks
from `Aftab_Resume_Google_Data_Analytics.pdf` (`source_folder: uploads`); the eval
harness works around this by hard-coding an `ALLOWED_SOURCES` allow-list. The
leak is real and already had to be manually filtered.

---

## 6. Summary of baseline figures

```
Retrieval (hybrid_rrf, production path)
  Recall@5        0.7222
  MRR             0.4713
  nDCG@5          0.5314
  Precision@5     0.1444

Retrieval (bm25_only)         Recall@5 0.6667  MRR 0.4648
Retrieval (hashed_vector)     Recall@5 0.3889  MRR 0.1963

URL detection (local only)
  Accuracy 0.875  Precision 1.000  Recall 0.750  F1 0.8571

Answer faithfulness / hallucination rate   NOT MEASURED (pending manual review)
Context relevance                          NOT MEASURED
Latency / tokens                           NOT MEASURED
Intent accuracy / tool-selection accuracy  NOT MEASURED
```

The "after" report will be produced with the same harness so the comparison is
like-for-like, plus a **new** agent-behaviour harness for the metrics that do not
exist today.
