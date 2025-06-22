"""
Enhanced Index Repository Agent Module

A modular system for indexing repositories and generating comprehensive documentation
with intelligent structure analysis, visual diagrams, examples, and multi-language AST support.
"""

from .main import IndexRepoAgent
from .ast_analyzer import ASTAnalyzer
from .documentation_generator import DocumentationGenerator
from .intelligent_structure_analyzer import IntelligentStructureAnalyzer
from .diagram_generator import DiagramGenerator
from .example_extractor import ExampleExtractor
from .gitignore_parser import GitignoreParser
from .models import (
    ASTAnalysis,
    DocumentationSection,
    DocumentationFolder,
    DocumentationStructure,
    IndexState
)

__all__ = [
    'IndexRepoAgent',
    'ASTAnalyzer', 
    'DocumentationGenerator',
    'IntelligentStructureAnalyzer',
    'DiagramGenerator',
    'ExampleExtractor',
    'GitignoreParser',
    'ASTAnalysis',
    'DocumentationSection',
    'DocumentationFolder',
    'DocumentationStructure',
    'IndexState'
]

__version__ = "3.0.0"
