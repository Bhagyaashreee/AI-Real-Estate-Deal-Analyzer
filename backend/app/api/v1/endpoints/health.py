from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.services.ollama_service import ollama_service

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive system health check:
    - FastAPI Backend status
    - SQLite Database connection
    - Local Ollama AI service status & model readiness
    """
    # 1. Database check
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Ollama AI service check
    ollama_info = await ollama_service.check_health()

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "type": "SQLite",
            "status": db_status,
        },
        "ai_engine": ollama_info,
    }
