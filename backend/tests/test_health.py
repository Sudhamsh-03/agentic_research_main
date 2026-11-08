async def test_health_reports_database_and_providers(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["llm_provider"] == "offline"
    assert body["search_provider"] == "offline"


async def test_root_points_at_the_docs(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
