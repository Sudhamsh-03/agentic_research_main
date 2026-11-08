import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import research as repo
from app.services.events import TERMINAL_EVENTS, event_bus

router = APIRouter(prefix="/api/sessions", tags=["stream"])

KEEPALIVE_SECONDS = 15.0


def _frame(event: dict) -> str:
    return f"event: {event.get('type', 'message')}\ndata: {json.dumps(event)}\n\n"


async def _replay_from_database(db: AsyncSession, session_id: str) -> list[dict]:
    """Rebuild a finished run from its persisted logs, so reloads still show the timeline."""
    session = await repo.get_session(db, session_id)
    if session is None:
        return []
    events = [
        {
            "type": "node",
            "agent": log.agent_name,
            "status": log.node_status,
            "message": log.step_output,
            "ts": log.timestamp.isoformat(timespec="seconds") + "Z",
            "session_id": session_id,
        }
        for log in session.logs
    ]
    if session.status in {"completed", "failed"}:
        events.append(
            {
                "type": "completed" if session.status == "completed" else "failed",
                "status": session.status,
                "message": session.error_message or "Brief generated",
                "session_id": session_id,
            }
        )
    return events


@router.get("/{session_id}/events")
async def stream_session_events(
    session_id: str, request: Request, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    session = await repo.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="research session not found")

    queue, replay = event_bus.subscribe(session_id)
    if not replay and session.status in {"completed", "failed"}:
        replay = await _replay_from_database(db, session_id)

    async def generator():
        try:
            for event in replay:
                yield _frame(event)
                if event.get("type") in TERMINAL_EVENTS:
                    return
            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_SECONDS)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield _frame(event)
                if event.get("type") in TERMINAL_EVENTS:
                    return
        finally:
            event_bus.unsubscribe(session_id, queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
