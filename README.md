# LangGraph Multi-Agent Data Analysis Copilot

A production-ready Python application that enables users to ask natural language questions about data and receive insightful answers through a multi-agent system built with LangGraph.

## Features

- **Natural Language Interface**: Ask questions about your data in plain English
- **Multi-Agent Architecture**: Specialized agents for planning, SQL generation, chart creation, and explanation
- **Visualization**: Automatic chart generation based on query results
- **Conversation Memory**: Maintains history of queries and responses
- **Production-Ready**: Includes FastAPI backend, Streamlit UI, Docker configuration, and comprehensive tests

## Architecture

The system uses a LangGraph workflow with the following agents:

1. **Planner Agent**: Analyzes the user query and creates an execution plan
2. **SQL Agent**: Generates and executes SQL queries against a SQLite database
3. **Chart Agent**: Creates visualizations of the query results
4. **Explainer Agent**: Provides natural language explanations of the results

## Tech Stack

- **Python 3.11**: Core programming language
- **LangGraph & LangChain**: Multi-agent orchestration and LLM integration
- **OpenAI/Anthropic**: LLM providers for natural language processing
- **FastAPI**: API backend
- **Streamlit**: User interface
- **SQLAlchemy & SQLite**: Database access and storage
- **Pandas & Matplotlib**: Data processing and visualization
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization
- **pytest, ruff, black, mypy**: Testing and code quality tools

## Project Structure

```
langgraph-data-copilot/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── chart.py
│   │   ├── config.py
│   │   ├── explainer.py
│   │   ├── graph.py
│   │   ├── planner.py
│   │   ├── prompts.py
│   │   └── sql.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── endpoints.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── seed.sql
│   ├── models/
│   │   ├── __init__.py
│   │   └── state.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── chart.py
│   └── __init__.py
├── charts/
├── tests/
│   ├── __init__.py
│   ├── test_chart.py
│   ├── test_graph.py
│   └── test_sql_agent.py
├── ui/
│   └── streamlit_app.py
├── .env.example
├── Dockerfile
├── Dockerfile.streamlit
├── docker-compose.yml
├── main.py
├── pyproject.toml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- OpenAI API key or Anthropic API key

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/langgraph-data-copilot.git
cd langgraph-data-copilot
```

2. Create and configure the environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Install dependencies:

```bash
pip install -e .
```

### Running Locally

1. Start the FastAPI backend:

```bash
python main.py
```

2. Start the Streamlit UI:

```bash
cd ui
streamlit run streamlit_app.py
```

3. Open your browser and navigate to http://localhost:8501

### Running with Docker

1. Build and start the containers:

```bash
docker-compose up -d
```

2. Access the UI at http://localhost:8501

## Usage Examples

### Example 1: Data Analysis Query

**User Query**: "Average sales per region in Q2"

**System Response**:
- Generates SQL to calculate average sales by region for Q2
- Executes the query against the database
- Creates a bar chart showing the results
- Provides a natural language explanation of the findings

### Example 2: Simple Arithmetic

**User Query**: "What is 2+2?"

**System Response**:
- Recognizes this as a non-SQL question
- Routes directly to the explainer agent
- Provides the answer without database access

## API Documentation

### POST /api/infer

Process a natural language query and return results.

**Request Body**:
```json
{
  "query": "Average sales per region in Q2",
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "answer": "The average sales per region in Q2 were highest in the South region at $1,600, followed by East at $1,300, North at $1,100, and West at $900.",
  "chart_url": "/api/charts/12345678-1234-5678-1234-567812345678.png",
  "rows": [...],
  "df_summary": {...},
  "processing_time_ms": 1234.56,
  "error": null
}
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LangGraph team for the multi-agent framework
- LangChain team for the LLM tooling
- OpenAI/Anthropic for the language models
