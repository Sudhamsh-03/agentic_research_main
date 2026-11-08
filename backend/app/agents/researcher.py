import json
import re

from app.agents.llm import build_chat_model
from app.agents.prompts import NOTES_PROMPT, QUERY_PROMPT
from app.agents.state import ResearchState
from app.config import get_settings
from app.services.search import SearchError, build_search_provider

AGENT_NAME = "researcher"
MAX_DOCUMENTS = 24
FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _text_of(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        parts = [
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ]
        return "\n".join(parts).strip()
    return str(content).strip()


def _parse_query_list(raw: str, fallback: list[str]) -> list[str]:
    cleaned = FENCE_PATTERN.sub("", raw).strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            queries = [str(item).strip() for item in parsed if str(item).strip()]
            if queries:
                return queries
    except json.JSONDecodeError:
        pass
    lines = [
        re.sub(r"^[-*\d.)\s]+", "", line).strip().strip('"')
        for line in cleaned.splitlines()
        if line.strip()
    ]
    queries = [line for line in lines if len(line) > 3]
    return queries or fallback


def _fallback_queries(topic: str, round_number: int, count: int) -> list[str]:
    angles = [
        topic,
        f"{topic} latest developments",
        f"{topic} criticism and limitations",
        f"{topic} practical examples",
        f"{topic} outlook",
        f"{topic} comparison",
    ]
    start = ((round_number - 1) * count) % len(angles)
    rotated = angles[start:] + angles[:start]
    return rotated[:count]


async def _plan_queries(
    model, state: ResearchState, round_number: int, count: int
) -> list[str]:
    fallback = _fallback_queries(state["topic"], round_number, count)
    if model is None:
        return fallback
    prompt = QUERY_PROMPT.format(
        topic=state["topic"],
        round=round_number,
        depth=state.get("depth", 1),
        count=count,
        notes="\n".join(state.get("notes", [])) or "(none yet)",
        used="\n".join(state.get("queries", [])) or "(none yet)",
    )
    try:
        response = await model.ainvoke(prompt)
    except Exception:
        # A provider hiccup degrades query planning; it must not end the run.
        return fallback
    return _parse_query_list(_text_of(response), fallback)[:count]


async def _condense(model, topic: str, documents: list[dict]) -> list[str]:
    if not documents:
        return []
    if model is None:
        return [
            f"- {doc['title']}: {doc['snippet'][:280]}".rstrip()
            for doc in documents
            if doc.get("snippet")
        ]
    rendered = "\n\n".join(
        f"[{index + 1}] {doc['title']}\n{doc['url']}\n{doc['snippet'][:1200]}"
        for index, doc in enumerate(documents)
    )
    prompt = NOTES_PROMPT.format(topic=topic, sources=rendered)
    try:
        response = await model.ainvoke(prompt)
    except Exception:
        return [
            f"- {doc['title']}: {doc['snippet'][:280]}".rstrip() for doc in documents
        ]
    bullets = [
        line.strip()
        for line in _text_of(response).splitlines()
        if line.strip().startswith("-")
    ]
    return bullets[:6]


async def researcher_node(state: ResearchState, config) -> dict:
    """Plan queries, run the search tool, and condense what came back into notes."""
    settings = get_settings()
    emit = config["configurable"]["emit"]
    round_number = state.get("round", 0) + 1

    await emit(
        agent=AGENT_NAME,
        status="active",
        message=f"Round {round_number}: planning search queries",
    )

    model = build_chat_model()
    queries = await _plan_queries(model, state, round_number, settings.queries_per_round)
    await emit(
        agent=AGENT_NAME,
        status="active",
        message="Searching: " + "; ".join(queries),
    )

    provider = build_search_provider()
    existing = state.get("documents", [])
    seen_urls = {doc.get("url") for doc in existing}
    collected: list[dict] = []
    for query in queries:
        if len(existing) + len(collected) >= MAX_DOCUMENTS:
            break
        try:
            results = await provider.search(query, settings.search_results_per_query)
        except SearchError as exc:
            await emit(
                agent=AGENT_NAME, status="warning", message=f"Search failed: {exc}"
            )
            continue
        for document in results:
            if not document.url or document.url in seen_urls:
                continue
            seen_urls.add(document.url)
            collected.append(document.as_dict())

    await emit(
        agent=AGENT_NAME,
        status="active",
        message=f"Collected {len(collected)} new source(s); condensing notes",
    )
    notes = await _condense(model, state["topic"], collected)

    await emit(
        agent=AGENT_NAME,
        status="complete",
        message=(
            f"Round {round_number} done: {len(collected)} source(s), {len(notes)} note(s)"
        ),
    )

    return {
        "round": round_number,
        "queries": queries,
        "documents": collected,
        "notes": notes,
        "new_documents_last_round": len(collected),
    }
