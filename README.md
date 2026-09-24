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
