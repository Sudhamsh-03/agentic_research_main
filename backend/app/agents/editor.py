from app.agents.llm import build_chat_model
from app.agents.prompts import EDITOR_PROMPT
from app.agents.state import ResearchState

AGENT_NAME = "editor"
MAX_SOURCES = 12


def _text_of(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        parts = [
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ]
        return "\n".join(parts).strip()
    return str(content).strip()


def _select_sources(documents: list[dict]) -> list[dict]:
    """Keep usable, de-duplicated sources, best-scored first."""
    seen: set[str] = set()
    usable = []
    for document in sorted(documents, key=lambda d: d.get("score", 0.0), reverse=True):
        url = (document.get("url") or "").strip()
        snippet = (document.get("snippet") or "").strip()
        if not url or not snippet or url in seen:
            continue
        seen.add(url)
        usable.append(
            {
                "title": (document.get("title") or url).strip(),
                "url": url,
                "snippet": snippet[:600],
            }
        )
        if len(usable) >= MAX_SOURCES:
            break
    return usable


def _render_sources(sources: list[dict]) -> str:
    if not sources:
        return ""
    lines = [
        f"{index + 1}. [{item['title']}]({item['url']})"
        for index, item in enumerate(sources)
    ]
    return "\n## Sources\n\n" + "\n".join(lines) + "\n"


def _template_brief(state: ResearchState, notes: list[str], sources: list[dict]) -> str:
    topic = state["topic"]
    findings = notes[:10] or ["- No usable research notes were collected for this topic."]
    summary = (
        f"This brief collates {len(sources)} source(s) gathered over "
        f"{state.get('round', 0)} research round(s) on {topic}. It was produced without a "
        "language model, so the findings below are the condensed source material rather "
        "than a synthesised narrative."
    )
    body = "\n".join(line if line.startswith("-") else f"- {line}" for line in findings)
    return (
        f"# {topic}\n\n"
        f"## Executive summary\n\n{summary}\n\n"
        f"## Key findings\n\n{body}\n\n"
        "## Open questions\n\n"
        "- Which of the collected sources are authoritative enough to rely on?\n"
        "- What has changed on this topic since the sources were published?\n"
    )


async def editor_node(state: ResearchState, config) -> dict:
    """Check the gathered material for usability and format a Markdown brief."""
    emit = config["configurable"]["emit"]
    await emit(agent=AGENT_NAME, status="active", message="Reviewing collected research")

    sources = _select_sources(state.get("documents", []))
    notes = [note for note in state.get("notes", []) if note.strip()]

    if not sources and not notes:
        await emit(
            agent=AGENT_NAME,
            status="warning",
            message="No usable sources were found; writing a minimal brief",
        )

    model = build_chat_model()
    if model is None:
        markdown = _template_brief(state, notes, sources)
    else:
        rendered_sources = (
            "\n".join(
                f"[{index + 1}] {item['title']} - {item['url']}\n{item['snippet']}"
                for index, item in enumerate(sources)
            )
            or "(none)"
        )
        prompt = EDITOR_PROMPT.format(
            topic=state["topic"],
            tone=state.get("tone", "neutral"),
            target_words=state.get("target_words", 600),
            notes="\n".join(notes) or "(none)",
            sources=rendered_sources,
        )
        await emit(agent=AGENT_NAME, status="active", message="Drafting the brief")
        try:
            response = await model.ainvoke(prompt)
            markdown = _text_of(response)
        except Exception as exc:
            await emit(
                agent=AGENT_NAME,
                status="warning",
                message=(
                    f"Model call failed ({exc.__class__.__name__}); using template output"
                ),
            )
            markdown = _template_brief(state, notes, sources)

    markdown = markdown.strip() + "\n" + _render_sources(sources)
    await emit(agent=AGENT_NAME, status="complete", message="Brief ready")
    return {"report_markdown": markdown, "sources": sources}
