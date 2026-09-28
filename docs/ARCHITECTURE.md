# CyberShield AI Architecture

## Overview

CyberShield AI is a cybersecurity platform built as a FastAPI backend with a
React frontend. It combines hybrid retrieval-augmented generation, a
deterministic tool layer, and a set of standalone security scanners (password,
URL, threat intelligence).

The assistant is called **CyberGPT**. Its defining behaviour is that it
*classifies before it answers*: an action request goes to a deterministic tool,
a question about security goes to retrieval, and a greeting gets a reply. This
document describes how that works and why it is built this way.

---

# High-Level Architecture

```text
                    React Frontend  (Vercel)
                           │
                           ▼
                    FastAPI Backend  (Render)
                           │
                           ▼
                  CyberGPT Orchestrator
                           │
                  Intent Router (rules)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   Tool Registry      RAG Service      Conversation
        │                  │                  │
        │                  ▼                  │
        │          Hybrid Retriever           │
        │                  │                  │
        │        ┌─────────┴─────────┐        │
        │        ▼                   ▼        │
        │   FAISS (dense)      BM25 (lexical) │
        │        │                   │        │
        │        └─────────┬─────────┘        │
        │                  ▼                  │
        │        Reciprocal Rank Fusion       │
        │                  ▼                  │
        │        MMR diversity selection      │
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                  Groq LLM (openai/gpt-oss-20b)
                           │
                           ▼
                    Labelled response
```

The three destinations exist because the three kinds of request need different
machinery. A generated password must not be reworded by a model, a CVSS score
must not be recalled from training data, and a greeting must not cost a
retrieval pass and a model call.

---

# Backend Layout

```text
app/
├── agents/
│   ├── intents.py          Intent taxonomy and answer-basis labels
│   ├── router.py           Deterministic-first intent classification
│   ├── tools.py            Tool registry - the deterministic actions
│   └── orchestrator.py     Single entry point; dispatch and persistence
│
├── api/                    HTTP routes, one module per feature
├── services/               Business logic (password, URL, threat, RAG, documents)
│   └── llm/                Provider abstraction (Groq, OpenAI) and factory
├── rag/
│   ├── loader.py           Parse PDF / DOCX / TXT into documents
│   ├── chunker.py          Split into overlapping passages
│   ├── embeddings.py       ONNX sentence encoder, with a hashed fallback
│   ├── vector_store.py     FAISS index
│   ├── bm25_store.py       BM25 index
│   ├── retriever.py        Hybrid search, fusion, reranking, MMR
│   └── index_meta.py       Index provenance stamp
├── intelligence/           Threat scoring and aggregation
├── integrations/           Third-party clients (VirusTotal)
├── clients/                Public data sources (NVD, CISA KEV, EPSS, MITRE)
├── core/                   Settings, security primitives, rate limiting
├── database/               Engine, session, models, CRUD
├── models/                 Feature ORM models
└── schemas/                Pydantic request and response contracts
```

The four files in `agents/` are the whole assistant. An earlier version of this
document described a larger set of "specialized agents" - `knowledge_agent`,
`threat_agent`, `url_agent`, `password_agent`, `capability_router`,
`intent_classifier` - with a sub-agent per capability. Those classes existed but
**nothing imported them**: the live route called the retrieval service directly.
They have been removed, and the capability they wrapped is reached through the
tool registry instead, which is one dispatch path rather than four subclasses.

---

# The Request Path

```
User Question
      │
      ▼
Length and emptiness validation
      │
      ▼
Intent Router ──── rules first (no model call)
      │                │
      │                └── model fallback only if rules find nothing,
      │                    and only for a question long enough to carry signal
      ▼
Resolve or create the conversation (ownership verified)
      │
      ▼
Redact secrets from the user message before it is stored
      │
      ├─── tool intent ──────► Tool Registry ──► formatted answer
      │                                          (no model call)
      │
      ├─── greeting ─────────► Conversation reply
      │
      └─── everything else ──► RAG Service
                                    │
                                    ▼
                            Hybrid retrieval
                                    │
                            Relevance gate on the
                            top semantic similarity
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                document        related        irrelevant
             (answer from    (answer from    (answer from
              the passages,   general         general
              cite them)      knowledge,      knowledge,
                              passages as     no passages)
                              related reading)
      │
      ▼
Persist both turns, return a labelled response
```

Every response carries an `answer_basis` field - `document`,
`general_knowledge`, `tool` or `conversation` - so the caller can always tell
whether an answer came from the indexed documents. A general answer is labelled
in its own text as well, because the label has to survive being read rather than
parsed.

---

# Retrieval

Retrieval runs two independent searches and fuses them, because each covers the
other's blind spot: BM25 matches the exact term a policy document uses, and the
dense encoder matches a paraphrase that shares no words with it.

1. **Lexical (BM25).** Tokenised with bigram phrase tokens, so
   `"zero trust"` scores as a phrase rather than as two unrelated words.
2. **Dense (FAISS).** `IndexFlatL2` over L2-normalised vectors, which makes
   the squared distance a monotone function of cosine similarity
   (`cos = 1 - d²/2`). 384-dimensional vectors from
   `sentence-transformers/all-MiniLM-L6-v2`, running on CPU through ONNX
   Runtime via `fastembed` - no PyTorch, which would not fit a 512MB
   free-tier container.
