"""Statistics and information commands."""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel

# Add agents to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))


@click.command()
def stats():
    """Show database and system statistics."""
    console = Console()
    
    try:
        from agents.shared.database import DatabaseManager
        from agents.shared.chroma_manager import ChromaManager
        
        db = DatabaseManager()
        stats_data = db.get_stats()
        
        # Try to get ChromaDB info
        try:
            chroma = ChromaManager()
            chroma_info = chroma.get_collection_info()
        except Exception:
            chroma_info = {"count": "Error", "name": "N/A"}
        
        panel_content = f"""
[bold cyan]Repository Statistics[/bold cyan]
• Total Repositories: {stats_data['total_repositories']}
• Indexed Repositories: {stats_data['indexed_repositories']}
• Pending Repositories: {stats_data['pending_repositories']}

[bold cyan]Chat Statistics[/bold cyan]
• Total Messages: {stats_data['total_chat_messages']}
• Total Sessions: {stats_data['total_chat_sessions']}

[bold cyan]Vector Database[/bold cyan]
• Collection: {chroma_info['name']}
• Documents: {chroma_info['count']}

[bold cyan]Database[/bold cyan]
• Database Path: {stats_data['database_path']}
        """
        
        console.print(Panel(panel_content, title="DeepL Wiki Statistics", expand=False))
        
    except Exception as e:
        console.print(f"[red]Error retrieving statistics: {e}[/red]")
        raise click.ClickException(str(e))


@click.command()
def health():
    """Check system health and configuration."""
    console = Console()
    
    try:
        from ..utils.validation import validate_environment, check_optional_dependencies
        
        console.print("[bold]System Health Check[/bold]")
        console.print("=" * 30)
          # Check environment
        if validate_environment():
            console.print("[green]Environment validation passed[/green]")
        else:
            console.print("[red]Environment validation failed[/red]")
        
        # Check optional dependencies
        if check_optional_dependencies():
            console.print("[green]All optional dependencies available[/green]")
        else:
            console.print("[yellow]Some optional dependencies missing[/yellow]")
        
        # Check agents import
        try:
            from agents.shared.database import DatabaseManager
            console.print("[green]Agents modules accessible[/green]")
        except ImportError as e:
            console.print(f"[red]Agents import failed: {e}[/red]")
        
        # Check database connection
        try:
            db = DatabaseManager()
            db.get_stats()
            console.print("[green]Database connection successful[/green]")
        except Exception as e:
            console.print(f"[red]Database connection failed: {e}[/red]")
        
        console.print("\n[dim]Use 'deepl-wiki stats' for detailed statistics[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error during health check: {e}[/red]")
        raise click.ClickException(str(e))
