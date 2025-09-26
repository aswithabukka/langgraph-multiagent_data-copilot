"""
Tests for chart generation functionality.

This module tests the chart generation utilities.
"""

import os
import tempfile
from typing import Dict, List

import pytest

from app.utils.chart import determine_chart_type, generate_chart


@pytest.fixture
def sample_data() -> List[Dict]:
    """Fixture providing sample data for testing."""
    return [
        {"region": "North", "sales": 1000, "date": "2024-01-01"},
        {"region": "South", "sales": 1500, "date": "2024-01-01"},
        {"region": "East", "sales": 1200, "date": "2024-01-01"},
        {"region": "West", "sales": 800, "date": "2024-01-01"},
        {"region": "North", "sales": 1100, "date": "2024-02-01"},
        {"region": "South", "sales": 1600, "date": "2024-02-01"},
        {"region": "East", "sales": 1300, "date": "2024-02-01"},
        {"region": "West", "sales": 900, "date": "2024-02-01"},
    ]


def test_determine_chart_type(sample_data):
    """Test chart type determination based on data characteristics."""
    # Categorical x, numeric y -> bar chart
    assert determine_chart_type(sample_data, "region", "sales") == "bar"
    
    # Two numeric columns -> scatter chart
    assert determine_chart_type(sample_data, "sales", "sales") == "scatter"


def test_generate_chart(sample_data):
    """Test chart generation functionality."""
    # Set temporary chart directory
    original_chart_dir = os.environ.get("CHART_DIR")
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["CHART_DIR"] = temp_dir
        
        # Test bar chart generation
        chart_path = generate_chart(
            rows=sample_data,
            chart_type="bar",
            x_column="region",
            y_column="sales",
            title="Sales by Region",
        )
        
        # Check that file was created
        assert os.path.exists(chart_path)
        assert chart_path.endswith(".png")
        
        # Test pie chart generation
        chart_path = generate_chart(
            rows=sample_data,
            chart_type="pie",
            x_column="region",
            y_column="sales",
            title="Sales Distribution by Region",
        )
        
        # Check that file was created
        assert os.path.exists(chart_path)
        assert chart_path.endswith(".png")
    
    # Restore original chart directory
    if original_chart_dir:
        os.environ["CHART_DIR"] = original_chart_dir
    else:
        del os.environ["CHART_DIR"]


def test_generate_chart_invalid_columns(sample_data):
    """Test chart generation with invalid columns."""
    with pytest.raises(ValueError):
        generate_chart(
            rows=sample_data,
            chart_type="bar",
            x_column="invalid_column",
            y_column="sales",
            title="Invalid Chart",
        )
    
    with pytest.raises(ValueError):
        generate_chart(
            rows=sample_data,
            chart_type="bar",
            x_column="region",
            y_column="invalid_column",
            title="Invalid Chart",
        )


def test_generate_chart_invalid_type(sample_data):
    """Test chart generation with invalid chart type."""
    with pytest.raises(ValueError):
        generate_chart(
            rows=sample_data,
            chart_type="invalid_type",
            x_column="region",
            y_column="sales",
            title="Invalid Chart Type",
        )
