"""
Chart agent.

Asks the LLM how to visualize the SQL result, then renders the chart via
`app.utils.chart.generate_chart`. The JSON parsing lives in
`app.agents.parsing.extract_chart_config`.
"""

from typing import Dict

from langchain.schema import HumanMessage
from langchain_core.messages import SystemMessage

from app.agents.config import AGENT_CONFIG, get_llm
from app.agents.parsing import extract_chart_config
from app.agents.prompts import CHART_PROMPT
from app.models.state import GraphState
from app.utils.chart import generate_chart

__all__ = ["chart_agent", "extract_chart_config"]


async def chart_agent(state: GraphState) -> Dict:
    """Generate a chart for the SQL result, if any data is available."""
    if not state.rows or state.sql_error:
        return {
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["chart"],
        }

    config = AGENT_CONFIG.get("chart", {})
    llm = get_llm(
        provider=config.get("provider", "openai"),
        model=config.get("model"),
        temperature=float(config.get("temperature", 0.0)),
    )

    prompt = CHART_PROMPT.format(
        user_query=state.user_query,
        sql=state.sql,
        sample_rows=state.rows[:5],
    )
    response = await llm.ainvoke(
        [
            SystemMessage(content="You are a data visualization assistant."),
            HumanMessage(content=prompt),
        ]
    )

    chart_config = extract_chart_config(response.content)

    try:
        chart_path = generate_chart(
            rows=state.rows,
            chart_type=chart_config["chart_type"],
            x_column=chart_config["x_column"],
            y_column=chart_config["y_column"],
            title=chart_config["title"],
        )
    except Exception as e:
        return {
            "chart_error": str(e),
            "next_agent": "explainer",
            "completed_agents": state.completed_agents + ["chart"],
        }

    return {
        "chart_path": chart_path,
        "next_agent": "explainer",
        "completed_agents": state.completed_agents + ["chart"],
    }
