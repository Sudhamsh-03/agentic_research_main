import logging

from app.agents.graph import get_graph
from app.db.base import SessionLocal
from app.repositories import research as repo
from app.services.events import event_bus

logger = logging.getLogger(__name__)

NODE_SEQUENCE = ["researcher", "editor"]


async def run_research_session(session_id: str) -> None:
    """Execute the agent graph for one session, persisting and streaming every step."""
    async with SessionLocal() as db:
        session = await repo.get_session(db, session_id)
        if session is None:
            logger.warning("run requested for unknown session %s", session_id)
            return

        async def emit(agent: str, status: str, message: str) -> None:
            await repo.append_log(
                db,
                session_id,
                agent_name=agent,
                node_status=status,
                step_output=message,
            )
            await event_bus.publish(
                session_id,
                {"type": "node", "agent": agent, "status": status, "message": message},
            )

        await repo.set_status(db, session_id, "running")
        await event_bus.publish(
            session_id,
            {
                "type": "status",
                "status": "running",
                "message": f"Researching: {session.topic}",
                "nodes": NODE_SEQUENCE,
            },
        )

        initial_state = {
            "session_id": session_id,
            "topic": session.topic,
            "depth": session.depth,
            "tone": session.tone,
            "target_words": session.target_words,
            "round": 0,
            "new_documents_last_round": 0,
            "queries": [],
            "documents": [],
            "notes": [],
        }

        try:
            result = await get_graph().ainvoke(
                initial_state,
                config={"configurable": {"emit": emit}, "recursion_limit": 25},
            )
            markdown = (result.get("report_markdown") or "").strip()
            if not markdown:
                raise RuntimeError("the editor produced an empty brief")
            report = await repo.save_report(
                db,
                session_id,
                summary_markdown=markdown,
                sources=result.get("sources", []),
            )
            await repo.set_status(db, session_id, "completed")
            await event_bus.publish(
                session_id,
                {
                    "type": "completed",
                    "status": "completed",
                    "message": "Brief generated",
                    "report_id": report.report_id,
                },
            )
        except Exception as exc:
            logger.exception("research run failed for session %s", session_id)
            message = f"{exc.__class__.__name__}: {exc}"
            await repo.set_status(db, session_id, "failed", error_message=message)
            await event_bus.publish(
                session_id,
                {"type": "failed", "status": "failed", "message": message},
            )
