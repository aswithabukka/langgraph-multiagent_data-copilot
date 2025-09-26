"""
FastAPI application for the LangGraph Data Copilot.

This module defines the FastAPI application and its configuration.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router
from app.db.database import init_db

# Load environment variables from .env file
dotenv.load_dotenv(Path(__file__).parent.parent.parent / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    This runs initialization code before the application starts
    and cleanup code when the application shuts down.
    
    Args:
        app: FastAPI application instance
    """
    # Initialize database
    init_db()
    
    # Create charts directory if it doesn't exist
    chart_dir = os.getenv("CHART_DIR", "./charts")
    os.makedirs(chart_dir, exist_ok=True)
    
    yield
    
    # Cleanup code here (if needed)


# Create FastAPI application
app = FastAPI(
    title="LangGraph Data Copilot",
    description="A multi-agent system for natural language data analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include router
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "LangGraph Data Copilot API is running"}