3. **Reciprocal Rank Fusion.** The two ranked lists are merged by rank
   position (k=60), so a passage neither arm ranked highly can still surface,
   and neither arm's raw score scale has to be calibrated against the other's.
4. **Reranking.** The fused candidates are rescored on a weighted blend of
   fusion score, semantic similarity, and query-term coverage.
5. **MMR selection.** The final passages are chosen for relevance *and*
   mutual diversity, so the top five are not five adjacent chunks of one page.
6. **Page deduplication** and a relevance floor that drops the tail when
   coverage is poor.

## Index provenance

An index is only valid for the encoder that built it. Two encoders can both
produce 384-dimensional vectors and live in unrelated vector spaces, in which
case searching one with the other returns confident nonsense rather than an
error. Every index therefore carries a stamp - schema version, backend, model
name, dimension, and chunk configuration - written at `vector_db/index_meta.json`
and checked before the index is reused. A mismatch rebuilds; a match loads in
under a second instead of several minutes.

This is not theoretical. The original index was built by the hashed fallback and
kept being searched after the semantic encoder was installed; the stamp is what
made that visible and self-correcting.

---

# Answering

The relevance gate is calibrated from measurement, not chosen by feel.
`evaluation/confidence_calibration.py` measures the top semantic similarity of
the best retrieved passage across three groups of questions:

| Group | n | min | median | max |
|---|---|---|---|---|
| In the knowledge base | 18 | 0.5644 | 0.6917 | 0.7878 |
| Security, not in the KB | 6 | 0.3082 | 0.3603 | 0.6109 |
| Unrelated to security | 6 | 0.1033 | 0.1311 | 0.2046 |

The unrelated group is cleanly separated and sits below the rejection
threshold of 0.30. The two security groups **overlap** - a security question
the corpus does not cover can score higher than one it does - so the fallback is
designed to be safe under that overlap rather than assuming it away: it never
claims document support it does not have, and the near-miss passages are still
returned to the user as *related reading*.

This is the honest version of the design. A single threshold that separated all
three groups perfectly does not exist at this corpus size, and pretending
otherwise would have meant a gate that silently mislabels.

---

# Provenance and Failure Behaviour

Every component that can fail degrades to saying so.

| Failure | Behaviour |
|---|---|
| LLM provider down or rate-limited | The answer says the model is unavailable; retrieval results are still returned |
| Knowledge-base index missing | Retrieval reports `empty`; answering falls back to the labelled general path |
| Index built by a different encoder | Detected by the stamp and rebuilt at startup |
| VirusTotal unreachable, rate-limited, or keyless | Reported as unavailable; scoring lowers its confidence instead of treating no data as no detections |
| CISA KEV feed unreachable | Reported as unreachable rather than answering from a model's memory of which CVEs are exploited |
| Embedding model unavailable | Falls back to the hashed encoder and reports which backend is live |
| Index build fails at startup | Logged; the API still starts, and only retrieval is affected |

The rule behind all of these: an outage must not be reported as a finding. "No
detections" and "we could not check" are different statements and the second one
is never rendered as the first.

---

# Security

| Area | Control |
|---|---|
| Authentication | JWT bearer on every endpoint that reads or writes user data, including `/copilot/ask` |
| JWT algorithm | Allow-list of HS256/HS384/HS512; `none` and asymmetric algorithms refuse to load |
| Tenant isolation | Conversation and document access is scoped by `user_id` at the query, and a foreign id answers 404 rather than 403 so it cannot be used to enumerate |
| Uploads | Path-traversal-resistant naming plus a resolved-path containment check; 15MB streamed cap with partial-file cleanup; extension allow-list |
| Password privacy | Scored locally, never sent to the model, masked with a fixed-width mask before the message is stored |
| Rate limiting | Per-user sliding window on the endpoints that spend LLM quota |
| Prompt injection | Retrieved passages are presented as context, not instructions; the system prompt states that document content is data |
| Secrets | Environment only; `.env` is gitignored and CI fails if it is ever tracked |

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, Vite, Axios, Recharts |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL (Neon) |
| ORM | SQLAlchemy 2 |
| Authentication | JWT (python-jose), bcrypt |
| LLM | Groq - `openai/gpt-oss-20b` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (ONNX, via fastembed) |
| Vector search | FAISS (CPU) |
| Keyword search | BM25 (rank_bm25) |
| Document parsing | PyMuPDF, pypdf, python-docx |
| Deployment | Vercel (frontend), Render (backend), Neon (database) |

---

# Design Principles

- **Classify before answering.** The most expensive way to answer "generate a
  password" is to retrieve documents about passwords and ask a model to invent
  one.
- **Deterministic where determinism is possible.** Password strength, CVSS
  scores and KEV membership have exact answers. Those come from code.
- **Say where the answer came from.** A general answer is labelled as one, in
  its own text.
- **Failures are reported, not disguised.** An outage never renders as a
  clean result.
- **Measure before tuning.** Every threshold and weight in the retrieval path
  has a number behind it in `evaluation/`, including the ones that turned out
  not to matter.
- **The free tier is a design constraint, not an afterthought.** CPU-only
  inference, no Redis, no GPU, no background workers.
