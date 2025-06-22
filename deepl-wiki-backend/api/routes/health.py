"""Health check and system status endpoints."""

import sys
import os
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

# Add the agents directory to the path
AGENTS_DIR = Path(__file__).parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, Any]


class SystemStats(BaseModel):
    total_repositories: int
    total_files_indexed: int
    database_size: str
    vector_db_size: str
    last_index_time: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Get system health status."""
    components = {}
    overall_status = "healthy"
    
    # Check database connection
    try:
        # Check if database files exist
        db_path = AGENTS_DIR / "deepl_wiki.db"
        if db_path.exists():
            components["database"] = {
                "status": "healthy",
                "path": str(db_path),
                "size": f"{db_path.stat().st_size} bytes"
            }
        else:
            components["database"] = {
                "status": "not_found",
                "message": "Database file not found"
            }
            overall_status = "degraded"
    except Exception as e:
        components["database"] = {
            "status": "error",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # Check ChromaDB
    try:
        chroma_path = AGENTS_DIR / "chroma_db"
        if chroma_path.exists():
            components["vector_db"] = {
                "status": "healthy",
                "path": str(chroma_path),
                "collections": len(list(chroma_path.iterdir())) if chroma_path.is_dir() else 0
            }
        else:
            components["vector_db"] = {
                "status": "not_found",
                "message": "ChromaDB directory not found"
            }
            overall_status = "degraded"
    except Exception as e:
        components["vector_db"] = {
            "status": "error",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # Check environment variables
    env_status = "healthy"
    missing_vars = []
    
    required_vars = ["OPENAI_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            env_status = "degraded"
    
    components["environment"] = {
        "status": env_status,
        "missing_variables": missing_vars
    }
    
    if env_status == "degraded":
        overall_status = "degraded"
    
    # Check agents
    try:
        # Try importing agents
        from agents.chat_agent import ChatAgent
        from agents.index_repo_agent import IndexRepoAgent
        from shared.database import Database
        
        components["agents"] = {
            "status": "healthy",
            "available": ["ChatAgent", "IndexRepoAgent", "Database"]
        }
    except ImportError as e:
        components["agents"] = {
            "status": "error",
            "error": f"Failed to import agents: {str(e)}"
        }
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        components=components
    )


@router.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics."""
    try:
        # Try to get database instance
        from shared.database import Database
        db = Database()
        
        # Get repository count
        repositories = db.get_all_repositories()
        total_repos = len(repositories)
        
        # Calculate database size
        db_path = AGENTS_DIR / "deepl_wiki.db"
        db_size = f"{db_path.stat().st_size} bytes" if db_path.exists() else "0 bytes"
        
        # Calculate vector database size
        chroma_path = AGENTS_DIR / "chroma_db"
        vector_db_size = "0 bytes"
        if chroma_path.exists():
            total_size = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file())
            vector_db_size = f"{total_size} bytes"
        
        return SystemStats(
            total_repositories=total_repos,
            total_files_indexed=0,  # This would need to be tracked in the database
            database_size=db_size,
            vector_db_size=vector_db_size,
            last_index_time="N/A"  # This would need to be tracked in the database
        )
        
    except Exception as e:
        # Return default stats if there's an error
        return SystemStats(
            total_repositories=0,
            total_files_indexed=0,
            database_size="Unknown",
            vector_db_size="Unknown",
            last_index_time="Unknown"
        )


@router.get("/version")
async def get_version():
    """Get API version information."""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "python_version": sys.version,
        "platform": sys.platform
    }
