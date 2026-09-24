# Deployment Guide

## Overview

CyberShield AI consists of:

- React Frontend
- FastAPI Backend
- PostgreSQL Database
- Knowledge Base (FAISS + BM25)

---

# Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Git

---

# Backend

```bash
cd backend

python -m venv .venv

source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs on:

```
http://localhost:8000
```

---

# Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on:

```
http://localhost:5173
```

---

# Knowledge Base

Build the vector database:

```bash
python -m scripts.build_knowledge_base
```

---

# Environment Variables

Backend:

```env
DATABASE_URL=
JWT_SECRET=
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Frontend:

```env
VITE_API_URL=http://localhost:8000
```

---

# Production Deployment

Recommended Stack

Frontend:
- Vercel

Backend:
- Railway

Database:
- PostgreSQL

Storage:
- Persistent Volume

---

# Health Check

```
GET /health
```

Should return

```
{
    "status":"ok"
}
```

The Docker deployment uses Groq's hosted, OpenAI-compatible API. No model
weights are downloaded into the backend image. Keep `GROQ_API_KEY` in
`backend/.env` or your deployment platform's secret manager; never commit it.

RAG storage:

- `backend/knowledge_base/` contains bundled PDFs.
- The bundled pack covers OWASP Top 10, OWASP ASVS 5.0, NIST CSF 2.0,
  NIST SP 800-53, NIST SP 800-61, and NIST SP 800-207.
- `backend/uploads/` contains user uploads in local development.
- `backend/vector_db/` contains FAISS and BM25 indexes in local development.
- Production Compose persists uploads and indexes using named Docker volumes.