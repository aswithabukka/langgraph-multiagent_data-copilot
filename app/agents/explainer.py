"""
Explainer agent for LangGraph Data Copilot.

This agent is responsible for generating natural language explanations
of the data analysis results.
"""

from datetime import datetime
from typing import Dict

from langchain.schema import HumanMessage
from langchain_core.messages import SystemMessage

from app.agents.config import AGENT_CONFIG, get_llm
from app.agents.prompts import EXPLAINER_PROMPT
from app.models.state import GraphState, HistoryEntry


def evaluate_arithmetic(query: str) -> str:
    """
    Evaluate arithmetic expressions using a safe evaluation approach.
    
    Args:
        query: User query string
        
    Returns:
        Answer to the arithmetic question
    """
    import re
    import ast
    import operator
    
    # Clean the query and extract mathematical expression
    query_lower = query.lower().strip()
    
    # Try to extract mathematical expressions from common question formats
    math_expression_patterns = [
        r'what\s+is\s+([\d\s+\-*/().]+)',  # "what is 2+3*4"
        r'calculate\s+([\d\s+\-*/().]+)',  # "calculate 2+3*4"
        r'compute\s+([\d\s+\-*/().]+)',   # "compute 2+3*4"
        r'solve\s+([\d\s+\-*/().]+)',     # "solve 2+3*4"
        r'^([\d\s+\-*/().]+)$',           # just "2+3*4"
    ]
    
    expression = None
    for pattern in math_expression_patterns:
        match = re.search(pattern, query_lower)
        if match:
            expression = match.group(1).strip()
            break
    
    if not expression:
        return "I couldn't find a mathematical expression in your query."
    
    # Clean up the expression (remove extra spaces, handle common symbols)
    expression = re.sub(r'\s+', '', expression)  # Remove all spaces
    expression = expression.replace('×', '*').replace('÷', '/')  # Replace symbols
    
    # Validate that the expression only contains safe characters
    if not re.match(r'^[\d+\-*/().]+$', expression):
        return "The expression contains invalid characters."
    
    try:
        # Use AST to safely evaluate the mathematical expression
        # This is much safer than eval() and handles order of operations correctly
        def safe_eval(node):
            if isinstance(node, ast.Constant):  # Python 3.8+
                return node.value
            elif isinstance(node, ast.Num):  # Python < 3.8
                return node.n
            elif isinstance(node, ast.BinOp):
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                return ops[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = safe_eval(node.operand)
                return ops[type(node.op)](operand)
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")
        
        # Define safe operations
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Parse and evaluate the expression
        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree.body)
        
        # Format the result nicely
        if isinstance(result, float) and result.is_integer():
            return f"The answer is {int(result)}"
        elif isinstance(result, float):
            return f"The answer is {result:.6g}"  # Use general format to avoid unnecessary decimals
        else:
            return f"The answer is {result}"
            
    except ZeroDivisionError:
        return "Error: Division by zero is not allowed."
    except (ValueError, SyntaxError, TypeError) as e:
        return f"Error: Could not evaluate the expression '{expression}'. Please check your math syntax."
    except Exception as e:
        return f"Error: An unexpected error occurred while evaluating the expression."


