from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env,
        "demo_mode": settings.demo_mode
    }


@router.get("/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/agents")
async def agents_health():
    from app.core.config import settings
    
    agents = {
        "classification": "unknown",
        "duplicate": "unknown",
        "priority": "unknown",
        "routing": "unknown",
        "monitoring": "unknown"
    }
    
    if settings.classification_agent_address:
        agents["classification"] = "configured"
    if settings.duplicate_agent_address:
        agents["duplicate"] = "configured"
    if settings.priority_agent_address:
        agents["priority"] = "configured"
    
    return {
        "status": "healthy",
        "agents": agents,
        "mode": settings.agent_mode
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}