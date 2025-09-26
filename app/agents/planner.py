"""
Planner agent for LangGraph Data Copilot.

This agent is responsible for creating an execution plan based on the user's query.
"""

import json
from typing import Dict, List

from langchain.schema import HumanMessage
from langchain_core.messages import SystemMessage

from app.agents.config import AGENT_CONFIG, get_llm
from app.agents.prompts import PLANNER_PROMPT
from app.models.state import GraphState, PlanStep


def parse_plan(plan_text: str) -> List[PlanStep]:
    """
    Parse the plan text into structured PlanStep objects.
    
    Args:
        plan_text: Raw plan text from the LLM
        
    Returns:
        List of PlanStep objects
    """
    steps = []
    current_step = {}
    
    try:
        # Try to parse as JSON first (in case LLM returned JSON)
        try:
            parsed_json = json.loads(plan_text)
            if isinstance(parsed_json, list):
                for i, step in enumerate(parsed_json):
                    steps.append(
                        PlanStep(
                            step_number=i + 1,
                            action=step.get("action", ""),
                            description=step.get("description", ""),
                            requires_sql=step.get("requires_sql", False),
                            requires_chart=step.get("requires_chart", False),
                        )
                    )
                return steps
        except json.JSONDecodeError:
            pass
        
        # Parse text format
        lines = plan_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # New step starts with a number
            if line[0].isdigit() and "." in line[:3]:
                # Save previous step if exists
                if current_step and "step_number" in current_step:
                    steps.append(PlanStep(**current_step))
                
                # Start new step
                parts = line.split(".", 1)
                step_num = int(parts[0])
                description = parts[1].strip()
                
                current_step = {
                    "step_number": step_num,
                    "action": description.split(":")[0] if ":" in description else description,
                    "description": description,
                    "requires_sql": False,
                    "requires_chart": False,
                }
            
            # Check for SQL requirement
            elif "sql" in line.lower():
                current_step["requires_sql"] = "true" in line.lower() or "yes" in line.lower()
            
            # Check for chart requirement
            elif "chart" in line.lower():
                current_step["requires_chart"] = "true" in line.lower() or "yes" in line.lower()
        
        # Add the last step
        if current_step and "step_number" in current_step:
            steps.append(PlanStep(**current_step))
    
    except Exception as e:
        # Fallback to a simple plan if parsing fails
        steps = [
            PlanStep(
                step_number=1,
                action="Process query",
                description=f"Process the query: {plan_text}",
                requires_sql=True,
                requires_chart=False,
            )
        ]
    
    return steps


def is_simple_arithmetic(query: str) -> bool:
    """
    Check if the query is a simple arithmetic question.
    
    Args:
        query: User query string
        
    Returns:
        True if the query is a simple arithmetic question, False otherwise
    """
    import re
    
    query_lower = query.lower().strip()
    
    # Check if the query contains numbers and mathematical operators
    has_numbers = bool(re.search(r'\d+', query_lower))
    has_math_operators = bool(re.search(r'[+\-*/()×÷]', query_lower))
    
    # Check for arithmetic question patterns
    arithmetic_patterns = [
        r'what\s+is\s+[\d\s+\-*/().×÷]+',     # "what is 2+3*4"
        r'calculate\s+[\d\s+\-*/().×÷]+',     # "calculate 2+3*4"
        r'compute\s+[\d\s+\-*/().×÷]+',       # "compute 2+3*4"
        r'solve\s+[\d\s+\-*/().×÷]+',         # "solve 2+3*4"
        r'^[\d\s+\-*/().×÷]+\s*[?]?$',        # just "2+3*4" or "2+3*4?"
        r'equals?\s*to\s*[\d\s+\-*/().×÷]+', # "equals to 2+3"
    ]
    
    # Check if query matches any arithmetic pattern
    for pattern in arithmetic_patterns:
        if re.search(pattern, query_lower):
            return True
    
    # Check for arithmetic keywords with numbers
    arithmetic_keywords = [
        'add', 'subtract', 'multiply', 'divide', 'plus', 'minus',
        'times', 'divided by', 'sum of', 'difference of', 'product of',
        'quotient of', 'square root', 'squared', 'power', 'exponent'
    ]
    
    if has_numbers:
        for keyword in arithmetic_keywords:
            if keyword in query_lower:
                return True
    
    # If it has both numbers and math operators, likely arithmetic
    if has_numbers and has_math_operators:
        # But exclude data-related queries
        data_keywords = [
            'table', 'database', 'data', 'records', 'rows', 'columns',
            'sales', 'orders', 'customers', 'products', 'revenue',
            'count', 'average', 'total', 'sum', 'group by', 'where',
            'select', 'from', 'show me', 'find', 'get', 'list'
        ]
        
        # If it contains data keywords, it's probably a data query, not arithmetic
        for keyword in data_keywords:
            if keyword in query_lower:
                return False
        
        return True
    
    return False


