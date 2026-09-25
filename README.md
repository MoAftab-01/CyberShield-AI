# 🛡️ CyberShield AI

CyberShield AI is an AI-powered cybersecurity platform that combines threat intelligence, document intelligence, vulnerability analysis, and an enterprise security copilot into a single application.

Built with **FastAPI, React, PostgreSQL, Docker, Docker Compose, Nginx, and Groq-hosted Llama**.

---

## ✨ Features

### 🤖 CyberGPT — Enterprise Security Copilot
- AI-powered cybersecurity assistant
- Hybrid RAG over uploaded security documents
- Conversation memory
- Document summarization
- Multi-document comparison
- Security best-practice recommendations
- Hosted LLM inference using Groq's OpenAI-compatible API

### 📄 Document Intelligence
- Upload PDF security reports
- Hybrid RAG using BM25 + vector search
- AI-powered document summaries
- Multi-document comparison
- Source citations and document references

### 🛡️ Threat Intelligence Dashboard
- AI-generated security summaries
- CVE insights
- Security recommendations
- Executive-level security dashboard

### 🔍 URL Scanner
- URL reputation analysis
- Phishing detection
- Risk assessment
- Security classification

### 🔐 Password Analyzer
- Password strength evaluation
- Entropy analysis
- Security recommendations

### 👤 Authentication
- User registration
- JWT-based authentication
- Login/logout
- Protected routes
- User-specific data

---

# 🏗️ Architecture

```text
                         Browser
                            │
                            ▼
                  ┌──────────────────┐
                  │  React Frontend  │
                  │   TypeScript     │
                  └────────┬─────────┘
                           │ REST API
                           ▼
                  ┌──────────────────┐
                  │      Nginx       │
                  │  Reverse Proxy   │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  FastAPI Backend │
                  │     Python       │
                  └───────┬───┬──────┘
                          │   │
              ┌───────────┘   └────────────┐
              ▼                            ▼
      ┌───────────────┐           ┌────────────────┐
      │  PostgreSQL   │           │  Groq API      │
      │   Database    │           │ Hosted Llama   │
      └───────────────┘           └───────┬────────┘
                                          │
                                          ▼
                                  ┌────────────────┐
                                  │   Hybrid RAG   │
                                  │ BM25 + Vector  │
                                  └────────────────┘
```

---

# 🧠 AI Architecture

CyberShield AI uses a hosted LLM architecture for AI inference.

```text
User Question
      │
      ▼
FastAPI API
      │
      ▼
RAG / AI Service
      │
      ├───────────────┐
      ▼               ▼
Conversation       Hybrid Retrieval
History            BM25 + Vector Search
      │               │
      └───────┬───────┘
              ▼
        Context Builder
              │
              ▼
        Groq / Llama
              │
              ▼
        AI Response
              │
              ▼
        Source References
```

For document-based questions, relevant document content is retrieved and supplied to the LLM as context.

---

# 🛠️ Tech Stack

## Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- LangChain
- Hybrid RAG
- BM25
- Vector Search
- Groq API
- Llama model
- JWT Authentication

## Frontend
- React
- TypeScript
- Vite
- TailwindCSS
- Axios
- Recharts

## Infrastructure
- Docker
- Docker Compose
- Nginx

---

# 📁 Project Structure

```text
CyberShield-AI/
│
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── ...
│
├── docker-compose.yml
└── README.md
```

---

# 🚀 Quick Start

## Prerequisites

Install:
- Docker Desktop
- Git

Make sure Docker Desktop is running before starting the application.

## 1. Clone the Repository

```bash
git clone https://github.com/MoAftab-01/CyberShield-AI.git
cd CyberShield-AI
```

## 2. Configure Environment Variables

### Windows PowerShell

```powershell
Copy-Item backend\.env.example backend\.env
```

### macOS / Linux

```bash
cp backend/.env.example backend/.env
```

The `.env.example` file contains placeholders and does not contain private credentials.

