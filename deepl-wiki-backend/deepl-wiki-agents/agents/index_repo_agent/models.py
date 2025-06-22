"""
Data models for the Index Repository Agent.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, TypedDict, Set, Union

@dataclass
class ASTAnalysis:
    """Container for AST analysis results."""
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    imports: Dict[str, Any] = field(default_factory=dict)
    apis: List[Dict[str, Any]] = field(default_factory=list)
    configs: List[Dict[str, Any]] = field(default_factory=list)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentationSection:
    """Represents a section within a documentation folder."""
    name: str
    title: str
    description: str
    content: str = ""
    subsections: List['DocumentationSection'] = field(default_factory=list)

@dataclass
class DocumentationFolder:
    """Represents a documentation folder with multiple sections."""
    name: str
    title: str
    description: str
    sections: List[DocumentationSection] = field(default_factory=list)

@dataclass
class DocumentationStructure:
    """Complete documentation structure for a repository."""
    readme: str
    folders: List[DocumentationFolder] = field(default_factory=list)

class IndexState(TypedDict):
    """Enhanced state for the index agent."""
    repo_paths: List[str]
    current_repo_index: int
    current_repo_path: str
    repo_files: List[Dict[str, Any]]
    ast_analysis: Dict[str, ASTAnalysis]
    generated_docs: Dict[str, str]
    documentation_structure: Optional[DocumentationStructure]
    current_folder_index: int
    current_section_index: int
    repo_metadata: Dict[str, Any]
    all_docs: List[Dict[str, Any]]
    general_memo: str
    success: bool
    error: Optional[str]
    output_dir: Optional[str]
