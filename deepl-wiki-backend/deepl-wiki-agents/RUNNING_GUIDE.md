# 🚀 DeepL Wiki Agents - Complete Running Guide

This guide shows you how to install, configure, and run the DeepL Wiki Agents system using modern Python tools like `uv` and `uvicorn`.

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Llama API key
- GitHub token (optional, for push operations)

## 🔧 Installation

### Option 1: Using uv (Recommended)

Install uv if you haven't already:

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

Clone and install the project:

```bash
git clone <repository-url>
cd deepl-wiki-agents

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Option 2: Using pip

```bash
git clone <repository-url>
cd deepl-wiki-agents

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## 🔑 Environment Setup

Create a `.env` file in the project root:

```bash
# Required
LLAMA_API_KEY=your_llama_api_key_here

# Optional (for push agent)
GITHUB_TOKEN=your_github_token_here
```

Or export directly:

```bash
export LLAMA_API_KEY="your_llama_api_key_here"
export GITHUB_TOKEN="your_github_token_here"  # Optional
```

## 🎯 CLI Commands Overview

The enhanced CLI provides the following commands:

- `list` - Show repositories and their status
- `add` - Add repositories for tracking
- `index` - Index repositories and generate documentation
- `chat` - Interactive chat with documentation (with SQLite history)
- `push` - Push documentation to GitHub
- `stats` - Show database statistics
- `serve` - Start web interface with uvicorn
- `demo` - Run demo mode

## 📊 Repository Management Workflow

### 1. List Available Repositories

```bash
# Show all repositories
python -m deepl_wiki_agents list

# Show only pending repositories
python -m deepl_wiki_agents list --status pending

# Show only indexed repositories
python -m deepl_wiki_agents list --status indexed

# Output as JSON
python -m deepl_wiki_agents list --format json
```

### 2. Add Repositories for Tracking

```bash
# Add single repository
python -m deepl_wiki_agents add /path/to/your/repo

# Add multiple repositories
python -m deepl_wiki_agents add ./frontend ./backend ./shared-utils

# Add current directory
python -m deepl_wiki_agents add .
```

### 3. Index Repositories and Generate Mono-Repo Documentation

```bash
# Index all pending repositories
python -m deepl_wiki_agents index

# Index specific repositories
python -m deepl_wiki_agents index /path/to/repo1 /path/to/repo2

# Force re-index already indexed repos
python -m deepl_wiki_agents index --force

# Generate structured mono-repo documentation
python -m deepl_wiki_agents index --output ./docs/memo-repo --mono-repo

# Save results to specific file
python -m deepl_wiki_agents index --output results.json

# Generate mono-repo with custom structure
python -m deepl_wiki_agents index \
  --output ./my-docs \
  --mono-repo \
  --include-diagrams \
  --format markdown
```

The `--mono-repo` flag creates a structured documentation repository with:

```
memo-repo/
├── README.md                 # Global overview
├── repos/
│   ├── repo1/
│   │   ├── README.md        # Repository documentation
│   │   ├── architecture.md  # Architecture diagrams
│   │   └── api.md          # API documentation
│   ├── repo2/
│   │   ├── README.md
│   │   ├── components.md
│   │   └── database.md
│   └── ...
├── global/
│   ├── overview.md          # Multi-repo overview
│   ├── architecture.md      # System architecture
│   └── integrations.md      # Inter-repo connections
└── diagrams/
    ├── system-overview.mermaid
    ├── data-flow.mermaid
    └── component-diagram.mermaid
```

## � Viewing Generated Documentation

After generating mono-repo documentation, you can view it in several ways:

### 1. Browse Documentation Files

```bash
# Navigate to generated docs
cd ./docs/memo-repo

# View global overview
cat README.md

# Browse individual repository docs
ls repos/
cat repos/flask/README.md

# View system diagrams
cat diagrams/system-overview.mermaid
```

### 2. Serve Documentation Locally

```bash
# Serve docs with simple HTTP server
cd ./docs/memo-repo
python -m http.server 8080

# Or use the built-in documentation server
python -m deepl_wiki_agents serve-docs --path ./docs/memo-repo --port 8080
```

