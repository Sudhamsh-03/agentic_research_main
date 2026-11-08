from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents.editor import editor_node
from app.agents.researcher import researcher_node
from app.agents.state import ResearchState

MAX_DOCUMENTS_BEFORE_EDIT = 20


def route_after_research(state: ResearchState) -> str:
    """Loop the researcher until the requested depth is reached.

    The loop also stops early when a round found nothing new or enough material is
    already in hand, so a thin topic does not burn the whole depth budget.
    """
    if state.get("round", 0) >= state.get("depth", 1):
        return "editor"
    if state.get("new_documents_last_round", 0) == 0:
        return "editor"
    if len(state.get("documents", [])) >= MAX_DOCUMENTS_BEFORE_EDIT:
        return "editor"
    return "researcher"


def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("researcher", researcher_node)
    graph.add_node("editor", editor_node)
    graph.add_edge(START, "researcher")
    graph.add_conditional_edges(
        "researcher",
        route_after_research,
        {"researcher": "researcher", "editor": "editor"},
    )
    graph.add_edge("editor", END)
    return graph.compile()


@lru_cache
def get_graph():
    return build_graph()
