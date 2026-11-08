async def test_create_session_runs_the_graph_and_saves_a_brief(client, topic):
    created = await client.post("/api/sessions", json={"topic": topic, "depth": 2})
    assert created.status_code == 201
    session_id = created.json()["session_id"]

    detail = await client.get(f"/api/sessions/{session_id}")
    assert detail.status_code == 200
    body = detail.json()

    assert body["status"] == "completed"
    assert body["report"] is not None
    assert body["report"]["summary_markdown"].startswith("# ")
    assert body["report"]["sources"]
    agents = {log["agent_name"] for log in body["logs"]}
    assert agents == {"researcher", "editor"}


async def test_depth_controls_the_number_of_research_rounds(client, topic):
    shallow = await client.post("/api/sessions", json={"topic": topic, "depth": 1})
    session_id = shallow.json()["session_id"]
    body = (await client.get(f"/api/sessions/{session_id}")).json()
    rounds = [
        log
        for log in body["logs"]
        if log["agent_name"] == "researcher" and log["node_status"] == "complete"
    ]
    assert len(rounds) == 1


async def test_short_topic_is_rejected(client):
    response = await client.post("/api/sessions", json={"topic": "ai"})
    assert response.status_code == 422


async def test_depth_outside_range_is_rejected(client, topic):
    response = await client.post("/api/sessions", json={"topic": topic, "depth": 9})
    assert response.status_code == 422


async def test_unknown_session_returns_404(client):
    response = await client.get("/api/sessions/does-not-exist")
    assert response.status_code == 404


async def test_list_sessions_is_newest_first(client, topic):
    first = await client.post("/api/sessions", json={"topic": topic, "depth": 1})
    second = await client.post("/api/sessions", json={"topic": topic + " two", "depth": 1})

    listing = await client.get("/api/sessions")
    assert listing.status_code == 200
    ids = [item["session_id"] for item in listing.json()]
    assert ids[0] == second.json()["session_id"]
    assert first.json()["session_id"] in ids
    assert all(item["has_report"] for item in listing.json())


async def test_delete_session_removes_it(client, topic):
    created = await client.post("/api/sessions", json={"topic": topic, "depth": 1})
    session_id = created.json()["session_id"]

    deleted = await client.delete(f"/api/sessions/{session_id}")
    assert deleted.status_code == 204
    assert (await client.get(f"/api/sessions/{session_id}")).status_code == 404
    assert (await client.delete(f"/api/sessions/{session_id}")).status_code == 404


async def test_finished_run_replays_its_timeline_over_sse(client, topic):
    created = await client.post("/api/sessions", json={"topic": topic, "depth": 1})
    session_id = created.json()["session_id"]

    async with client.stream("GET", f"/api/sessions/{session_id}/events") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        payload = ""
        async for chunk in response.aiter_text():
            payload += chunk
    assert "event: node" in payload
    assert "event: completed" in payload
