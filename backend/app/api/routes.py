from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.database import get_db

from app.core.logger import logger

router = APIRouter()


@router.get("/")
def home():
    logger.info("Home endpoint accessed")

    return {
        "message": "Welcome to CyberShield AI"
    }


@router.get("/health")
def health():
    logger.info("Health check endpoint accessed")

    return {
        "status": "ok"
    }

@router.get("/ready")
def ready(details: bool = False, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db.execute(text("SELECT user_id FROM threat_searches LIMIT 0"))
    except Exception:
        db.rollback()
        raise HTTPException(503, "Database or required ownership schema unavailable.") from None
    if not details:
        return {"status": "ready", "database": "available", "ownership_schema": "available"}
    from app.core.config import settings
    from app.knowledge.production_catalog import availability
    try:
        knowledge = availability()
    except Exception:
        knowledge = {"bundled_sources_available": 0, "shared_index_available": False}
    return {"status": "ready", "database": "available", "ownership_schema": "available",
            "cybergpt_v2": {"enabled": settings.CYBERGPT_V2_ENABLED, "provider": settings.LLM_PROVIDER,
                            "model": settings.GROQ_MODEL if settings.LLM_PROVIDER == "groq" else settings.OPENAI_MODEL, **knowledge}}
