"""Push commands for GitHub integration."""

import sys
import os
from pathlib import Path
import click
from rich.console import Console

# Add agents to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))


@click.command()
@click.option('--memo-repo', required=True, help='Memo repository URL')
@click.option('--branch', required=True, help='Target branch')
@click.option('--source-repo', required=True, help='Source repository name')
@click.option('--memo-file', required=True, help='Path to memo file')
def push(memo_repo, branch, source_repo, memo_file):
    """Push memo to repository using GitHub integration."""
    console = Console()
    
    # Check for GitHub token
    if not os.environ.get("GITHUB_TOKEN"):
        console.print("[red]Error: GITHUB_TOKEN environment variable is required for push operations[/red]")
        console.print("[dim]Please set it with: export GITHUB_TOKEN='your-github-token'[/dim]")
        raise click.ClickException("Missing GITHUB_TOKEN")
    
    console.print("Initializing Push Agent...")
    
    memo_file_path = Path(memo_file)
    if not memo_file_path.exists():
        console.print(f"[red]Error: Memo file does not exist: {memo_file}[/red]")
        raise click.ClickException(f"File not found: {memo_file}")
    
    try:
        with open(memo_file_path, 'r', encoding='utf-8') as f:
            memo_content = f.read()
    except Exception as e:
        console.print(f"[red]Error reading memo file: {e}[/red]")
        raise click.ClickException(str(e))
    
    memo_metadata = {
        'source_repo': source_repo,
        'target_branch': branch,
        'memo_file': str(memo_file_path),
        'timestamp': str(memo_file_path.stat().st_mtime)
    }
    
    try:
        from agents.push_agent import PushAgent
        agent = PushAgent()
    except Exception as e:
        console.print(f"[red]Failed to initialize Push Agent: {e}[/red]")
        raise click.ClickException(str(e))
    
    console.print(f"Pushing memo to {memo_repo} on branch {branch}...")
    
    try:
        result = agent.push_memo(
            memo_repo_url=memo_repo,
            target_branch=branch,
            source_repo_name=source_repo,
            memo_content=memo_content,
            memo_metadata=memo_metadata
        )
        
        if result['success']:
            console.print("[bold green]Push completed successfully![/bold green]")
            if result.get('commit_hash'):
                console.print(f"[green]Commit hash: {result['commit_hash']}[/green]")
            console.print(f"[green]Branch: {result['branch']}[/green]")
        else:
            console.print(f"[red]Push failed: {result.get('error', 'Unknown error')}[/red]")
            raise click.ClickException("Push operation failed")
            
    except Exception as e:
        console.print(f"[red]Error during push: {e}[/red]")
        raise click.ClickException(str(e))
