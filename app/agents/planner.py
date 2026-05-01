"""
Planner agent.

Builds the execution plan that the rest of the graph follows. For arithmetic
and off-topic queries we short-circuit straight to the explainer; for data
queries we lay out SQL → (optional chart) → explainer.
"""

from typing import Dict

from app.agents.intent import (
    is_data_related_query,
    is_simple_arithmetic,
    requires_chart,
)
from app.agents.parsing import parse_plan  # re-exported for callers
from app.models.state import GraphState, PlanStep

__all__ = [
    "is_data_related_query",
    "is_simple_arithmetic",
    "parse_plan",
    "planner_agent",
    "requires_chart",
]


def planner_agent(state: GraphState) -> Dict:
    """Create the execution plan for the user's query."""
    if is_simple_arithmetic(state.user_query):
        return {
            "plan": [
                PlanStep(
                    step_number=1,
                    action="Answer directly",
                    description="Answer the arithmetic question directly",
                    requires_sql=False,
                    requires_chart=False,
                )
            ],
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["planner"],
        }

    if not is_data_related_query(state.user_query):
        return {
            "plan": [
                PlanStep(
                    step_number=1,
                    action="Handle off-topic",
                    description="Provide helpful response for off-topic query and guide back to data analysis",
                    requires_sql=False,
                    requires_chart=False,
                )
            ],
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["planner"],
        }

    needs_chart = requires_chart(state.user_query)
    plan = [
        PlanStep(
            step_number=1,
            action="Generate SQL query",
            description="Create SQL query to retrieve data for analysis",
            requires_sql=True,
            requires_chart=False,
        ),
        PlanStep(
            step_number=2,
            action="Generate chart" if needs_chart else "Skip chart",
            description="Create visualization of the data" if needs_chart else "No chart requested",
            requires_sql=False,
            requires_chart=needs_chart,
        ),
        PlanStep(
            step_number=3,
            action="Explain results",
            description="Provide natural language explanation of the analysis",
            requires_sql=False,
            requires_chart=False,
        ),
    ]
    return {
        "plan": plan,
        "next_agent": "sql_agent",
        "completed_agents": state.completed_agents + ["planner"],
    }