### 3. Chat with Generated Documentation

```bash
# Chat with the generated documentation
python -m deepl_wiki_agents chat --docs-path ./docs/memo-repo

# Ask specific questions about the documentation
python -m deepl_wiki_agents chat --query "Show me the system architecture" --docs-path ./docs/memo-repo
```

## �💬 Interactive Chat with SQLite History

The chat system now saves conversation history to SQLite database:

```bash
# Start interactive chat (auto-generates session ID)
python -m deepl_wiki_agents chat

# Use specific session ID
python -m deepl_wiki_agents chat --session my-session-123

# Single query mode
python -m deepl_wiki_agents chat --query "What APIs does this codebase expose?"
```

Chat features:
- ✅ Persistent conversation history across sessions
- ✅ Session management with unique IDs
- ✅ Rich terminal interface with colors
- ✅ SQLite database for reliable storage

## 🌐 Web Interface with uvicorn

Start the web interface using uvicorn:

```bash
# Basic web server
python -m deepl_wiki_agents serve

# Custom host and port
python -m deepl_wiki_agents serve --host 0.0.0.0 --port 3000

# Development mode with auto-reload
python -m deepl_wiki_agents serve --reload

# Or directly with uvicorn
uv run uvicorn deepl_wiki_agents.simple_web:app --reload
```

Access the web interface at: http://localhost:8000

## 📈 Database Statistics

View comprehensive statistics:

```bash
python -m deepl_wiki_agents stats
```

This shows:
- Repository counts (total, indexed, pending)
- Chat message statistics
- Database information
- Session counts

## 🔗 Example Workflows for Specific Repositories

### Example 1: React Frontend Project

```bash
# Add React project
python -m deepl_wiki_agents add ~/projects/my-react-app

# Check status
python -m deepl_wiki_agents list --status pending

# Index the project
python -m deepl_wiki_agents index

# Chat about React components
python -m deepl_wiki_agents chat --query "What React components are available?"
python -m deepl_wiki_agents chat --query "How is state management handled?"
python -m deepl_wiki_agents chat --query "What are the main API endpoints used?"
```

### Example 2: Python API Backend

```bash
# Add Python project
python -m deepl_wiki_agents add ~/projects/fastapi-backend

# Index with output file
python -m deepl_wiki_agents index --output backend-docs.json

# Interactive chat session
python -m deepl_wiki_agents chat --session backend-analysis

# Example queries for Python API:
# "What database models are defined?"
# "How is authentication implemented?"
# "What are the main API routes?"
# "How are database migrations handled?"
```

### Example 3: Multiple Microservices

```bash
# Add multiple services at once
python -m deepl_wiki_agents add \
  ~/projects/user-service \
  ~/projects/payment-service \
  ~/projects/notification-service \
  ~/projects/api-gateway

# Check all repositories
python -m deepl_wiki_agents list

# Index all services
python -m deepl_wiki_agents index --output microservices-docs.json

# Chat about the architecture
python -m deepl_wiki_agents chat --session microservices

# Example microservices queries:
# "How do the services communicate with each other?"
# "What databases are used by each service?"
# "How is authentication handled across services?"
# "What are the main API contracts between services?"
```

### Example 4: Open Source Project Analysis

```bash
# Clone and analyze popular repositories
git clone https://github.com/fastapi/fastapi.git /tmp/fastapi
git clone https://github.com/pallets/flask.git /tmp/flask

# Add them for analysis
python -m deepl_wiki_agents add /tmp/fastapi /tmp/flask

# Index and compare
python -m deepl_wiki_agents index --output oss-analysis.json

# Chat session for comparison
python -m deepl_wiki_agents chat --session oss-comparison

# Example comparison queries:
# "Compare the architecture of FastAPI vs Flask"
# "What are the main differences in how they handle routing?"
# "How do their dependency injection systems work?"
```

## 🔄 GitHub Integration Workflow

Push generated documentation to GitHub:

