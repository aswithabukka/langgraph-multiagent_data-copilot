"""
Tests for the LangGraph workflow.

This module tests the graph routing logic and workflow execution.
"""

import pytest

from app.agents.graph import create_graph
from app.models.state import GraphState, PlanStep


def test_graph_creation():
    """Test that the graph can be created successfully."""
    graph = create_graph()
    assert graph is not None


def test_graph_routing():
    """Test the graph routing logic with different states."""
    # Create the graph
    graph = create_graph()
    
    # Test routing to planner first
    state = GraphState(user_query="What is the total sales by region?")
    next_node = graph.get_next_node(state)
    assert next_node == "planner"
    
    # Test routing to SQL after planner
    state = GraphState(
        user_query="What is the total sales by region?",
        completed_agents=["planner"],
        plan=[
            PlanStep(
                step_number=1,
                action="Generate SQL",
                description="Generate SQL to get total sales by region",
                requires_sql=True,
                requires_chart=True,
            )
        ],
    )
    next_node = graph.get_next_node(state)
    assert next_node == "sql"
    
    # Test routing to chart after SQL
    state = GraphState(
        user_query="What is the total sales by region?",
        completed_agents=["planner", "sql"],
        plan=[
            PlanStep(
                step_number=1,
                action="Generate SQL",
                description="Generate SQL to get total sales by region",
                requires_sql=True,
                requires_chart=True,
            )
        ],
        sql="SELECT region, SUM(sales_amount) FROM orders GROUP BY region",
        rows=[{"region": "North", "sum": 1000}],
    )
    next_node = graph.get_next_node(state)
    assert next_node == "chart"
    
    # Test routing to explainer after chart
    state = GraphState(
        user_query="What is the total sales by region?",
        completed_agents=["planner", "sql", "chart"],
        plan=[
            PlanStep(
                step_number=1,
                action="Generate SQL",
                description="Generate SQL to get total sales by region",
                requires_sql=True,
                requires_chart=True,
            )
        ],
        sql="SELECT region, SUM(sales_amount) FROM orders GROUP BY region",
        rows=[{"region": "North", "sum": 1000}],
        chart_path="/path/to/chart.png",
    )
    next_node = graph.get_next_node(state)
    assert next_node == "explainer"
    
    # Test routing to end after explainer
    state = GraphState(
        user_query="What is the total sales by region?",
        completed_agents=["planner", "sql", "chart", "explainer"],
        plan=[
            PlanStep(
                step_number=1,
                action="Generate SQL",
                description="Generate SQL to get total sales by region",
                requires_sql=True,
                requires_chart=True,
            )
        ],
        sql="SELECT region, SUM(sales_amount) FROM orders GROUP BY region",
        rows=[{"region": "North", "sum": 1000}],
        chart_path="/path/to/chart.png",
        answer="The total sales for the North region is $1000.",
    )
    next_node = graph.get_next_node(state)
    assert next_node == "__end__"
    
    # Test direct routing with next_agent
    state = GraphState(
        user_query="What is the total sales by region?",
        next_agent="chart",
    )
    next_node = graph.get_next_node(state)
    assert next_node == "chart"
    
    # Test routing to end with next_agent
    state = GraphState(
        user_query="What is the total sales by region?",
        next_agent="end",
    )
    next_node = graph.get_next_node(state)
    assert next_node == "__end__"


def test_non_sql_routing():
    """Test routing for non-SQL questions."""
    # Create the graph
    graph = create_graph()
    
    # Test routing for a non-SQL question
    state = GraphState(
        user_query="What is 2+2?",
        completed_agents=["planner"],
        plan=[
            PlanStep(
                step_number=1,
                action="Answer directly",
                description="Answer the arithmetic question directly",
                requires_sql=False,
                requires_chart=False,
            )
        ],
    )
    next_node = graph.get_next_node(state)
    assert next_node == "explainer"
