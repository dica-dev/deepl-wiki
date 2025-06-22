# DeepL Wiki CLI - Usage Guide

The CLI has been successfully separated and modularized. Here's how to use it:

## Installation

```bash
cd deepl-wiki-cli
pip install -e .
```

## Basic Commands

### List repositories
```bash
deepl-wiki list
deepl-wiki list --status pending
deepl-wiki list --format json
```

### Add repositories
```bash
deepl-wiki add /path/to/repo1 /path/to/repo2
deepl-wiki add .  # Add current directory
```

### Index repositories
```bash
deepl-wiki index  # Index all pending repositories
deepl-wiki index /path/to/repo  # Index specific repository
deepl-wiki index --force  # Force re-indexing
deepl-wiki index --output ./docs --mono-repo --include-diagrams
```

### Chat with documentation
```bash
deepl-wiki chat  # Interactive mode
deepl-wiki chat --query "What files are in the repository?"
deepl-wiki chat --session my-session
deepl-wiki chat --history --session my-session
```

### Statistics and health
```bash
deepl-wiki stats  # Show database statistics
deepl-wiki health  # Check system health
```

### Push to GitHub
```bash
deepl-wiki push --memo-repo https://github.com/user/repo \
                --branch main \
                --source-repo my-project \
                --memo-file ./memo.md
```

### Demo
```bash
deepl-wiki demo  # Simple demo
deepl-wiki demo --interactive  # Interactive demo
deepl-wiki demo --path /path/to/repo
```

## Environment Setup

Create a `.env` file in the CLI directory:
```bash
LLAMA_API_KEY=your-llama-api-key
GITHUB_TOKEN=your-github-token  # Optional, for push operations
```

## Command Structure

The CLI now supports both grouped and direct commands:

- **Direct commands**: `deepl-wiki list`, `deepl-wiki add`
- **Grouped commands**: `deepl-wiki repositories list`, `deepl-wiki repositories add`

Both work the same way, use whichever you prefer.

## Features

✅ **Modular Architecture**: Commands organized by functionality  
✅ **Rich Output**: Colorful, formatted terminal output  
✅ **Error Handling**: Comprehensive validation and user-friendly messages  
✅ **Health Checks**: Built-in system validation  
✅ **Flexible Configuration**: Support for custom config files  
✅ **Agent Integration**: Seamlessly calls the agents in the deepl-wiki-agents directory  

## Running Guide Compatibility

This CLI maintains full compatibility with the original running guide commands, just use `deepl-wiki` instead of `python -m deepl_wiki_agents`.

The server functionality has been excluded as requested.
