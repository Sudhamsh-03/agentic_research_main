import json
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

Tone = Literal["neutral", "executive", "technical", "conversational"]


def _iso_utc(value: datetime | None) -> str | None:
    """Timestamps are stored as naive UTC; make that explicit on the wire."""
    if value is None:
        return None
    return value.isoformat(timespec="seconds") + "Z"


UtcDatetime = Annotated[datetime, PlainSerializer(_iso_utc, return_type=str)]
OptionalUtcDatetime = Annotated[
    datetime | None, PlainSerializer(_iso_utc, return_type=str | None)
]


class SessionCreate(BaseModel):
    topic: str = Field(min_length=4, max_length=500)
    depth: int = Field(default=2, ge=1, le=4)
    tone: Tone = "neutral"
    target_words: int = Field(default=600, ge=150, le=2500)

    @field_validator("topic")
    @classmethod
    def strip_topic(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 4:
            raise ValueError("topic must be at least 4 characters")
        return cleaned


class SourceRead(BaseModel):
    title: str = ""
    url: str = ""
    snippet: str = ""


class AgentLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    agent_name: str
    node_status: str
    step_output: str
    timestamp: UtcDatetime


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    summary_markdown: str
    generated_at: UtcDatetime
    sources: list[SourceRead] = Field(default_factory=list)

    @classmethod
    def from_model(cls, report) -> "ReportRead":
        try:
            sources = json.loads(report.raw_sources or "[]")
        except json.JSONDecodeError:
            sources = []
        return cls(
            report_id=report.report_id,
            summary_markdown=report.summary_markdown,
            generated_at=report.generated_at,
            sources=[SourceRead(**item) for item in sources if isinstance(item, dict)],
        )


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    topic: str
    status: str
    depth: int
    tone: str
    target_words: int
    error_message: str | None = None
    started_at: UtcDatetime
    completed_at: OptionalUtcDatetime = None
    has_report: bool = False


class SessionDetail(SessionSummary):
    logs: list[AgentLogRead] = Field(default_factory=list)
    report: ReportRead | None = None


class HealthRead(BaseModel):
    status: str
    database: str
    llm_provider: str
    search_provider: str
