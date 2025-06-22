"""Repository management endpoints for DeepL Wiki API."""

import sys
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Add the agents directory to the path
AGENTS_DIR = Path(__file__).parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))

try:
    from agents.index_repo_agent import IndexRepoAgent
    from agents.shared.database import DatabaseManager
except ImportError:
    IndexRepoAgent = None
    DatabaseManager = None

router = APIRouter()


class Repository(BaseModel):
    id: Optional[int] = None
    path: str
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "active"
    indexed_at: Optional[str] = None


class RepositoryCreate(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None


class IndexRequest(BaseModel):
    repository_ids: Optional[List[int]] = None  # If None, index all repos


class IndexResponse(BaseModel):
    message: str
    repositories_indexed: List[int]
    status: str


def get_database():
    """Get database instance."""
    if DatabaseManager is None:
        raise HTTPException(
            status_code=500,
            detail="Database not available. Please check your configuration."
        )
    return DatabaseManager()


def get_index_agent():
    """Get index agent instance."""
    if IndexRepoAgent is None:
        raise HTTPException(
            status_code=500,
            detail="Index agent not available. Please check your configuration."
        )
    return IndexRepoAgent()


@router.get("/repositories", response_model=List[Repository])
async def list_repositories():
    """Get all tracked repositories."""
    try:
        db = get_database()
        repositories = db.get_all_repositories()
        return [
            Repository(
                id=repo.get("id"),
                path=repo.get("path"),
                name=repo.get("name"),
                description=repo.get("description"),
                status=repo.get("status", "active"),
                indexed_at=repo.get("indexed_at")
            )
            for repo in repositories
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving repositories: {str(e)}"
        )


@router.post("/repositories", response_model=Repository)
async def add_repository(repository: RepositoryCreate):
    """Add a new repository for tracking."""
    try:
        # Validate path exists
        repo_path = Path(repository.path)
        if not repo_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Repository path does not exist: {repository.path}"
            )
        
        if not repo_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Path is not a directory: {repository.path}"
            )
        
        db = get_database()
        
        # Check if repository already exists
        existing_repos = db.get_all_repositories()
        for repo in existing_repos:
            if repo.get("path") == str(repo_path.absolute()):
                raise HTTPException(
                    status_code=400,
                    detail="Repository already exists"
                )
        
        # Add repository to database
        repo_id = db.add_repository(
            path=str(repo_path.absolute()),
            name=repository.name or repo_path.name,
            description=repository.description
        )
        
        return Repository(
            id=repo_id,
            path=str(repo_path.absolute()),
            name=repository.name or repo_path.name,
            description=repository.description,
            status="active"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding repository: {str(e)}"
        )


@router.get("/repositories/{repository_id}", response_model=Repository)
async def get_repository(repository_id: int):
    """Get a specific repository by ID."""
    try:
        db = get_database()
        repo = db.get_repository(repository_id)
        
        if not repo:
            raise HTTPException(
                status_code=404,
                detail="Repository not found"
            )
        
        return Repository(
            id=repo.get("id"),
            path=repo.get("path"),
            name=repo.get("name"),
            description=repo.get("description"),
            status=repo.get("status", "active"),
            indexed_at=repo.get("indexed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving repository: {str(e)}"
        )


@router.delete("/repositories/{repository_id}")
async def remove_repository(repository_id: int):
    """Remove a repository from tracking."""
    try:
        db = get_database()
        
        # Check if repository exists
        repo = db.get_repository(repository_id)
        if not repo:
            raise HTTPException(
                status_code=404,
                detail="Repository not found"
            )
        
        # Remove repository
        db.remove_repository(repository_id)
        
        return {"message": "Repository removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error removing repository: {str(e)}"
        )


@router.post("/repositories/index", response_model=IndexResponse)
async def index_repositories(
    request: IndexRequest,
    background_tasks: BackgroundTasks
):
    """Index repositories in the background."""
    try:
        db = get_database()
        index_agent = get_index_agent()
        
        # Get repositories to index
        if request.repository_ids:
            repositories = []
            for repo_id in request.repository_ids:
                repo = db.get_repository(repo_id)
                if repo:
                    repositories.append(repo)
        else:
            repositories = db.get_all_repositories()
        
        if not repositories:
            raise HTTPException(
                status_code=400,
                detail="No repositories found to index"
            )
        
        # Start indexing in background
        background_tasks.add_task(
            index_repositories_task,
            repositories,
            index_agent
        )
        
        return IndexResponse(
            message="Indexing started in background",
            repositories_indexed=[repo["id"] for repo in repositories],
            status="started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting indexing: {str(e)}"
        )


async def index_repositories_task(repositories: List[dict], index_agent):
    """Background task to index repositories."""
    try:
        for repo in repositories:
            await index_agent.index_repository(repo["path"])
    except Exception as e:
        # Log error in production
        print(f"Error indexing repositories: {str(e)}")


@router.get("/repositories/index/status")
async def get_index_status():
    """Get the status of repository indexing."""
    # This would need to be implemented with a proper task queue
    # For now, return a simple status
    return {
        "status": "available",
        "message": "Indexing service is running"
    }
