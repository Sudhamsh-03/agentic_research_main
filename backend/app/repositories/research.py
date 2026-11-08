import json
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AgentLog, FinalReport, ResearchSession, utcnow


async def create_session(
    db: AsyncSession,
    *,
    user_id: str,
    topic: str,
    depth: int,
    tone: str,
    target_words: int,
) -> ResearchSession:
    session = ResearchSession(
        user_id=user_id,
        topic=topic,
        depth=depth,
        tone=tone,
        target_words=target_words,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str) -> ResearchSession | None:
    result = await db.execute(
        select(ResearchSession)
        .options(selectinload(ResearchSession.logs), selectinload(ResearchSession.report))
        .where(ResearchSession.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession, *, limit: int = 50, offset: int = 0, status: str | None = None
) -> list[ResearchSession]:
    query = (
        select(ResearchSession)
        .options(selectinload(ResearchSession.report))
        .order_by(ResearchSession.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        query = query.where(ResearchSession.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_sessions(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(ResearchSession))
    return int(result.scalar_one())


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    result = await db.execute(
        delete(ResearchSession).where(ResearchSession.session_id == session_id)
    )
    await db.commit()
    return bool(result.rowcount)


async def set_status(
    db: AsyncSession,
    session_id: str,
    status: str,
    *,
    error_message: str | None = None,
    completed_at: datetime | None = None,
) -> None:
    session = await db.get(ResearchSession, session_id)
    if session is None:
        return
    session.status = status
    if error_message is not None:
        session.error_message = error_message
    if completed_at is not None:
        session.completed_at = completed_at
    elif status in {"completed", "failed"}:
        session.completed_at = utcnow()
    await db.commit()


async def append_log(
    db: AsyncSession,
    session_id: str,
    *,
    agent_name: str,
    node_status: str,
    step_output: str = "",
) -> AgentLog:
    log = AgentLog(
        session_id=session_id,
        agent_name=agent_name,
        node_status=node_status,
        step_output=step_output,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_logs(db: AsyncSession, session_id: str) -> list[AgentLog]:
    result = await db.execute(
        select(AgentLog)
        .where(AgentLog.session_id == session_id)
        .order_by(AgentLog.timestamp)
    )
    return list(result.scalars().all())


async def save_report(
    db: AsyncSession,
    session_id: str,
    *,
    summary_markdown: str,
    sources: list[dict],
) -> FinalReport:
    existing = await db.execute(
        select(FinalReport).where(FinalReport.session_id == session_id)
    )
    report = existing.scalar_one_or_none()
    payload = json.dumps(sources, ensure_ascii=False)
    if report is None:
        report = FinalReport(
            session_id=session_id, summary_markdown=summary_markdown, raw_sources=payload
        )
        db.add(report)
    else:
        report.summary_markdown = summary_markdown
        report.raw_sources = payload
        report.generated_at = utcnow()
    await db.commit()
    await db.refresh(report)
    return report
