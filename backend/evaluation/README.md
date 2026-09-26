# Evaluation Benchmarks

Run from the repository root after installing `backend/requirements.txt`:

```powershell
.\.venv\Scripts\python.exe backend\evaluate_benchmarks.py
```

The report is written to `backend/evaluation/results.json` and summarized in
the terminal.

## Retrieval

`rag_cases.json` contains 18 manually labeled questions with relevant source
PDF pages. The runner compares BM25-only, the production 384-dimensional
hashed-vector representation with FAISS, and the production-style BM25/vector
Reciprocal Rank Fusion pipeline. It reports macro Recall@5, MRR, nDCG@5, and
exact source-page precision/recall at 5. Only the six public knowledge-base
PDFs are included; other indexed documents are excluded from both rankings and
the report.

The gold labels are page-level and hand-curated, so they are useful for a
baseline comparison but are not a broad, independently adjudicated benchmark.
Expand and independently review the question set before making generalizable
quality claims.

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