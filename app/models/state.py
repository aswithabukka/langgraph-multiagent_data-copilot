"""
GraphState models for LangGraph Multi-Agent Data Analysis Copilot.

This module defines the Pydantic models that represent the state
passed between agents in the LangGraph workflow.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    """Represents a single entry in the conversation history."""
    
    query: str = Field(..., description="User's original query")
    answer: str = Field(..., description="System's response")
    chart_path: Optional[str] = Field(None, description="Path to generated chart")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this entry was created")


class PlanStep(BaseModel):
    """Represents a single step in the execution plan."""
    
    step_number: int = Field(..., description="Order of this step")
    action: str = Field(..., description="What action to take")
    description: str = Field(..., description="Human-readable description")
    requires_sql: bool = Field(False, description="Whether this step needs SQL execution")
    requires_chart: bool = Field(False, description="Whether this step needs chart generation")


class GraphState(BaseModel):
    """
    Main state object passed between LangGraph agents.
    
    This contains all the information needed for the multi-agent workflow
    including user queries, execution plans, SQL results, charts, and history.
    """
    
    # Input
    user_query: str = Field(..., description="Original user query")
    session_id: Optional[str] = Field(None, description="Session identifier for state persistence")
    
    # Planning
    plan: List[PlanStep] = Field(default_factory=list, description="Execution plan steps")
    
    # SQL Execution
    sql: Optional[str] = Field(None, description="Generated SQL query")
    sql_error: Optional[str] = Field(None, description="SQL execution error if any")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="SQL query results")
    df_summary: Optional[Dict[str, Any]] = Field(None, description="DataFrame summary statistics")
    
    # Chart Generation
    chart_path: Optional[str] = Field(None, description="Path to generated chart file")
    chart_error: Optional[str] = Field(None, description="Chart generation error if any")
    
    # Final Output
    answer: str = Field("", description="Final response to user")
    
    # Conversation Memory
    history: List[HistoryEntry] = Field(default_factory=list, description="Conversation history")
    
    # Agent Routing
    next_agent: Optional[str] = Field(None, description="Next agent to route to")
    completed_agents: List[str] = Field(default_factory=list, description="Agents that have completed processing")
    
    # Metadata
    processing_start_time: Optional[datetime] = Field(None, description="When processing started")
    processing_end_time: Optional[datetime] = Field(None, description="When processing completed")


class QueryRequest(BaseModel):
    """Request model for the API endpoint."""
    
    query: str = Field(..., description="Natural language query from user")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class QueryResponse(BaseModel):
    """Response model for the API endpoint."""
    
    answer: str = Field(..., description="Generated answer to the query")
    chart_url: Optional[str] = Field(None, description="URL to generated chart")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Data rows (max 50)")
    df_summary: Optional[Dict[str, Any]] = Field(None, description="DataFrame summary")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if processing failed")
