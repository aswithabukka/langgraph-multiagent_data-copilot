"""
Intent classification + canned responders.

Pure helpers used by the planner and the explainer to:
  * decide whether a query is arithmetic, off-topic, or data-related;
  * compute a safe arithmetic answer without an LLM;
  * produce a guidance reply for off-topic queries.

These functions never call an LLM or hit the database — keeps the planner /
explainer thin and lets us test the heuristics in isolation.
"""

from __future__ import annotations

import ast
import operator
import re
from typing import Callable, Dict


# ---------------------------------------------------------------------------
# classification
# ---------------------------------------------------------------------------


_DATA_KEYWORDS_EXCLUDE_FROM_ARITHMETIC = (
    "table", "database", "data", "records", "rows", "columns",
    "sales", "orders", "customers", "products", "revenue",
    "count", "average", "total", "sum", "group by", "where",
    "select", "from", "show me", "find", "get", "list",
)

_ARITHMETIC_PATTERNS = (
    r"what\s+is\s+[\d\s+\-*/().×÷]+",
    r"calculate\s+[\d\s+\-*/().×÷]+",
    r"compute\s+[\d\s+\-*/().×÷]+",
    r"solve\s+[\d\s+\-*/().×÷]+",
    r"^[\d\s+\-*/().×÷]+\s*[?]?$",
    r"equals?\s*to\s*[\d\s+\-*/().×÷]+",
)

_ARITHMETIC_KEYWORDS = (
    "add", "subtract", "multiply", "divide", "plus", "minus",
    "times", "divided by", "sum of", "difference of", "product of",
    "quotient of", "square root", "squared", "power", "exponent",
)


def is_simple_arithmetic(query: str) -> bool:
    """True if the query is a math expression we can answer without an LLM."""
    q = query.lower().strip()

    for pattern in _ARITHMETIC_PATTERNS:
        if re.search(pattern, q):
            return True

    has_numbers = bool(re.search(r"\d+", q))
    has_operators = bool(re.search(r"[+\-*/()×÷]", q))

    if has_numbers and any(kw in q for kw in _ARITHMETIC_KEYWORDS):
        return True

    if has_numbers and has_operators:
        # numbers + operators alone aren't enough — many data queries match
        # too ("sum of orders by region"). Exclude those.
        if any(kw in q for kw in _DATA_KEYWORDS_EXCLUDE_FROM_ARITHMETIC):
            return False
        return True

    return False


_DATA_KEYWORDS = (
    "select", "from", "where", "group by", "order by", "having",
    "count", "sum", "average", "avg", "min", "max", "distinct",
    "data", "database", "table", "records", "rows", "columns",
    "sales", "orders", "customers", "products", "revenue", "profit",
    "total", "show me", "find", "get", "list", "display",
    "how many", "what are", "which", "who has", "when did",
    "analyze", "analysis", "report", "summary", "breakdown",
    "trend", "pattern", "distribution", "comparison", "correlation",
    "top", "bottom", "highest", "lowest", "best", "worst",
    "by region", "by category", "by month", "by year", "by date",
    "chart", "graph", "plot", "visualize", "show chart", "create chart",
    "generate chart", "make chart", "draw chart", "visualization",
)

_DATA_PATTERNS = (
    r"how many .+ (are|were|in)",
    r"what (is|are) the .+ (sales|revenue|orders|customers)",
    r"show me .+ (data|information|records)",
    r"list .+ (customers|orders|products)",
    r"find .+ (with|having|where)",
    r"which .+ (has|have|had) the (most|least|highest|lowest)",
    r"total .+ (by|for|in)",
    r"average .+ (per|by|for)",
)


def is_data_related_query(query: str) -> bool:
    """True if the query looks like it wants data from the database."""
    q = query.lower().strip()

    if any(kw in q for kw in _DATA_KEYWORDS):
        return True

    for pattern in _DATA_PATTERNS:
        if re.search(pattern, q):
            return True

    return False


_CHART_KEYWORDS = (
    "chart", "graph", "plot", "visualize", "visualization",
    "show chart", "create chart", "generate chart", "make chart",
    "draw chart", "bar chart", "line chart", "pie chart",
    "scatter plot", "histogram", "give me graph", "also give me graph",
)


def requires_chart(query: str) -> bool:
    """True if the query explicitly asks for a visualization."""
    q = query.lower().strip()
    return any(kw in q for kw in _CHART_KEYWORDS)


# ---------------------------------------------------------------------------
# arithmetic responder (AST-based, no eval)
# ---------------------------------------------------------------------------


