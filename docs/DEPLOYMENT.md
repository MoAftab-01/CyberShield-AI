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
GROQ_MODEL=openai/gpt-oss-20b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Frontend:

```env
VITE_API_URL=http://localhost:8000
```

---

# Production Deployment (Free-Tier Setup)

Use Vercel for the static frontend, Render for the Dockerized FastAPI backend,
and Neon for PostgreSQL. Deploy the frontend and backend as separate services.

## 1. Neon Database

Create a Neon project and copy its PostgreSQL connection string. Use the pooled
connection string for the Render service, and ensure it includes
`sslmode=require`. Keep this value private.

## 2. Render Backend

Create a Web Service from the repository with:

- Root Directory: `backend`
- Runtime: Docker
- Health Check Path: `/health`
- Plan: Free

Set these environment variables in Render (never commit their real values):

```env
APP_NAME=CyberShield AI
APP_VERSION=1.0.0
ENVIRONMENT=production
DATABASE_URL=<Neon pooled connection string with sslmode=require>
JWT_SECRET=<long random secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GROQ_API_KEY=<Groq API key>
GROQ_MODEL=openai/gpt-oss-20b
CORS_ORIGINS=https://<your-vercel-domain>
```

The Dockerfile uses Render's `PORT` value automatically. After the first deploy,
verify `https://<your-render-service>.onrender.com/health` returns `{"status":"ok"}`.

## 3. Vercel Frontend

Import the same repository in Vercel and set:

- Root Directory: `frontend`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variable: `VITE_API_URL=https://<your-render-service>.onrender.com`

Add the exact production Vercel origin to Render's `CORS_ORIGINS`, then redeploy
the backend. If you use a custom domain, include that origin too. `VITE_API_URL`
is embedded in the frontend at build time, so redeploy Vercel after changing it.

## Free-Tier Tradeoffs

- Free Render services can spin down when idle, so the first request after idle
  can be slow. This is expected; a paid always-on instance is the direct fix.
- Render's local filesystem is ephemeral on a free service. User-uploaded files
  and indexes created at runtime can disappear after a restart or deploy. Keep
  important uploads in object storage or a database-backed storage service; do
  not rely on local disk for durable user data.
- Neon and Render have usage limits that can change. Monitor both dashboards for
  compute, storage, and connection limits; avoid running multiple backend
  instances against a small free database.
- The frontend can stay static on Vercel. Do not put database URLs, JWT secrets,
  or provider API keys in `VITE_*` variables, because those are public in the
  browser bundle.

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