# Evaluation Benchmarks

Run from the repository root after installing `backend/requirements.txt`:

```powershell
.\.venv\Scripts\python.exe backend\evaluate_benchmarks.py
```

The report is written to `backend/evaluation/results.json` and summarized in
the terminal.

## Retrieval

`rag_cases.json` contains the stable 18-question baseline. The additive
`rag_cases_expanded.json` contains eleven additional manually labeled questions
from the expanded public knowledge base. The evaluator verifies every gold source page is
present in the indexed knowledge base before scoring. The runner compares
BM25-only, legacy hashed vectors, the active 384-dimensional embedding backend,
hybrid retrieval, and the production retriever. It reports macro Recall@5,
MRR, nDCG@5, and exact source-page precision/recall at 5. Only public
knowledge-base documents are included; user uploads are excluded.

The gold labels are page-level and hand-curated, so they are useful for a
baseline comparison but are not a broad, independently adjudicated benchmark.
Expand and independently review the question set before making generalizable
quality claims. New PDFs are listed in `docs/RAG_INGESTION_CHECKLIST.md` and can
be downloaded with `backend/download_knowledge_base.py`.

The latest 28-question result is summarized in `expanded_report.md`. The
production number is the relevant user-facing result; the separate `hybrid_rrf`
arm is an evaluator implementation and can score differently from production's
reranking and diversity stages.

## URL Detection

`url_cases.json` is a synthetic set of suspicious/ordinary URL fixtures. The
runner evaluates only the local URL heuristic and classifies `High` or
`Critical` as suspicious. It reports accuracy, precision, recall, F1,
specificity, and the confusion matrix. It does not call VirusTotal, and these
synthetic fixture scores are not real-world phishing-detection accuracy. For a
resume-grade result, evaluate a dated, labeled public phishing/benign corpus,
deduplicate domains, document the split, and report precision/recall/F1 on a
held-out set.

## Answer Citations And Faithfulness

Source-page precision/recall measures whether retrieval returns labeled pages;
it does not establish whether generated claims are supported. To score generated
answers, run the questions through the application, paste each answer into
`answer_annotations.csv`, and have a reviewer set:

- `citations_correct` to `1` only when cited source/page references support the
  associated claims, otherwise `0`.
- `all_factual_claims_supported` to `1` only when every factual claim is
  supported by the cited context, otherwise `0`.

Rerun the evaluator to calculate those annotation rates. Empty annotations are
reported as pending, not as zero or 100%.

## Growing the benchmark safely

The benchmark is intentionally small enough to reason about by hand, but it can
be grown without destabilising evaluation or the app itself. The safest pattern
is:

1. Keep the original `rag_cases.json` as the stable baseline.
2. Add cases to `rag_cases_expanded.json` with page labels checked against the
  actual PDF text.
3. Re-run `backend/evaluate_benchmarks.py` and compare before/after numbers.
4. Only update the default benchmark once the new questions are reviewed, not
   while the doc set is still changing.

This preserves a clean baseline while allowing measurements to improve as the
knowledge base expands. The project also includes a curated ingestion checklist in
`docs/RAG_INGESTION_CHECKLIST.md`, which lists the categories and quality gates
for adding 5–15 high-quality cybersecurity PDFs without overloading a free-tier
Render instance.