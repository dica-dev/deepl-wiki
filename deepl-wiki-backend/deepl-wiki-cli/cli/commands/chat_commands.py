"""Chat commands for interactive conversations."""

import sys
import uuid
from pathlib import Path
import click
from rich.console import Console

# Add agents to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))


@click.command()
@click.option('--query', '-q', help='Single query mode')
@click.option('--session', '-s', help='Chat session ID')
@click.option('--history', is_flag=True, help='Show conversation history')
def chat(query, session, history):
    """Start interactive chat with the documentation system."""
    console = Console()
    
    try:
        from agents.chat_agent import ChatAgent
        from agents.shared.database import DatabaseManager
        
        db = DatabaseManager()
        
        # Generate or use provided session ID
        session_id = session if session else str(uuid.uuid4())[:8]
        
        if history:
            # Show conversation history
            db_history = db.get_chat_history(session_id, limit=50)
            if db_history:
                console.print(f"[bold]Chat History (Session: {session_id})[/bold]")
                console.print("=" * 50)
                for msg in db_history:
                    role_color = "cyan" if msg["role"] == "user" else "magenta"
                    console.print(f"[bold {role_color}]{msg['role'].title()}:[/bold {role_color}] {msg['content']}")
                    console.print()
            else:
                console.print(f"[yellow]No chat history found for session: {session_id}[/yellow]")
            return
        
        console.print(f"[bold green]Initializing Chat Agent...[/bold green]")
        console.print(f"[dim]Session ID: {session_id}[/dim]")
        
        agent = ChatAgent()
        
        if query:
            # Single query mode
            result = agent.chat(query)
            console.print(f"\n[bold]Query:[/bold] {query}")
            console.print(f"[bold]Response:[/bold] {result['response']}")
            
            # Save to database
            db.add_chat_message(session_id, "user", query)
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
                    user_query = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                    if user_query.lower() in ['quit', 'exit', 'q']:
                        console.print("[bold green]Goodbye![/bold green]")
                        break
                    
                    if not user_query:
                        continue
                    
                    # Show thinking indicator
                    with console.status("[bold green]Thinking..."):
                        result = agent.chat(user_query, conversation_history)
                    
                    console.print(f"[bold magenta]Assistant:[/bold magenta] {result['response']}")
                    
                    # Save to database
                    db.add_chat_message(session_id, "user", user_query)
                    db.add_chat_message(session_id, "assistant", result['response'])
                    
                    # Update conversation history
                    conversation_history.append({"role": "user", "content": user_query})
                    conversation_history.append({"role": "assistant", "content": result['response']})
                    
                    if len(conversation_history) > 20:
                        conversation_history = conversation_history[-20:]
                    
                    if result.get('error'):
                        console.print(f"[yellow]Warning: {result['error']}[/yellow]")
                        
                except EOFError:
                    console.print("\n[bold green]Goodbye![/bold green]")
                    break
    
    except Exception as e:
        console.print(f"[red]Error in chat: {e}[/red]")
        raise click.ClickException(str(e))
