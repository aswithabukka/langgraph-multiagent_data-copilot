"""
Database connection and utilities for the LangGraph Data Copilot.

This module provides database connection management and query execution
functions using SQLAlchemy with SQLite.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default to SQLite in-memory if no DATABASE_URL is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")


def get_engine() -> Engine:
    """
    Create and return a SQLAlchemy engine instance.
    
    Returns:
        Engine: SQLAlchemy engine connected to the database
    """
    return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    """
    Initialize the database by running the seed script.
    
    This function creates tables and populates them with sample data.
    """
    engine = get_engine()
    
    # Read the seed SQL file
    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")
    with open(seed_path, "r") as f:
        seed_sql = f.read()
    
    # Split SQL into individual statements
    statements = [stmt.strip() for stmt in seed_sql.split(';') if stmt.strip()]
    
    # Execute each statement separately
    with engine.connect() as conn:
        for statement in statements:
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()


def execute_query(query: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return the results as a list of dictionaries.
    
    Args:
        query: SQL query string to execute
        
    Returns:
        List of dictionaries representing rows from the query result
        
    Raises:
        SQLAlchemyError: If there's an error executing the query
    """
    engine = get_engine()
    
    try:
        # Execute the query and convert to DataFrame
        df = pd.read_sql_query(query, engine)
        
        # Convert DataFrame to list of dictionaries
        rows = df.to_dict(orient="records")
        
        # Limit to 50 rows maximum
        return rows[:50]
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Error executing query: {str(e)}")


def get_dataframe_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of a pandas DataFrame.
    
    Args:
        df: DataFrame to summarize
        
    Returns:
        Dictionary with DataFrame summary information
    """
    return {
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "shape": df.shape,
        "head": df.head(5).to_dict(orient="records"),
        "null_counts": df.isnull().sum().to_dict(),
    }


def execute_query_with_summary(query: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Execute a SQL query and return both results and a DataFrame summary.
    
    Args:
        query: SQL query string to execute
        
    Returns:
        Tuple of (rows, summary) where rows is a list of dictionaries and
        summary is a dictionary with DataFrame summary information
        
    Raises:
        SQLAlchemyError: If there's an error executing the query
    """
    engine = get_engine()
    
    try:
        # Execute the query and convert to DataFrame
        df = pd.read_sql_query(query, engine)
        
        # Generate summary
        summary = get_dataframe_summary(df)
        
        # Convert DataFrame to list of dictionaries
        rows = df.to_dict(orient="records")
        
        # Limit to 50 rows maximum
        return rows[:50], summary
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Error executing query: {str(e)}")


def validate_sql_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a SQL query for safety.
    
    This function checks that:
    1. The query only contains SELECT statements
    2. No semicolons for chaining multiple statements
    3. No DDL/DML operations
    
    Args:
        query: SQL query string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Convert to lowercase for case-insensitive checks
    query_lower = query.lower()
    
    # Check for SELECT statement
    if not query_lower.strip().startswith("select"):
        return False, "Query must start with SELECT"
    
    # Check for semicolons (except at the end)
    if ";" in query_lower[:-1]:
        return False, "Multiple statements are not allowed"
    
    # Check for DDL/DML operations
    forbidden_keywords = [
        "insert", "update", "delete", "drop", "alter", "create", 
        "truncate", "replace", "attach", "detach", "pragma"
    ]
    
    for keyword in forbidden_keywords:
        if keyword in query_lower:
            return False, f"Forbidden keyword found: {keyword}"
    
    return True, None


def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    Get schema information for a specific table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        Dictionary with table schema information
    """
    engine = get_engine()
    inspector = inspect(engine)
    
    if table_name not in inspector.get_table_names():
        raise ValueError(f"Table '{table_name}' does not exist")
    
    # Get raw column information
    raw_columns = inspector.get_columns(table_name)
    
    # Convert columns to serializable format
    columns = []
    for col in raw_columns:
        columns.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col.get("nullable", True),
            "default": str(col.get("default")) if col.get("default") is not None else None,
            "autoincrement": col.get("autoincrement", False),
        })
    
    primary_key = inspector.get_pk_constraint(table_name)
    foreign_keys = inspector.get_foreign_keys(table_name)
    indexes = inspector.get_indexes(table_name)
    
    return {
        "columns": columns,
        "primary_key": primary_key,
        "foreign_keys": foreign_keys,
        "indexes": indexes,
    }


def get_all_tables() -> List[str]:
    """
    Get a list of all tables in the database.
    
    Returns:
        List of table names
    """
    engine = get_engine()
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_database_info() -> Dict[str, Any]:
    """
    Get comprehensive information about the database schema.
    
    Returns:
        Dictionary with database schema information
    """
    tables = get_all_tables()
    result = {}
    
    for table in tables:
        result[table] = get_table_schema(table)
    
    return result


def check_database_health() -> Tuple[bool, Optional[str]]:
    """
    Check if the database is accessible and contains the expected tables.
    
    Returns:
        Tuple of (is_healthy, error_message)
    """
    try:
        tables = get_all_tables()
        if "orders" not in tables:
            return False, "Required table 'orders' not found"
        
        # Test a simple query
        execute_query("SELECT COUNT(*) FROM orders")
        return True, None
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False, str(e)
