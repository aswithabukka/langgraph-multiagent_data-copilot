"""
Pure parsers for LLM responses.

These functions take raw LLM output strings and turn them into the structured
objects the agents need (plan steps, SQL strings, chart configs). They have
no LLM calls, no DB access, and no I/O — which makes them straightforward to
unit-test without mocks.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from app.models.state import PlanStep


# ---------------------------------------------------------------------------
# planner
# ---------------------------------------------------------------------------


def parse_plan(plan_text: str) -> List[PlanStep]:
    """Parse a plan from LLM output into a list of PlanStep objects.

    Accepts either a JSON array of step objects or a numbered text list.
    Falls back to a single best-effort step on parse failure so callers always
    get a non-empty plan.
    """
    # JSON-first path: many models will emit a clean JSON array.
    try:
        parsed = json.loads(plan_text)
        if isinstance(parsed, list):
            steps: List[PlanStep] = []
            for i, step in enumerate(parsed):
                steps.append(
                    PlanStep(
                        step_number=i + 1,
                        action=step.get("action", ""),
                        description=step.get("description", ""),
                        requires_sql=bool(step.get("requires_sql", False)),
                        requires_chart=bool(step.get("requires_chart", False)),
                    )
                )
            if steps:
                return steps
    except (json.JSONDecodeError, TypeError):
        pass

    steps = []
    current: Dict[str, Any] = {}

    for raw in plan_text.strip().split("\n"):
        line = raw.strip()
        if not line:
            continue

        # New step starts with "<num>." — flush previous and open a new one.
        if line[0].isdigit() and "." in line[:3]:
            if current.get("step_number") is not None:
                steps.append(PlanStep(**current))
            num_str, _, rest = line.partition(".")
            description = rest.strip()
            current = {
                "step_number": int(num_str),
                "action": description.split(":", 1)[0] if ":" in description else description,
                "description": description,
                "requires_sql": False,
                "requires_chart": False,
            }
        elif "sql" in line.lower():
            current["requires_sql"] = "true" in line.lower() or "yes" in line.lower()
        elif "chart" in line.lower():
            current["requires_chart"] = "true" in line.lower() or "yes" in line.lower()

    if current.get("step_number") is not None:
        steps.append(PlanStep(**current))

    if steps:
        return steps

    # Last-resort fallback — never return an empty plan.
    return [
        PlanStep(
            step_number=1,
            action="Process query",
            description=f"Process the query: {plan_text}",
            requires_sql=True,
            requires_chart=False,
        )
    ]


# ---------------------------------------------------------------------------
# sql
# ---------------------------------------------------------------------------


def extract_sql_query(sql_text: str) -> str:
    """Pull a SQL statement out of the LLM response.

    Handles ```sql ...``` fences, plain ``` ...``` fences, and bare SQL.
    """
    if "```sql" in sql_text:
        body = sql_text.split("```sql", 1)[1]
        return body.split("```", 1)[0].strip()

    if "```" in sql_text:
        body = sql_text.split("```", 1)[1]
        return body.split("```", 1)[0].strip()

    return sql_text.strip()


# ---------------------------------------------------------------------------
# chart
# ---------------------------------------------------------------------------


_CHART_DEFAULT: Dict[str, Any] = {
    "chart_type": "bar",
    "x_column": "",
    "y_column": "",
    "title": "Data Analysis Chart",
}


def _coerce_chart(parsed: Dict[str, Any]) -> Dict[str, Any]:
    return {**_CHART_DEFAULT, **{k: v for k, v in parsed.items() if v is not None}}


def extract_chart_config(chart_text: str) -> Dict[str, Any]:
    """Pull a chart-config dict out of the LLM response.

    Tries JSON in fences, then bare JSON, then a permissive key:value scan.
    Always returns a dict containing all four expected keys.
    """
    # Fenced JSON.
    for fence in ("```json", "```"):
        if fence in chart_text:
            body = chart_text.split(fence, 1)[1].split("```", 1)[0]
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    return _coerce_chart(parsed)
            except json.JSONDecodeError:
                pass

    # Bare JSON.
    try:
        parsed = json.loads(chart_text)
        if isinstance(parsed, dict):
            return _coerce_chart(parsed)
    except json.JSONDecodeError:
        pass

    # Lenient key:value scan as a last resort.
    config = dict(_CHART_DEFAULT)
    text_lower = chart_text.lower()

    if "chart_type" in text_lower:
        for chart_type in ("bar", "line", "scatter", "pie", "histogram"):
            if chart_type in text_lower:
                config["chart_type"] = chart_type
                break

    for key in ("x_column", "y_column", "title"):
        if key in text_lower and ":" in chart_text:
            for line in chart_text.split("\n"):
                if key in line.lower() and ":" in line:
                    config[key] = line.split(":", 1)[1].strip().strip("\"'")
                    break

    return config
