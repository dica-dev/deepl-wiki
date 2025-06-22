"""File system endpoints for DeepL Wiki API."""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add the agents directory to the path
AGENTS_DIR = Path(__file__).parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))

try:
    from agents.mono_repo_generator import MonoRepoGenerator
    from agents.shared.database import DatabaseManager
except ImportError:
    MonoRepoGenerator = None
    DatabaseManager = None

router = APIRouter()


class FileNode(BaseModel):
    name: str
    path: str
    type: str  # "file" or "directory"
    size: Optional[int] = None
    children: Optional[List["FileNode"]] = None


class MonoRepoResponse(BaseModel):
    mono_repo_path: str
    structure: FileNode
    total_files: int
    total_size: int


class FileContent(BaseModel):
    path: str
    content: str
    encoding: str
    size: int


def get_database():
    """Get database instance."""
    if DatabaseManager is None:
        raise HTTPException(
            status_code=500,
            detail="Database not available. Please check your configuration."
        )
    return DatabaseManager()


def get_mono_repo_generator():
    """Get mono repo generator instance."""
    if MonoRepoGenerator is None:
        raise HTTPException(
            status_code=500,
            detail="Mono repo generator not available. Please check your configuration."
        )
    return MonoRepoGenerator()


def build_file_tree(path: Path, max_depth: int = 10, current_depth: int = 0) -> FileNode:
    """Build a file tree structure from a directory path."""
    if current_depth > max_depth:
        return FileNode(
            name=path.name,
            path=str(path),
            type="directory",
            children=[]
        )
    
    try:
        if path.is_file():
            size = path.stat().st_size
            return FileNode(
                name=path.name,
                path=str(path),
                type="file",
                size=size
            )
        elif path.is_dir():
            children = []
            try:
                for child in sorted(path.iterdir()):
                    # Skip hidden files and common build directories
                    if child.name.startswith('.') or child.name in ['node_modules', '__pycache__', 'venv', '.git']:
                        continue
                    children.append(build_file_tree(child, max_depth, current_depth + 1))
            except PermissionError:
                # Skip directories we can't access
                pass
            
            return FileNode(
                name=path.name,
                path=str(path),
                type="directory",
                children=children
            )
    except Exception:
        # Return basic node for problematic paths
        return FileNode(
            name=path.name,
            path=str(path),
            type="unknown"
        )


def calculate_tree_stats(node: FileNode) -> Dict[str, int]:
    """Calculate total files and size in a file tree."""
    stats = {"files": 0, "size": 0}
    
    if node.type == "file":
        stats["files"] = 1
        stats["size"] = node.size or 0
    elif node.children:
        for child in node.children:
            child_stats = calculate_tree_stats(child)
            stats["files"] += child_stats["files"]
            stats["size"] += child_stats["size"]
    
    return stats


