"""
FastAPI endpoints for the LangGraph Data Copilot.

This module defines the API endpoints for the application.
"""

import os
import re
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse

from app.agents.graph import process_query
from app.db.database import check_database_health, get_all_tables, get_database_info, get_table_schema
from app.models.state import QueryRequest, QueryResponse

# Create router
router = APIRouter()

# Get chart directory from environment or use default
CHART_DIR = os.path.realpath(os.getenv("CHART_DIR", "./charts"))

# Charts are written by the chart agent with safe filenames (UUID + extension);
# accept only that shape to prevent path traversal via the URL.
_CHART_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-]+\.(png|jpg|jpeg|svg)$")


@router.post("/infer", response_model=QueryResponse)
async def infer(request: QueryRequest) -> Dict:
    """
    Process a natural language query and return the results.
    
    Args:
        request: Query request with natural language query
        
    Returns:
        Dictionary with answer, chart URL, and data rows
    """
    try:
        # Process the query
        result = await process_query({
            "query": request.query,
            "session_id": request.session_id,
        })
        
        # Convert chart path to URL if exists
        chart_url = None
        if result.get("chart_url"):
            # Extract filename from path
            chart_filename = os.path.basename(result["chart_url"])
            chart_url = f"/api/charts/{chart_filename}"
        
        # Return response
        return {
            "answer": result["answer"],
            "sql": result.get("sql"),  # Include SQL query
            "chart_url": chart_url,
            "rows": result["rows"],
            "df_summary": result["df_summary"],
            "processing_time_ms": result["processing_time_ms"],
            "error": None,
        }
    
    except Exception as e:
        # Handle errors
        return {
            "answer": f"Error processing query: {str(e)}",
            "sql": None,
            "chart_url": None,
            "rows": [],
            "df_summary": None,
            "processing_time_ms": None,
            "error": str(e),
        }


@router.get("/charts/{filename}")
async def get_chart(filename: str) -> FileResponse:
    """
    Serve a chart image by filename.
    
    Args:
        filename: Name of the chart file
        
    Returns:
        FileResponse with the chart image
        
    Raises:
        HTTPException: If the chart file is not found
    """
    # Reject anything that doesn't match the expected chart-filename shape
    # (defends against path traversal like `../../etc/passwd`).
    if not _CHART_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="Chart not found")

    # Resolve and confine the path to CHART_DIR
    file_path = os.path.realpath(os.path.join(CHART_DIR, filename))
    if os.path.commonpath([file_path, CHART_DIR]) != CHART_DIR:
        raise HTTPException(status_code=404, detail="Chart not found")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Chart not found")

    return FileResponse(file_path)


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check endpoint to verify the API and database are working.
    
    Returns:
        Dictionary with health status information
    """
    is_healthy, error_message = check_database_health()
    
    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": {
                    "status": "unhealthy",
                    "error": error_message,
                },
            },
        )
    
    return {
        "status": "healthy",
        "database": {
            "status": "healthy",
        },
    }


@router.get("/schema")
async def get_schema() -> Dict:
    """
    Get the database schema information.
    
    Returns:
        Dictionary with database schema information
    """
    try:
        return {"schema": get_database_info()}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )


@router.get("/tables")
async def get_tables() -> Dict[str, List[str]]:
    """
    Get a list of all tables in the database.
    
    Returns:
        Dictionary with list of table names
    """
    try:
        return {"tables": get_all_tables()}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )


@router.get("/tables/{table_name}")
async def get_table_schema_endpoint(table_name: str) -> Dict:
    """
    Get schema information for a specific table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        Dictionary with table schema information
    """
    from app.db.database import get_table_schema
    
    try:
        schema = get_table_schema(table_name)
        return {"schema": schema}
    except Exception as e:
        return {"error": str(e), "schema": {}}


@router.get("/tables/{table_name}/data")
async def get_table_data(table_name: str, limit: int = 50) -> Dict:
    """
    Get sample data from a specific table.

    Args:
        table_name: Name of the table
        limit: Maximum number of rows to return (default: 50, capped at 1000)

    Returns:
        Dictionary with table data and count
    """
    from app.db.database import execute_query

    # Whitelist the table against the live schema — prevents both injection
    # and access to internal/sqlite_* tables.
    allowed = set(get_all_tables())
    if table_name not in allowed:
        raise HTTPException(status_code=404, detail="Unknown table")

    # Bound the limit so a caller can't ask for the whole table.
    safe_limit = max(1, min(int(limit), 1000))

    try:
        # `table_name` is now whitelist-bounded, so interpolating it is safe.
        # SQLite parameter binding does not support identifiers, only values.
        rows = execute_query(f"SELECT * FROM {table_name} LIMIT {safe_limit}")

        count_result = execute_query(f"SELECT COUNT(*) AS total FROM {table_name}")
        total_count = count_result[0]["total"] if count_result else 0

        return {
            "rows": rows,
            "count": len(rows),
            "total_count": total_count,
            "table_name": table_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
