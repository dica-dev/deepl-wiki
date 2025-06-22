# DeepL Wiki API Routes

Complete API reference for the DeepL Wiki backend. All routes are prefixed with `/api/v1`.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required. In production, implement API keys or JWT tokens.

---

## 🏥 Health & System Routes

### GET `/api/v1/health`
Get comprehensive system health status.

**Response Example:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "path": "/path/to/deepl_wiki.db",
      "size": "2048 bytes"
    },
    "vector_db": {
      "status": "healthy",
      "path": "/path/to/chroma_db",
      "collections": 3
    },
    "environment": {
      "status": "healthy",
      "missing_variables": []
    },
    "agents": {
      "status": "healthy",
      "available": ["ChatAgent", "IndexRepoAgent", "Database"]
    }
  }
}
```

### GET `/api/v1/stats`
Get system statistics and usage information.

**Response Example:**
```json
{
  "total_repositories": 5,
  "total_files_indexed": 1250,
  "database_size": "4096 bytes",
  "vector_db_size": "10240 bytes",
  "last_index_time": "2025-06-21T10:30:00Z"
}
```

### GET `/api/v1/version`
Get API version information.

**Response Example:**
```json
{
  "version": "1.0.0",
  "api_version": "v1",
  "python_version": "3.11.0",
  "platform": "win32"
}
```

---

## 💬 Chat Routes

### POST `/api/v1/chat`
Send a message to the AI chat agent.

**Request Body:**
```json
{
  "message": "How do I use this function?",
  "session_id": "optional-existing-session-id"
}
```

**Response Example:**
```json
{
  "response": "This function is used to process data by taking an input parameter and returning a formatted result. Here's how you can use it...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}
```

### GET `/api/v1/chat/sessions`
Get all chat sessions.

**Response Example:**
```json
[
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-06-21T10:00:00Z",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "How do I use this function?",
        "timestamp": "2025-06-21T10:00:00Z"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "This function is used to...",
        "timestamp": "2025-06-21T10:00:05Z"
      }
    ]
  }
]
```

### GET `/api/v1/chat/sessions/{session_id}`
Get a specific chat session by ID.

**Response Example:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-06-21T10:00:00Z",
  "messages": [...]
}
```

### DELETE `/api/v1/chat/sessions/{session_id}`
Delete a specific chat session.

**Response Example:**
```json
{
  "message": "Session deleted successfully"
}
```

### DELETE `/api/v1/chat/sessions`
Clear all chat sessions.

**Response Example:**
```json
{
  "message": "All sessions cleared successfully"
}
```

---

## 📁 Repository Management Routes

### GET `/api/v1/repositories`
Get all tracked repositories.

**Response Example:**
```json
[
  {
    "id": 1,
    "path": "/Users/user/projects/my-repo",
    "name": "My Repository",
    "description": "A sample Node.js project",
    "status": "active",
    "indexed_at": "2025-06-21T10:00:00Z"
  },
  {
    "id": 2,
    "path": "/Users/user/projects/python-app",
    "name": "Python App",
    "description": "A Python web application",
    "status": "active",
    "indexed_at": null
  }
]
```

### POST `/api/v1/repositories`
Add a new repository for tracking.

**Request Body:**
```json
{
  "path": "/path/to/your/repository",
  "name": "My Awesome Project",
  "description": "A description of what this repository contains"
}
```

**Response Example:**
```json
{
  "id": 3,
  "path": "/path/to/your/repository",
  "name": "My Awesome Project",
  "description": "A description of what this repository contains",
  "status": "active",
  "indexed_at": null
}
```

### GET `/api/v1/repositories/{repository_id}`
Get a specific repository by ID.

**Response Example:**
```json
{
  "id": 1,
  "path": "/Users/user/projects/my-repo",
  "name": "My Repository",
  "description": "A sample Node.js project",
  "status": "active",
  "indexed_at": "2025-06-21T10:00:00Z"
}
```

### DELETE `/api/v1/repositories/{repository_id}`
Remove a repository from tracking.

