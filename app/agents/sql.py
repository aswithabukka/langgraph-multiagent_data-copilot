"""
SQL agent for LangGraph Data Copilot.

This agent is responsible for generating and executing SQL queries
based on the user's question and the execution plan.
"""

import json
from typing import Dict, List

from langchain.schema import HumanMessage
from langchain_core.messages import SystemMessage

from app.agents.config import AGENT_CONFIG, get_llm
from app.agents.prompts import SQL_PROMPT
from app.db.database import execute_query_with_summary, validate_sql_query
from app.models.state import GraphState, PlanStep


def extract_sql_query(sql_text: str) -> str:
    """
    Extract the SQL query from the LLM response.
    
    Args:
        sql_text: Raw SQL text from the LLM
        
    Returns:
        Clean SQL query string
    """
    # Try to extract SQL from markdown code blocks
    if "```sql" in sql_text:
        parts = sql_text.split("```sql", 1)[1].split("```", 1)
        if parts:
            return parts[0].strip()
    
    # Try to extract SQL from regular code blocks
    if "```" in sql_text:
        parts = sql_text.split("```", 1)[1].split("```", 1)
        if parts:
            return parts[0].strip()
    
    # Return as is if no code blocks found
    return sql_text.strip()


def format_plan_for_prompt(plan: List[PlanStep]) -> str:
    """
    Format the plan steps for inclusion in the SQL prompt.
    
    Args:
        plan: List of PlanStep objects
        
    Returns:
        Formatted plan string
    """
    plan_text = ""
    for step in plan:
        plan_text += f"{step.step_number}. {step.description}\n"
    return plan_text


def sql_agent(state: GraphState) -> Dict:
    """
    Generate and execute SQL query based on the user's question.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated graph state with SQL query and results
    """
    # Get LLM configuration
    config = AGENT_CONFIG.get("sql", {})
    llm = get_llm(
        provider=config.get("provider", "openai"),
        model=config.get("model"),
        temperature=float(config.get("temperature", 0.0)),
    )
    
    # Format prompt
    formatted_plan = format_plan_for_prompt(state.plan)
    prompt = SQL_PROMPT.format(
        user_query=state.user_query,
        plan=formatted_plan,
    )
    
    # Get response from LLM
    messages = [
        SystemMessage(content="You are a SQL query generation assistant."),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    
    # Extract SQL query
    sql_query = extract_sql_query(response.content)
    
    # Validate SQL query
    is_valid, error_message = validate_sql_query(sql_query)
    if not is_valid:
        return {
            "sql": sql_query,
            "sql_error": f"Invalid SQL query: {error_message}",
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["sql"],
        }
    
    try:
        # Execute SQL query
        rows, df_summary = execute_query_with_summary(sql_query)
        
        # Determine next agent
        requires_chart = any(step.requires_chart for step in state.plan)
        next_agent = "chart" if requires_chart else "explainer"
        
        return {
            "sql": sql_query,
            "rows": rows,
            "df_summary": df_summary,
            "next_agent": next_agent,
            "completed_agents": state.completed_agents + ["sql"],
        }
    
    except Exception as e:
        # Handle SQL execution error
        return {
            "sql": sql_query,
            "sql_error": str(e),
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["sql"],
        }
