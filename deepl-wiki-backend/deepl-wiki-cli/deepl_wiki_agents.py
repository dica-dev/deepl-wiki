"""Compatibility wrapper to match the running guide command format."""

import sys
import subprocess
from pathlib import Path


def main():
    """Forward commands to the CLI module."""
    # Get the CLI directory
    cli_dir = Path(__file__).parent
    
    # Forward all arguments to the CLI module
    cmd = [sys.executable, "-m", "cli"] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, cwd=cli_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running CLI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
