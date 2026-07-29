from fastapi import APIRouter

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
        "status": "Healthy"
    }