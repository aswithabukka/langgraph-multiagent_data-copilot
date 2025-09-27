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

# Configure Streamlit page
st.set_page_config(
    page_title=" LangGraph Data Analysis Copilot",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8012")
API_URL = f"http://{API_HOST}:{API_PORT}/api"

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "history" not in st.session_state:
    st.session_state.history = []

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main background and theme */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    
    /* Title styling */
    .main-title {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Query input styling */
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid #667eea;
        border-radius: 15px;
        color: white;
        font-size: 16px;
        padding: 15px;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Results container */
    .results-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* SQL query container */
    .sql-container {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        font-family: 'Courier New', monospace;
    }
    
    /* Answer container */
    .answer-container {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #2ecc71;
    }
    
    /* Chart container */
    .chart-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
        border: 2px dashed rgba(255, 255, 255, 0.3);
    }
    
    /* Data table styling */
    .dataframe {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Metrics styling */
    .metric-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px 10px 0 0;
        color: white;
        font-weight: bold;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #667eea, #764ba2);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: rgba(46, 204, 113, 0.2);
        border: 1px solid #2ecc71;
        border-radius: 10px;
    }
    
    .stError {
        background: rgba(231, 76, 60, 0.2);
        border: 1px solid #e74c3c;
        border-radius: 10px;
    }
    
    /* Loading spinner */
    .stSpinner {
        color: #667eea;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def query_api(query: str) -> dict:
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
    
    # Enhanced Header with gradient background
    st.markdown("""
    <div class="main-title">
        🤖 LangGraph Data Analysis Copilot
    </div>
    """, unsafe_allow_html=True)
    
    # Subtitle with styling
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; font-size: 1.2rem; color: rgba(255,255,255,0.8);">
        🚀 Ask natural language questions and get instant insights with AI-powered analytics
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with enhanced styling
    with st.sidebar:
        st.markdown("### 🔧 System Status")
        
        # API Health Check with visual indicators
        try:
            health_response = requests.get(f"{API_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("🟢 API Server Online")
                health_data = health_response.json()
                st.metric("Response Time", f"{health_data.get('timestamp', 'N/A')}")
            else:
                st.error("🔴 API Server Issues")
        except Exception as e:
            st.error("🔴 API Server Offline")
            st.error("⚠️ Cannot connect to the API server. Please ensure the FastAPI server is running.")
            return
        
        st.markdown("---")
        st.markdown("### 💡 Example Queries")
        st.markdown("""
        **📊 Business Analytics:**
        - "Show profit margins by category with chart"
        - "Top 5 customers by revenue"
        - "Sales performance by region"
        
        **⚡ Quick Math:**
        - "What is 25 * 4 + 10?"
        - "Calculate (100 + 50) / 3"
        
        **🔍 Data Exploration:**
        - "How many products in each category?"
        - "List all sales representatives"
        """)
        
        st.markdown("---")
        st.markdown("### 🗄️ Database Info")
        st.info(f"Connected to: {API_URL}")
        
        # Quick stats
        try:
            tables_response = requests.get(f"{API_URL}/tables", timeout=5)
            if tables_response.status_code == 200:
                tables = tables_response.json().get("tables", [])
                st.metric("Tables Available", len(tables))
                with st.expander("View Tables"):
                    for table in tables:
                        st.write(f"📋 {table}")
        except:
            st.warning("Could not fetch table info")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Query Data", "Database Info"])
    
    with tab1:
        # Query input with enhanced styling
        st.markdown("### 💭 Ask Your Question")
        st.markdown("Type your question below and click Analyze to get insights from your data:")
        
        with st.form(key="query_form"):
            query = st.text_area(
                "🔍 Enter your query here:",
                height=120,
                placeholder="e.g., 'Show me profit margins by product category with a chart' or 'What is 25 * 4?'",
                help="You can ask business questions, request charts, or even simple math calculations!"
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_button = st.form_submit_button(
                    "🚀 Analyze",
                    use_container_width=True
                )
        
        # Process query
        if submit_button and query:
            with st.spinner("🤖 Analyzing your query..."):
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
            
            # Results container with styling
            st.markdown('<div class="results-container">', unsafe_allow_html=True)
            
            # Query info header
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**📝 Query:** {latest['query']}")
            with col2:
                processing_time = latest["result"].get("processing_time_ms", 0)
                st.metric("⏱️ Processing Time", f"{processing_time:.1f}ms")
            with col3:
                if latest["result"].get("error"):
                    st.error("❌ Error")
                else:
                    st.success("✅ Success")
            
            st.markdown("---")
            
            # SQL Query Section (if available)
            if latest["result"].get("sql"):
                st.markdown("### 🗄️ SQL Query Executed")
                st.markdown('<div class="sql-container">', unsafe_allow_html=True)
                st.code(latest["result"]["sql"], language="sql")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Query metrics
                if latest["result"].get("rows"):
                    row_count = len(latest["result"]["rows"])
                    st.info(f"📊 Query returned {row_count} rows")
            
            # Answer Section
            st.markdown("### 💬 Analysis Result")
            st.markdown('<div class="answer-container">', unsafe_allow_html=True)
            st.markdown(latest["result"]["answer"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Chart Section
            if latest["result"].get("chart_url"):
                st.markdown("### 📈 Visualization")
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                chart_url = f"http://{API_HOST}:{API_PORT}{latest['result']['chart_url']}"
                try:
                    st.image(chart_url, caption="📊 Generated Chart", use_column_width=True)
                    st.success("🎨 Chart generated successfully!")
                except Exception as e:
                    st.error(f"❌ Could not display chart: {str(e)}")
                    st.markdown(f"🔗 [View Chart Directly]({chart_url})")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Data Section
            if latest["result"].get("rows"):
                st.markdown("### 📋 Data Results")
                
                # Data summary metrics
                df_summary = latest["result"].get("df_summary")
                if df_summary:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Rows", df_summary.get("shape", [0])[0])
                    with col2:
                        st.metric("📋 Columns", df_summary.get("shape", [0, 0])[1])
                    with col3:
                        null_count = sum(df_summary.get("null_counts", {}).values())
                        st.metric("❌ Null Values", null_count)
                
                # Display table
                display_data_table(
                    latest["result"]["rows"],
                    latest["result"].get("df_summary"),
                )
            
            # Error Section
            if latest["result"].get("error"):
                st.markdown("### ❌ Error Details")
                st.error(latest["result"]["error"])
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # History section
        if len(st.session_state.history) > 1:
            st.markdown("## 📚 Query History")
            
            # Add clear history button
            if st.button("🗑️ Clear History"):
                st.session_state.history = []
                st.rerun()
            
            for i, item in enumerate(reversed(st.session_state.history[:-1])):
                with st.expander(f"🕒 {item['timestamp']} - {item['query'][:50]}...", expanded=False):
                    # Show SQL query if available
                    if item["result"].get("sql"):
                        st.markdown("**🗄️ SQL Query:**")
                        st.code(item["result"]["sql"], language="sql")
                        st.markdown("---")
                    
                    # Show answer
                    st.markdown("**💬 Result:**")
                    st.markdown(item["result"]["answer"])
                    
                    # Show chart if available
                    if item["result"].get("chart_url"):
                        chart_url = f"http://{API_HOST}:{API_PORT}{item['result']['chart_url']}"
                        try:
                            st.image(chart_url, caption="📊 Generated Chart", use_column_width=True)
                        except Exception as e:
                            st.error(f"❌ Could not display chart: {str(e)}")
                            st.markdown(f"🔗 [View Chart]({chart_url})")
                    
                    # Show processing time
                    processing_time = item["result"].get("processing_time_ms", 0)
                    st.caption(f"⏱️ Processing time: {processing_time:.1f}ms")
    
    with tab2:
        # Show database schema information
        show_database_info()


if __name__ == "__main__":
    main()
