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
from app.api.dashboard_ai_routes import (
    router as dashboard_ai_router,
)

from app.api.upload_routes import (
    router as upload_router,
)

from app.core.config import settings
from app.services.knowledge_base_service import KnowledgeBaseService

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# Creating the tables is unguarded in the sense that a failure is fatal to the
# request path either way - but not to the process. Uncaught, an unreachable
# database at import time kills the application before it can bind a port, so
# the platform sees a crashed service and /health cannot report anything. The
# message below names the host, which is the actual mistake nine times out of
# ten: a DATABASE_URL still pointing at the compose service name (`postgres`)
# on a machine where that name does not resolve.
try:
    init_db()
except Exception as error:  # pragma: no cover - depends on the environment
    print(
        f"[startup] database not reachable ({type(error).__name__}). "
        f"DATABASE_URL host is "
        f"{settings.DATABASE_URL.rsplit('@', 1)[-1].split('/')[0]!r}. "
        "The API will start, but every endpoint that touches the database "
        "will fail until this is fixed. For local development, point "
        "DATABASE_URL at SQLite: sqlite:///./local_dev.db"
    )

# The index build runs at startup and is the one step that can take a minute or
# more on a cold free-tier instance: it loads the ONNX encoder and embeds every
# knowledge-base chunk. It is wrapped because a failure here used to abort the
# import and take the whole application down - including /health and every
# endpoint that does not need retrieval. Degrading to "retrieval unavailable"
# is strictly better than not booting, and the reason is logged so it is not
# silent.
try:
    index_status = KnowledgeBaseService.ensure_index()
    print(f"[startup] knowledge base index: {index_status}")
except Exception as error:  # pragma: no cover - depends on the environment
    print(
        "[startup] knowledge base index could not be prepared "
        f"({type(error).__name__}: {error}). The API will start, but "
        "knowledge-base retrieval will report no results until it succeeds."
    )
# ==========================================
# CORS Configuration
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
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
app.include_router(dashboard_ai_router)
app.include_router(upload_router)

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