import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Naive UTC, so values round-trip identically on SQLite and PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    sessions: Mapped[list["ResearchSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    topic: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    depth: Mapped[int] = mapped_column(Integer, default=2)
    tone: Mapped[str] = mapped_column(String(50), default="neutral")
    target_words: Mapped[int] = mapped_column(Integer, default=600)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")
    logs: Mapped[list["AgentLog"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AgentLog.timestamp",
    )
    report: Mapped["FinalReport | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )


class AgentLog(Base):
    __tablename__ = "agent_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("research_sessions.session_id", ondelete="CASCADE"),
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(50))
    node_status: Mapped[str] = mapped_column(String(20))
    step_output: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    session: Mapped[ResearchSession] = relationship(back_populates="logs")


class FinalReport(Base):
    __tablename__ = "final_reports"

    report_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("research_sessions.session_id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    summary_markdown: Mapped[str] = mapped_column(Text)
    raw_sources: Mapped[str] = mapped_column(Text, default="[]")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    session: Mapped[ResearchSession] = relationship(back_populates="report")
