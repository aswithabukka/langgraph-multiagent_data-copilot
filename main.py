"""
Main entry point for the LangGraph Data Copilot API.

This script starts the FastAPI server using uvicorn.
"""

import os
from pathlib import Path

import dotenv
import uvicorn

from app.api.app import app

# Load environment variables from .env file
dotenv.load_dotenv(Path(".env"))

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    # Start server
    uvicorn.run(app, host=host, port=port)
