"""
Explainer agent.

Either short-circuits to a canned response (arithmetic / off-topic, both pure
helpers in `app.agents.intent`) or asks the LLM to summarize the SQL result
in natural language.
"""

from datetime import datetime
from typing import Dict

from langchain.schema import HumanMessage
from langchain_core.messages import SystemMessage

from app.agents.config import AGENT_CONFIG, get_llm
from app.agents.intent import evaluate_arithmetic, handle_off_topic_query
from app.agents.prompts import EXPLAINER_PROMPT
from app.models.state import GraphState, HistoryEntry

__all__ = ["evaluate_arithmetic", "explainer_agent", "handle_off_topic_query"]


def _history(state: GraphState, answer: str) -> HistoryEntry:
    return HistoryEntry(
        query=state.user_query,
        answer=answer,
        chart_path=state.chart_path,
        timestamp=datetime.now(),
    )


async def explainer_agent(state: GraphState) -> Dict:
    """Produce the final natural-language answer."""
    actions = {step.action for step in state.plan}

    if "Answer directly" in actions:
        answer = evaluate_arithmetic(state.user_query)
        return {
            "answer": answer,
            "history": state.history + [_history(state, answer)],
            "processing_end_time": datetime.now(),
            "completed_agents": state.completed_agents + ["explainer"],
        }

    if "Handle off-topic" in actions:
        answer = handle_off_topic_query(state.user_query)
        return {
            "answer": answer,
            "history": state.history + [_history(state, answer)],
            "processing_end_time": datetime.now(),
            "completed_agents": state.completed_agents + ["explainer"],
        }

    config = AGENT_CONFIG.get("explainer", {})
    llm = get_llm(
        provider=config.get("provider", "openai"),
        model=config.get("model"),
        temperature=float(config.get("temperature", 0.2)),
    )

    prompt = EXPLAINER_PROMPT.format(
        user_query=state.user_query,
        sql=state.sql or "No SQL query was executed.",
        sample_rows=state.rows[:5] if state.rows else [],
        chart_path=state.chart_path or "No chart was generated.",
    )
    response = await llm.ainvoke(
        [
            SystemMessage(content="You are a data explanation assistant."),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "answer": response.content,
        "sql": state.sql,
        "history": state.history + [_history(state, response.content)],
        "processing_end_time": datetime.now(),
        "completed_agents": state.completed_agents + ["explainer"],
    }
