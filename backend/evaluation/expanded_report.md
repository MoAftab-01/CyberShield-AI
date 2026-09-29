# Expanded Retrieval Evaluation

**Captured:** 2026-09-29
**Question set:** 29 page-labeled questions (18 stable baseline + 11 expanded)
**Public corpus:** 11 PDFs, including five newly added official NIST publications
**Top K:** 5

## Results

| Runtime / method | Recall@5 | MRR | nDCG@5 | Page Precision@5 |
| --- | ---: | ---: | ---: | ---: |
| Local semantic production (`fastembed`) | 0.7931 | 0.6052 | 0.6507 | 0.1632 |
| Local free-tier fallback production (`hash`) | 0.6897 | 0.4351 | 0.4988 | 0.1552 |
| Semantic benchmark hybrid arm (`fastembed`) | 0.8621 | 0.5259 | 0.6076 | 0.1724 |
| Free-tier fallback benchmark hybrid arm (`hash`) | 0.6897 | 0.5615 | 0.5935 | 0.1448 |

The app's production retriever is the user-facing result. Its measured Recall@5
was 79.3% with the semantic encoder locally and 69.0% with the hash fallback
used to model memory-constrained free hosting. The `hybrid` rows are offline
benchmark arms, not the production path, and must not be reported as the
application's production accuracy.

## Interpretation and limits

- The 90% production target has **not** been reached.
- Recall@5 is page-level retrieval coverage, not answer accuracy or
  faithfulness. Answer citations and factual support remain pending manual
  review.
- Questions are manually curated, and the expanded questions were added to the
  same public documents used by the retriever. This is a development benchmark,
  not an independent test set.
- With 29 questions, small changes can move the macro score noticeably. A
  broader independently reviewed set is needed before making general quality
  claims.
- Page precision is still low, so improving corpus balance and reranking should
  remain a priority.
- The hash gate classified 0/6 off-KB security and 0/6 unrelated calibration
  questions as document-supported. Fastembed classified 1/6 off-KB security
  prompts as document-supported. These negative sets are small and should be
  expanded before treating the gate as fully calibrated.

## Free Render setting

Keep `EMBEDDING_BACKEND=auto` and `EMBEDDING_MEMORY_FLOOR_MB=900` on Render.
The service will select the semantic encoder only when the memory limit permits
it; otherwise it falls back to hashes and remains available. Do not set the
memory floor to zero on Render. The `hash` result above is the safer estimate
for a 512 MB free instance, not a measurement from Render itself.

To reproduce semantic local measurements, install the configured fastembed
model and run the evaluator with `EMBEDDING_BACKEND=fastembed`. To measure the
free-tier fallback, use `EMBEDDING_BACKEND=hash`. The evaluator checks that all
gold source pages exist in the indexed KB before scoring.