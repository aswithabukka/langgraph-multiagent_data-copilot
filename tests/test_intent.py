"""Tests for app.agents.intent — classifiers + canned responders."""

import pytest

from app.agents.intent import (
    evaluate_arithmetic,
    handle_off_topic_query,
    is_data_related_query,
    is_simple_arithmetic,
    requires_chart,
)


# ---------------------------------------------------------------------------
# is_simple_arithmetic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "2+2",
        "what is 15*3+7",
        "calculate (100-25)/3",
        "50*2-10+5",
        "compute 7×8",
        "what is 2 plus 3",
    ],
)
def test_arithmetic_positive(query):
    assert is_simple_arithmetic(query)


@pytest.mark.parametrize(
    "query",
    [
        "show me total sales",
        "list all customers",
        "how many orders are there",
        "sum of revenue by region",
    ],
)
def test_arithmetic_negative(query):
    assert not is_simple_arithmetic(query)


# ---------------------------------------------------------------------------
# is_data_related_query
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "show me total sales by region",
        "how many orders are there",
        "what is the total revenue last quarter",
        "list customers with the highest order value",
        "create a bar chart of monthly revenue",
    ],
)
def test_data_related_positive(query):
    assert is_data_related_query(query)


@pytest.mark.parametrize(
    "query",
    [
        "what is mapreduce",
        "tell me about blockchain",
        "how do I cook pasta",
    ],
)
def test_data_related_negative(query):
    assert not is_data_related_query(query)


# ---------------------------------------------------------------------------
# requires_chart
# ---------------------------------------------------------------------------


def test_requires_chart_true():
    assert requires_chart("show me sales by region as a bar chart")
    assert requires_chart("plot monthly revenue")
    assert requires_chart("visualize customer growth")


def test_requires_chart_false():
    assert not requires_chart("how many orders are there")


# ---------------------------------------------------------------------------
# evaluate_arithmetic
# ---------------------------------------------------------------------------


def test_evaluate_arithmetic_basic():
    assert evaluate_arithmetic("what is 2+3") == "The answer is 5"
    assert evaluate_arithmetic("calculate 10/4") == "The answer is 2.5"
    assert evaluate_arithmetic("3*5") == "The answer is 15"


def test_evaluate_arithmetic_respects_precedence():
    # (4 + 2) * 3 = 18, not (4 + (2 * 3)) = 10
    assert evaluate_arithmetic("(4+2)*3") == "The answer is 18"


def test_evaluate_arithmetic_handles_unicode_operators():
    assert evaluate_arithmetic("8×3") == "The answer is 24"
    assert evaluate_arithmetic("12÷4") == "The answer is 3"


def test_evaluate_arithmetic_division_by_zero():
    assert "Division by zero" in evaluate_arithmetic("1/0")


def test_evaluate_arithmetic_rejects_non_math():
    # No expression to evaluate.
    assert "couldn't find" in evaluate_arithmetic("hello there")


def test_evaluate_arithmetic_rejects_letters_in_expression():
    # Pattern only captures digits + operators, so "abc" never matches —
    # we get the "couldn't find" branch, not an eval bypass.
    out = evaluate_arithmetic("calculate abc + def")
    assert "couldn't find" in out or "invalid characters" in out


# ---------------------------------------------------------------------------
# handle_off_topic_query
# ---------------------------------------------------------------------------


def test_off_topic_known_topic():
    response = handle_off_topic_query("what is mapreduce")
    assert "MapReduce" in response


def test_off_topic_default_response():
    response = handle_off_topic_query("just chatting")
    # Default response includes the example queries.
    assert "Show me total sales by region" in response
