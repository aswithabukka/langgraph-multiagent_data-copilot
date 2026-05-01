"""Tests for app.agents.parsing — pure LLM-output parsers."""

from app.agents.parsing import (
    extract_chart_config,
    extract_sql_query,
    parse_plan,
)


# ---------------------------------------------------------------------------
# extract_sql_query
# ---------------------------------------------------------------------------


def test_extract_sql_query_with_sql_fence():
    text = "Here you go:\n```sql\nSELECT * FROM orders\nWHERE id = 1\n```\nDone."
    assert extract_sql_query(text) == "SELECT * FROM orders\nWHERE id = 1"


def test_extract_sql_query_with_plain_fence():
    text = "```\nSELECT 1\n```"
    assert extract_sql_query(text) == "SELECT 1"


def test_extract_sql_query_no_fence():
    assert extract_sql_query("  SELECT 1  ") == "SELECT 1"


# ---------------------------------------------------------------------------
# parse_plan
# ---------------------------------------------------------------------------


def test_parse_plan_from_json_array():
    text = '[{"action": "sql", "description": "run it", "requires_sql": true, "requires_chart": false}]'
    plan = parse_plan(text)
    assert len(plan) == 1
    assert plan[0].action == "sql"
    assert plan[0].requires_sql is True
    assert plan[0].requires_chart is False


def test_parse_plan_from_numbered_text():
    text = "1. Generate SQL: pull totals\n   sql: true\n2. Explain results\n"
    plan = parse_plan(text)
    assert len(plan) == 2
    assert plan[0].step_number == 1
    assert plan[0].requires_sql is True
    assert plan[1].step_number == 2


def test_parse_plan_falls_back_to_default_on_garbage():
    plan = parse_plan("not a plan, not even close")
    assert len(plan) == 1
    assert plan[0].requires_sql is True


def test_parse_plan_handles_invalid_json_gracefully():
    plan = parse_plan('{"this": "is": "broken"}')
    # Should fall through to the text path, then fallback.
    assert len(plan) >= 1


# ---------------------------------------------------------------------------
# extract_chart_config
# ---------------------------------------------------------------------------


def test_extract_chart_config_from_json_fence():
    text = '```json\n{"chart_type": "line", "x_column": "month", "y_column": "revenue", "title": "Trend"}\n```'
    cfg = extract_chart_config(text)
    assert cfg["chart_type"] == "line"
    assert cfg["x_column"] == "month"
    assert cfg["y_column"] == "revenue"
    assert cfg["title"] == "Trend"


def test_extract_chart_config_from_bare_json():
    cfg = extract_chart_config('{"chart_type": "pie", "x_column": "region", "y_column": "sales", "title": "Pie"}')
    assert cfg["chart_type"] == "pie"


def test_extract_chart_config_falls_back_to_keyvalue_scan():
    text = "chart_type: bar\nx_column: 'region'\ny_column: \"sales\"\ntitle: My Chart"
    cfg = extract_chart_config(text)
    assert cfg["chart_type"] == "bar"
    assert cfg["x_column"] == "region"
    assert cfg["y_column"] == "sales"
    assert cfg["title"] == "My Chart"


def test_extract_chart_config_returns_defaults_on_garbage():
    cfg = extract_chart_config("garbage that mentions nothing useful")
    assert set(cfg.keys()) == {"chart_type", "x_column", "y_column", "title"}
    assert cfg["chart_type"] == "bar"  # default
