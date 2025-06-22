"""Server commands for web interfaces."""

import sys
import os
import subprocess
from pathlib import Path
import click
from rich.console import Console

# Add agents to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))


@click.group()
def server():
    """Start various server interfaces."""
    pass


@server.command('web')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', type=int, default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def web_server(host, port, reload):
    """Start the web interface using FastAPI."""
    console = Console()
    
    try:
        import uvicorn
        
        console.print(f"[bold green]Starting DeepL Wiki web interface...[/bold green]")
        console.print(f"[blue]Server: http://{host}:{port}[/blue]")
        
        # Create a simple FastAPI app if it doesn't exist
        _create_simple_web_app()
        
        uvicorn.run(
            "deepl_wiki_agents.simple_web:app",
            host=host,
            port=port,
            reload=reload
        )
        
    except ImportError:
        console.print("[red]Error: uvicorn not installed. Install with: pip install uvicorn[/red]")
        raise click.ClickException("Missing dependency: uvicorn")
    except Exception as e:
        console.print(f"[red]Error starting web server: {e}[/red]")
        raise click.ClickException(str(e))


@server.command('docs')
@click.option('--path', required=True, help='Path to documentation directory')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', type=int, default=8080, help='Port to bind to')
def docs_server(path, host, port):
    """Serve generated documentation with a simple HTTP server."""
    console = Console()
    docs_path = Path(path)
    
    if not docs_path.exists():
        console.print(f"[red]Error: Documentation path does not exist: {path}[/red]")
        raise click.ClickException(f"Path not found: {path}")
    
    if not docs_path.is_dir():
        console.print(f"[red]Error: Path is not a directory: {path}[/red]")
        raise click.ClickException(f"Not a directory: {path}")
    
    console.print(f"[bold green]Serving documentation from: {docs_path}[/bold green]")
    console.print(f"[blue]Documentation server: http://{host}:{port}[/blue]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")
    
    try:
        # Change to docs directory and start server
        original_cwd = os.getcwd()
        os.chdir(docs_path)
        
        subprocess.run([
            "python", "-m", "http.server", str(port),
            "--bind", host
        ])
        
    except KeyboardInterrupt:
        console.print("\n[bold green]Documentation server stopped.[/bold green]")
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        raise click.ClickException(str(e))
    finally:
        if 'original_cwd' in locals():
            os.chdir(original_cwd)


def _create_simple_web_app():
    """Create a simple web app file."""
    web_app_content = '''"""Simple FastAPI web application for DeepL Wiki Agents."""

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
deepl-wiki repositories add /path/to/repo1 /path/to/repo2<br><br>

# Index repositories<br>
deepl-wiki index<br><br>

# Start chatting<br>
deepl-wiki chat
                </div>
            </div>
            
            <div class="feature">
                <h3>📋 CLI Commands</h3>
                <ul>
                    <li><code>repositories list</code> - Show tracked repositories</li>
                    <li><code>repositories add</code> - Add repositories for tracking</li>
                    <li><code>index</code> - Index repositories and generate docs</li>
                    <li><code>chat</code> - Interactive chat with documentation</li>
                    <li><code>stats</code> - Show database statistics</li>
                    <li><code>server web</code> - Start web interface</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
'''
    
    agents_dir = Path(__file__).parent.parent.parent.parent / "deepl-wiki-agents"
    web_app_path = agents_dir / "deepl_wiki_agents" / "simple_web.py"
    
    # Create directory if it doesn't exist
    web_app_path.parent.mkdir(exist_ok=True)
    
    with open(web_app_path, "w") as f:
        f.write(web_app_content)
