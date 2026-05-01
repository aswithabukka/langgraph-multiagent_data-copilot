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

# Startup logging — never log the key itself, even a prefix.
logger.info("OpenAI configured: %s (model=%s)", bool(OPENAI_API_KEY), OPENAI_MODEL)
logger.info("Anthropic configured: %s (model=%s)", bool(ANTHROPIC_API_KEY), ANTHROPIC_MODEL)


def _maybe_enable_llm_cache() -> None:
    """Turn on LangChain's process-global LLM cache when LLM_CACHE is set.

    `LLM_CACHE=memory` (or `1`/`true`) — in-process cache. Cleared on restart.
    `LLM_CACHE=sqlite` — persistent SQLite cache at `LLM_CACHE_PATH`
                        (defaults to `./.llm_cache.sqlite`). Useful for dev
                        and for low-traffic prod where identical prompts
                        recur. Requires `langchain-community`.

    Identical (model, prompt, temperature) tuples skip the network call —
    biggest win is on deterministic agents (planner / SQL at temperature 0).
    """
    mode = os.getenv("LLM_CACHE", "").strip().lower()
    if mode in ("", "0", "false", "no", "off"):
        return

    try:
        from langchain.globals import set_llm_cache
    except ImportError:
        logger.warning("LLM_CACHE set but langchain.globals not available; skipping")
        return

    if mode == "sqlite":
        try:
            from langchain_community.cache import SQLiteCache
        except ImportError:
            logger.warning("LLM_CACHE=sqlite needs `langchain-community`; falling back to in-memory")
            mode = "memory"
        else:
            path = os.getenv("LLM_CACHE_PATH", "./.llm_cache.sqlite")
            set_llm_cache(SQLiteCache(database_path=path))
            logger.info("LLM SQLite cache enabled at %s", path)
            return

    # default: in-memory (covers "1", "true", "yes", "on", "memory")
    from langchain_core.caches import InMemoryCache

    set_llm_cache(InMemoryCache())
    logger.info("LLM in-memory cache enabled")


_maybe_enable_llm_cache()


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
        if not OPENAI_API_KEY:
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
