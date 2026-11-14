# Batch 2 synthetic benchmark

Corpus and history files contain original synthetic CC0-1.0 text, not official recommendations. Fictional CVE identifiers, policy intervals, scores and organization names must not be used as security guidance. Queries and relevance judgments live in separate files and are never supplied to index building, model prompts or reranking. Only the query string, actor and explicit source-time cutoff enter retrieval.

The corpus was authored and labels were checked in a separate consistency pass before any ranking/tuning run. Independent human/domain review has not occurred; this is not a blindly curated external test set. Fixed topic-family groups separate development and held-out questions. They share document collections and security concepts; this does not establish cross-domain generalization. Held-out results must not drive tuning.

Passage relevance is explicit: record ID + heading, grade 2 direct evidence, grade 1 supporting context (when supplied), absence grade 0 under this small closed-world benchmark. Each labeled section is deliberately shorter than one chunk. Exact supporting quotes make stale-version labels detectable. A relevant malicious or conflicting passage can still require answer abstention. Historical questions use only known versions at an explicit source modification cutoff; retrieval timestamps are not policy effective dates.
