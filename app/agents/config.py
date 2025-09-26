"""
Configuration for LangGraph Data Copilot agents.

This module provides configuration for the LLM models and agent settings.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

import dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
logger.info(f"Loading environment variables from: {env_path}")
dotenv.load_dotenv(env_path)

# Default model settings
DEFAULT_OPENAI_MODEL = "gpt-4"
DEFAULT_ANTHROPIC_MODEL = "claude-3-sonnet-20240229"
DEFAULT_TEMPERATURE = 0.0

# Get configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)

# Debug logging
logger.info(f"OPENAI_API_KEY exists: {OPENAI_API_KEY is not None}")
logger.info(f"OPENAI_MODEL: {OPENAI_MODEL}")
logger.info(f"ANTHROPIC_API_KEY exists: {ANTHROPIC_API_KEY is not None}")
logger.info(f"ANTHROPIC_MODEL: {ANTHROPIC_MODEL}")


def get_llm(provider: str = "openai", **kwargs) -> ChatOpenAI | ChatAnthropic:
    """
    Get a configured LLM instance based on provider.
    
    Args:
        provider: LLM provider ('openai' or 'anthropic')
        **kwargs: Additional arguments to pass to the LLM constructor
        
    Returns:
        Configured LLM instance
        
    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    # Default parameters
    params = {
        "temperature": kwargs.get("temperature", DEFAULT_TEMPERATURE),
    }
    
    if provider.lower() == "openai":
        # Debug logging for OpenAI API key
        if OPENAI_API_KEY:
            logger.info(f"Using OpenAI API key (first 5 chars): {OPENAI_API_KEY[:5]}...")
        else:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not found in environment variables")
        
        return ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=kwargs.get("model", OPENAI_MODEL),
            **params
        )
    
    elif provider.lower() == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not found in environment variables")
        
        return ChatAnthropic(
            api_key=ANTHROPIC_API_KEY,
            model=kwargs.get("model", ANTHROPIC_MODEL),
            **params
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Agent configuration
AGENT_CONFIG: Dict[str, Dict[str, Optional[str]]] = {
    "planner": {
        "provider": "openai",
        "model": OPENAI_MODEL,
        "temperature": "0.0",
    },
    "sql": {
        "provider": "openai",
        "model": OPENAI_MODEL,
        "temperature": "0.0",
    },
    "chart": {
        "provider": "openai",
        "model": OPENAI_MODEL,
        "temperature": "0.0",
    },
    "explainer": {
        "provider": "openai",
        "model": OPENAI_MODEL,
        "temperature": "0.2",  # Slightly higher for more natural explanations
    },
}
