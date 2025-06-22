"""Command-line interface for deepl-wiki agents."""

import argparse
import json
import sys
import os
import uuid
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from .shared.database import DatabaseManager

def main():
    """Main CLI entry point."""
    # Load environment variables from .env file
    # Look for .env in the project root (parent directories)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent  # Go up from agents/cli.py to project root
    env_file = project_root / '.env'
    
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Fallback to default behavior (look in current dir and parents)
        load_dotenv()
    
    parser = argparse.ArgumentParser(description="DeepL Wiki Agents CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List repositories")
    list_parser.add_argument("--status", choices=["pending", "indexed", "error"], help="Filter by status")
    list_parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add repositories for indexing")
    add_parser.add_argument("repos", nargs="+", help="Repository paths to add")
      # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")
    chat_parser.add_argument("--query", "-q", help="Single query mode")
    chat_parser.add_argument("--session", "-s", help="Chat session ID")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index repositories")
    index_parser.add_argument("repos", nargs="*", help="Repository paths to index (if not specified, indexes all pending)")
    index_parser.add_argument("--output", "-o", help="Output file or directory for results")
    index_parser.add_argument("--force", action="store_true", help="Force re-indexing of already indexed repos")
    index_parser.add_argument("--mono-repo", action="store_true", help="Generate structured mono-repo documentation")
    index_parser.add_argument("--include-diagrams", action="store_true", help="Include Mermaid diagrams in documentation")
    index_parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    
    # Push command
    push_parser = subparsers.add_parser("push", help="Push memo to repository")
    push_parser.add_argument("--memo-repo", required=True, help="Memo repository URL")
    push_parser.add_argument("--branch", required=True, help="Target branch")
    push_parser.add_argument("--source-repo", required=True, help="Source repository name")
    push_parser.add_argument("--memo-file", required=True, help="Path to memo file")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
      # Serve command (for web interface)
    serve_parser = subparsers.add_parser("serve", help="Start web interface")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Serve docs command
    serve_docs_parser = subparsers.add_parser("serve-docs", help="Serve generated documentation")
    serve_docs_parser.add_argument("--path", required=True, help="Path to documentation directory")
    serve_docs_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_docs_parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demo")
    demo_parser.add_argument("--interactive", action="store_true", help="Interactive demo mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Check for required environment variables
    if not os.environ.get("LLAMA_API_KEY"):
        print("Error: LLAMA_API_KEY environment variable is required")
        print("Please set it with: export LLAMA_API_KEY='your-api-key'")
        sys.exit(1)    
    try:
        if args.command == "list":
            run_list(args)
        elif args.command == "add":
            run_add(args)
        elif args.command == "chat":
            run_chat(args)
        elif args.command == "index":
            run_index(args)
        elif args.command == "push":
            run_push(args)
        elif args.command == "stats":
            run_stats(args)
        elif args.command == "serve":
            run_serve(args)
        elif args.command == "serve-docs":
            run_serve_docs(args)
        elif args.command == "demo":
            run_demo(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def run_list(args):
    """List repositories."""
    console = Console()
    db = DatabaseManager()
    
    repositories = db.get_repositories(status=args.status)
    
    if args.format == "json":
        print(json.dumps(repositories, indent=2))
        return
    
    # Table format
    table = Table(title="Repositories" + (f" ({args.status})" if args.status else ""))
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

def run_add(args):
    """Add repositories to tracking."""
    console = Console()
    db = DatabaseManager()
    
    added_count = 0
    for repo_path in args.repos:
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
            db.add_repository(str(repo_path_obj), repo_metadata)
            console.print(f"[green]✓[/green] Added repository: {repo_path_obj.name}")
            added_count += 1
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to add {repo_path}: {e}")
    
    console.print(f"\n[bold]Added {added_count} repositories[/bold]")

def run_stats(args):
    """Show database statistics."""
    console = Console()
    db = DatabaseManager()
    
    stats = db.get_stats()
    
    panel_content = f"""
[bold cyan]Repository Statistics[/bold cyan]
• Total Repositories: {stats['total_repositories']}
• Indexed Repositories: {stats['indexed_repositories']}
• Pending Repositories: {stats['pending_repositories']}

[bold cyan]Chat Statistics[/bold cyan]
• Total Messages: {stats['total_chat_messages']}
• Total Sessions: {stats['total_chat_sessions']}

[bold cyan]Database[/bold cyan]
• Database Path: {stats['database_path']}
    """
    
    console.print(Panel(panel_content, title="DeepL Wiki Stats", expand=False))

def run_serve(args):
    """Start web interface using uvicorn."""
    try:
        import uvicorn
        
        console = Console()
        console.print(f"[bold green]Starting DeepL Wiki web interface...[/bold green]")
        console.print(f"[blue]http://{args.host}:{args.port}[/blue]")
        
        # Create a simple FastAPI app
        create_simple_web_app()
        
        uvicorn.run(
            "deepl_wiki_agents.simple_web:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except ImportError:
        print("Error: uvicorn not installed. Install with: pip install uvicorn")

def create_simple_web_app():
    """Create a simple web app file."""
    web_app_content = '''
"""Simple FastAPI web application for DeepL Wiki Agents."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="DeepL Wiki Agents", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DeepL Wiki Agents</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; margin-bottom: 20px; }
            .feature { margin-bottom: 20px; }
            .code { background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: 'Monaco', 'Consolas', monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 DeepL Wiki Agents</h1>
            <p>Interactive documentation management system powered by LangGraph and Llama API.</p>
            
            <div class="feature">
                <h3>🔍 Available Features</h3>
                <ul>
                    <li><strong>Chat Agent:</strong> Interactive documentation queries</li>
                    <li><strong>Index Agent:</strong> Repository analysis and documentation generation</li>
                    <li><strong>Push Agent:</strong> GitHub integration for documentation updates</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>🚀 Quick Start</h3>
                <div class="code">
# Install and setup<br>
pip install -e .<br>
export LLAMA_API_KEY="your-key"<br><br>

# Add repositories<br>
python -m deepl_wiki_agents add /path/to/repo1 /path/to/repo2<br><br>

# Index repositories<br>
python -m deepl_wiki_agents index<br><br>

# Start chatting<br>
python -m deepl_wiki_agents chat
                </div>
            </div>
            
            <div class="feature">
                <h3>📋 CLI Commands</h3>
                <ul>
                    <li><code>list</code> - Show tracked repositories</li>
                    <li><code>add</code> - Add repositories for tracking</li>
                    <li><code>index</code> - Index repositories and generate docs</li>
                    <li><code>chat</code> - Interactive chat with documentation</li>
                    <li><code>stats</code> - Show database statistics</li>
                    <li><code>serve</code> - Start web interface</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
'''
    
    with open("deepl_wiki_agents/simple_web.py", "w") as f:
        f.write(web_app_content)

def run_chat(args):
    """Run chat agent."""
    from .chat_agent import ChatAgent
    
    console = Console()
    db = DatabaseManager()
    
    # Generate or use provided session ID
    session_id = args.session if args.session else str(uuid.uuid4())[:8]
    
    console.print(f"[bold green]Initializing Chat Agent...[/bold green]")
    console.print(f"[dim]Session ID: {session_id}[/dim]")
    
    try:
        agent = ChatAgent()
    except Exception as e:
        console.print(f"[red]Failed to initialize Chat Agent: {e}[/red]")
        return
    
    if args.query:
        # Single query mode
        result = agent.chat(args.query)
        console.print(f"\n[bold]Query:[/bold] {args.query}")
        console.print(f"[bold]Response:[/bold] {result['response']}")
        
        # Save to database
        db.add_chat_message(session_id, "user", args.query)
        db.add_chat_message(session_id, "assistant", result['response'])
        
        if result.get('error'):
            console.print(f"[red]Error: {result['error']}[/red]")
    else:
        # Interactive mode
        console.print("[bold green]Chat Agent ready![/bold green] Type 'quit' to exit.")
        
        # Load conversation history from database
        conversation_history = []
        db_history = db.get_chat_history(session_id, limit=20)
        
        if db_history:
            console.print(f"[dim]Loaded {len(db_history)} previous messages[/dim]")
            conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in db_history]
        
        while True:
            try:
                query = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    console.print("[bold green]Goodbye![/bold green]")
                    break
                
                if not query:
                    continue
                
                # Show thinking indicator
                with console.status("[bold green]Thinking..."):
                    result = agent.chat(query, conversation_history)
                
                console.print(f"[bold magenta]Assistant:[/bold magenta] {result['response']}")
                
                # Save to database
                db.add_chat_message(session_id, "user", query)
                db.add_chat_message(session_id, "assistant", result['response'])
                
                # Update conversation history
                conversation_history.append({"role": "user", "content": query})
                conversation_history.append({"role": "assistant", "content": result['response']})
                
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
                
                if result.get('error'):
                    console.print(f"[yellow]Warning: {result['error']}[/yellow]")
                    
            except EOFError:
                console.print("\n[bold green]Goodbye![/bold green]")
                break

def run_index(args):
    """Run index agent."""
    from .index_repo_agent import IndexRepoAgent
    
    console = Console()
    db = DatabaseManager()
    
    # Determine which repositories to index
    if args.repos:
        # Index specified repositories
        repo_paths = []
        for repo in args.repos:
            repo_path = Path(repo).resolve()
            if not repo_path.exists():
                console.print(f"[red]Warning: Repository path does not exist: {repo}[/red]")
                continue
            repo_paths.append(str(repo_path))
    else:
        # Index pending repositories from database
        if args.force:
            repositories = db.get_repositories()
        else:
            repositories = db.get_repositories(status="pending")
        
        if not repositories:
            console.print("[yellow]No repositories to index. Use 'add' command to add repositories first.[/yellow]")
            return
        
        repo_paths = [repo["repo_path"] for repo in repositories]
        console.print(f"[blue]Found {len(repo_paths)} repositories to index[/blue]")
    
    if not repo_paths:
        console.print("[red]Error: No valid repository paths provided.[/red]")
        return
    
    console.print(f"[bold green]Initializing Index Agent for {len(repo_paths)} repositories...[/bold green]")
    
    try:
        agent = IndexRepoAgent()
    except Exception as e:
        console.print(f"[red]Failed to initialize Index Agent: {e}[/red]")
        return
    
    # Start indexing session
    session_id = str(uuid.uuid4())
    db.start_indexing_session(session_id, len(repo_paths))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Indexing repositories...", total=len(repo_paths))
        
        result = agent.index_repositories(repo_paths)
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
        
        if args.output:
            if args.mono_repo:
                # Generate structured mono-repo documentation
                try:
                    from .mono_repo_generator import MonoRepoGenerator
                    
                    generator = MonoRepoGenerator(
                        include_diagrams=args.include_diagrams,
                        output_format=args.format
                    )
                    
                    mono_repo_path = generator.generate_mono_repo(
                        output_dir=args.output,
                        repositories=result['individual_memos'],
                        general_memo=result['general_memo']
                    )
                    
                    console.print(f"[blue]Mono-repo documentation generated at: {mono_repo_path}[/blue]")
                    console.print(f"[green]You can serve it with: python -m agents serve-docs --path {mono_repo_path}[/green]")
                    
                except ImportError:
                    console.print("[yellow]MonoRepoGenerator not found. Falling back to JSON output.[/yellow]")
                    # Fallback to JSON output
                    output_data = {
                        'repositories': result['individual_memos'],
                        'general_memo': result['general_memo'],
                        'metadata': {
                            'total_repos': result['total_repos'],
                            'success': result['success'],
                            'session_id': session_id
                        }
                    }
                    
                    with open(f"{args.output}/results.json", 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)
                    console.print(f"[blue]Results saved to: {args.output}/results.json[/blue]")
            else:
                # Standard JSON output
                output_data = {
                    'repositories': result['individual_memos'],
                    'general_memo': result['general_memo'],
                    'metadata': {
                        'total_repos': result['total_repos'],
                        'success': result['success'],
                        'session_id': session_id
                    }
                }
                
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                console.print(f"[blue]Results saved to: {args.output}[/blue]")
        
        # Show general memo in a panel
        console.print("\n")
        console.print(Panel(result['general_memo'], title="General Memo", expand=False))
        
    else:
        console.print(f"[red]✗ Indexing failed: {result.get('error', 'Unknown error')}[/red]")
        db.complete_indexing_session(session_id, 0, len(repo_paths))

def run_push(args):
    """Run push agent."""
    from .push_agent import PushAgent
    
    if not os.environ.get("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN environment variable is required for push operations")
        print("Please set it with: export GITHUB_TOKEN='your-github-token'")
        return
    
    print("Initializing Push Agent...")
    
    memo_file_path = Path(args.memo_file)
    if not memo_file_path.exists():
        print(f"Error: Memo file does not exist: {args.memo_file}")
        return
    
    try:
        with open(memo_file_path, 'r', encoding='utf-8') as f:
            memo_content = f.read()
    except Exception as e:
        print(f"Error reading memo file: {e}")
        return
    
    memo_metadata = {
        'source_repo': args.source_repo,
        'target_branch': args.branch,
        'memo_file': str(memo_file_path),
        'timestamp': str(memo_file_path.stat().st_mtime)
    }
    
    try:
        agent = PushAgent()
    except Exception as e:
        print(f"Failed to initialize Push Agent: {e}")
        return
    
    print(f"Pushing memo to {args.memo_repo} on branch {args.branch}...")
    result = agent.push_memo(
        memo_repo_url=args.memo_repo,
        target_branch=args.branch,
        source_repo_name=args.source_repo,
        memo_content=memo_content,
        memo_metadata=memo_metadata
    )
    
    if result['success']:
        print("Push completed successfully!")
        if result.get('commit_hash'):
            print(f"Commit hash: {result['commit_hash']}")
        print(f"Branch: {result['branch']}")
    else:
        print(f"Push failed: {result.get('error', 'Unknown error')}")

def run_demo(args):
    """Run demo."""
    console = Console()
    console.print("[bold]DeepL Wiki Agents - Demo[/bold]")
    console.print("=" * 30)
    
    if args.interactive:
        run_interactive_demo()
    else:
        run_simple_demo()

def run_simple_demo():
    """Run a simple demo."""
    from .index_repo_agent import IndexRepoAgent
    from .chat_agent import ChatAgent
    
    console = Console()
    console.print("Running simple demo with current directory...")
    
    try:
        console.print("\n[bold]1. Indexing current directory...[/bold]")
        index_agent = IndexRepoAgent()
        result = index_agent.index_repositories(["."])
        
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
    console.print("  [blue]python -m deepl_wiki_agents chat[/blue]")
    console.print("  [blue]python -m deepl_wiki_agents index /path/to/your/repo[/blue]")

def run_interactive_demo():
    """Run interactive demo."""
    from .index_repo_agent import IndexRepoAgent
    from .chat_agent import ChatAgent
    from .shared.chroma_manager import ChromaManager
    
    console = Console()
    
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

def run_serve_docs(args):
    """Serve generated documentation with a simple HTTP server."""
    import os
    import subprocess
    from pathlib import Path
    
    console = Console()
    docs_path = Path(args.path)
    
    if not docs_path.exists():
        console.print(f"[red]Error: Documentation path does not exist: {args.path}[/red]")
        return
    
    if not docs_path.is_dir():
        console.print(f"[red]Error: Path is not a directory: {args.path}[/red]")
        return
    
    console.print(f"[bold green]Serving documentation from: {docs_path}[/bold green]")
    console.print(f"[blue]Documentation server: http://{args.host}:{args.port}[/blue]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")
    
    try:
        # Change to docs directory and start server
        os.chdir(docs_path)
        subprocess.run([
            "python", "-m", "http.server", str(args.port),
            "--bind", args.host
        ])
    except KeyboardInterrupt:
        console.print("\n[bold green]Documentation server stopped.[/bold green]")
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")

if __name__ == "__main__":
    main()
