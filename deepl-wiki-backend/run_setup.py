#!/usr/bin/env python3
"""
DeepL Wiki Backend Setup Script

This script sets up the complete DeepL Wiki backend environment.
Run this after cloning the repository to get everything ready.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print("❌ Python 3.8+ is required")
            return False
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} found")
    except Exception as e:
        print(f"❌ Error checking Python version: {e}")
        return False
    
    # Check uv
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv found: {result.stdout.strip()}")
        else:
            print("❌ uv not found. Please install uv first:")
            print("Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
            print("Unix: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
    except FileNotFoundError:
        print("❌ uv not found. Please install uv first:")
        print("Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        print("Unix: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    return True


def setup_environment():
    """Set up the Python environment and install dependencies."""
    print("\n📦 Setting up Python environment...")
    
    # Create virtual environment
    if not run_command("uv venv", "Creating virtual environment"):
        print("❌ Failed to create virtual environment")
        return False
    
    # Install dependencies from requirements.txt
    if not run_command("uv pip install -r requirements.txt", "Installing dependencies from requirements.txt"):
        print("❌ Failed to install dependencies")
        return False
    
    return True


def install_cli():
    """Install the CLI package in development mode."""
    print("\n🔧 Installing CLI package...")
    
    # Check if we're in a virtual environment or use uv pip
    cli_path = Path("deepl-wiki-cli")
    if not cli_path.exists():
        print("❌ CLI directory not found")
        return False
    
    if not run_command("uv pip install -e ./deepl-wiki-cli", "Installing CLI package in development mode"):
        print("❌ Failed to install CLI package")
        return False
    
    return True


def create_env_file():
    """Create a .env file template if it doesn't exist."""
    print("\n⚙️ Setting up environment configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_template = """# DeepL Wiki Configuration
# Copy this file to .env and fill in your values

# Required: OpenAI API Key for AI functionality
OPENAI_API_KEY=your_openai_api_key_here

# Optional: GitHub token for repository integration
GITHUB_TOKEN=your_github_token_here

# Optional: Development settings
DEBUG=true
LOG_LEVEL=INFO

# Optional: API settings
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Database settings
DATABASE_URL=sqlite:///./deepl-wiki-agents/deepl_wiki.db
CHROMA_DB_PATH=./deepl-wiki-agents/chroma_db
"""
    
    try:
        env_file.write_text(env_template)
        print("✅ Created .env template file")
        print("⚠️ Please edit .env and add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def verify_installation():
    """Verify that everything is installed correctly."""
    print("\n🧪 Verifying installation...")
    
    # Test CLI
    if run_command("uv run deepl-wiki --help", "Testing CLI installation"):
        print("✅ CLI is working correctly")
    else:
        print("❌ CLI test failed")
        return False
    
    # Test API imports
    try:
        # Add current directory to path for testing
        sys.path.insert(0, str(Path.cwd()))
        from api.main import app
        print("✅ API imports are working correctly")
    except ImportError as e:
        print(f"⚠️ API imports have some issues (this is normal if agents aren't set up): {e}")
    
    return True


def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\n📝 Next steps:")
    print("\n1. Configure your environment:")
    print("   - Edit the .env file and add your OpenAI API key")
    print("   - Optionally add GitHub token for repository integration")
    
    print("\n2. Activate the virtual environment:")
    if platform.system() == "Windows":
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    
    print("\n3. Test the CLI:")
    print("   deepl-wiki --help")
    print("   deepl-wiki health")
    
    print("\n4. Run the API server:")
    print("   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
    
    print("\n5. Access the API documentation:")
    print("   http://localhost:8000/docs")
    print("   http://localhost:8000/redoc")
    
    print("\n📚 Available commands:")
    print("   deepl-wiki list           # List repositories")
    print("   deepl-wiki add <path>     # Add repository")
    print("   deepl-wiki index          # Index repositories")
    print("   deepl-wiki chat           # Start chat")
    print("   deepl-wiki demo           # Run demo")
    
    print("\n🔗 API Routes:")
    print("   GET  /api/v1/health           # Health check")
    print("   POST /api/v1/chat             # Chat with agents")
    print("   GET  /api/v1/repositories     # List repositories")
    print("   POST /api/v1/repositories     # Add repository")
    print("   GET  /api/v1/files/mono-repo  # Get file structure")
    
    print("\n📖 For detailed API documentation, see:")
    print("   README.md")
    print("   API_DOCUMENTATION.md")


def main():
    """Main setup function."""
    print("🚀 DeepL Wiki Backend Setup")
    print("="*40)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Set up environment
    if not setup_environment():
        sys.exit(1)
    
    # Install CLI
    if not install_cli():
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("⚠️ Some verification steps failed, but setup may still be functional")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
