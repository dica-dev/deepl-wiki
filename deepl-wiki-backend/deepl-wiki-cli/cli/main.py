"""Main CLI entry point for deepl-wiki agents."""

import sys
import os
from pathlib import Path
import click
from dotenv import load_dotenv
from rich.console import Console

# Add the agents directory to the path
AGENTS_DIR = Path(__file__).parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))

from .commands import (
    repository_commands,
    chat_commands,
    index_commands,
    stats_commands,
    demo_commands,
    push_commands
)
from .utils.config import load_environment_config
from .utils.validation import validate_environment


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', help='Path to configuration file')
@click.pass_context
def cli(ctx, verbose, config):
    """DeepL Wiki Agents CLI - Interactive documentation management system."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    
    # Load environment configuration
    load_environment_config(config)
    
    # Validate environment
    if not validate_environment():
        console = Console()
        console.print("[red]Environment validation failed. Please check your configuration.[/red]")
        sys.exit(1)


# Add command groups
cli.add_command(repository_commands.repositories)
cli.add_command(chat_commands.chat)
cli.add_command(index_commands.index)
cli.add_command(stats_commands.stats)
cli.add_command(stats_commands.health)
cli.add_command(demo_commands.demo)
cli.add_command(push_commands.push)

# Add direct commands for convenience
cli.add_command(repository_commands.list_repositories, name='list')
cli.add_command(repository_commands.add_repositories, name='add')


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")
        if os.environ.get('DEBUG'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
