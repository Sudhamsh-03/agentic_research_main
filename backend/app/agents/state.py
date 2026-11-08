import operator
from typing import Annotated, Any, TypedDict


class ResearchState(TypedDict, total=False):
    """State carried between graph nodes.

    `queries`, `documents` and `notes` use an additive reducer so each researcher round
    contributes to the running set instead of replacing it.
    """

    session_id: str
    topic: str
    depth: int
    tone: str
    target_words: int
    round: int
    new_documents_last_round: int
    queries: Annotated[list[str], operator.add]
    documents: Annotated[list[dict[str, Any]], operator.add]
    notes: Annotated[list[str], operator.add]
    report_markdown: str
    sources: list[dict[str, Any]]
