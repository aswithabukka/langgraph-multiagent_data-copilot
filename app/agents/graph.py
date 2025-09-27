"""
LangGraph workflow for the Data Analysis Copilot.

This module defines the LangGraph workflow that orchestrates the agents.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.chart import chart_agent
from app.agents.explainer import explainer_agent
from app.agents.planner import planner_agent
from app.agents.sql import sql_agent
from app.models.state import GraphState


def create_graph() -> StateGraph:
    """
    Create the LangGraph workflow for the Data Analysis Copilot.
    
    Returns:
        StateGraph: The configured workflow graph
    """
    # Create a new graph
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("planner", planner_agent)
    graph.add_node("sql", sql_agent)
    graph.add_node("chart", chart_agent)
    graph.add_node("explainer", explainer_agent)
    
    # Define the conditional routing logic
    def router(state: GraphState) -> str:
        """Route to the next agent based on the state."""
        # Safety check to prevent infinite loops
        if len(state.completed_agents) >= 4:  # Max 4 agents
            return END
        
        # Check if we have a specific next agent set by an agent
        if hasattr(state, 'next_agent') and state.next_agent:
            if state.next_agent == "end" or state.next_agent == END:
                return END
            # Ensure we don't revisit completed agents
            if state.next_agent not in state.completed_agents:
                return state.next_agent
        
        # Sequential routing based on completed agents
        if "planner" not in state.completed_agents:
            return "planner"
        elif "sql" not in state.completed_agents and state.plan and any(step.requires_sql for step in state.plan):
            return "sql"
        elif "chart" not in state.completed_agents and state.plan and any(step.requires_chart for step in state.plan):
            return "chart"
        elif "explainer" not in state.completed_agents:
            return "explainer"
        else:
            return END
    
    # Set the entry point
    graph.set_entry_point("planner")
    
    # Add conditional edges from each node
    graph.add_conditional_edges("planner", router)
    graph.add_conditional_edges("sql", router)
    graph.add_conditional_edges("chart", router)
    graph.add_conditional_edges("explainer", router)
    
    # Compile the graph with explicit configuration
    return graph.compile(
        checkpointer=None,
        interrupt_before=None,
        interrupt_after=None,
        debug=False
    )


class ProcessRequest(TypedDict):
    """Request type for the process function."""
    
    query: str
    session_id: Optional[str]


class ProcessResponse(TypedDict):
    """Response type for the process function."""
    
    answer: str
    sql: Optional[str]
    chart_url: Optional[str]
    rows: List[Dict]
    df_summary: Optional[Dict]
    processing_time_ms: float


async def process_query(request: ProcessRequest) -> ProcessResponse:
    """
    Process a user query through the LangGraph workflow.
    
    Args:
        request: Dictionary with query and optional session_id
        
    Returns:
        Dictionary with the processing results
    """
    try:
        # Check if this is a simple arithmetic question
        from app.agents.planner import is_simple_arithmetic, is_data_related_query
        from app.agents.explainer import evaluate_arithmetic, handle_off_topic_query
        
        # For simple arithmetic, bypass the graph entirely
        if is_simple_arithmetic(request["query"]):
            answer = evaluate_arithmetic(request["query"])
            return {
                "answer": answer,
                "sql": None,
                "chart_url": None,
                "rows": [],
                "df_summary": None,
                "processing_time_ms": 0.0,
            }
        
        # For off-topic queries, handle them directly without going through the graph
        if not is_data_related_query(request["query"]):
            answer = handle_off_topic_query(request["query"])
            return {
                "answer": answer,
                "sql": None,
                "chart_url": None,
                "rows": [],
                "df_summary": None,
                "processing_time_ms": 0.0,
            }
        
        # For other queries, use the graph
        # Create the graph
        graph = create_graph()
        
        # Generate session ID if not provided
        session_id = request.get("session_id") or str(uuid.uuid4())
        
        # Initialize state
        state = GraphState(
            user_query=request["query"],
            session_id=session_id,
            processing_start_time=datetime.now(),
        )
        
        # Execute the graph
        result = await graph.ainvoke(state)
        
        # Calculate processing time
        start_time = state.processing_start_time
        end_time = datetime.now()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Prepare response
        return {
            "answer": result.get("answer", ""),
            "sql": result.get("sql"),  # Include SQL query
            "chart_url": result.get("chart_path"),
            "rows": result.get("rows", [])[:50],  # Limit to 50 rows
            "df_summary": result.get("df_summary"),
            "processing_time_ms": processing_time_ms,
        }
    except Exception as e:
        import traceback
        print(f"Error processing query: {str(e)}")
        print(traceback.format_exc())
        return {
            "answer": f"Error processing query: {str(e)}",
            "chart_url": None,
            "rows": [],
            "df_summary": None,
            "processing_time_ms": None,
            "error": str(e),
        }