_AST_OPS: Dict[type, Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_EXPR_PATTERNS = (
    r"what\s+is\s+([\d\s+\-*/().]+)",
    r"calculate\s+([\d\s+\-*/().]+)",
    r"compute\s+([\d\s+\-*/().]+)",
    r"solve\s+([\d\s+\-*/().]+)",
    r"^([\d\s+\-*/().]+)$",
)


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("unsupported literal")
    if isinstance(node, ast.BinOp):
        return _AST_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _AST_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"unsupported node: {type(node).__name__}")


def evaluate_arithmetic(query: str) -> str:
    """Evaluate a simple arithmetic question — never uses eval()."""
    q = query.lower().strip()

    expression = None
    for pattern in _EXPR_PATTERNS:
        match = re.search(pattern, q)
        if match:
            expression = match.group(1).strip()
            break

    if not expression:
        return "I couldn't find a mathematical expression in your query."

    expression = re.sub(r"\s+", "", expression).replace("×", "*").replace("÷", "/")

    if not re.match(r"^[\d+\-*/().]+$", expression):
        return "The expression contains invalid characters."

    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
    except ZeroDivisionError:
        return "Error: Division by zero is not allowed."
    except (ValueError, SyntaxError, TypeError, KeyError):
        return f"Error: Could not evaluate the expression '{expression}'. Please check your math syntax."

    if isinstance(result, float) and result.is_integer():
        return f"The answer is {int(result)}"
    if isinstance(result, float):
        return f"The answer is {result:.6g}"
    return f"The answer is {result}"


# ---------------------------------------------------------------------------
# off-topic responder
# ---------------------------------------------------------------------------


_OFF_TOPIC_RESPONSES: Dict[str, str] = {
    "mapreduce": (
        "MapReduce is a programming model for processing large datasets across "
        "distributed systems. However, I'm designed to help you analyze your "
        "sales data! Try asking me about your orders, customers, or revenue trends."
    ),
    "machine learning": (
        "Machine Learning involves algorithms that learn from data to make "
        "predictions. I'd love to help you discover patterns in your sales "
        "data instead! Ask me about customer trends or product performance."
    ),
    "artificial intelligence": (
        "AI involves creating systems that can perform tasks requiring human "
        "intelligence. Speaking of intelligence, let me help you gain insights "
        "from your data! Try asking about sales by region or top customers."
    ),
    "blockchain": (
        "Blockchain is a distributed ledger technology. While that's interesting, "
        "I'm here to help you understand your business data! Ask me about "
        "revenue trends or order patterns."
    ),
    "cloud computing": (
        "Cloud computing delivers computing services over the internet. I'm "
        "focused on helping you analyze your local sales data though! Try "
        "asking about customer segments or product sales."
    ),
}

_DEFAULT_OFF_TOPIC = (
    "I'm a data analysis copilot designed to help you understand your sales "
    "data. I can answer questions about your orders, customers, products, "
    "and revenue using natural language. Try asking something like:\n\n"
    "• 'Show me total sales by region'\n"
    "• 'What are the top 5 products?'\n"
    "• 'How many customers do we have?'\n"
    "• 'Create a chart of monthly revenue'\n\n"
    "What would you like to know about your data?"
)


def handle_off_topic_query(query: str) -> str:
    """Return a helpful redirection for queries outside the data scope."""
    q = query.lower().strip()

    for topic, response in _OFF_TOPIC_RESPONSES.items():
        if topic in q:
            return response

    if any(w in q for w in ("what is", "what are", "define", "explain")):
        if any(w in q for w in ("technology", "programming", "software", "algorithm", "system")):
            return (
                "That's an interesting technical question! However, I'm specialized "
                "in analyzing sales and business data. I can help you explore your "
                "orders, customers, revenue trends, and create visualizations. Try "
                "asking me something like 'Show me sales by region' or 'What are "
                "the top products?'"
            )
        return (
            "I'm a data analysis assistant focused on helping you understand your "
            "sales data. While I can't answer general questions, I'd be happy to "
            "help you analyze your orders, customers, products, or revenue! Try "
            "asking about trends, totals, or specific data insights."
        )

    if any(w in q for w in ("how to", "how do", "tutorial", "guide")):
        return (
            "I'm designed to help you analyze your business data rather than "
            "provide tutorials. I can show you insights about your sales, "
            "customers, and products through natural language queries. Try "
            "asking 'How many orders this month?' or 'Show me top customers "
            "by revenue'."
        )

    if any(w in q for w in ("weather", "news", "sports", "entertainment")):
        return (
            "I don't have access to external information like weather or news. "
            "I'm specialized in analyzing your sales database! I can help you "
            "discover trends in your orders, analyze customer behavior, or "
            "create charts. Ask me about your business data instead!"
        )

    return _DEFAULT_OFF_TOPIC
