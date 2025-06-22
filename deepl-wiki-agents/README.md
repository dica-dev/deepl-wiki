# DeepL Wiki Agents

A collection of LangGraph-based agents for automated documentation management using Llama API and ChromaDB.

## 🚀 Features

- **Chat Agent**: Interactive documentation query system with natural language processing
- **Push Agent**: Automated GitHub repository management for documentation updates  
- **Index Repo Agent**: Intelligent codebase analysis and documentation generation
- **Vector Search**: ChromaDB integration for efficient document retrieval
- **Multi-Repository Support**: Handle multiple codebases simultaneously

## 📦 Installation

### 1. Install Dependencies

```bash
cd deepl-wiki-agents
pip install -e .
```

### 2. Environment Setup

Set your environment variables:

```bash
export LLAMA_API_KEY="your_llama_api_key_here"
export GITHUB_TOKEN="your_github_token_here"  # Optional, for push agent
```

## 🎯 Quick Start

### Command Line Interface

```bash
# Index repositories
python -m deepl_wiki_agents index /path/to/repo1 /path/to/repo2

# Start interactive chat
python -m deepl_wiki_agents chat

# Single query
python -m deepl_wiki_agents chat --query "What is the main functionality?"

# Push documentation to GitHub
python -m deepl_wiki_agents push \
  --memo-repo https://github.com/user/memo-repo.git \
  --branch repo1/feature-x \
  --source-repo my-repo \
  --memo-file memo.md

# Run demo
python -m deepl_wiki_agents demo
python -m deepl_wiki_agents demo --interactive
```

### Python API

```python
from deepl_wiki_agents import ChatAgent, PushAgent, IndexRepoAgent

# Index repositories
index_agent = IndexRepoAgent()
result = index_agent.index_repositories(["/path/to/repo1", "/path/to/repo2"])

# Chat with indexed content
chat_agent = ChatAgent()
response = chat_agent.chat("What is the main functionality of this codebase?")
print(response['response'])

# Push to GitHub (requires GITHUB_TOKEN)
push_agent = PushAgent()
push_result = push_agent.push_memo(
    memo_repo_url="https://github.com/user/memo-repo.git",
    target_branch="repo1/feature-x", 
    source_repo_name="my-repo",
    memo_content="# Documentation...",
    memo_metadata={"commit_hash": "abc123"}
)
```

## 🤖 Agents Overview

### Index Repo Agent

Analyzes codebases and generates comprehensive documentation:

- **File Analysis**: Scans repositories for relevant source files
- **Language Detection**: Identifies primary programming languages and frameworks
- **Documentation Generation**: Creates detailed memos using AI analysis
- **Vector Storage**: Stores documents in ChromaDB for efficient retrieval
- **Multi-Repo Support**: Processes multiple repositories and creates unified documentation

**Key Features:**
- Configurable file filtering (excludes binaries, dependencies, etc.)
- Intelligent chunking for large files
- Git metadata extraction
- Comprehensive project structure analysis

### Chat Agent

Provides interactive querying capabilities:

- **Natural Language Queries**: Ask questions about your codebase in plain English
- **Context-Aware Responses**: Uses vector search to find relevant documentation
- **Conversation Memory**: Maintains context across conversation turns
- **Source Attribution**: References specific files and repositories in responses

**Example Queries:**
- "What APIs does this service expose?"
- "How is authentication handled?"
- "What are the main dependencies?"
- "Show me the database schema"

### Push Agent

Automates GitHub repository operations:

- **Branch Management**: Creates and manages documentation branches
- **Automated Commits**: Commits generated documentation with meaningful messages
- **Repository Integration**: Works with existing GitHub workflows
- **Error Handling**: Robust error handling and rollback capabilities

**Workflow Integration:**
- Integrates with GitHub Actions
- Supports both feature branches and main branch updates
- Handles authentication securely
- Provides detailed operation feedback

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLAMA_API_KEY` | Yes | Llama API authentication key |
| `GITHUB_TOKEN` | No | GitHub personal access token (for push agent) |

### Custom Configuration

```python
from deepl_wiki_agents.shared import LlamaClient, ChromaManager