@router.get("/files/mono-repo", response_model=MonoRepoResponse)
async def get_mono_repo_structure():
    """Get the mono repository structure and file tree."""
    try:
        generator = get_mono_repo_generator()
        db = get_database()
          # Get or generate mono repo
        mono_repo_path = await generator.get_mono_repo_path()
        
        if not mono_repo_path or not Path(mono_repo_path).exists():
            # Auto-generate mono repo if it doesn't exist
            repositories = db.get_all_repositories()
            
            if not repositories:
                raise HTTPException(
                    status_code=400,
                    detail="No repositories found. Please add repositories first."
                )
            
            # Transform repository data for MonoRepoGenerator
            transformed_repos = []
            for repo in repositories:
                transformed_repo = {
                    "repo_path": repo["path"],
                    "repo_name": repo["name"],
                    "metadata": {
                        "description": repo.get("description", ""),
                        "primary_language": "Unknown",
                        "file_count": 0,
                        "total_size": 0,
                        "status": repo.get("status", "active")
                    }
                }
                transformed_repos.append(transformed_repo)
            
            mono_repo_path = generator.generate_mono_repo(
                output_dir="./mono_repo_docs",
                repositories=transformed_repos,
                general_memo="Auto-generated mono repository documentation"
            )
        
        # Build file tree
        mono_path = Path(mono_repo_path)
        file_tree = build_file_tree(mono_path)
        
        # Calculate statistics
        stats = calculate_tree_stats(file_tree)
        
        return MonoRepoResponse(
            mono_repo_path=str(mono_path),
            structure=file_tree,
            total_files=stats["files"],
            total_size=stats["size"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving mono repository structure: {str(e)}"
        )


@router.get("/files/mono-repo/generate")
async def generate_mono_repo():
    """Generate a new mono repository from all tracked repositories."""
    try:
        db = get_database()
        generator = get_mono_repo_generator()
          # Get all repositories
        repositories = db.get_all_repositories()
        
        if not repositories:
            raise HTTPException(
                status_code=400,
                detail="No repositories found. Please add repositories first."
            )
        
        # Transform repository data for MonoRepoGenerator
        transformed_repos = []
        for repo in repositories:
            transformed_repo = {
                "repo_path": repo["path"],
                "repo_name": repo["name"],
                "metadata": {
                    "description": repo.get("description", ""),
                    "primary_language": "Unknown",
                    "file_count": 0,
                    "total_size": 0,
                    "status": repo.get("status", "active")
                }
            }
            transformed_repos.append(transformed_repo)
        
        # Generate mono repo
        mono_repo_path = generator.generate_mono_repo(
            output_dir="./mono_repo_docs",
            repositories=transformed_repos,
            general_memo="Auto-generated mono repository documentation"
        )
        
        return {
            "message": "Mono repository generated successfully",
            "mono_repo_path": mono_repo_path,
            "repositories_included": len(repositories)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating mono repository: {str(e)}"
        )


@router.get("/files/content")
async def get_file_content(file_path: str) -> FileContent:
    """Get the content of a specific file."""
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        if not path.is_file():
            raise HTTPException(
                status_code=400,
                detail="Path is not a file"
            )
        
        # Get file size
        size = path.stat().st_size
        
        # Limit file size to prevent memory issues
        max_size = 1024 * 1024 * 5  # 5MB
        if size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {max_size} bytes."
            )
        
        # Try to read as text, fallback to binary
        try:
            content = path.read_text(encoding="utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding="latin-1")
                encoding = "latin-1"
            except UnicodeDecodeError:
                # For binary files, return base64 encoded content
                import base64
                content = base64.b64encode(path.read_bytes()).decode("ascii")
                encoding = "base64"
        
        return FileContent(
            path=str(path),
            content=content,
            encoding=encoding,
            size=size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading file: {str(e)}"
        )


@router.get("/files/search")
async def search_files(
    query: str,
    file_type: Optional[str] = None,
    repository_id: Optional[int] = None
):
    """Search for files in tracked repositories."""
    try:
        db = get_database()
        
        # Get repositories to search
        if repository_id:
            repo = db.get_repository(repository_id)
            if not repo:
                raise HTTPException(
                    status_code=404,
                    detail="Repository not found"
                )
            repositories = [repo]
        else:
            repositories = db.get_all_repositories()
        
        results = []
        
        for repo in repositories:
            repo_path = Path(repo["path"])
            if not repo_path.exists():
                continue
            
            # Search files in repository
            for file_path in repo_path.rglob("*"):
                if file_path.is_file():
                    # Filter by file type if specified
                    if file_type and not file_path.suffix.lower().endswith(file_type.lower()):
                        continue
                    
                    # Check if query matches file name or path
                    if query.lower() in file_path.name.lower() or query.lower() in str(file_path).lower():
                        results.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "size": file_path.stat().st_size,
                            "repository_id": repo["id"],
                            "repository_name": repo["name"]
                        })
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching files: {str(e)}"
        )
