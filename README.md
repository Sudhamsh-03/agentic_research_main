# Agentic Research & Summarizer Dashboard

An autonomous research pipeline with a live dashboard. Submit a topic and two agents work
it end to end: a **Researcher** plans search queries, calls a web search tool and collects
sources, then an **Editor** checks the material, synthesises it and formats a Markdown
executive brief. Node-level status is streamed to the browser over Server-Sent Events, so
the UI shows *Researcher active → Editor active → Completed* as it happens. Every run is
saved and browsable afterwards.

- `backend/` — FastAPI, LangGraph state graph, SQLAlchemy over SQLite
- `frontend/` — React + Vite single-page app

See [PLAN.md](PLAN.md) for the architecture, data model and design decisions.

## Status

The code has not been executed. Nothing was installed and no server, build or test run was
started while writing it, so treat the first local run as the real smoke test. The commands
below are what it is designed to run with.

## Features

- Research form with depth (number of research rounds), tone and target length.
- LangGraph `StateGraph` where the researcher node loops until the requested depth is
  reached, then hands off to the editor node.
- Live agent timeline over SSE, with replay so a late or reloaded page still sees every
  step of a run.
- Markdown brief with numbered sources, viewable in the app and downloadable as `.md`.
- History view of past briefs with topic filter and delete.
- Runs without any API keys in offline mode, so the whole flow is demonstrable before you
  wire up real providers.

## Requirements

- Python 3.11 or newer
- Node.js 18 or newer

## Local setup

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

On Windows PowerShell use `.venv\Scripts\Activate.ps1` instead.

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file from the template at the repository root:

```bash
cp ../.env.example .env
```

The defaults in that file (`LLM_PROVIDER=offline`, `SEARCH_PROVIDER=offline`) let the app
run with no credentials. The database file `app.db` is created automatically on first
start.

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
```

```bash
cp .env.example .env
```

```bash
npm run dev
```

Open http://localhost:5173.

## Configuration

All backend settings are read from environment variables (see `.env.example`).

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./app.db` | SQLAlchemy async connection string |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed CORS origin(s), comma-separated |
| `LLM_PROVIDER` | `offline` | `openai`, `google` or `offline` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for the chosen provider |
| `OPENAI_API_KEY` | empty | Required when `LLM_PROVIDER=openai` |
| `OPENAI_BASE_URL` | empty | Point at any OpenAI-compatible server |
| `GOOGLE_API_KEY` | empty | Required when `LLM_PROVIDER=google` |
| `SEARCH_PROVIDER` | `offline` | `tavily` or `offline` |
| `TAVILY_API_KEY` | empty | Required when `SEARCH_PROVIDER=tavily` |
| `SEARCH_RESULTS_PER_QUERY` | `4` | Results requested per search query |

### Using real providers

For live web search, set `SEARCH_PROVIDER=tavily` and supply a `TAVILY_API_KEY`.

For real synthesis, set `LLM_PROVIDER=openai` with an `OPENAI_API_KEY`, or point
`OPENAI_BASE_URL` at a local OpenAI-compatible server. To use Gemini instead, install the
optional extra and set `LLM_PROVIDER=google` with a `GOOGLE_API_KEY`:

```bash
pip install langchain-google-genai
```

In offline mode the search tool returns deterministic placeholder documents and the editor
produces a template brief from them. Both failure paths are also exercised in offline
mode: a provider error degrades to the template output rather than failing the run.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API, database and provider status |
| `POST` | `/api/sessions` | Create a session and start the run in the background |
| `GET` | `/api/sessions` | List sessions, newest first |
| `GET` | `/api/sessions/{id}` | Session detail with agent log and brief |
| `GET` | `/api/sessions/{id}/events` | SSE stream of node events for a run |
| `DELETE` | `/api/sessions/{id}` | Delete a session, its logs and its brief |

SSE event names are `status`, `node`, `completed` and `failed`; each carries a JSON
payload with the agent name, status and message.

## Tests

```bash
cd backend
pytest
```

The suite covers the health endpoint, session creation through to a saved brief, depth
handling, validation and 404 paths, SSE replay of a finished run, graph routing, source
de-duplication and the event bus. It runs entirely in offline mode, so no network access or
API keys are needed.

## Known limitations

- The event bus is in-process, so run a single Uvicorn worker. Multiple workers would need
  a shared broker such as Redis pub/sub.
- There is no authentication. The schema keeps a `users` table and every session is owned
  by one seeded local user.
- Background runs are tied to the API process; restarting it mid-run leaves that session in
  `running` until it is deleted.
- SQLite is the default store. Moving to PostgreSQL is a `DATABASE_URL` change plus a
  driver install; no migration tooling is wired up yet.
