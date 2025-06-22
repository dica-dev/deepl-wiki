"""Index commands for repository analysis and documentation generation."""

import sys
import json
import uuid
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add agents to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))

@click.command()
@click.argument('repos', nargs=-1)
@click.option('--output', '-o', help='Output file or directory for results')
@click.option('--force', is_flag=True, help='Force re-indexing of already indexed repos')
@click.option('--mono-repo', is_flag=True, help='Generate structured mono-repo documentation')
@click.option('--include-diagrams', is_flag=True, help='Include Mermaid diagrams in documentation')
@click.option('--diagram-format', type=click.Choice(['mermaid', 'd2', 'plantuml']), default='mermaid', help='Diagram format to use')
@click.option('--include-examples', is_flag=True, help='Include code examples and usage patterns')
@click.option('--intelligent-structure', is_flag=True, default=True, help='Use intelligent structure analysis')
@click.option('--format', type=click.Choice(['json', 'markdown']), default='json', help='Output format')
def index(repos, output, force, mono_repo, include_diagrams, diagram_format, include_examples, intelligent_structure, format):
    """Index repositories and generate documentation."""
    console = Console()
    
    try:
        from agents.index_repo_agent import IndexRepoAgent
        from agents.shared.database import DatabaseManager
        
        db = DatabaseManager()
        
        # Determine which repositories to index
        if repos:
            # Index specified repositories
            repo_paths = []
            for repo in repos:
                repo_path = Path(repo).resolve()
                if not repo_path.exists():
                    console.print(f"[red]Warning: Repository path does not exist: {repo}[/red]")
                    continue
                repo_paths.append(str(repo_path))
        else:
            # Index pending repositories from database
            if force:
                repositories = db.get_repositories()
            else:
                repositories = db.get_repositories(status="pending")
            
            if not repositories:
                console.print("[yellow]No repositories to index. Use 'repositories add' command to add repositories first.[/yellow]")
                return
            
            repo_paths = [repo["repo_path"] for repo in repositories]
            console.print(f"[blue]Found {len(repo_paths)} repositories to index[/blue]")
        
        if not repo_paths:
            console.print("[red]Error: No valid repository paths provided.[/red]")
            return
        
        console.print(f"[bold green]Initializing Enhanced Index Agent for {len(repo_paths)} repositories...[/bold green]")
        
        # Configure enhanced features
        enhanced_config = {
            'include_diagrams': include_diagrams,
            'diagram_format': diagram_format,
            'include_examples': include_examples,
            'intelligent_structure': intelligent_structure
        }
        
        if include_diagrams:
            console.print(f"[cyan]✓ Visual diagrams enabled ({diagram_format} format)[/cyan]")
        if include_examples:
            console.print(f"[cyan]✓ Code examples extraction enabled[/cyan]")
        if intelligent_structure:
            console.print(f"[cyan]✓ Intelligent structure analysis enabled[/cyan]")
        
        # Always pass the output directory to IndexRepoAgent
        # This ensures all generated docs are saved to the specified location
        agent_output_dir = output
        
        agent = IndexRepoAgent()
        
        # Start indexing session
        session_id = str(uuid.uuid4())
        db.start_indexing_session(session_id, len(repo_paths))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Indexing repositories with enhanced features...", total=len(repo_paths))
            
            # Pass enhanced configuration to the agent
            result = agent.index_repositories(
                repo_paths, 
                output_dir=agent_output_dir,
                enhanced_features=enhanced_config
            )
            progress.update(task, completed=len(repo_paths))
        
        if result['success']:
            console.print(f"\n[bold green]✓ Indexing completed successfully![/bold green]")
            console.print(f"[green]Processed {result['total_repos']} repositories[/green]")
            console.print(f"[green]Generated {len(result['individual_memos'])} individual memos[/green]")
            
            # Update database with results
            success_count = 0
            for memo_entry in result['individual_memos']:
                try:
                    db.add_repository(memo_entry['repo_path'], memo_entry['metadata'])
                    success_count += 1
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to save {memo_entry['repo_path']}: {e}[/yellow]")
            
            db.complete_indexing_session(session_id, success_count, len(repo_paths) - success_count)
            
            # Handle output
            if output:
                _handle_output(console, result, output, mono_repo, include_diagrams, diagram_format, include_examples, format, session_id)
            
            # Show general memo
            if result.get('general_memo'):
                from rich.panel import Panel
                console.print("\n")
                console.print(Panel(result['general_memo'], title="General Memo", expand=False))
            
        else:
            console.print(f"[red]✗ Indexing failed: {result.get('error', 'Unknown error')}[/red]")
            db.complete_indexing_session(session_id, 0, len(repo_paths))
    
    except Exception as e:
        console.print(f"[red]Error during indexing: {e}[/red]")
        raise click.ClickException(str(e))

def _handle_output(console, result, output, mono_repo, include_diagrams, diagram_format, include_examples, format, session_id):
    """Handle output generation with enhanced features."""
    if mono_repo:
        try:
            from agents.mono_repo_generator import MonoRepoGenerator
            
            generator = MonoRepoGenerator(
                include_diagrams=include_diagrams,
                diagram_format=diagram_format,
                include_examples=include_examples,
                output_format=format
            )
            
            mono_repo_path = generator.generate_mono_repo(
                output_dir=output,
                repositories=result['individual_memos'],
                general_memo=result['general_memo']
            )
            
            console.print(f"[blue]Mono-repo documentation generated at: {mono_repo_path}[/blue]")
            console.print(f"[green]You can serve it with: deepl-wiki server docs --path {mono_repo_path}[/green]")
            
        except ImportError:
            console.print("[yellow]MonoRepoGenerator not found. Falling back to JSON output.[/yellow]")
            _save_json_output(output, result, session_id)
        except Exception as e:
            console.print(f"[yellow]MonoRepoGenerator failed: {e}. Falling back to JSON output.[/yellow]")
            _save_json_output(output, result, session_id)
    else:
        _save_json_output(output, result, session_id)

def _save_json_output(output_path, result, session_id):
    """Save results as JSON."""
    output_data = {
        'repositories': result['individual_memos'],
        'general_memo': result['general_memo'],
        'metadata': {
            'total_repos': result['total_repos'],
            'success': result['success'],
            'session_id': session_id
        }
    }
    
    output_file = Path(output_path)
    if output_file.is_dir():
        output_file = output_file / 'results.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    console = Console()
    console.print(f"[blue]Results saved to: {output_file}[/blue]")
