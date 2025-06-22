# DeepL Wiki Backend

An interactive documentation management system that uses AI agents to index repositories, generate wikis, and provide intelligent chat-based assistance for codebases.

> **Note**: This project uses [uv](https://docs.astral.sh/uv/) for fast Python package management and virtual environment handling.

## Features

- **Repository Indexing**: Automatically index and analyze code repositories
- **Interactive Chat**: Chat with your documentation using AI agents
- **Wiki Generation**: Generate comprehensive wikis from your codebase
- **Multi-format Support**: Support for various programming languages and frameworks
- **Vector Database**: ChromaDB integration for semantic search
- **GitHub Integration**: Push generated documentation directly to repositories

## Prerequisites

- Python 3.8 or higher
- Git
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver

## Installation

### 1. Install uv

If you don't have `uv` installed, install it first:

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository

```bash
git clone <repository-url>
cd deepl-wiki/deepl-wiki-backend
```

### 3. Create and Activate Virtual Environment with uv

```bash
# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 4. Install CLI Package

```bash
uv pip install -e ./deepl-wiki-cli
```

## Configuration

### Environment Variables

Create a `.env` file in the project root or set the following environment variables:

```bash
# Required for AI functionality
OPENAI_API_KEY=your_openai_api_key_here

# Optional: GitHub integration
GITHUB_TOKEN=your_github_token_here

# Optional: Custom configuration
DEBUG=true
```

## Usage

### Command Line Interface

Once installed, you can use the `deepl-wiki` command from anywhere while your virtual environment is activated:

```bash
# Show help
deepl-wiki --help

# Check system health
deepl-wiki health

# List tracked repositories
deepl-wiki list

# Add a repository for tracking
deepl-wiki add /path/to/your/repository

# Index repositories
deepl-wiki index

# Start interactive chat
deepl-wiki chat

# Run demo
deepl-wiki demo

# Show statistics
deepl-wiki stats

# Push documentation to repository
deepl-wiki push
```

### Available Commands

| Command | Description |
|---------|-------------|
| `add` | Add repositories for tracking and indexing |
| `chat` | Start interactive chat with the documentation system |
| `demo` | Run demo to showcase DeepL Wiki functionality |
| `health` | Check system health and configuration |
| `index` | Index repositories and generate documentation |
| `list` | List tracked repositories |
| `push` | Push memo to repository using GitHub integration |
| `repositories` | Manage repositories for indexing and tracking |
| `stats` | Show database and system statistics |

### Alternative Ways to Run

If you prefer not to install the package globally, you can run it directly:

```bash
# From the deepl-wiki-cli directory
python -m cli.main --help

# Using the compatibility wrapper
python deepl_wiki_agents.py --help
```

## Project Structure

```
deepl-wiki-backend/
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── deepl-wiki-agents/       # Core agent functionality
│   ├── agents/              # AI agents implementation
│   ├── shared/              # Shared utilities
│   └── chroma_db/          # Vector database storage
├── deepl-wiki-cli/         # Command-line interface
│   ├── cli/                # CLI implementation
│   ├── commands/           # CLI commands
│   └── utils/              # CLI utilities
└── deepl-wiki-frontend/    # Web interface (separate)
```

## Development

### Running Tests

```bash
# Activate virtual environment first
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run CLI tests
cd deepl-wiki-cli
uv run pytest test_cli.py

# Run specific test
uv run python test_running_guide.py
```

### Database

The system uses ChromaDB for vector storage. The database files are stored in:
- `deepl-wiki-agents/chroma_db/` - Vector database
- `deepl-wiki-agents/deepl_wiki.db` - SQLite database

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure you've activated your virtual environment and installed all dependencies:
   ```bash
   uv sync
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

2. **CLI not found**: Install the CLI package in development mode:
   ```bash
   uv pip install -e ./deepl-wiki-cli
   ```

3. **Permission errors**: Make sure you have proper permissions for the directories you're trying to index.

4. **API errors**: Ensure your OpenAI API key is properly set in your environment variables.

### Logs and Debugging

Enable debug mode by setting the `DEBUG` environment variable:
```bash
export DEBUG=true  # Linux/macOS
set DEBUG=true     # Windows
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions, please create an issue in the GitHub repository or contact the development team.