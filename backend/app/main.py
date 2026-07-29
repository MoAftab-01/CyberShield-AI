from fastapi import FastAPI

from app.api.routes import router as base_router
from app.api.user_routes import router as user_router
from app.api.password_routes import router as password_router
from app.api.url_routes import router as url_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
# 🛡️ CyberShield AI

An AI-Powered Cybersecurity Platform built with FastAPI.

## Features

- 🔐 JWT Authentication
- 👤 User Management
- 🔑 Password Intelligence Engine
- 🌐 URL Reputation Scanner
- 🚀 Threat Intelligence (Coming Soon)
- 🤖 AI Security Advisor (Coming Soon)
- 📚 Hybrid RAG (Coming Soon)
- 🧠 Multi-Agent AI (Coming Soon)
""",
)

# Base Routes
app.include_router(base_router)

# User Authentication Routes
app.include_router(user_router)

# Password Intelligence Routes
app.include_router(password_router)

# URL Scanner Routes
app.include_router(url_router)


@app.get("/", tags=["Home"])
def home():
    return {
        "message": "Welcome to CyberShield AI 🚀",
        "version": settings.APP_VERSION,
        "status": "Running",
    }