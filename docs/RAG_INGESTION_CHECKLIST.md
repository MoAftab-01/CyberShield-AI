# RAG ingestion checklist for safe, high-quality KB growth

This checklist is meant for adding 5–15 curated cybersecurity PDFs without overloading a free Render instance or creating a noisy knowledge base.

## Goal

Add high-value, domain-specific documents that improve retrieval quality for the CyberShield AI assistant, while keeping the app stable on free-tier hosting.

## Safe-growth rules

1. Keep the corpus curated and tight.
   - Prefer 5–15 strong documents over 50 low-value PDFs.
   - Every PDF should match at least one priority domain:
     - OWASP / web application security
     - NIST / CSF / zero trust / control families
     - CISA / incident response / hardening
     - IAM / MFA / authentication
     - secure SDLC / DevSecOps
     - threat intelligence / malware / phishing

2. Avoid duplicates and near-duplicates.
   - Reject alternate copies of the same PDF.
   - Normalize file names and metadata before indexing.
   - Deduplicate repeated sections after chunking.

3. Prefer source material with clear sections.
   - PDFs with headings, tables, or numbered controls score better in retrieval.
   - Avoid scanned-only PDFs unless they are needed for a very specific use case.

4. Keep the knowledge base balanced.
   - Do not let a single 500-page control catalog dominate the index.
   - Add a small number of complementary references from other domains.

5. Keep free Render safe.
   - Do not force a huge index or massive reranker in the same container.
   - Prefer the existing hybrid retrieval path with controlled chunking.
   - Use the semantic backend only when the memory floor is safe.

## Selected PDFs

The initial batch is five official NIST publications. All are downloaded only
when the maintenance command is run; application startup never accesses the
network.

| Publication | Coverage | Official PDF |
| --- | --- | --- |
| NIST SP 800-63B-4 | Authentication and authenticator management | [NIST download](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63b-4.pdf) |
| NIST SP 800-218 | Secure Software Development Framework | [NIST download](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf) |
| NIST SP 800-190 | Application container security | [NIST download](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf) |
| NIST SP 800-171 Rev. 3 | Protecting controlled unclassified information | [NIST download](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-171r3.pdf) |
| NIST SP 800-161 Rev. 1 Update 1 | Cybersecurity supply-chain risk management | [NIST download](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-161r1-upd1.pdf) |

The downloader pins every source to `nvlpubs.nist.gov`, caps each file at 15
MiB, checks the PDF signature, and replaces files atomically. Additions should
be reviewed and benchmarked before the shortlist is expanded further.

## Initial evaluation questions

The expanded benchmark includes two page-verified questions per new PDF:

| PDF | Question coverage | Gold pages |
| --- | --- | --- |
| NIST SP 800-63B-4 | Blocklisted/compromised passwords; usable password entry | 25, 27 |
| NIST SP 800-218 | Defining SDLC security requirements; SSDF design practice PW.1 | 14, 20 |
| NIST SP 800-190 | Microservice architecture; container registry automation | 16, 22 |
| NIST SP 800-171 Rev. 3 | Least privilege for privileged accounts; incident-handling phases | 21, 49 |
| NIST SP 800-161 Rev. 1 Update 1 | Supplier due diligence; supplier risk assessment | 55, 61 |

These are seed labels checked against extracted PDF page text, not an
independent quality review. Update `backend/evaluation/rag_cases_expanded.json`
when a reviewer finds a better supporting page or adds question variants.

## Ingestion quality gate

A PDF should only be added if all of the following are true:

- It is relevant to cyber security, secure engineering, or risk management.
- It is authoritative and stable enough to be cited.
- It contains distinct sections that map to concrete questions.
- It adds new retrieval coverage, not just duplicate wording.
- It fits the project’s chunking and memory constraints.

## Evaluation gate before accepting a PDF

After adding a new document:

1. Rebuild the knowledge base index.
2. Run the benchmark script.
3. Add at least two new gold questions for the document, each with a page
   verified from the PDF text.
4. Confirm the new document improves Recall@5 or removes a previously failing pattern.
5. Keep the benchmark stable and document the result in the evaluation report.

## Example gold-question categories

Add question sets that cover:

- password and authentication policy
- zero trust architecture
- secure software development lifecycle
- incident response responsibilities
- access control enforcement
- OWASP risk categories
- URL and phishing protections
- MFA and account recovery requirements

## Download and index

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe backend\download_knowledge_base.py --dry-run
.\.venv\Scripts\python.exe backend\download_knowledge_base.py
```

The next backend startup detects the new source inventory and rebuilds FAISS
and BM25 indexes. On a free Render instance, keep `EMBEDDING_BACKEND=auto` and
`EMBEDDING_MEMORY_FLOOR_MB=900`; the model then falls back to the lightweight
hash backend if the container does not have enough memory. Do not set the
floor to zero on Render.
