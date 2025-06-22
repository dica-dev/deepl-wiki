"""Setup script for DeepL Wiki CLI."""

from setuptools import setup, find_packages

setup(
    name="deepl-wiki-cli",
    version="1.0.0",
    description="Command-line interface for DeepL Wiki Agents",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "click>=8.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
        "uvicorn>=0.20.0",
        "fastapi>=0.95.0",
    ],    entry_points={
        "console_scripts": [
            "deepl-wiki=cli.main:main",
        ],
    },
    python_requires=">=3.8",
)
