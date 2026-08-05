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
OPENAI_API_KEY=
OPENAI_MODEL=
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