# 🛡️ CyberShield AI

An AI-powered cybersecurity platform that combines threat intelligence, document intelligence, vulnerability analysis, and an enterprise security copilot into a single application.

Built using **FastAPI**, **React**, **PostgreSQL**, **Docker**, and **Ollama (Llama 3)**.

---

# Features

### 🤖 CyberGPT (Enterprise Security Copilot)

- AI-powered cybersecurity assistant
- Hybrid RAG over uploaded security documents
- Conversation memory
- Document summarization
- Multi-document comparison
- Security best practice recommendations

---

### 📄 Document Intelligence

- Upload PDF security reports
- Hybrid RAG (BM25 + Vector Search)
- AI summaries
- AI document comparison
- Source citations

---

### 🛡️ Threat Intelligence Dashboard

- AI-generated security summaries
- CVE insights
- Security recommendations
- Executive dashboard

---

### 🔍 URL Scanner

- URL reputation analysis
- Phishing detection
- Risk assessment

---

### 🔐 Password Analyzer

- Password strength evaluation
- Entropy analysis
- Security recommendations

---

### 👤 Authentication

- JWT Authentication
- Login / Registration
- Protected routes

---

# Tech Stack

## Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- LangChain
- Hybrid RAG
- Ollama
- Llama 3

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

# Project Architecture

```
                    Browser
                        │
                        ▼
               React Frontend
                        │
                REST API Calls
                        │
                        ▼
                 FastAPI Backend
          ┌─────────────┴─────────────┐
          ▼                           ▼
   PostgreSQL                  Ollama (Llama 3)
          │                           │
          └─────────────┬─────────────┘
                        ▼
                  Hybrid RAG Engine
```

---

# Screenshots

> Add screenshots here.

- Login
- Dashboard
- CyberGPT
- Threat Intelligence
- URL Scanner
- Password Analyzer

---

# Quick Start

## Prerequisites

Install:

- Docker Desktop

---

## Clone Repository

```bash
git clone https://github.com/MoAftab-01/CyberShield-AI.git

cd CyberShield-AI
```

---

## Run the Project

```bash
docker compose up -d
```

---

## Open the Application

Frontend

```
http://localhost
```

Backend API

```
http://localhost:8000/docs
```

---

# First Startup

On the first startup Docker will automatically:

- Build the backend
- Build the frontend
- Start PostgreSQL
- Start Ollama
- Automatically download the **Llama 3** model (one-time setup)

The initial setup may take several minutes depending on your internet connection.

Subsequent startups are significantly faster because the model is cached.

---

# Docker Services

| Service | Port |
|----------|------|
| Frontend | 80 |
| Backend | 8000 |
| PostgreSQL | 5432 |
| Ollama | 11434 |

---

# Stopping the Application

```bash
docker compose down
```

---

# Restarting

```bash
docker compose up -d
```

---

# Development

Backend

```bash
cd backend

uvicorn app.main:app --reload
```

Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# Future Improvements

- AWS Deployment
- Kubernetes Deployment
- CI/CD Pipeline
- Multi-model AI Support
- Real-time Threat Feeds
- Redis Caching
- User Role Management

---

# License

This project is intended for educational and portfolio purposes.
