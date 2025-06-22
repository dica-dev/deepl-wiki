"""Environment validation utilities."""

import os
import sys
from pathlib import Path
from rich.console import Console


def validate_environment():
    """Validate that the environment is properly configured."""
    console = Console()
    valid = True
    
    # Check for required environment variables
    required_vars = {
        'LLAMA_API_KEY': 'Llama API key for AI functionality'
    }
    
    for var, description in required_vars.items():
        if not os.environ.get(var):
            console.print(f"[red]Missing required environment variable: {var}[/red]")
            console.print(f"[dim]Description: {description}[/dim]")
            valid = False
    
    # Check if agents directory exists
    current_dir = Path(__file__).parent
    agents_path = current_dir.parent.parent.parent / "deepl-wiki-agents"
    
    if not agents_path.exists():
        console.print(f"[red]Agents directory not found: {agents_path}[/red]")
        valid = False
    
    # Check Python version
    if sys.version_info < (3, 8):
        console.print(f"[red]Python 3.8+ required, found: {sys.version}[/red]")
        valid = False
    
    return valid


def validate_agents_import():
    """Validate that agents can be imported."""
    try:
        # Add agents to path
        current_dir = Path(__file__).parent
        agents_path = current_dir.parent.parent.parent / "deepl-wiki-agents"
        
        if str(agents_path) not in sys.path:
            sys.path.insert(0, str(agents_path))
        
        # Try importing key modules
        from agents.shared.database import DatabaseManager
        from agents.chat_agent import ChatAgent
        from agents.index_repo_agent import IndexRepoAgent
        
        return True
    except ImportError as e:
        console = Console()
        console.print(f"[red]Failed to import agents: {e}[/red]")
        return False


def check_optional_dependencies():
    """Check for optional dependencies and warn if missing."""
    console = Console()
    optional_deps = {
        'uvicorn': 'Web server functionality',
        'fastapi': 'Web API functionality',
        'git': 'Git integration (push agent)',
    }
    
    missing = []
    
    for dep, description in optional_deps.items():
        try:
            if dep == 'git':
                import subprocess
                subprocess.run(['git', '--version'], capture_output=True, check=True)
            else:
                __import__(dep)
        except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
            missing.append((dep, description))
    
    if missing:
        console.print("[yellow]Optional dependencies missing:[/yellow]")
        for dep, desc in missing:
            console.print(f"  [dim]• {dep}: {desc}[/dim]")
        console.print("[dim]Some features may be limited.[/dim]")
    
    return len(missing) == 0
