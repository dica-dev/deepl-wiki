"""Demo commands for testing and showcasing functionality."""

import sys
from pathlib import Path
import click
from rich.console import Console

# Add agents to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))


@click.command()
@click.option('--interactive', is_flag=True, help='Interactive demo mode')
@click.option('--path', default='.', help='Repository path for demo (default: current directory)')
def demo(interactive, path):
    """Run demo to showcase DeepL Wiki functionality."""
    console = Console()
    
    console.print("[bold]DeepL Wiki Agents - Demo[/bold]")
    console.print("=" * 30)
    
    if interactive:
        _run_interactive_demo(console)
    else:
        _run_simple_demo(console, path)


def _run_simple_demo(console, repo_path):
    """Run a simple demo."""
    console.print(f"Running simple demo with repository: {repo_path}")
    
    try:
        from agents.index_repo_agent import IndexRepoAgent
        from agents.chat_agent import ChatAgent
        
        console.print("\n[bold]1. Indexing repository...[/bold]")
        index_agent = IndexRepoAgent()
        result = index_agent.index_repositories([repo_path])
        
        if result['success']:
            console.print("[green]✓ Indexing completed successfully![/green]")
            console.print(f"[green]✓ Generated memo for {result['total_repos']} repository[/green]")
        else:
            console.print(f"[red]✗ Indexing failed: {result.get('error')}[/red]")
            return
            
    except Exception as e:
        console.print(f"[red]✗ Error during indexing: {e}[/red]")
        return
    
    try:
        console.print("\n[bold]2. Testing chat functionality...[/bold]")
        chat_agent = ChatAgent()
        
        test_queries = [
            "What files are in this repository?",
            "What programming language is used?",
            "Describe the project structure"
        ]
        
        for query in test_queries:
            console.print(f"\n[cyan]Query: {query}[/cyan]")
            chat_result = chat_agent.chat(query)
            
            if chat_result.get('error'):
                console.print(f"[red]Error: {chat_result['error']}[/red]")
            else:
                response = chat_result['response']
                if len(response) > 150:
                    console.print(f"[green]Response: {response[:150]}...[/green]")
                else:
                    console.print(f"[green]Response: {response}[/green]")
                    
    except Exception as e:
        console.print(f"[red]✗ Error during chat testing: {e}[/red]")
    
    console.print("\n" + "=" * 30)
    console.print("[bold green]Demo completed![/bold green]")
    console.print("\n[bold]Try running:[/bold]")
    console.print("  [blue]deepl-wiki chat[/blue]")
    console.print("  [blue]deepl-wiki index /path/to/your/repo[/blue]")


def _run_interactive_demo(console):
    """Run interactive demo."""
    try:
        from agents.index_repo_agent import IndexRepoAgent
        from agents.chat_agent import ChatAgent
        from agents.shared.chroma_manager import ChromaManager
        
        while True:
            console.print("\n[bold]DeepL Wiki Agents - Interactive Demo[/bold]")
            console.print("1. Index a repository")
            console.print("2. Chat with indexed content")
            console.print("3. Show ChromaDB status")
            console.print("4. Exit")
            
            try:
                choice = console.input("\n[bold]Enter your choice (1-4):[/bold] ").strip()
                
                if choice == "1":
                    repo_path = console.input("Enter repository path (or '.' for current): ").strip()
                    if not repo_path:
                        repo_path = "."
                    
                    try:
                        agent = IndexRepoAgent()
                        result = agent.index_repositories([repo_path])
                        
                        if result['success']:
                            console.print(f"[green]✓ Successfully indexed repository: {repo_path}[/green]")
                            console.print(f"[green]✓ Generated {len(result['individual_memos'])} memos[/green]")
                        else:
                            console.print(f"[red]✗ Indexing failed: {result.get('error')}[/red]")
                            
                    except Exception as e:
                        console.print(f"[red]✗ Error: {e}[/red]")
                
                elif choice == "2":
                    query = console.input("Enter your question: ").strip()
                    if query:
                        try:
                            agent = ChatAgent()
                            result = agent.chat(query)
                            console.print(f"\n[bold]Response:[/bold] {result['response']}")
                            
                            if result.get('error'):
                                console.print(f"[yellow]Warning: {result['error']}[/yellow]")
                                
                        except Exception as e:
                            console.print(f"[red]✗ Error: {e}[/red]")
                
                elif choice == "3":
                    try:
                        manager = ChromaManager()
                        info = manager.get_collection_info()
                        console.print(f"\n[bold]ChromaDB Status:[/bold]")
                        console.print(f"  Collection: {info['name']}")
                        console.print(f"  Documents: {info['count']}")
                        console.print(f"  Directory: {info['persist_directory']}")
                        
                    except Exception as e:
                        console.print(f"[red]✗ Error accessing ChromaDB: {e}[/red]")
                
                elif choice == "4":
                    console.print("[bold green]Goodbye![/bold green]")
                    break
                
                else:
                    console.print("[yellow]Invalid choice. Please enter 1-4.[/yellow]")
                    
            except KeyboardInterrupt:
                console.print("\n[bold green]Goodbye![/bold green]")
                break
                
    except Exception as e:
        console.print(f"[red]Error in interactive demo: {e}[/red]")
        raise click.ClickException(str(e))
