"""Repository management commands."""

import sys
from pathlib import Path
import click
import json
from rich.console import Console
from rich.table import Table

# Add agents to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))


@click.group()
def repositories():
    """Manage repositories for indexing and tracking."""
    pass


@repositories.command('list')
@click.option('--status', type=click.Choice(['pending', 'indexed', 'error']), 
              help='Filter by status')
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def list_repositories(status, format):
    """List tracked repositories."""
    console = Console()
    
    try:
        from agents.shared.database import DatabaseManager
        db = DatabaseManager()
        repositories = db.get_repositories(status=status)
        
        if format == "json":
            click.echo(json.dumps(repositories, indent=2))
            return
        
        # Table format
        table = Table(title="Repositories" + (f" ({status})" if status else ""))
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="blue")
        table.add_column("Language", style="green")
        table.add_column("Files", justify="right")
        table.add_column("Size", justify="right")
        table.add_column("Last Indexed", style="yellow")
        table.add_column("Status", style="bold")
        
        for repo in repositories:
            size_mb = repo["total_size"] / 1024 / 1024 if repo["total_size"] else 0
            size_str = f"{size_mb:.1f} MB" if size_mb > 0 else "Unknown"
            
            status_color = {"indexed": "green", "pending": "yellow", "error": "red"}.get(repo["status"], "white")
            
            table.add_row(
                repo["repo_name"],
                repo["repo_path"],
                repo["primary_language"],
                str(repo["file_count"]),
                size_str,
                repo["last_indexed"][:19] if repo["last_indexed"] else "Never",
                f"[{status_color}]{repo['status']}[/{status_color}]"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing repositories: {e}[/red]")
        raise click.ClickException(str(e))


@repositories.command('add')
@click.argument('repos', nargs=-1, required=True)
def add_repositories(repos):
    """Add repositories for tracking and indexing."""
    console = Console()
    
    try:
        from agents.shared.database import DatabaseManager
        db = DatabaseManager()
        
        added_count = 0
        for repo_path in repos:
            repo_path_obj = Path(repo_path).resolve()
            
            if not repo_path_obj.exists():
                console.print(f"[red]Warning: Repository path does not exist: {repo_path}[/red]")
                continue
            
            # Add with basic metadata
            repo_metadata = {
                "repo_name": repo_path_obj.name,
                "repo_path": str(repo_path_obj),
                "primary_language": "Unknown",
                "file_count": 0,
                "total_size": 0
            }
            
            try:
                db.add_repository(str(repo_path_obj), str(repo_metadata))
                console.print(f"[green]✓[/green] Added repository: {repo_path_obj.name}")
                added_count += 1
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to add {repo_path}: {e}")
        
        console.print(f"\n[bold]Added {added_count} repositories[/bold]")
        
    except Exception as e:
        console.print(f"[red]Error adding repositories: {e}[/red]")
        raise click.ClickException(str(e))


@repositories.command('remove')
@click.argument('repo_path')
@click.option('--force', is_flag=True, help='Force removal without confirmation')
def remove_repository(repo_path, force):
    """Remove a repository from tracking."""
    console = Console()
    
    if not force:
        if not click.confirm(f"Remove repository '{repo_path}' from tracking?"):
            console.print("Operation cancelled.")
            return
    
    try:
        from agents.shared.database import DatabaseManager
        db = DatabaseManager()
        
        # Note: This would need to be implemented in DatabaseManager
        console.print(f"[yellow]Repository removal not yet implemented: {repo_path}[/yellow]")
        console.print("[dim]This feature will be added in a future version.[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error removing repository: {e}[/red]")
        raise click.ClickException(str(e))
