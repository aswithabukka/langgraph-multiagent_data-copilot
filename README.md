# LangGraph Multi-Agent Data Analysis Copilot

A production-ready Python application that lets users ask natural language
questions about data and receive insightful answers through a multi-agent
system built with LangGraph.

## Features

- **Natural language interface** — ask questions about your data in plain English
- **Multi-agent architecture** — specialized agents for planning, SQL generation, chart creation, and explanation
- **Async LLM calls** — agents use `ainvoke` so concurrent requests don't queue behind a single model call
- **Visualization** — automatic chart generation based on query results
- **Conversation memory** — maintains the history of queries and responses
- **Optional LLM cache** — memoize identical (model, prompt, temperature) tuples to skip the network round-trip
- **Production-ready** — FastAPI backend, Streamlit UI, multi-stage Dockerfiles running as non-root, and a full test suite

## Architecture

The system is a LangGraph workflow with four nodes plus pure helper modules.

| Module | Role |
|---|---|
| `app/agents/planner.py`   | Heuristics-based plan builder (no LLM call). Routes arithmetic and off-topic queries away from the graph. |
| `app/agents/sql.py`       | Generates and executes SQL via the LLM. Validates the query is read-only before running. |
| `app/agents/chart.py`     | Asks the LLM how to visualize the result, then renders via Matplotlib. |
| `app/agents/explainer.py` | Final natural-language answer. Short-circuits to canned responses for arithmetic and off-topic queries. |
| `app/agents/graph.py`     | Wires the nodes together and exposes `route_next` (pure routing logic, unit-tested in isolation). |
| `app/agents/parsing.py`   | Pure parsers for LLM output — `extract_sql_query`, `parse_plan`, `extract_chart_config`. No LLM, no DB. |
| `app/agents/intent.py`    | Classifiers + canned responders — `is_simple_arithmetic`, `is_data_related_query`, `requires_chart`, AST-based `evaluate_arithmetic` (never `eval`), `handle_off_topic_query`. |

Cheap shortcuts run before any LLM call: an arithmetic question is answered
deterministically by `evaluate_arithmetic`, and an off-topic query gets a
canned guidance reply from `handle_off_topic_query`.

## Tech stack

- **Python 3.11+**
- **LangGraph & LangChain** — multi-agent orchestration and LLM integration
- **OpenAI / Anthropic** — LLM providers
- **FastAPI** — API backend
- **Streamlit** — user interface
- **SQLAlchemy + SQLite** — database access
- **Pandas & Matplotlib** — data processing and visualization
- **Pydantic** — data validation
- **Docker** — multi-stage build, runs as a non-root `appuser`
- **pytest, ruff, black, mypy** — testing and code quality

## Project structure

```
langgraph-data-copilot/
├── app/
│   ├── agents/
│   │   ├── chart.py            # LLM-driven chart generator
│   │   ├── config.py           # LLM config + opt-in response cache
│   │   ├── explainer.py        # final natural-language answer
│   │   ├── graph.py            # workflow + route_next (testable)
│   │   ├── intent.py           # pure classifiers + canned responders
│   │   ├── parsing.py          # pure LLM-output parsers
│   │   ├── planner.py          # heuristic plan builder
│   │   ├── prompts.py
│   │   └── sql.py              # LLM-driven SQL generator
│   ├── api/
│   │   ├── app.py              # FastAPI app + CORS configuration
│   │   └── endpoints.py        # /infer, /charts, /tables, /schema, /health
│   ├── db/
│   │   ├── database.py
│   │   └── seed.sql
│   ├── models/
│   │   └── state.py            # Pydantic models (GraphState, etc.)
│   └── utils/
│       └── chart.py
├── charts/                     # generated chart images
├── scripts/
│   ├── init_db.py
│   └── integration/            # live-API smoke scripts (not pytest tests)
│       ├── README.md
│       ├── test_comprehensive.py
│       ├── test_full_system.py
│       └── test_new_schema.py
├── tests/                      # unit tests (no live API needed)
│   ├── test_chart.py
│   ├── test_graph.py
│   ├── test_intent.py
│   ├── test_parsing.py
│   └── test_sql_agent.py
├── ui/
│   └── streamlit_app.py
├── .env.example
├── Dockerfile                  # multi-stage, non-root, healthcheck
├── Dockerfile.streamlit        # non-root UI image
├── docker-compose.yml
├── main.py
├── pyproject.toml
├── DATABASE_SCHEMA.md
├── DEPLOYMENT_GUIDE.md
├── ENHANCED_FEATURES.md
├── SAMPLE_QUERIES.md
└── README.md
```

## Getting started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- OpenAI or Anthropic API key

### Installation

```bash
git clone https://github.com/aswithabukka/langgraph-multiagent_data-copilot.git
cd langgraph-multiagent_data-copilot

# Configure environment
cp .env.example .env
# edit .env with your API key(s) and any overrides

# Install (editable, with dev tools)
pip install -e ".[dev]"

# Initialize the database
python scripts/init_db.py
```

### Running locally

```bash
# Terminal 1 — API
python main.py

# Terminal 2 — Streamlit UI
streamlit run ui/streamlit_app.py
```

