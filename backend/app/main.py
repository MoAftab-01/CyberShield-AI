from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as base_router
from app.api.user_routes import router as user_router
from app.api.password_routes import router as password_router
from app.api.url_routes import router as url_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.report_routes import router as report_router
from app.database.init_db import init_db
from app.api.threat_routes import router as threat_router
from app.api.conversation_routes import router as conversation_router

from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)
init_db()
# ==========================================
# CORS Configuration
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Register Routers
# ==========================================

app.include_router(base_router)
app.include_router(user_router)
app.include_router(password_router)
app.include_router(url_router)
app.include_router(dashboard_router)
app.include_router(report_router)
app.include_router(threat_router)
app.include_router(conversation_router)

from app.api.copilot_routes import (
    router as copilot_router,
)


app.include_router(
    copilot_router
)

# ==========================================
# Root Endpoint
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Welcome to CyberShield AI 🚀",
        "version": settings.APP_VERSION,
        "status": "Running",
    }