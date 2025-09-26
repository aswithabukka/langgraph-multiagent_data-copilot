"""
FastAPI endpoints for the LangGraph Data Copilot.

This module defines the API endpoints for the application.
"""

import os
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse

from app.agents.graph import process_query
from app.db.database import check_database_health, get_all_tables, get_database_info, get_table_schema
from app.models.state import QueryRequest, QueryResponse

# Create router
router = APIRouter()

# Get chart directory from environment or use default
CHART_DIR = os.getenv("CHART_DIR", "./charts")


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
    # Construct file path
    file_path = os.path.join(CHART_DIR, filename)
    
    # Check if file exists
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Chart not found")
    
    # Return file
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
async def get_table(table_name: str) -> Dict:
    """
    Get schema information for a specific table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        Dictionary with table schema information
    """
    try:
        return {"table": table_name, "schema": get_table_schema(table_name)}
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": str(e)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )
