# DeepL Wiki CLI

A modular command-line interface for DeepL Wiki Agents - an interactive documentation management system powered by LangGraph and Llama API.

## Features

- **Repository Management**: Add, list, and track repositories for documentation
- **Interactive Chat**: Query your documentation using natural language
- **Intelligent Indexing**: Analyze repositories and generate structured documentation
- **Web Interfaces**: Serve documentation and provide web-based access
- **GitHub Integration**: Push documentation updates to repositories
- **Health Monitoring**: Check system status and configuration

## Installation

```bash
cd deepl-wiki-cli
pip install -e .
```

## Quick Start

1. **Set up environment variables:**
```bash
export LLAMA_API_KEY="your-llama-api-key"
export GITHUB_TOKEN="your-github-token"  # Optional, for push operations
```

2. **Add repositories for tracking:**
```bash
deepl-wiki repositories add /path/to/repo1 /path/to/repo2
```

3. **Index repositories:**
```bash
deepl-wiki index
```

4. **Start chatting with your documentation:**
```bash
deepl-wiki chat
```

## Command Reference

### Repository Management
```bash
# List tracked repositories
deepl-wiki repositories list

# Add repositories
deepl-wiki repositories add /path/to/repo1 /path/to/repo2

# Remove a repository
deepl-wiki repositories remove /path/to/repo
```

### Indexing
```bash
# Index all pending repositories
deepl-wiki index

# Index specific repositories
deepl-wiki index /path/to/repo1 /path/to/repo2

# Generate structured documentation
deepl-wiki index --mono-repo --include-diagrams --output ./docs

# Force re-indexing
deepl-wiki index --force
```

### Chat Interface
```bash
# Interactive chat
deepl-wiki chat

# Single query
deepl-wiki chat --query "What files are in the repository?"

# Use specific session
deepl-wiki chat --session my-session-id

# Show conversation history
deepl-wiki chat --history --session my-session-id
```

### Web Servers
```bash
# Start web interface
deepl-wiki server web --host 0.0.0.0 --port 8000

# Serve generated documentation
deepl-wiki server docs --path ./docs --port 8080
```

### Statistics and Health
```bash
# Show system statistics
deepl-wiki stats

# Check system health
deepl-wiki health
```

### GitHub Integration
```bash
# Push memo to repository
deepl-wiki push --memo-repo https://github.com/user/repo \
                --branch main \
                --source-repo my-project \
                --memo-file ./memo.md
```

### Demo and Testing
```bash
# Run simple demo
deepl-wiki demo

# Run interactive demo
deepl-wiki demo --interactive

# Demo with specific repository
deepl-wiki demo --path /path/to/repo
```

## Configuration

### Environment Variables

- `LLAMA_API_KEY`: Required for AI functionality
- `GITHUB_TOKEN`: Required for push operations
- `DEBUG`: Enable debug output

### Configuration File

You can specify a custom configuration file:
```bash
deepl-wiki --config /path/to/config.env command
```

## Architecture

The CLI is designed with a modular architecture:

```
cli/
├── main.py              # Main entry point and CLI setup
├── commands/            # Command modules
│   ├── repository_commands.py
│   ├── chat_commands.py
│   ├── index_commands.py
│   ├── server_commands.py
│   ├── stats_commands.py
│   ├── demo_commands.py
│   └── push_commands.py
└── utils/               # Utility modules
    ├── config.py        # Configuration management
    └── validation.py    # Environment validation
```

## Integration with Agents

The CLI maintains separation of concerns while integrating with the main agents:

- **Agents Directory**: `../deepl-wiki-agents/`
- **Dynamic Import**: Agents are imported at runtime
- **Path Management**: Automatically adds agents to Python path
- **Error Handling**: Graceful handling of missing dependencies

## Development

### Adding New Commands

1. Create a new command module in `cli/commands/`
2. Add the import to `cli/commands/__init__.py`
3. Register the command in `cli/main.py`

### Example Command Module

```python
import click
from rich.console import Console

@click.command()
@click.option('--option', help='Example option')
def my_command(option):
    \"\"\"Example command description.\"\"\"
    console = Console()
    console.print(f"Hello from my command: {option}")
```

## Error Handling

The CLI provides comprehensive error handling:

- Environment validation before execution
- Graceful handling of missing dependencies
- User-friendly error messages
- Debug mode for detailed error information

## Output Formats

- **Rich Console**: Colorful, formatted terminal output
- **JSON**: Machine-readable output for integration
- **Tables**: Structured data presentation
- **Progress Indicators**: Real-time operation feedback

## License

This project is part of the DeepL Wiki Agents system.