Set `GROQ_API_KEY` in `backend/.env` using a key from
[console.groq.com](https://console.groq.com/). The application defaults to
`llama-3.1-8b-instant`; you can change it with `GROQ_MODEL`.

## 3. Start the Application

```bash
docker compose up -d
```

Docker Compose automatically:
1. Builds the backend
2. Builds the frontend
3. Starts PostgreSQL
4. Starts the FastAPI backend
5. Starts the React/Nginx frontend
6. Connects the backend to Groq using `GROQ_API_KEY`
7. Exposes a backend health check at `/health`

---

# 🧠 CyberGPT RAG

CyberGPT uses a document-grounded retrieval-augmented generation pipeline.
The `/copilot/ask` endpoint always uses the RAG service; it does not route
questions to the Password Analyzer, URL Scanner, CVE tools, or other
application features.

The pipeline:

1. Extracts uploaded PDF text page by page.
2. Splits documents into overlapping chunks while preserving filename and page.
3. Searches with both FAISS semantic retrieval and BM25 lexical retrieval.
4. Combines results with Reciprocal Rank Fusion.
5. Removes weakly matching passages and duplicate page results.
6. Sends labeled passages to Groq with source-citation instructions.
7. Returns answer sources and retrieval metrics.

If the documents do not contain enough evidence, CyberGPT is instructed to say
so instead of guessing. The response includes metrics such as
`retrieved_count`, `candidate_count`, `top_score`, `top_term_coverage`, and
`relevance_floor`.

The bundled knowledge base currently contains:

- OWASP Top 10
- OWASP ASVS 5.0
- NIST CSF 2.0
- NIST SP 800-53 security controls
- NIST SP 800-61 incident response
- NIST SP 800-207 zero trust architecture

Bundled PDFs are stored in `backend/knowledge_base/`. Uploaded files are
stored in `backend/uploads/user_<id>/` locally. FAISS and BM25 indexes are
stored in `backend/vector_db/`. Indexes are built automatically at backend
startup when they do not exist, and uploaded files are indexed immediately.

---

# Hosted model configuration

The container does not download or store model weights. Each AI request is sent
to Groq's hosted API, so startup remains lightweight. If the API key is absent,
AI requests fail explicitly with a configuration error rather than silently
falling back to a local model.

---

# 🌐 Access the Application

### Frontend

```text
http://localhost
```

### Backend API Documentation

```text
http://localhost:8000/docs
```

The frontend is served through Nginx, which routes API requests to the FastAPI backend.

---

# ☁️ Free Hosting

The application can be hosted using free tiers, but free hosting is best
suited for a demo or portfolio deployment rather than production workloads.

Recommended split:

| Component | Free-tier option | Important limitation |
|---|---|---|
| Frontend | Vercel or Netlify | Set `VITE_API_URL` to the public backend URL |
| Backend | Render, Koyeb, or another Docker host | Free instances may sleep |
| PostgreSQL | Neon or Supabase | Storage, connection, and compute limits |
| LLM | Groq API | Rate limits and usage quotas |
| Uploaded files | Supabase Storage or Cloudflare R2 | Required if files must survive redeploys |

The bundled PDFs are included in the backend image, so they can be rebuilt on
startup. Do not rely on a free host's local filesystem for user uploads or
generated FAISS/BM25 indexes: many free services erase local files during
redeployments or restarts. The production Compose file uses named Docker
volumes for self-hosted deployments, but cloud deployment needs persistent
object storage or a persistent disk.

## Cloud deployment checklist

1. Create a managed PostgreSQL database and copy its connection URL.
2. Create a backend web service from the `backend/` Dockerfile.
3. Configure `DATABASE_URL`, `JWT_SECRET`, `LLM_PROVIDER=groq`,
   `GROQ_API_KEY`, `GROQ_MODEL`, and `GROQ_BASE_URL` as service secrets.
4. Confirm the service health check works at `/health`.
5. Deploy the frontend and set `VITE_API_URL` to the backend URL.
6. Configure persistent storage before enabling user PDF uploads.
7. Test registration, login, upload, document Q&A, and a cold start.

Never commit `backend/.env`, API keys, database passwords, or JWT secrets.
Free-tier services can change quotas and pricing, so verify current limits
before choosing a provider.

---

# 🐳 Docker Services

| Service | Description | Port |
|---|---|---:|
| Frontend | React + Nginx | 80 |
| Backend | FastAPI REST API | 8000 |
| PostgreSQL | Application database | 5432 |
| Groq API | Hosted Llama inference | External API |

## RAG document storage

- Bundled knowledge-base PDFs are stored in
  `backend/knowledge_base/` and are copied into the backend image.
- The current bundled pack includes OWASP Top 10, OWASP ASVS 5.0,
  NIST CSF 2.0, NIST SP 800-53, NIST SP 800-61 incident response, and
  NIST SP 800-207 zero trust architecture.
- User-uploaded PDFs are stored under `backend/uploads/user_<id>/` during local
  development.
- The generated FAISS and BM25 indexes are stored under
  `backend/vector_db/`.
- The production Compose file persists uploads in the `backend_uploads` Docker
  volume and indexes in the `backend_vector_db` Docker volume.

The backend automatically indexes documents in `backend/knowledge_base/` on
startup when the RAG indexes do not exist. Newly uploaded documents are indexed
immediately and added to both the semantic and lexical indexes.

---

# 🔎 Verify Running Containers

```bash
docker ps
```

Expected services:

```text
cybershield-frontend
cybershield-backend
cybershield-postgres
```

---

# 🧪 Testing the Application

After startup:

1. Open `http://localhost`
2. Create an account
3. Log in
4. Open the Dashboard
5. Test the AI Dashboard
6. Ask CyberGPT a cybersecurity question
7. Test Password Analyzer
8. Test URL Scanner
9. Upload a security document
10. Test document Q&A and summarization
11. Confirm the answer cites the uploaded document and inspect retrieval metrics

Example CyberGPT question:

```text
What is phishing and how can an organization protect against it?
```

---

# 🛑 Stop the Application

```bash
docker compose down
```

This stops and removes the containers while preserving persistent Docker volumes.

# 🔄 Restart the Application

```bash
docker compose up -d
```

# 🧹 Full Reset

To stop the application and remove persistent Docker volumes:

```bash
docker compose down -v
```

> **Warning:** Removing volumes deletes the PostgreSQL database. Hosted model
> configuration is kept in `backend/.env` and is not stored in Docker volumes.

---

# 🔐 Security Notes

- Do not commit the `.env` file.
- Use `.env.example` as the configuration template.
- Replace placeholder secrets before production deployment.
- Store external API keys in environment variables.
- The included configuration is intended primarily for local and portfolio deployment.

---

# 🖼️ Screenshots

Screenshots can be added here to showcase:
- Login
- Registration
- Dashboard
- AI Dashboard
- CyberGPT
- Threat Intelligence
- URL Scanner
- Password Analyzer
- Document Intelligence

Example structure:

```text
docs/
└── screenshots/
    ├── login.png
    ├── dashboard.png
    ├── cybergpt.png
    ├── threat-intelligence.png
    ├── url-scanner.png
    └── password-analyzer.png
```

---

# 💻 Development

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

> For the complete application, including PostgreSQL, Groq API integration, and Nginx, Docker Compose is recommended.

---

# 🚧 Future Improvements

- AWS deployment
- Kubernetes deployment
- CI/CD pipeline
- Multi-model AI support
- Real-time threat intelligence feeds
- Redis caching
- Role-based access control
- Production monitoring and observability

---

# 📌 Project Highlights

CyberShield AI demonstrates hands-on experience with:

- Full-stack application development
- REST API design
- FastAPI backend development
- React + TypeScript frontend development
- PostgreSQL database design
- JWT authentication
- Docker containerization
- Docker Compose orchestration
- Nginx reverse proxy
- Local LLM deployment
- RAG pipelines
- Hybrid retrieval
- BM25 search
- Vector search
- AI-powered cybersecurity workflows

---

# 📄 License

This project is intended for educational, demonstration, and portfolio purposes.