```bash
# Generate memo file first
python -m deepl_wiki_agents index --output my-project-memo.json

# Extract memo content to markdown file
# (You can write a script to convert JSON to markdown)

# Push to GitHub repository
python -m deepl_wiki_agents push \
  --memo-repo https://github.com/myorg/documentation.git \
  --branch my-project/feature-docs \
  --source-repo my-project \
  --memo-file my-project-memo.md
```

## 🎮 Demo and Testing

```bash
# Quick demo with current directory
python -m deepl_wiki_agents demo

# Interactive demo mode
python -m deepl_wiki_agents demo --interactive
```

## 🛠️ Development and Debugging

### Using uv for Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Code formatting
uv run black deepl_wiki_agents/
uv run ruff check deepl_wiki_agents/

# Type checking
uv run mypy deepl_wiki_agents/
```

### Running with uvicorn in Development

```bash
# Development server with auto-reload
uv run uvicorn deepl_wiki_agents.simple_web:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level debug

# Production-like server
uv run uvicorn deepl_wiki_agents.simple_web:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

## 📁 Database and File Locations

The system creates the following files:

```
deepl-wiki-agents/
├── deepl_wiki.db          # SQLite database (chat history, repo tracking)
├── chroma_db/             # ChromaDB vector database
├── .env                   # Environment variables
└── *.json                # Output files from indexing
```

## 🐛 Troubleshooting

### Common Issues and Solutions

1. **"LLAMA_API_KEY not found"**
   ```bash
   export LLAMA_API_KEY="your-actual-api-key"
   ```

2. **"No repositories to index"**
   ```bash
   # Add repositories first
   python -m deepl_wiki_agents add /path/to/repo
   python -m deepl_wiki_agents list  # Verify added
   python -m deepl_wiki_agents index
   ```

3. **"ChromaDB initialization failed"**
   ```bash
   # Remove and recreate ChromaDB
   rm -rf chroma_db/
   python -m deepl_wiki_agents index  # Will recreate
   ```

4. **"Web interface not accessible"**
   ```bash
   # Check if port is available
   python -m deepl_wiki_agents serve --port 3000
   # Or bind to all interfaces
   python -m deepl_wiki_agents serve --host 0.0.0.0
   ```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m deepl_wiki_agents chat --query "test"
```

## 🚀 Advanced Usage Examples

### Batch Processing Multiple Projects

```bash
#!/bin/bash
# batch_index.sh

PROJECTS=(
  "~/work/project1"
  "~/work/project2"
  "~/work/project3"
)

for project in "${PROJECTS[@]}"; do
  echo "Adding $project..."
  python -m deepl_wiki_agents add "$project"
done

echo "Indexing all projects..."
python -m deepl_wiki_agents index --output batch-results.json

echo "Starting interactive chat..."
python -m deepl_wiki_agents chat --session batch-analysis
```

### Automated Documentation Pipeline

```bash
#!/bin/bash
# auto_docs.sh

# Add repositories
python -m deepl_wiki_agents add ./src ./docs ./tests

# Index with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
python -m deepl_wiki_agents index --output "docs_${TIMESTAMP}.json"

# Generate summary
python -m deepl_wiki_agents chat --query "Summarize the main components and architecture" --session auto-summary

echo "Documentation updated: docs_${TIMESTAMP}.json"
```

## 📊 Performance Tips

1. **Large repositories**: Use `--force` sparingly as it re-processes everything
2. **Memory usage**: ChromaDB stores embeddings in memory; restart if needed
3. **Chat history**: Old sessions are kept in SQLite; clean up periodically
4. **File limits**: Default max file size is 100KB; configure in code if needed

## 🔗 Integration with CI/CD

### GitHub Actions Example

```yaml
name: Generate Documentation
on:
  push:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: |
          uv venv
          uv pip install -e .
      
      - name: Generate documentation
        env:
          LLAMA_API_KEY: ${{ secrets.LLAMA_API_KEY }}
        run: |
          source .venv/bin/activate
          python -m deepl_wiki_agents add .
          python -m deepl_wiki_agents index --output docs.json
      
      - name: Upload docs
        uses: actions/upload-artifact@v4
        with:
          name: documentation
          path: docs.json
```

This comprehensive guide covers all aspects of running the DeepL Wiki Agents system with modern tooling and real-world examples.
