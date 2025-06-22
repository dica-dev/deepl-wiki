"""Test the CLI installation and basic functionality."""

import subprocess
import sys
from pathlib import Path


def test_cli_installation():
    """Test that the CLI can be imported and shows help."""
    try:
        # Test import
        sys.path.insert(0, str(Path(__file__).parent))
        from cli.main import main
        
        print("✓ CLI module imports successfully")
        return True
    except ImportError as e:
        print(f"✗ CLI import failed: {e}")
        return False


def test_cli_help():
    """Test CLI help command."""
    try:
        result = subprocess.run([
            sys.executable, "-m", "cli.main", "--help"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0 and "DeepL Wiki Agents CLI" in result.stdout:
            print("✓ CLI help command works")
            return True
        else:
            print(f"✗ CLI help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ CLI help test error: {e}")
        return False


def test_environment():
    """Test environment setup."""
    import os
    
    if os.environ.get("LLAMA_API_KEY"):
        print("✓ LLAMA_API_KEY is set")
        return True
    else:
        print("⚠ LLAMA_API_KEY not set (required for full functionality)")
        return False


def main():
    """Run all tests."""
    print("Testing DeepL Wiki CLI...")
    print("=" * 30)
    
    tests = [
        test_cli_installation,
        test_cli_help,
        test_environment,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed! CLI is ready to use.")
    else:
        print("⚠ Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
