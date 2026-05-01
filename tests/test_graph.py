"""
Tests for the LangGraph workflow.

Covers two things:
  * `route_next` (pure routing logic, no LLM, no DB) — exhaustively.
  * `create_graph` — smoke test that the compiled graph builds.
"""

from langgraph.graph import END

from app.agents.graph import create_graph, route_next
from app.models.state import GraphState, PlanStep


def _step(requires_sql: bool = True, requires_chart: bool = False) -> PlanStep:
    return PlanStep(
        step_number=1,
        action="Generate SQL",
        description="x",
        requires_sql=requires_sql,
        requires_chart=requires_chart,
    )


def test_create_graph_builds():
    assert create_graph() is not None


def test_route_starts_at_planner():
    state = GraphState(user_query="how many orders are there")
    assert route_next(state) == "planner"


def test_route_planner_to_sql_when_sql_required():
    state = GraphState(
        user_query="how many orders",
        completed_agents=["planner"],
        plan=[_step(requires_sql=True)],
    )
    assert route_next(state) == "sql"


def test_route_sql_to_chart_when_chart_required():
    state = GraphState(
        user_query="show me sales by region as a bar chart",
        completed_agents=["planner", "sql"],
        plan=[_step(requires_sql=True, requires_chart=True)],
        sql="SELECT region, SUM(x) FROM orders GROUP BY region",
        rows=[{"region": "N", "sum": 1}],
    )
    assert route_next(state) == "chart"


def test_route_chart_to_explainer():
    state = GraphState(
        user_query="show me sales by region as a bar chart",
        completed_agents=["planner", "sql", "chart"],
        plan=[_step(requires_sql=True, requires_chart=True)],
        sql="SELECT 1",
        rows=[{"region": "N", "sum": 1}],
        chart_path="/tmp/chart.png",
    )
    assert route_next(state) == "explainer"


def test_route_terminates_after_explainer():
    state = GraphState(
        user_query="how many orders",
        completed_agents=["planner", "sql", "chart", "explainer"],
        plan=[_step()],
        answer="There are 27 orders.",
    )
    assert route_next(state) == END


def test_route_explicit_next_agent_wins():
    state = GraphState(user_query="x", next_agent="chart")
    assert route_next(state) == "chart"


def test_route_explicit_next_agent_end():
    state = GraphState(user_query="x", next_agent="end")
    assert route_next(state) == END


def test_route_skips_completed_next_agent():
    # If the agent was already completed, fall back to sequential routing.
    state = GraphState(
        user_query="x",
        completed_agents=["planner", "sql"],
        plan=[_step(requires_sql=True)],
        next_agent="sql",  # already done
    )
    # No chart required → should advance to explainer.
    assert route_next(state) == "explainer"


def test_route_max_steps_breaks_loops():
    # 4 completed agents = hard limit, return END no matter what.
    state = GraphState(
        user_query="x",
        completed_agents=["planner", "sql", "chart", "explainer"],
        plan=[_step()],
    )
    assert route_next(state) == END


def test_route_skips_sql_when_plan_does_not_need_it():
    state = GraphState(
        user_query="what is 2+2",
        completed_agents=["planner"],
        plan=[
            PlanStep(
                step_number=1,
                action="Answer directly",
                description="arithmetic",
                requires_sql=False,
                requires_chart=False,
            )
        ],
    )
    assert route_next(state) == "explainer"
