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
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db.execute(text("SELECT user_id FROM threat_searches LIMIT 0"))
    except Exception:
        db.rollback()
        raise HTTPException(503, "Database or required ownership schema unavailable.") from None
    return {"status": "ready", "database": "available", "ownership_schema": "available"}
