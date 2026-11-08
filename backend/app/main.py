import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, sessions, stream
from app.config import get_settings
from app.db.base import init_db

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Multi-agent research pipeline. A researcher agent gathers sources and an "
        "editor agent turns them into a Markdown brief, with node status streamed "
        "over Server-Sent Events."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(stream.router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}
