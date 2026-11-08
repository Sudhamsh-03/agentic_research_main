from app.agents.editor import _select_sources, _template_brief
from app.agents.graph import route_after_research
from app.agents.researcher import _fallback_queries, _parse_query_list
from app.services.events import EventBus
from app.services.search import OfflineSearchProvider


def test_router_loops_until_depth_is_reached():
    state = {"round": 1, "depth": 3, "new_documents_last_round": 2, "documents": [{}]}
    assert route_after_research(state) == "researcher"


def test_router_hands_off_once_depth_is_reached():
    state = {"round": 3, "depth": 3, "new_documents_last_round": 2, "documents": [{}]}
    assert route_after_research(state) == "editor"


def test_router_stops_early_when_a_round_found_nothing():
    state = {"round": 1, "depth": 4, "new_documents_last_round": 0, "documents": [{}]}
    assert route_after_research(state) == "editor"


def test_query_parser_reads_a_json_array():
    raw = '["agent orchestration", "state graphs"]'
    assert _parse_query_list(raw, ["fallback"]) == ["agent orchestration", "state graphs"]


def test_query_parser_recovers_from_a_bulleted_list():
    raw = "- agent orchestration\n- state graphs"
    assert _parse_query_list(raw, ["fallback"]) == ["agent orchestration", "state graphs"]


def test_query_parser_falls_back_on_unusable_output():
    assert _parse_query_list("", ["fallback"]) == ["fallback"]


def test_fallback_queries_rotate_per_round():
    first = _fallback_queries("langgraph", 1, 3)
    second = _fallback_queries("langgraph", 2, 3)
    assert first != second
    assert len(first) == 3


def test_editor_drops_duplicate_and_empty_sources():
    documents = [
        {"title": "A", "url": "https://example.invalid/a", "snippet": "useful", "score": 0.9},
        {"title": "A again", "url": "https://example.invalid/a", "snippet": "dupe", "score": 0.8},
        {"title": "B", "url": "https://example.invalid/b", "snippet": "", "score": 0.7},
        {"title": "C", "url": "", "snippet": "no url", "score": 0.6},
    ]
    selected = _select_sources(documents)
    assert [item["url"] for item in selected] == ["https://example.invalid/a"]


def test_template_brief_has_the_expected_sections():
    state = {"topic": "langgraph", "round": 1}
    markdown = _template_brief(state, ["- a note"], [])
    assert markdown.startswith("# langgraph")
    assert "## Executive summary" in markdown
    assert "## Key findings" in markdown
    assert "## Open questions" in markdown


async def test_offline_search_is_deterministic():
    provider = OfflineSearchProvider()
    first = await provider.search("langgraph", 3)
    second = await provider.search("langgraph", 3)
    assert [doc.url for doc in first] == [doc.url for doc in second]
    assert len(first) == 3


async def test_event_bus_replays_to_a_late_subscriber():
    bus = EventBus()
    await bus.publish("s1", {"type": "node", "message": "first"})

    queue, replay = bus.subscribe("s1")
    assert [event["message"] for event in replay] == ["first"]

    await bus.publish("s1", {"type": "completed", "message": "done"})
    delivered = await queue.get()
    assert delivered["message"] == "done"
    assert bus.is_finished("s1")

    bus.unsubscribe("s1", queue)
    bus.clear("s1")
    assert not bus.is_finished("s1")
