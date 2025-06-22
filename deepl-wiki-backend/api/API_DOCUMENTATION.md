# DeepL Wiki API Documentation

## Overview

The DeepL Wiki API provides a RESTful interface to interact with the DeepL Wiki system. It allows you to manage repositories, chat with AI agents, and access generated documentation.

## Base URL

```
http://localhost:8000
```

## API Endpoints

### Health & Status

#### GET `/api/v1/health`
Get system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "path": "/path/to/db",
      "size": "1024 bytes"
    },
    "vector_db": {
      "status": "healthy",
      "path": "/path/to/chroma",
      "collections": 3
    }
  }
}
```

#### GET `/api/v1/stats`
Get system statistics.

**Response:**
```json
{
  "total_repositories": 5,
  "total_files_indexed": 1250,
  "database_size": "2048 bytes",
  "vector_db_size": "10240 bytes",
  "last_index_time": "2025-06-21T10:30:00Z"
}
```

### Chat

#### POST `/api/v1/chat`
Send a message to the chat agent.

**Request Body:**
```json
{
  "message": "How do I use this function?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "This function is used to...",
  "session_id": "uuid-session-id",
  "message_id": "uuid-message-id"
}
```

#### GET `/api/v1/chat/sessions`
Get all chat sessions.

**Response:**
```json
[
  {
    "session_id": "uuid",
    "created_at": "2025-06-21T10:00:00Z",
    "messages": [...]
  }
]
```

#### GET `/api/v1/chat/sessions/{session_id}`
Get a specific chat session.

#### DELETE `/api/v1/chat/sessions/{session_id}`
Delete a chat session.

#### DELETE `/api/v1/chat/sessions`
Clear all chat sessions.

### Repositories

#### GET `/api/v1/repositories`
Get all tracked repositories.

**Response:**
```json
[
  {
    "id": 1,
    "path": "/path/to/repo",
    "name": "My Repository",
    "description": "A sample repository",
    "status": "active",
    "indexed_at": "2025-06-21T10:00:00Z"
  }
]
```

#### POST `/api/v1/repositories`
Add a new repository for tracking.

**Request Body:**
```json
{
  "path": "/path/to/repository",
  "name": "Repository Name",
  "description": "Optional description"
}
```

#### GET `/api/v1/repositories/{repository_id}`
Get a specific repository by ID.

#### DELETE `/api/v1/repositories/{repository_id}`
Remove a repository from tracking.

#### POST `/api/v1/repositories/index`
Index repositories in the background.

**Request Body:**
```json
{
  "repository_ids": [1, 2, 3]  // Optional: if not provided, index all
}
```

**Response:**
```json
{
  "message": "Indexing started in background",
  "repositories_indexed": [1, 2, 3],
  "status": "started"
}
```

#### GET `/api/v1/repositories/index/status`
Get the status of repository indexing.

### Files

#### GET `/api/v1/files/mono-repo`
Get the mono repository structure and file tree.

**Response:**
```json
{
  "mono_repo_path": "/path/to/mono/repo",
  "structure": {
    "name": "mono-repo",
    "path": "/path/to/mono/repo",
    "type": "directory",
    "children": [...]
  },
  "total_files": 150,
  "total_size": 1048576
}
```

#### GET `/api/v1/files/mono-repo/generate`
Generate a new mono repository from all tracked repositories.

#### GET `/api/v1/files/content?file_path=/path/to/file`
Get the content of a specific file.

**Response:**
```json
{
  "path": "/path/to/file.py",
  "content": "def hello():\n    print('Hello, World!')",
  "encoding": "utf-8",
  "size": 1024
}
```

#### GET `/api/v1/files/search?query=function&file_type=py&repository_id=1`
Search for files in tracked repositories.

**Query Parameters:**
- `query`: Search term
- `file_type`: Optional file extension filter
- `repository_id`: Optional repository filter

## Running the API

### Development

```bash
# Activate your virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run the API server
python run_api.py
```

### Production

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

Error responses follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Session Management

Chat sessions are stored in memory. In a production environment, you should implement persistent session storage using Redis or a database.

## File Access

The API has access to:
1. All tracked repositories
2. The generated mono repository
3. The vector database for semantic search

File access is restricted to tracked repositories for security.
