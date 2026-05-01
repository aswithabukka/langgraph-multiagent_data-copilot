"""
FastAPI endpoints for the LangGraph Data Copilot.

Error-handling contract:

* `/api/infer` returns 200 with the structured `QueryResponse` shape — the
  Streamlit UI relies on the `error` field for partial-success rendering.
  An *unhandled* internal failure still raises 500 (FastAPI default) so
  ops can spot bugs.
* All other endpoints raise `HTTPException` with the right status code
  and let FastAPI's exception handler render the body. Returning 200 with
  `{"error": ...}` was masking failures from clients.
"""

import logging
import os
import re
from typing import Dict, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse

from app.agents.graph import process_query
from app.db.database import (
    check_database_health,
    execute_query,
    get_all_tables,
    get_database_info,
    get_table_schema,
)
from app.models.state import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter()

CHART_DIR = os.path.realpath(os.getenv("CHART_DIR", "./charts"))

# Charts are written by the chart agent with safe filenames (UUID + extension);
# accept only that shape to prevent path traversal via the URL.
_CHART_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-]+\.(png|jpg|jpeg|svg)$")

# Cap on /tables/{name}/data — keep one source of truth.
_MAX_TABLE_LIMIT = 1000


@router.post("/infer", response_model=QueryResponse)
async def infer(request: QueryRequest) -> Dict:
    """Run a natural-language query through the agent graph.

    Returns 200 with `error` populated for handled failures (so the UI can
    still render context). Truly unexpected exceptions bubble up as 500.
    """
    result = await process_query(
        {"query": request.query, "session_id": request.session_id}
    )

    chart_url = None
    chart_path = result.get("chart_url")
    if chart_path:
        chart_url = f"/api/charts/{os.path.basename(chart_path)}"

    return {
        "answer": result.get("answer", ""),
        "sql": result.get("sql"),
        "chart_url": chart_url,
        "rows": result.get("rows", []),
        "df_summary": result.get("df_summary"),
        "processing_time_ms": result.get("processing_time_ms"),
        "error": result.get("error"),
    }


@router.get("/charts/{filename}")
async def get_chart(filename: str) -> FileResponse:
    """Serve a chart image, with strict filename + path-confinement checks."""
    if not _CHART_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="Chart not found")

    file_path = os.path.realpath(os.path.join(CHART_DIR, filename))
    if os.path.commonpath([file_path, CHART_DIR]) != CHART_DIR:
        raise HTTPException(status_code=404, detail="Chart not found")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Chart not found")

    return FileResponse(file_path)


@router.get("/health")
async def health_check():
    """Liveness probe — returns 503 if the database is unreachable."""
    is_healthy, error_message = check_database_health()

    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": {"status": "unhealthy", "error": error_message},
            },
        )

    return {"status": "healthy", "database": {"status": "healthy"}}


@router.get("/schema")
async def get_schema() -> Dict:
    """Return the full database schema."""
    try:
        return {"schema": get_database_info()}
    except Exception as e:
        logger.exception("get_schema failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
async def get_tables() -> Dict[str, List[str]]:
    """List every table in the database."""
    try:
        return {"tables": get_all_tables()}
    except Exception as e:
        logger.exception("get_tables failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}")
async def get_table_schema_endpoint(table_name: str) -> Dict:
    """Return schema info for a single table."""
    if table_name not in set(get_all_tables()):
        raise HTTPException(status_code=404, detail="Unknown table")

    try:
        return {"schema": get_table_schema(table_name)}
    except Exception as e:
        logger.exception("get_table_schema_endpoint failed for %s", table_name)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/data")
async def get_table_data(table_name: str, limit: int = 50) -> Dict:
    """Return sample data from a single table.

    `table_name` is whitelisted against the live schema (no injection, no
    access to `sqlite_*` internals); `limit` is bounded to [1, 1000].
    """
    if table_name not in set(get_all_tables()):
        raise HTTPException(status_code=404, detail="Unknown table")

    safe_limit = max(1, min(int(limit), _MAX_TABLE_LIMIT))

    try:
        rows = execute_query(f"SELECT * FROM {table_name} LIMIT {safe_limit}")
        count_result = execute_query(f"SELECT COUNT(*) AS total FROM {table_name}")
        total_count = count_result[0]["total"] if count_result else 0
    except Exception as e:
        logger.exception("get_table_data failed for %s", table_name)
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "rows": rows,
        "count": len(rows),
        "total_count": total_count,
        "table_name": table_name,
    }
