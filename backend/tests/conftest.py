import os
import tempfile
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / "agentic_research_test.db"
if TEST_DB.exists():
    TEST_DB.unlink()

# Settings are read at import time, so the test environment must be set first.
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB.as_posix()}"
os.environ["LLM_PROVIDER"] = "offline"
os.environ["SEARCH_PROVIDER"] = "offline"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db.base import engine, init_db  # noqa: E402
from app.db.models import Base  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


@pytest.fixture
def topic() -> str:
    return "state machines for multi-agent orchestration"