# Custom Llama client with different model
custom_llama = LlamaClient(model="custom-model-name")

# Custom ChromaDB with different settings
custom_chroma = ChromaManager(
    persist_directory="/custom/path/chroma",
    collection_name="my_docs"
)

# Use custom clients with agents
from deepl_wiki_agents import ChatAgent

chat_agent = ChatAgent(
    llama_client=custom_llama,
    chroma_manager=custom_chroma,
    max_search_results=10
)
```

## 📚 Examples

### Complete Workflow Example

```python
import os
from deepl_wiki_agents import ChatAgent, PushAgent, IndexRepoAgent

# Set environment variable
os.environ['LLAMA_API_KEY'] = 'your-api-key'

# 1. Index multiple repositories
index_agent = IndexRepoAgent()
index_result = index_agent.index_repositories([
    "/path/to/frontend-app",
    "/path/to/backend-api", 
    "/path/to/shared-utils"
])

if index_result['success']:
    print(f"Indexed {index_result['total_repos']} repositories")
    print("General Memo:", index_result['general_memo'])

# 2. Interactive chat session
chat_agent = ChatAgent()
conversation = []

while True:
    query = input("Ask about your codebase: ")
    if query.lower() == 'quit':
        break
        
    result = chat_agent.chat(query, conversation)
    print("Response:", result['response'])
    
    # Update conversation history
    conversation.extend([
        {"role": "user", "content": query},
        {"role": "assistant", "content": result['response']}
    ])

# 3. Push documentation updates (if GitHub token available)
if os.environ.get('GITHUB_TOKEN'):
    push_agent = PushAgent()
    push_result = push_agent.push_memo(
        memo_repo_url="https://github.com/company/documentation.git",
        target_branch="frontend-app/new-feature",
        source_repo_name="frontend-app",
        memo_content=index_result['individual_memos'][0]['memo_content'],
        memo_metadata={'timestamp': 'now'}
    )
    print("Push result:", push_result['success'])
```

### Custom Agent Configuration

```python
from deepl_wiki_agents import IndexRepoAgent

# Custom exclusions and settings
custom_agent = IndexRepoAgent(
    max_file_size=200000,  # 200KB max file size
    excluded_dirs={"custom_dir", "special_build"},
    excluded_extensions={".custom", ".special"}
)

result = custom_agent.index_repositories(["/path/to/repo"])
```

## 🛠️ Development

### Project Structure

```
deepl-wiki-agents/
├── deepl_wiki_agents/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── chat_agent.py
│   ├── push_agent.py
│   ├── index_repo_agent.py
│   └── shared/
│       ├── __init__.py
│       ├── llama_client.py
│       └── chroma_manager.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
black deepl_wiki_agents/
flake8 deepl_wiki_agents/
mypy deepl_wiki_agents/
```

## 🔗 Integration with DeepL Wiki System

These agents are designed to work with the broader DeepL Wiki ecosystem:

- **deepl-wiki-cli**: Orchestrates agent workflows
- **deepl-wiki-frontend**: Provides web interface for agent interactions
- **GitHub Actions**: Automates documentation updates using push agent

## ⚠️ Important Notes

- **API Keys**: Ensure your Llama API key is valid and has sufficient quota
- **GitHub Token**: Required for push operations, needs repo write permissions
- **Storage**: ChromaDB data is stored locally in `./chroma_db/` by default
- **File Limits**: Large files (>100KB by default) are truncated for processing
- **Error Handling**: All agents include graceful error handling and logging

## 🐛 Troubleshooting

### Common Issues

1. **"LLAMA_API_KEY not found"**
   - Set the environment variable: `export LLAMA_API_KEY="your-key"`

2. **"Failed to initialize ChromaDB"**
   - Check directory permissions for ChromaDB storage location
   - Ensure sufficient disk space

3. **"GitHub authentication failed"**
   - Verify GITHUB_TOKEN has correct permissions
   - Check token hasn't expired

4. **"No documents found in search"**
   - Run index agent first to populate ChromaDB
   - Check that repositories were successfully indexed

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your agent code here
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review the examples in this README
- Open an issue on GitHub
