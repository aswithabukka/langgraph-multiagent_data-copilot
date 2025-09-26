"""
Tests for the SQL agent.

This module tests the SQL generation and validation functionality.
"""

import pytest

from app.agents.sql import extract_sql_query, sql_agent
from app.db.database import validate_sql_query
from app.models.state import GraphState, PlanStep


def test_extract_sql_query():
    """Test SQL query extraction from LLM response."""
    # Test with markdown code block
    markdown_sql = """
    Here's the SQL query:
    
    ```sql
    SELECT * FROM orders
    WHERE region = 'North'
    ```
    
    This query will get all orders from the North region.
    """
    
    expected = "SELECT * FROM orders\nWHERE region = 'North'"
    assert extract_sql_query(markdown_sql) == expected
    
    # Test with regular code block
    code_block_sql = """
    Here's the SQL query:
    
    ```
    SELECT * FROM orders
    WHERE region = 'South'
    ```
    
    This query will get all orders from the South region.
    """
    
    expected = "SELECT * FROM orders\nWHERE region = 'South'"
    assert extract_sql_query(code_block_sql) == expected
    
    # Test with no code block
    plain_sql = "SELECT * FROM orders WHERE region = 'East'"
    assert extract_sql_query(plain_sql) == plain_sql


def test_validate_sql_query():
    """Test SQL query validation."""
    # Valid queries
    assert validate_sql_query("SELECT * FROM orders")
    assert validate_sql_query("SELECT region, SUM(sales_amount) FROM orders GROUP BY region")
    
    # Invalid queries
    assert not validate_sql_query("INSERT INTO orders VALUES (1, 2, 'Product')")
    assert not validate_sql_query("UPDATE orders SET region = 'North'")
    assert not validate_sql_query("DELETE FROM orders")
    assert not validate_sql_query("DROP TABLE orders")
    assert not validate_sql_query("CREATE TABLE new_table (id INT)")
    assert not validate_sql_query("SELECT * FROM orders; DELETE FROM orders")


@pytest.mark.asyncio
async def test_sql_agent():
    """Test SQL agent functionality."""
    # Create test state
    state = GraphState(
        user_query="What is the total sales by region?",
        plan=[
            PlanStep(
                step_number=1,
                action="Generate SQL",
                description="Generate SQL to get total sales by region",
                requires_sql=True,
                requires_chart=True,
            )
        ],
        completed_agents=["planner"],
    )
    
    # Mock the SQL agent (we can't actually run it without a database)
    # In a real test, we would use a test database or mock the database functions
    
    # Just test that the function doesn't raise an exception
    try:
        result = sql_agent(state)
        assert isinstance(result, dict)
    except Exception as e:
        pytest.fail(f"SQL agent raised an exception: {e}")
