"""
Streamlit UI for the LangGraph Data Copilot.

This module provides a web interface for interacting with the Data Copilot.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import dotenv
import pandas as pd
import requests
import streamlit as st

# Load environment variables from .env file
dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

# API configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8010")
API_URL = f"http://{API_HOST}:{API_PORT}/api"

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "history" not in st.session_state:
    st.session_state.history = []


def query_api(query: str) -> Dict:
    """
    Send a query to the API and return the response.
    
    Args:
        query: Natural language query
        
    Returns:
        API response as dictionary
    """
    try:
        response = requests.post(
            f"{API_URL}/infer",
            json={"query": query, "session_id": st.session_state.session_id},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {
            "answer": f"Error: {str(e)}",
            "chart_url": None,
            "rows": [],
            "df_summary": None,
            "error": str(e),
        }


def display_data_table(rows: List[Dict], df_summary: Optional[Dict] = None):
    """
    Display data rows in a table with summary information.
    
    Args:
        rows: List of dictionaries representing data rows
        df_summary: Optional DataFrame summary information
    """
    if not rows:
        st.info("No data to display")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    
    # Display summary if available
    if df_summary:
        with st.expander("Data Summary", expanded=False):
            st.write(f"Shape: {df_summary.get('shape', (0, 0))}")
            st.write(f"Columns: {', '.join(df_summary.get('columns', []))}")
            
            # Display dtypes
            if "dtypes" in df_summary:
                st.write("Data Types:")
                for col, dtype in df_summary["dtypes"].items():
                    st.write(f"- {col}: {dtype}")
    
    # Display data table
    st.dataframe(df)


def get_database_schema():
    """Get database schema information from the API."""
    try:
        response = requests.get(f"{API_URL}/tables")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching database schema: {str(e)}")
        return {"tables": []}


def get_table_schema(table_name: str):
    """Get schema information for a specific table."""
    try:
        response = requests.get(f"{API_URL}/tables/{table_name}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching table schema: {str(e)}")
        return {"schema": {}}


def show_database_info():
    """Show database schema information."""
    st.subheader("Database Schema")
    
    # Get tables
    schema_info = get_database_schema()
    tables = schema_info.get("tables", [])
    
    if not tables:
        st.info("No tables found in the database.")
        return
    
    # Show tables
    selected_table = st.selectbox("Select a table", tables)
    
    if selected_table:
        # Get table schema
        table_info = get_table_schema(selected_table)
        schema = table_info.get("schema", {})
        
        # Show columns
        if "columns" in schema:
            st.write("**Columns:**")
            columns_data = []
            for col in schema["columns"]:
                columns_data.append({
                    "Name": col.get("name"),
                    "Type": col.get("type"),
                    "Nullable": "Yes" if col.get("nullable") else "No",
                    "Default": col.get("default"),
                })
            st.table(columns_data)
        
        # Show primary key
        if "primary_key" in schema:
            pk = schema["primary_key"]
            if pk and "constrained_columns" in pk:
                st.write(f"**Primary Key:** {', '.join(pk['constrained_columns'])}")
        
        # Show indexes
        if "indexes" in schema and schema["indexes"]:
            st.write("**Indexes:**")
            for idx in schema["indexes"]:
                st.write(f"- {idx.get('name')}: {', '.join(idx.get('column_names', []))}")


def main():
    """Main Streamlit application."""
    # Set page config
    st.set_page_config(
        page_title="Data Analysis Copilot",
        page_icon="📊",
        layout="wide",
    )
    
    # Debug information
    st.sidebar.write("### Debug Info")
    st.sidebar.write(f"API URL: {API_URL}")
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        st.sidebar.success(f"API Health: {health_response.status_code}")
        st.sidebar.json(health_response.json())
    except Exception as e:
        st.sidebar.error(f"API Connection Error: {str(e)}")
        st.error("⚠️ Cannot connect to the API server. Please ensure the FastAPI server is running.")
        return
    
    
    # Header
    st.title("📊 LangGraph Data Analysis Copilot")
    st.markdown(
        """
        Ask natural language questions about your data and get instant insights!
        
        Example questions:
        - "Average sales per region in Q2"
        - "Which product category had the highest sales in 2024?"
        - "Show me monthly sales trends by region"
        - "What is 2+2?" (non-SQL question)
        """
    )
    
    # Create tabs
    tab1, tab2 = st.tabs(["Query Data", "Database Info"])
    
    with tab1:
        # Query input
        with st.form(key="query_form"):
            query = st.text_area("Ask a question about your data:", height=100)
            submit_button = st.form_submit_button("Analyze")
        
        # Process query
        if submit_button and query:
            with st.spinner("Analyzing data..."):
                # Call API
                result = query_api(query)
                
                # Add to history
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.history.append({
                    "query": query,
                    "result": result,
                    "timestamp": timestamp,
                })
    
        # Display current result if available
        if st.session_state.history:
            latest = st.session_state.history[-1]
            
            st.markdown("## Results")
            
            # Display answer
            st.markdown("### Answer")
            st.markdown(latest["result"]["answer"])
            
            # Display chart if available
            if latest["result"].get("chart_url"):
                st.markdown("### Chart")
                chart_url = f"http://{API_HOST}:{API_PORT}{latest['result']['chart_url']}"
                try:
                    st.image(chart_url, caption="Generated Chart", use_column_width=True)
                except Exception as e:
                    st.error(f"Could not display chart: {str(e)}")
                    st.write(f"Chart URL: {chart_url}")
                    # Try to display as a link
                    st.markdown(f"[View Chart]({chart_url})")
            
            # Display data
            if latest["result"].get("rows"):
                st.markdown("### Data")
                display_data_table(
                    latest["result"]["rows"],
                    latest["result"].get("df_summary"),
                )
        
        # History section
        if len(st.session_state.history) > 1:
            st.markdown("## History")
            
            for i, item in enumerate(reversed(st.session_state.history[:-1])):
                with st.expander(f"{item['timestamp']} - {item['query'][:50]}...", expanded=False):
                    st.markdown(item["result"]["answer"])
                    
                    if item["result"].get("chart_url"):
                        chart_url = f"http://{API_HOST}:{API_PORT}{item['result']['chart_url']}"
                        try:
                            st.image(chart_url, caption="Generated Chart", use_column_width=True)
                        except Exception as e:
                            st.error(f"Could not display chart: {str(e)}")
                            st.markdown(f"[View Chart]({chart_url})")
    
    with tab2:
        # Show database schema information
        show_database_info()


if __name__ == "__main__":
    main()
