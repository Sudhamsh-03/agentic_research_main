from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.schemas.research import HealthRead

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthRead)
async def health(db: AsyncSession = Depends(get_db)) -> HealthRead:
    settings = get_settings()
    try:
        await db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"
    return HealthRead(
        status="ok" if database == "ok" else "degraded",
        database=database,
        llm_provider=settings.llm_provider,
        search_provider=settings.search_provider,
    )