**Response Example:**
```json
{
  "message": "Repository removed successfully"
}
```

### POST `/api/v1/repositories/index`
Start indexing repositories in the background.

**Request Body (Optional):**
```json
{
  "repository_ids": [1, 2, 3]
}
```
*If `repository_ids` is not provided, all repositories will be indexed.*

**Response Example:**
```json
{
  "message": "Indexing started in background",
  "repositories_indexed": [1, 2, 3],
  "status": "started"
}
```

### GET `/api/v1/repositories/index/status`
Get the current status of repository indexing.

**Response Example:**
```json
{
  "status": "available",
  "message": "Indexing service is running"
}
```

---

## 📄 File System Routes

### GET `/api/v1/files/mono-repo`
Get the mono repository structure as a file tree.

**Response Example:**
```json
{
  "mono_repo_path": "/path/to/generated/mono-repo",
  "structure": {
    "name": "mono-repo",
    "path": "/path/to/generated/mono-repo",
    "type": "directory",
    "children": [
      {
        "name": "src",
        "path": "/path/to/generated/mono-repo/src",
        "type": "directory",
        "children": [
          {
            "name": "main.py",
            "path": "/path/to/generated/mono-repo/src/main.py",
            "type": "file",
            "size": 1024
          }
        ]
      },
      {
        "name": "README.md",
        "path": "/path/to/generated/mono-repo/README.md",
        "type": "file",
        "size": 2048
      }
    ]
  },
  "total_files": 150,
  "total_size": 1048576
}
```

### GET `/api/v1/files/mono-repo/generate`
Generate a new mono repository from all tracked repositories.

**Response Example:**
```json
{
  "message": "Mono repository generated successfully",
  "mono_repo_path": "/path/to/generated/mono-repo",
  "repositories_included": 5
}
```

### GET `/api/v1/files/content?file_path=/path/to/file.py`
Get the content of a specific file.

**Query Parameters:**
- `file_path` (required): Absolute path to the file

**Response Example:**
```json
{
  "path": "/path/to/file.py",
  "content": "def hello_world():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello_world()",
  "encoding": "utf-8",
  "size": 87
}
```

### GET `/api/v1/files/search?query=function&file_type=py&repository_id=1`
Search for files in tracked repositories.

**Query Parameters:**
- `query` (required): Search term to look for in file names and paths
- `file_type` (optional): File extension filter (e.g., "py", "js", "md")
- `repository_id` (optional): Limit search to specific repository

**Response Example:**
```json
{
  "query": "function",
  "results": [
    {
      "path": "/path/to/repo/src/utils/functions.py",
      "name": "functions.py",
      "size": 2048,
      "repository_id": 1,
      "repository_name": "My Repository"
    },
    {
      "path": "/path/to/repo/tests/test_functions.py",
      "name": "test_functions.py",
      "size": 1024,
      "repository_id": 1,
      "repository_name": "My Repository"
    }
  ],
  "total": 2
}
```

---

## 🚀 Quick Start Examples

### Start a Chat Session
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me understand this codebase?"}'
```

### Add a Repository
```bash
curl -X POST "http://localhost:8000/api/v1/repositories" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/your/project",
    "name": "My Project",
    "description": "A sample project"
  }'
```

### Index All Repositories
```bash
curl -X POST "http://localhost:8000/api/v1/repositories/index" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Get File Tree Structure
```bash
curl "http://localhost:8000/api/v1/files/mono-repo"
```

### Search for Files
```bash
curl "http://localhost:8000/api/v1/files/search?query=main&file_type=py"
```

---

## 🔧 Running the API

### Development Mode
```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run with auto-reload
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root endpoint**: http://localhost:8000/

---

## 📝 Error Responses

All endpoints return errors in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (resource doesn't exist)
- `413` - Payload Too Large (file too big)
- `500` - Internal Server Error

---

## 🔒 Security Notes

- File access is restricted to tracked repositories only
- File size limits are enforced (5MB max for content endpoint)
- Path traversal attacks are prevented
- In production, implement proper authentication and rate limiting
