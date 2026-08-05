# CyberShield AI Architecture

## Overview

CyberShield AI is an enterprise-grade cybersecurity platform built using a modular multi-agent architecture. The platform combines Hybrid Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and specialized cybersecurity agents to provide intelligent security analysis.

---

# High-Level Architecture

```text
                    React Frontend
                           │
                           ▼
                    FastAPI Backend
                           │
                           ▼
                 CyberGPT Orchestrator
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
 Knowledge Agent      Threat Agent      Security Agents
        │
        ▼
    Capability Router
        │
        ▼
      RAG Service
        │
        ▼
   Hybrid Retriever
        │
 ┌──────┴───────────┐
 │                  │
 ▼                  ▼
FAISS            BM25 Search
 │                  │
 └──────┬───────────┘
        ▼
 Knowledge Base
        │
        ▼
    OpenAI LLM
        │
        ▼
   AI Generated Response
```

---

# Backend Architecture

```
app/
├── agents/
│   ├── orchestrator.py
│   ├── knowledge_agent.py
│   ├── threat_agent.py
│   ├── url_agent.py
│   └── password_agent.py
│
├── services/
│
├── rag/
│
├── api/
│
├── database/
│
└── schemas/
```

---

# AI Pipeline

```
User Question
      │
      ▼
Intent Classifier
      │
      ▼
Capability Router
      │
      ▼
Knowledge Agent
      │
      ▼
Hybrid Retriever
      │
      ▼
FAISS + BM25
      │
      ▼
OpenAI LLM
      │
      ▼
Final Response
```

---

# RAG Pipeline

1. Documents are indexed into the knowledge base.
2. Documents are split into semantic chunks.
3. Embeddings are generated using Sentence Transformers.
4. FAISS performs semantic similarity search.
5. BM25 performs keyword-based retrieval.
6. Results are merged by the Hybrid Retriever.
7. Retrieved context is passed to the LLM.
8. The LLM generates the final response.

---

# Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | React, TypeScript, Tailwind CSS |
| Backend | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | JWT |
| AI | OpenAI |
| RAG | LangChain |
| Vector Database | FAISS |
| Keyword Search | BM25 |
| Embeddings | Sentence Transformers |

---

# Design Principles

- Modular multi-agent architecture
- Separation of AI agents by capability
- Hybrid retrieval for improved accuracy
- Scalable backend services
- Conversation-aware interactions
- Enterprise-ready API design