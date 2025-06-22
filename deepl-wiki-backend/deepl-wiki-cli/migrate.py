"""Migration guide and helper for transitioning to the new CLI structure."""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def show_migration_guide():
    """Show migration guide from old CLI to new CLI."""
    console = Console()
    
    console.print(Panel(
        "[bold]DeepL Wiki CLI Migration Guide[/bold]\n\n"
        "The CLI has been restructured for better modularity and maintainability.",
        title="Migration Guide",
        expand=False
    ))
    
    # Command mapping table
    table = Table(title="Command Changes")
    table.add_column("Old Command", style="red")
    table.add_column("New Command", style="green")
    table.add_column("Notes", style="blue")
    
    mappings = [
        ("python -m deepl_wiki_agents list", "deepl-wiki repositories list", "Repository management grouped"),
        ("python -m deepl_wiki_agents add", "deepl-wiki repositories add", "Repository management grouped"),
        ("python -m deepl_wiki_agents chat", "deepl-wiki chat", "Same functionality, cleaner command"),
        ("python -m deepl_wiki_agents index", "deepl-wiki index", "Same functionality, cleaner command"),
        ("python -m deepl_wiki_agents push", "deepl-wiki push", "Same functionality, cleaner command"),
        ("python -m deepl_wiki_agents stats", "deepl-wiki stats", "Same functionality, cleaner command"),
        ("python -m deepl_wiki_agents serve", "deepl-wiki server web", "Server commands grouped"),
        ("python -m deepl_wiki_agents serve-docs", "deepl-wiki server docs", "Server commands grouped"),
        ("python -m deepl_wiki_agents demo", "deepl-wiki demo", "Same functionality, cleaner command"),
        ("N/A", "deepl-wiki health", "New health check command"),
    ]
    
    for old, new, notes in mappings:
        table.add_row(old, new, notes)
    
    console.print(table)
    
    # Installation instructions
    install_panel = Panel(
        "[bold cyan]Installation Steps:[/bold cyan]\n\n"
        "1. Navigate to the CLI directory:\n"
        "   [blue]cd deepl-wiki-cli[/blue]\n\n"
        "2. Install the CLI package:\n"
        "   [blue]pip install -e .[/blue]\n\n"
        "3. Test the installation:\n"
        "   [blue]deepl-wiki --help[/blue]\n\n"
        "4. Copy your environment variables:\n"
        "   [blue]cp ../.env .env[/blue]  (if you have an existing .env)\n\n"
        "[green]The new CLI maintains full compatibility with the agents![/green]",
        title="Installation",
        expand=False
    )
    
    console.print(install_panel)
    
    # Benefits panel
    benefits_panel = Panel(
        "[bold cyan]Benefits of the New CLI:[/bold cyan]\n\n"
        "• [green]Modular Architecture:[/green] Commands organized by functionality\n"
        "• [green]Better Error Handling:[/green] Comprehensive validation and user-friendly messages\n"
        "• [green]Rich Output:[/green] Colorful, formatted terminal output\n"
        "• [green]Extensibility:[/green] Easy to add new commands and features\n"
        "• [green]Health Checks:[/green] Built-in system validation\n"
        "• [green]Flexible Configuration:[/green] Support for custom config files\n"
        "• [green]Better Help:[/green] Comprehensive help for all commands",
        title="Benefits",
        expand=False
    )
    
    console.print(benefits_panel)


def check_old_cli():
    """Check if old CLI structure exists."""
    console = Console()
    agents_dir = Path(__file__).parent.parent / "deepl-wiki-agents"
    old_cli = agents_dir / "agents" / "cli.py"
    
    if old_cli.exists():
        console.print(f"[yellow]Found old CLI at: {old_cli}[/yellow]")
        console.print("[dim]The old CLI will continue to work, but consider migrating to the new structure.[/dim]")
        return True
    else:
        console.print("[green]Old CLI structure not found.[/green]")
        return False


def main():
    """Main migration guide."""
    console = Console()
    
    console.print("[bold]DeepL Wiki CLI Migration[/bold]")
    console.print("=" * 40)
    
    # Check for old CLI
    check_old_cli()
    console.print()
    
    # Show migration guide
    show_migration_guide()
    
    console.print("\n[bold green]Ready to get started with the new CLI![/bold green]")
    console.print("[dim]Run 'python test_cli.py' to test your installation.[/dim]")


if __name__ == "__main__":
    main()
