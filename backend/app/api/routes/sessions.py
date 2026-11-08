from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.base import ensure_default_user
from app.db.models import ResearchSession
from app.repositories import research as repo
from app.schemas.research import (
    AgentLogRead,
    ReportRead,
    SessionCreate,
    SessionDetail,
    SessionSummary,
)
from app.services.events import event_bus
from app.services.pipeline import run_research_session

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _to_summary(session: ResearchSession, *, has_report: bool | None = None) -> SessionSummary:
    return SessionSummary(
        session_id=session.session_id,
        topic=session.topic,
        status=session.status,
        depth=session.depth,
        tone=session.tone,
        target_words=session.target_words,
        error_message=session.error_message,
        started_at=session.started_at,
        completed_at=session.completed_at,
        has_report=(session.report is not None) if has_report is None else has_report,
    )


@router.post("", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> SessionSummary:
    user = await ensure_default_user()
    session = await repo.create_session(
        db,
        user_id=user.user_id,
        topic=payload.topic,
        depth=payload.depth,
        tone=payload.tone,
        target_words=payload.target_words,
    )
    background_tasks.add_task(run_research_session, session.session_id)
    return _to_summary(session, has_report=False)


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[SessionSummary]:
    sessions = await repo.list_sessions(db, limit=limit, offset=offset, status=status_filter)
    return [_to_summary(session) for session in sessions]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)) -> SessionDetail:
    session = await repo.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="research session not found")
    summary = _to_summary(session)
    return SessionDetail(
        **summary.model_dump(),
        logs=[AgentLogRead.model_validate(log) for log in session.logs],
        report=ReportRead.from_model(session.report) if session.report else None,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)) -> None:
    deleted = await repo.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="research session not found")
    event_bus.clear(session_id)
