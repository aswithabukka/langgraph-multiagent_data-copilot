"""
SQL agent.

Asks the LLM to translate the plan into a SELECT query, validates it, and
executes it against the database. All string parsing lives in
`app.agents.parsing`.
"""

from typing import Dict, List

from langchain.schema import HumanMessage
from langchain_core.messages import SystemMessage

from app.agents.config import AGENT_CONFIG, get_llm
from app.agents.parsing import extract_sql_query
from app.agents.prompts import SQL_PROMPT
from app.db.database import execute_query_with_summary, validate_sql_query
from app.models.state import GraphState, PlanStep

__all__ = ["extract_sql_query", "format_plan_for_prompt", "sql_agent"]


def format_plan_for_prompt(plan: List[PlanStep]) -> str:
    """Render the plan as the simple numbered list our SQL prompt expects."""
    return "".join(f"{step.step_number}. {step.description}\n" for step in plan)


async def sql_agent(state: GraphState) -> Dict:
    """Generate and execute a SQL query for the current state."""
    config = AGENT_CONFIG.get("sql", {})
    llm = get_llm(
        provider=config.get("provider", "openai"),
        model=config.get("model"),
        temperature=float(config.get("temperature", 0.0)),
    )

    prompt = SQL_PROMPT.format(
        user_query=state.user_query,
        plan=format_plan_for_prompt(state.plan),
    )
    response = await llm.ainvoke(
        [
            SystemMessage(content="You are a SQL query generation assistant."),
            HumanMessage(content=prompt),
        ]
    )

    sql_query = extract_sql_query(response.content)

    is_valid, error_message = validate_sql_query(sql_query)
    if not is_valid:
        return {
            "sql": sql_query,
            "sql_error": f"Invalid SQL query: {error_message}",
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["sql"],
        }

    try:
        rows, df_summary = execute_query_with_summary(sql_query)
    except Exception as e:
        return {
            "sql": sql_query,
            "sql_error": str(e),
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["sql"],
        }

    requires_chart = any(step.requires_chart for step in state.plan)
    return {
        "sql": sql_query,
        "rows": rows,
        "df_summary": df_summary,
        "next_agent": "chart" if requires_chart else "explainer",
        "completed_agents": state.completed_agents + ["sql"],
    }
