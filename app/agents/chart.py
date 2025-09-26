"""
Chart agent for LangGraph Data Copilot.

This agent is responsible for generating charts based on SQL query results.
"""

import json
from typing import Dict, List, Optional

from langchain.schema import HumanMessage
from langchain_core.messages import SystemMessage

from app.agents.config import AGENT_CONFIG, get_llm
from app.agents.prompts import CHART_PROMPT
from app.models.state import GraphState
from app.utils.chart import generate_chart


def extract_chart_config(chart_text: str) -> Dict:
    """
    Extract chart configuration from the LLM response.
    
    Args:
        chart_text: Raw chart configuration text from the LLM
        
    Returns:
        Dictionary with chart configuration
    """
    # Default configuration
    default_config = {
        "chart_type": "bar",
        "x_column": "",
        "y_column": "",
        "title": "Data Analysis Chart",
    }
    
    try:
        # Try to extract JSON from markdown code blocks
        if "```json" in chart_text:
            json_str = chart_text.split("```json", 1)[1].split("```", 1)[0]
            config = json.loads(json_str)
            return {**default_config, **config}
        
        # Try to extract JSON from regular code blocks
        elif "```" in chart_text:
            json_str = chart_text.split("```", 1)[1].split("```", 1)[0]
            config = json.loads(json_str)
            return {**default_config, **config}
        
        # Try to parse the entire response as JSON
        else:
            config = json.loads(chart_text)
            return {**default_config, **config}
    
    except Exception:
        # If JSON parsing fails, try to extract key-value pairs
        config = default_config.copy()
        
        if "chart_type" in chart_text.lower():
            for chart_type in ["bar", "line", "scatter", "pie", "histogram"]:
                if chart_type in chart_text.lower():
                    config["chart_type"] = chart_type
                    break
        
        if "x_column" in chart_text.lower() and ":" in chart_text:
            lines = chart_text.split("\n")
            for line in lines:
                if "x_column" in line.lower() and ":" in line:
                    value = line.split(":", 1)[1].strip().strip('"\'')
                    config["x_column"] = value
        
        if "y_column" in chart_text.lower() and ":" in chart_text:
            lines = chart_text.split("\n")
            for line in lines:
                if "y_column" in line.lower() and ":" in line:
                    value = line.split(":", 1)[1].strip().strip('"\'')
                    config["y_column"] = value
        
        if "title" in chart_text.lower() and ":" in chart_text:
            lines = chart_text.split("\n")
            for line in lines:
                if "title" in line.lower() and ":" in line:
                    value = line.split(":", 1)[1].strip().strip('"\'')
                    config["title"] = value
    
    return config


def chart_agent(state: GraphState) -> Dict:
    """
    Generate a chart based on SQL query results.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated graph state with chart path
    """
    # Skip if there's no data or SQL error
    if not state.rows or state.sql_error:
        return {
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["chart"],
        }
    
    # Get LLM configuration
    config = AGENT_CONFIG.get("chart", {})
    llm = get_llm(
        provider=config.get("provider", "openai"),
        model=config.get("model"),
        temperature=float(config.get("temperature", 0.0)),
    )
    
    # Format prompt with sample rows (limit to 5 for brevity)
    sample_rows = state.rows[:5]
    prompt = CHART_PROMPT.format(
        user_query=state.user_query,
        sql=state.sql,
        sample_rows=sample_rows,
    )
    
    # Get response from LLM
    messages = [
        SystemMessage(content="You are a data visualization assistant."),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    
    # Extract chart configuration
    chart_config = extract_chart_config(response.content)
    
    try:
        # Generate chart
        chart_path = generate_chart(
            rows=state.rows,
            chart_type=chart_config["chart_type"],
            x_column=chart_config["x_column"],
            y_column=chart_config["y_column"],
            title=chart_config["title"],
        )
        
        return {
            "chart_path": chart_path,
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["chart"],
        }
    
    except Exception as e:
        # Handle chart generation error
        return {
            "chart_error": str(e),
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["chart"],
        }
