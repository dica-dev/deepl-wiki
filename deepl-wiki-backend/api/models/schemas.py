"""Pydantic models for API requests and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


# Chat Models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str


class ChatSession(BaseModel):
    session_id: str
    created_at: str
    messages: List[Dict[str, Any]]


# Repository Models
class RepositoryBase(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    pass


class Repository(RepositoryBase):
    id: int
    status: str = "active"
    indexed_at: Optional[str] = None

    class Config:
        from_attributes = True


# File Models
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


# Index Models
class IndexRequest(BaseModel):
    repository_ids: Optional[List[int]] = None


class IndexResponse(BaseModel):
    message: str
    repositories_indexed: List[int]
    status: str


# Health Models
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


# Update forward references
FileNode.model_rebuild()