def handle_off_topic_query(query: str) -> str:
    """
    Handle off-topic queries with helpful responses and guidance.
    
    Args:
        query: User query string
        
    Returns:
        Helpful response for off-topic queries
    """
    query_lower = query.lower().strip()
    
    # Common off-topic categories and responses
    responses = {
        # Technology/Programming concepts
        'mapreduce': "MapReduce is a programming model for processing large datasets across distributed systems. However, I'm designed to help you analyze your sales data! Try asking me about your orders, customers, or revenue trends.",
        
        'machine learning': "Machine Learning involves algorithms that learn from data to make predictions. I'd love to help you discover patterns in your sales data instead! Ask me about customer trends or product performance.",
        
        'artificial intelligence': "AI involves creating systems that can perform tasks requiring human intelligence. Speaking of intelligence, let me help you gain insights from your data! Try asking about sales by region or top customers.",
        
        'blockchain': "Blockchain is a distributed ledger technology. While that's interesting, I'm here to help you understand your business data! Ask me about revenue trends or order patterns.",
        
        'cloud computing': "Cloud computing delivers computing services over the internet. I'm focused on helping you analyze your local sales data though! Try asking about customer segments or product sales.",
    }
    
    # Check for specific topics
    for topic, response in responses.items():
        if topic in query_lower:
            return response
    
    # Generic responses for different question types
    if any(word in query_lower for word in ['what is', 'what are', 'define', 'explain']):
        if any(word in query_lower for word in ['technology', 'programming', 'software', 'algorithm', 'system']):
            return f"That's an interesting technical question! However, I'm specialized in analyzing sales and business data. I can help you explore your orders, customers, revenue trends, and create visualizations. Try asking me something like 'Show me sales by region' or 'What are the top products?'"
        else:
            return f"I'm a data analysis assistant focused on helping you understand your sales data. While I can't answer general questions, I'd be happy to help you analyze your orders, customers, products, or revenue! Try asking about trends, totals, or specific data insights."
    
    elif any(word in query_lower for word in ['how to', 'how do', 'tutorial', 'guide']):
        return f"I'm designed to help you analyze your business data rather than provide tutorials. I can show you insights about your sales, customers, and products through natural language queries. Try asking 'How many orders this month?' or 'Show me top customers by revenue'."
    
    elif any(word in query_lower for word in ['weather', 'news', 'sports', 'entertainment']):
        return f"I don't have access to external information like weather or news. I'm specialized in analyzing your sales database! I can help you discover trends in your orders, analyze customer behavior, or create charts. Ask me about your business data instead!"
    
    else:
        return f"I'm a data analysis copilot designed to help you understand your sales data. I can answer questions about your orders, customers, products, and revenue using natural language. Try asking something like:\n\n• 'Show me total sales by region'\n• 'What are the top 5 products?'\n• 'How many customers do we have?'\n• 'Create a chart of monthly revenue'\n\nWhat would you like to know about your data?"


def explainer_agent(state: GraphState) -> Dict:
    """
    Generate a natural language explanation of the data analysis results.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated graph state with explanation
    """
    # Check if this is a simple arithmetic question that we can handle directly
    is_arithmetic = any(step.action == "Answer directly" for step in state.plan)
    is_off_topic = any(step.action == "Handle off-topic" for step in state.plan)
    
    if is_arithmetic:
        # Handle arithmetic question directly
        answer = evaluate_arithmetic(state.user_query)
        
        # Create history entry
        history_entry = HistoryEntry(
            query=state.user_query,
            answer=answer,
            chart_path=None,
            timestamp=datetime.now(),
        )
        
        # Update state
        return {
            "answer": answer,
            "history": state.history + [history_entry],
            "processing_end_time": datetime.now(),
            "completed_agents": state.completed_agents + ["explainer"],
        }
    
    if is_off_topic:
        # Handle off-topic question with helpful guidance
        answer = handle_off_topic_query(state.user_query)
        
        # Create history entry
        history_entry = HistoryEntry(
            query=state.user_query,
            answer=answer,
            chart_path=None,
            timestamp=datetime.now(),
        )
        
        # Update state
        return {
            "answer": answer,
            "history": state.history + [history_entry],
            "processing_end_time": datetime.now(),
            "completed_agents": state.completed_agents + ["explainer"],
        }
    
    # For other queries, use the LLM
    config = AGENT_CONFIG.get("explainer", {})
    llm = get_llm(
        provider=config.get("provider", "openai"),
        model=config.get("model"),
        temperature=float(config.get("temperature", 0.2)),
    )
    
    # Format prompt
    sample_rows = state.rows[:5] if state.rows else []
    prompt = EXPLAINER_PROMPT.format(
        user_query=state.user_query,
        sql=state.sql or "No SQL query was executed.",
        sample_rows=sample_rows,
        chart_path=state.chart_path or "No chart was generated.",
    )
    
    # Get response from LLM
    messages = [
        SystemMessage(content="You are a data explanation assistant."),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    
    # Create history entry
    history_entry = HistoryEntry(
        query=state.user_query,
        answer=response.content,
        chart_path=state.chart_path,
        timestamp=datetime.now(),
    )
    
    # Update state
    return {
        "answer": response.content,
        "sql": state.sql,  # Pass through the SQL query
        "history": state.history + [history_entry],
        "processing_end_time": datetime.now(),
        "completed_agents": state.completed_agents + ["explainer"],
    }
