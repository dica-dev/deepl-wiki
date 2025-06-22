#!/usr/bin/env python3
"""Demo script showing CLI functionality according to running guide."""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a CLI command and show results."""
    print(f"\n{'='*50}")
    print(f"🚀 {description}")
    print(f"{'='*50}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        # Change to CLI directory
        cli_dir = Path(__file__).parent
        
        result = subprocess.run(
            cmd.split(),
            cwd=cli_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    """Test CLI commands from the running guide."""
    print("🧪 DeepL Wiki CLI - Running Guide Commands Test")
    print("This tests the commands mentioned in RUNNING_GUIDE.md")
    
    # Check environment
    if not os.environ.get("LLAMA_API_KEY"):
        print("\n⚠️  WARNING: LLAMA_API_KEY not set!")
        print("Some commands may fail. Set it with:")
        print("export LLAMA_API_KEY='your-api-key'")
    
    # Test commands from running guide (excluding server commands)
    commands = [
        ("python -m cli --help", "Show main help"),
        ("python -m cli repositories --help", "Show repositories help"),
        ("python -m cli chat --help", "Show chat help"),  
        ("python -m cli index --help", "Show index help"),
        ("python -m cli stats --help", "Show stats help"),
        ("python -m cli health", "Check system health"),
        ("python -m cli demo --help", "Show demo help"),
        ("python -m cli push --help", "Show push help"),
    ]
    
    # If LLAMA_API_KEY is set, test more commands
    if os.environ.get("LLAMA_API_KEY"):
        commands.extend([
            ("python -m cli repositories list", "List repositories (should be empty initially)"),
            ("python -m cli stats", "Show database statistics"),
        ])
    
    passed = 0
    total = len(commands)
    
    for cmd, desc in commands:
        success = run_command(cmd, desc)
        if success:
            passed += 1
            print("✅ PASSED")
        else:
            print("❌ FAILED")
    
    print(f"\n{'='*50}")
    print(f"📊 RESULTS: {passed}/{total} commands passed")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 All CLI commands are working!")
        print("\nNext steps from RUNNING_GUIDE.md:")
        print("1. Set LLAMA_API_KEY environment variable")
        print("2. Add repositories: python -m cli repositories add /path/to/repo")
        print("3. Index repositories: python -m cli index")
        print("4. Start chatting: python -m cli chat")
    else:
        print("⚠️  Some commands failed. Check the output above.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
