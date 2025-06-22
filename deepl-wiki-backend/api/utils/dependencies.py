"""Dependency injection utilities for the API."""

import sys
from pathlib import Path
from fastapi import HTTPException

# Add the agents directory to the path
AGENTS_DIR = Path(__file__).parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))


def get_chat_agent():
    """Dependency to get chat agent instance."""
    try:
        from agents.chat_agent import ChatAgent
        return ChatAgent()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Chat agent not available. Please check your configuration."
        )


def get_index_agent():
    """Dependency to get index agent instance."""
    try:
        from agents.index_repo_agent import IndexRepoAgent
        return IndexRepoAgent()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Index agent not available. Please check your configuration."
        )


def get_database():
    """Dependency to get database instance."""
    try:
        from shared.database import Database
        return Database()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Database not available. Please check your configuration."
        )


def get_mono_repo_generator():
    """Dependency to get mono repo generator instance."""
    try:
        from agents.mono_repo_generator import MonoRepoGenerator
        return MonoRepoGenerator()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Mono repo generator not available. Please check your configuration."
        )
