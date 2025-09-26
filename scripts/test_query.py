"""
Test query script.

This script tests the LangGraph workflow with a sample query.
"""

import asyncio
import os
import sys
from pprint import pprint

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.graph import process_query
from app.db.database import init_db


async def main():
    """Run a test query through the system."""
    # Initialize database if needed
    init_db()
    
    # Test query
    query = "Average sales per region in Q2"
    print(f"Processing query: '{query}'")
    
    # Process query
    result = await process_query({"query": query})
    
    # Print results
    print("\nResults:")
    print(f"Answer: {result['answer']}")
    print(f"Chart: {result['chart_url']}")
    print("\nData rows:")
    pprint(result["rows"])
    print(f"\nProcessing time: {result['processing_time_ms']:.2f} ms")


if __name__ == "__main__":
    # Set up environment variables for testing
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: No API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
    
    # Run the test
    asyncio.run(main())
