"""Configuration utilities for the CLI."""

import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console


def load_environment_config(config_file=None):
    """Load environment configuration from .env files."""
    console = Console()
    
    if config_file:
        # Load from specific config file
        config_path = Path(config_file)
        if config_path.exists():
            load_dotenv(config_path)
            console.print(f"[green]Loaded configuration from: {config_path}[/green]")
        else:
            console.print(f"[yellow]Configuration file not found: {config_path}[/yellow]")
    else:
        # Look for .env in project root and parent directories
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent  # Go up to deepl-wiki root
        env_file = project_root / '.env'
        
        if env_file.exists():
            load_dotenv(env_file)
            if os.environ.get('DEBUG'):
                console.print(f"[dim]Loaded environment from: {env_file}[/dim]")
        else:
            # Fallback to default behavior (look in current dir and parents)
            load_dotenv()


def get_agents_path():
    """Get the path to the agents directory."""
    current_dir = Path(__file__).parent
    agents_path = current_dir.parent.parent.parent / "deepl-wiki-agents"
    return str(agents_path.resolve())


def get_config_value(key, default=None, required=False):
    """Get a configuration value from environment variables."""
    value = os.environ.get(key, default)
    
    if required and not value:
        raise ValueError(f"Required configuration key '{key}' not found")
    
    return value
