"""
Chart generation utilities for LangGraph Data Copilot.

This module provides functions to create and save matplotlib charts
based on SQL query results.
"""

import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# Use Agg backend for non-interactive environments (like Docker)
matplotlib.use("Agg")

# Get chart directory from environment or use default
CHART_DIR = os.getenv("CHART_DIR", "./charts")

# Ensure chart directory exists
os.makedirs(CHART_DIR, exist_ok=True)


def generate_chart(
    rows: List[Dict[str, Any]],
    chart_type: str,
    x_column: str,
    y_column: str,
    title: Optional[str] = None,
    color: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
) -> str:
    """
    Generate a chart from query results and save it to disk.
    
    Args:
        rows: List of dictionaries representing data rows
        chart_type: Type of chart ('bar', 'line', 'scatter', 'pie', 'histogram')
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        title: Chart title
        color: Color for the chart elements
        figsize: Figure size as (width, height) tuple
        
    Returns:
        Path to the saved chart image
        
    Raises:
        ValueError: If chart_type is not supported or columns don't exist
    """
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    
    # Validate columns exist
    if x_column not in df.columns:
        raise ValueError(f"Column '{x_column}' not found in data")
    if y_column not in df.columns and chart_type != "histogram":
        raise ValueError(f"Column '{y_column}' not found in data")
    
    # Create figure
    plt.figure(figsize=figsize)
    
    # Generate chart based on type
    if chart_type == "bar":
        ax = df.plot(kind="bar", x=x_column, y=y_column, color=color)
        plt.xticks(rotation=45)
        
    elif chart_type == "line":
        ax = df.plot(kind="line", x=x_column, y=y_column, color=color, marker="o")
        
    elif chart_type == "scatter":
        ax = df.plot(kind="scatter", x=x_column, y=y_column, color=color)
        
    elif chart_type == "pie":
        # For pie charts, we need values and labels
        ax = df.plot(kind="pie", y=y_column, labels=df[x_column], autopct="%1.1f%%")
        plt.axis("equal")  # Equal aspect ratio ensures the pie chart is circular
        
    elif chart_type == "histogram":
        ax = df[x_column].plot(kind="hist", bins=10, color=color)
        
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")
    
    # Add title if provided
    if title:
        plt.title(title)
    
    # Add labels
    plt.xlabel(x_column)
    if chart_type != "pie" and chart_type != "histogram":
        plt.ylabel(y_column)
    
    # Add grid
    plt.grid(True, linestyle="--", alpha=0.7)
    
    # Tight layout
    plt.tight_layout()
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(CHART_DIR, filename)
    
    # Save chart
    plt.savefig(filepath, dpi=100)
    plt.close()
    
    return filepath


def determine_chart_type(
    rows: List[Dict[str, Any]], x_column: str, y_column: str
) -> str:
    """
    Automatically determine the best chart type based on data characteristics.
    
    Args:
        rows: List of dictionaries representing data rows
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        
    Returns:
        Recommended chart type as string
    """
    df = pd.DataFrame(rows)
    
    # Check if x is categorical/datetime and y is numeric
    x_is_numeric = pd.api.types.is_numeric_dtype(df[x_column])
    x_is_datetime = pd.api.types.is_datetime64_dtype(df[x_column])
    x_unique_count = df[x_column].nunique()
    
    y_is_numeric = pd.api.types.is_numeric_dtype(df[y_column])
    
    # Decision logic for chart type
    if x_is_datetime and y_is_numeric:
        return "line"  # Time series data
    elif not x_is_numeric and y_is_numeric and x_unique_count <= 20:
        return "bar"  # Categorical data with reasonable number of categories
    elif x_is_numeric and y_is_numeric:
        return "scatter"  # Two numeric variables
    elif not x_is_numeric and x_unique_count <= 8:
        return "pie"  # Few categories, good for pie chart
    else:
        return "bar"  # Default to bar chart