Open `http://localhost:8501` for the UI. The API is on `http://localhost:8000`
(`/docs` for the OpenAPI explorer).

### Running with Docker

```bash
docker-compose up -d --build
```

Containers run as a non-root `appuser`; the API image carries no compilers
(multi-stage build) and exposes a `HEALTHCHECK`.

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `OPENAI_API_KEY`     | _(required for OpenAI provider)_  |  |
| `OPENAI_MODEL`       | `gpt-4`                           |  |
| `ANTHROPIC_API_KEY`  | _(required for Anthropic provider)_ |  |
| `ANTHROPIC_MODEL`    | `claude-3-sonnet-20240229`        |  |
| `DATABASE_URL`       | `sqlite:///./app.db`              |  |
| `CHART_DIR`          | `./charts`                        | Where generated charts are written. Path is realpath-resolved on startup. |
| `LOG_LEVEL`          | `INFO`                            |  |
| `API_HOST`           | `0.0.0.0`                         |  |
| `API_PORT`           | `8000`                            |  |
| `CORS_ALLOW_ORIGINS` | `http://localhost:8501,http://127.0.0.1:8501` | Comma-separated allow-list. **No wildcard fallback.** |
| `LLM_CACHE`          | _(unset → off)_                   | `memory` for in-process cache, `sqlite` for persistent cache (needs `langchain-community`). |
| `LLM_CACHE_PATH`     | `./.llm_cache.sqlite`             | Used only when `LLM_CACHE=sqlite`. |

## Usage examples

### Data query

**User**: _"Average sales per region in Q2"_

The planner detects a data query, the SQL agent generates and runs the query,
the chart agent draws a bar chart, and the explainer summarizes the result.

### Arithmetic (no LLM call)

**User**: _"What is 25*4+10?"_

`is_simple_arithmetic` matches, `evaluate_arithmetic` parses the expression
through Python's `ast` module (never `eval`), and the answer is returned
without invoking the graph.

### Off-topic (no LLM call)

**User**: _"What is MapReduce?"_

`is_data_related_query` returns false. `handle_off_topic_query` returns a
canned redirection toward the data-analysis use case.

## API

### `POST /api/infer`

Run a natural-language query through the agent graph.

```json
// Request
{ "query": "Average sales per region in Q2", "session_id": "optional" }

// Response
{
  "answer": "...",
  "sql": "SELECT region, AVG(...) FROM orders ...",
  "chart_url": "/api/charts/<uuid>.png",
  "rows": [ /* up to 50 */ ],
  "df_summary": { "columns": [...], "shape": [...], "...": "..." },
  "processing_time_ms": 1234.5,
  "error": null
}
```

`/infer` returns 200 even on agent-level errors so the UI can render partial
results — check the `error` field. Truly unexpected exceptions surface as a
FastAPI 500.

### Other endpoints

| Endpoint | Behavior |
|---|---|
| `GET  /api/health`                       | Liveness probe. 200 healthy / 503 if the database is unreachable. |
| `GET  /api/schema`                       | Full database schema. 500 with `{"detail": ...}` on backend failure. |
| `GET  /api/tables`                       | List of tables. |
| `GET  /api/tables/{name}`                | Schema for a single table. **404 for unknown tables (whitelist).** |
| `GET  /api/tables/{name}/data?limit=N`   | Sample rows. `limit` is bounded to `[1, 1000]`. |
| `GET  /api/charts/{filename}`            | Serves a generated chart. **Filename validated and path confined to `CHART_DIR`** — path traversal returns 404. |

## Security & production-readiness

- CORS is an explicit allow-list (`CORS_ALLOW_ORIGINS` env). The wildcard `*`
  default is gone.
- The chart endpoint validates the filename against a strict regex and
  rejects any resolved path that escapes `CHART_DIR`.
- `/api/tables/{name}` and `/api/tables/{name}/data` whitelist the table
  against the live schema, so `sqlite_master` and other internals are not
  reachable.
- The OpenAI / Anthropic key is never logged — not even a prefix.
- `validate_sql_query` rejects anything that isn't a single `SELECT`.
- Both Docker images run as a dedicated non-root `appuser`. The API image
  is multi-stage so build tooling never ships in the runtime layer.
- LLM responses can be cached with `LLM_CACHE=memory` (zero deps) or
  `LLM_CACHE=sqlite` for persistence across restarts.

## Testing

Unit tests don't need a live API or an LLM key:

```bash
pytest tests/                       # 56 tests, ~1.5s
pytest --cov=app                    # with coverage
pytest -k "test_route or test_intent"   # targeted runs
```

`tests/test_sql_agent.py::test_sql_agent` is gated on `OPENAI_API_KEY` and
will be skipped if the key is not set.

The end-to-end smoke scripts under `scripts/integration/` hit a running
server (default `http://localhost:8000`, override with `API_URL`):

```bash
python main.py &
python scripts/integration/test_comprehensive.py
python scripts/integration/test_full_system.py
```

See [`scripts/integration/README.md`](scripts/integration/README.md) for the
full set.

## License

MIT — see `LICENSE`.

## Acknowledgments

- LangGraph team for the multi-agent framework
- LangChain team for the LLM tooling
- OpenAI / Anthropic for the language models