def is_data_related_query(query: str) -> bool:
    """
    Check if the query is related to data analysis or database operations.
    
    Args:
        query: User query string
        
    Returns:
        True if the query is data-related, False otherwise
    """
    import re
    
    query_lower = query.lower().strip()
    
    # Data-related keywords and patterns
    data_keywords = [
        # Database operations
        'select', 'from', 'where', 'group by', 'order by', 'having',
        'count', 'sum', 'average', 'avg', 'min', 'max', 'distinct',
        
        # Data analysis terms
        'data', 'database', 'table', 'records', 'rows', 'columns',
        'sales', 'orders', 'customers', 'products', 'revenue', 'profit',
        'total', 'show me', 'find', 'get', 'list', 'display',
        'how many', 'what are', 'which', 'who has', 'when did',
        
        # Analysis terms
        'analyze', 'analysis', 'report', 'summary', 'breakdown',
        'trend', 'pattern', 'distribution', 'comparison', 'correlation',
        'top', 'bottom', 'highest', 'lowest', 'best', 'worst',
        'by region', 'by category', 'by month', 'by year', 'by date',
        
        # Chart/visualization terms
        'chart', 'graph', 'plot', 'visualize', 'show chart', 'create chart',
        'generate chart', 'make chart', 'draw chart', 'visualization'
    ]
    
    # Check for data-related keywords
    for keyword in data_keywords:
        if keyword in query_lower:
            return True
    
    # Check for question patterns that suggest data queries
    data_patterns = [
        r'how many .+ (are|were|in)',
        r'what (is|are) the .+ (sales|revenue|orders|customers)',
        r'show me .+ (data|information|records)',
        r'list .+ (customers|orders|products)',
        r'find .+ (with|having|where)',
        r'which .+ (has|have|had) the (most|least|highest|lowest)',
        r'total .+ (by|for|in)',
        r'average .+ (per|by|for)',
    ]
    
    for pattern in data_patterns:
        if re.search(pattern, query_lower):
            return True
    
    return False


def requires_chart(query: str) -> bool:
    """
    Check if the query explicitly requests a chart or visualization.
    
    Args:
        query: User query string
        
    Returns:
        True if a chart is requested, False otherwise
    """
    query_lower = query.lower().strip()
    
    chart_keywords = [
        'chart', 'graph', 'plot', 'visualize', 'visualization',
        'show chart', 'create chart', 'generate chart', 'make chart',
        'draw chart', 'bar chart', 'line chart', 'pie chart',
        'scatter plot', 'histogram', 'give me graph', 'also give me graph'
    ]
    
    for keyword in chart_keywords:
        if keyword in query_lower:
            return True
    
    return False


def planner_agent(state: GraphState) -> Dict:
    """
    Create an execution plan for the user's query.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated graph state with execution plan
    """
    # Check for simple arithmetic questions first
    if is_simple_arithmetic(state.user_query):
        # Create a simple plan for arithmetic questions
        plan_steps = [
            PlanStep(
                step_number=1,
                action="Answer directly",
                description="Answer the arithmetic question directly",
                requires_sql=False,
                requires_chart=False,
            )
        ]
        
        return {
            "plan": plan_steps,
            "next_agent": "explainer",  # Skip SQL and chart for arithmetic
            "completed_agents": state.completed_agents + ["planner"],
        }
    
    # Check if the query is data-related
    if not is_data_related_query(state.user_query):
        # Create a plan for off-topic questions
        plan_steps = [
            PlanStep(
                step_number=1,
                action="Handle off-topic",
                description="Provide helpful response for off-topic query and guide back to data analysis",
                requires_sql=False,
                requires_chart=False,
            )
        ]
        
        return {
            "plan": plan_steps,
            "next_agent": "explainer",  # Skip SQL and chart for off-topic
            "completed_agents": state.completed_agents + ["planner"],
        }
    
    # For data queries, create a plan based on requirements
    needs_chart = requires_chart(state.user_query)
    
    # Create plan steps
    plan_steps = [
        PlanStep(
            step_number=1,
            action="Generate SQL query",
            description="Create SQL query to retrieve data for analysis",
            requires_sql=True,
            requires_chart=False,
        ),
        PlanStep(
            step_number=2,
            action="Generate chart" if needs_chart else "Skip chart",
            description="Create visualization of the data" if needs_chart else "No chart requested",
            requires_sql=False,
            requires_chart=needs_chart,
        ),
        PlanStep(
            step_number=3,
            action="Explain results",
            description="Provide natural language explanation of the analysis",
            requires_sql=False,
            requires_chart=False,
        )
    ]

    # Update state
    return {
        "plan": plan_steps,
        "next_agent": "sql",
        "completed_agents": state.completed_agents + ["planner"],
    }
