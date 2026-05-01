"""
LangGraph workflow for the Data Analysis Copilot.

`route_next` decides which agent runs next given the current `GraphState`. It
is exported separately from `create_graph` so unit tests can exercise the
routing logic without compiling and invoking the full graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.chart import chart_agent
from app.agents.explainer import explainer_agent
from app.agents.intent import (
    evaluate_arithmetic,
    handle_off_topic_query,
    is_data_related_query,
    is_simple_arithmetic,
)
from app.agents.planner import planner_agent
from app.agents.sql import sql_agent
from app.models.state import GraphState

logger = logging.getLogger(__name__)


_MAX_AGENT_STEPS = 4  # planner, sql, chart, explainer — guard against loops


def route_next(state: GraphState) -> str:
    """Pick the next node for `state`. Returns a node name or `END`."""
    if len(state.completed_agents) >= _MAX_AGENT_STEPS:
        return END

    if getattr(state, "next_agent", None):
        if state.next_agent in ("end", END):
            return END
        if state.next_agent not in state.completed_agents:
            return state.next_agent

    if "planner" not in state.completed_agents:
        return "planner"
    if (
        "sql_agent" not in state.completed_agents
        and state.plan
        and any(step.requires_sql for step in state.plan)
    ):
        return "sql_agent"
    if (
        "chart" not in state.completed_agents
        and state.plan
        and any(step.requires_chart for step in state.plan)
    ):
        return "chart"
    if "explainer" not in state.completed_agents:
        return "explainer"
    return END


def create_graph() -> StateGraph:
    """Build and compile the agent workflow."""
    graph = StateGraph(GraphState)

    graph.add_node("planner", planner_agent)
    # Node name "sql_agent" (not "sql") because LangGraph forbids nodes that
    # share a name with a GraphState field (`state.sql` holds the query).
    graph.add_node("sql_agent", sql_agent)
    graph.add_node("chart", chart_agent)
    graph.add_node("explainer", explainer_agent)

    graph.set_entry_point("planner")
    for node in ("planner", "sql_agent", "chart", "explainer"):
        graph.add_conditional_edges(node, route_next)

    return graph.compile(
        checkpointer=None,
        interrupt_before=None,
        interrupt_after=None,
        debug=False,
    )


class ProcessRequest(TypedDict):
    """Request type for the process function."""

    query: str
    session_id: Optional[str]


class ProcessResponse(TypedDict, total=False):
    """Response type for the process function."""

    answer: str
    sql: Optional[str]
    chart_url: Optional[str]
    rows: List[Dict]
    df_summary: Optional[Dict]
    processing_time_ms: Optional[float]
    error: Optional[str]


def _empty_response(answer: str, error: Optional[str] = None) -> ProcessResponse:
    return {
        "answer": answer,
        "sql": None,
        "chart_url": None,
        "rows": [],
        "df_summary": None,
        "processing_time_ms": 0.0,
        "error": error,
    }


async def process_query(request: ProcessRequest) -> ProcessResponse:
    """Run a user query through the workflow and shape the response."""
    query = request["query"]

    # Cheap shortcuts before paying for the LLM graph.
    if is_simple_arithmetic(query):
        return _empty_response(evaluate_arithmetic(query))

    if not is_data_related_query(query):
        return _empty_response(handle_off_topic_query(query))

    try:
        graph = create_graph()
        session_id = request.get("session_id") or str(uuid.uuid4())
        state = GraphState(
            user_query=query,
            session_id=session_id,
            processing_start_time=datetime.now(),
        )

        result = await graph.ainvoke(state)

        elapsed_ms = (datetime.now() - state.processing_start_time).total_seconds() * 1000
        return {
            "answer": result.get("answer", ""),
            "sql": result.get("sql"),
            "chart_url": result.get("chart_path"),
            "rows": result.get("rows", [])[:50],
            "df_summary": result.get("df_summary"),
            "processing_time_ms": elapsed_ms,
            "error": None,
        }
    except Exception as e:
        # Log full traceback for ops, but only surface the message to clients.
        logger.exception("process_query failed")
        return _empty_response(f"Error processing query: {e}", error=str(e))
