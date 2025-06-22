"""Enhanced Index repository agent with AST integration for comprehensive documentation generation."""

import os
import ast
import json
import logging
import subprocess
import fnmatch
from typing import Dict, List, Any, Optional, TypedDict, Set, Union
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import git
from git import Repo
from langgraph.graph import StateGraph, END

from .shared.llama_client import LlamaClient
from .shared.chroma_manager import ChromaManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitignoreParser:
    """Parser for .gitignore files to filter out ignored files."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.patterns = []
        self._load_gitignore_patterns()
    
    def _load_gitignore_patterns(self):
        """Load patterns from .gitignore files."""
        gitignore_files = [
            self.repo_path / ".gitignore",
            self.repo_path / ".git" / "info" / "exclude"
        ]
        
        # Also check for global gitignore
        try:
            global_gitignore = os.path.expanduser("~/.gitignore_global")
            if os.path.exists(global_gitignore):
                gitignore_files.append(Path(global_gitignore))
        except Exception:
            pass
        
        for gitignore_file in gitignore_files:
            if gitignore_file.exists():
                try:
                    with open(gitignore_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                self.patterns.append(self._normalize_pattern(line))
                except Exception as e:
                    logger.warning(f"Failed to read gitignore file {gitignore_file}: {str(e)}")
    
    def _normalize_pattern(self, pattern: str) -> Dict[str, Any]:
        """Normalize gitignore pattern for matching."""
        original_pattern = pattern
        is_negation = pattern.startswith('!')
        if is_negation:
            pattern = pattern[1:]
        
        is_directory = pattern.endswith('/')
        if is_directory:
            pattern = pattern[:-1]
        
        # Handle absolute paths (starting with /)
        is_absolute = pattern.startswith('/')
        if is_absolute:
            pattern = pattern[1:]
        
        return {
            'pattern': pattern,
            'original': original_pattern,
            'is_negation': is_negation,
            'is_directory': is_directory,
            'is_absolute': is_absolute
        }
    
    def is_ignored(self, file_path: Path) -> bool:
        """Check if a file path should be ignored based on gitignore patterns."""
        try:
            relative_path = file_path.relative_to(self.repo_path)
            path_str = str(relative_path).replace('\\', '/')  # Normalize path separators
            
            # Quick check for common patterns first (performance optimization)
            if self._is_common_ignored_path(path_str):
                return True
            
            is_ignored = False
            
            for pattern_info in self.patterns:
                pattern = pattern_info['pattern']
                is_negation = pattern_info['is_negation']
                is_directory = pattern_info['is_directory']
                is_absolute = pattern_info['is_absolute']
                
                # Skip directory patterns for files and vice versa
                if is_directory and file_path.is_file():
                    continue
                if not is_directory and file_path.is_dir():
                    # For non-directory patterns, also match if it's a directory
                    pass
                
                matches = False
                
                if is_absolute:
                    # Absolute pattern - match from root
                    matches = fnmatch.fnmatch(path_str, pattern)
                else:
                    # Relative pattern - match any part of the path
                    path_parts = path_str.split('/')
                    for i in range(len(path_parts)):
                        subpath = '/'.join(path_parts[i:])
                        if fnmatch.fnmatch(subpath, pattern):
                            matches = True
                            break
                        
                        # Also check individual path components
                        if fnmatch.fnmatch(path_parts[i], pattern):
                            matches = True
                            break
                
                if matches:
                    if is_negation:
                        is_ignored = False  # Negation patterns un-ignore files
                    else:
                        is_ignored = True
            
            return is_ignored
        except ValueError:
            # File is not relative to repo_path, ignore it
            return True
    
    def _is_common_ignored_path(self, path_str: str) -> bool:
        """Quick check for commonly ignored paths for performance."""
        common_ignored = [
            'node_modules/', '__pycache__/', '.git/', '.svn/', '.hg/',
            'venv/', 'env/', '.env/', 'virtualenv/', '.venv/',
            'build/', 'dist/', 'target/', 'out/', '.next/', '.nuxt/',
            '.idea/', '.vscode/', '.vs/', '*.pyc', '*.pyo', '*.class',
            '*.o', '*.so', '*.dll', '*.exe', '*.bin', '*.jar', '*.war',
            '*.log', '*.tmp', '*.temp', '*.cache', '*.swp', '*.swo',
            '.DS_Store', 'Thumbs.db', '*.min.js', '*.min.css',
            'coverage/', '.coverage', '.nyc_output/', 'htmlcov/',
            '.pytest_cache/', '.tox/', '.mypy_cache/', '.ruff_cache/'
        ]
        
        for ignored in common_ignored:
            if ignored.endswith('/'):
                if ignored[:-1] in path_str.split('/'):
                    return True
            elif ignored.startswith('*.'):
                if path_str.endswith(ignored[1:]):
                    return True
            elif ignored in path_str:
                return True
        
        return False

@dataclass
class ASTAnalysis:
    """Container for AST analysis results."""
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: Dict[str, Any]
    apis: List[Dict[str, Any]]
    configs: List[Dict[str, Any]]
    complexity_metrics: Dict[str, Any]

class IndexState(TypedDict):
    """Enhanced state for the index agent."""
    repo_paths: List[str]
    current_repo_index: int
    current_repo_path: str
    repo_files: List[Dict[str, Any]]
    ast_analysis: Dict[str, ASTAnalysis]
    generated_docs: Dict[str, str]
    repo_metadata: Dict[str, Any] 
    all_docs: List[Dict[str, Any]]
    general_memo: str
    success: bool
    error: Optional[str]
    output_dir: Optional[str]

class ASTAnalyzer:
    """Multi-language AST analyzer for deep code understanding."""
    
    def __init__(self):
        self.supported_extensions = {
            '.py': self._analyze_python,
            '.js': self._analyze_javascript,
            '.ts': self._analyze_typescript,
            '.java': self._analyze_java,
            '.go': self._analyze_go,
            '.cpp': self._analyze_cpp,
            '.c': self._analyze_c
        }
    
    def analyze_file(self, file_path: str, content: str) -> Optional[ASTAnalysis]:
        """Analyze a file using appropriate AST parser."""
        ext = Path(file_path).suffix.lower()
        analyzer = self.supported_extensions.get(ext)
        
        if analyzer:
            try:
                return analyzer(file_path, content)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {str(e)}")
                return None
        return None
    
    def _analyze_python(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {str(e)}")
            return ASTAnalysis([], [], {}, [], [], {})
        
        functions = self._extract_python_functions(tree)
        classes = self._extract_python_classes(tree)
        imports = self._extract_python_imports(tree)
        apis = self._extract_python_apis(tree, file_path)
        configs = self._extract_python_configs(tree, content)
        complexity = self._calculate_python_complexity(tree)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _extract_python_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function information from Python AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    'name': node.name,
                    'line_number': node.lineno,
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'parameters': [],
                    'return_annotation': None,
                    'decorators': [],
                    'docstring': ast.get_docstring(node),
                    'complexity': self._calculate_function_complexity(node)
                }
                
                # Extract parameters
                for arg in node.args.args:
                    param_info = {'name': arg.arg}
                    if arg.annotation:
                        param_info['type'] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else 'annotated'
                    func_info['parameters'].append(param_info)
                
                # Extract return annotation
                if node.returns:
                    func_info['return_annotation'] = ast.unparse(node.returns) if hasattr(ast, 'unparse') else 'annotated'
                
                # Extract decorators
                for decorator in node.decorator_list:
                    if hasattr(decorator, 'id'):
                        func_info['decorators'].append(decorator.id)
                    elif hasattr(decorator, 'attr'):
                        func_info['decorators'].append(decorator.attr)
                
                functions.append(func_info)
        
        return functions
    
    def _extract_python_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class information from Python AST."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line_number': node.lineno,
                    'bases': [],
                    'methods': [],
                    'properties': [],
                    'docstring': ast.get_docstring(node),
                    'decorators': []
                }
                
                # Extract base classes
                for base in node.bases:
                    if hasattr(base, 'id'):
                        class_info['bases'].append(base.id)
                    elif hasattr(base, 'attr'):
                        class_info['bases'].append(base.attr)
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            'name': item.name,
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'is_property': any(d.id == 'property' for d in item.decorator_list if hasattr(d, 'id')),
                            'is_classmethod': any(d.id == 'classmethod' for d in item.decorator_list if hasattr(d, 'id')),
                            'is_staticmethod': any(d.id == 'staticmethod' for d in item.decorator_list if hasattr(d, 'id')),
                            'docstring': ast.get_docstring(item)
                        }
                        
                        if method_info['is_property']:
                            class_info['properties'].append(method_info)
                        else:
                            class_info['methods'].append(method_info)
                
                classes.append(class_info)
        
        return classes
    
    def _extract_python_imports(self, tree: ast.AST) -> Dict[str, Any]:
        """Extract import information from Python AST."""
        imports = {
            'standard_library': [],
            'third_party': [],
            'local': [],
            'from_imports': {}
        }
        
        stdlib_modules = {
            'os', 'sys', 'json', 'logging', 'pathlib', 'typing', 'dataclasses',
            'collections', 'itertools', 'functools', 'operator', 're', 'math',
            'datetime', 'time', 'random', 'uuid', 'hashlib', 'base64', 'urllib',
            'http', 'email', 'html', 'xml', 'sqlite3', 'csv', 'configparser'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in stdlib_modules:
                        imports['standard_library'].append(alias.name)
                    elif module_name.startswith('.'):
                        imports['local'].append(alias.name)
                    else:
                        imports['third_party'].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imported_names = [alias.name for alias in node.names]
                imports['from_imports'][module] = imported_names
                
                if module:
                    base_module = module.split('.')[0]
                    if base_module in stdlib_modules:
                        imports['standard_library'].extend([f"{module}.{name}" for name in imported_names])
                    elif module.startswith('.'):
                        imports['local'].extend([f"{module}.{name}" for name in imported_names])
                    else:
                        imports['third_party'].extend([f"{module}.{name}" for name in imported_names])
        
        return imports
    
    def _extract_python_apis(self, tree: ast.AST, file_path: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from Python code."""
        apis = []
        
        # Look for Flask/FastAPI route decorators
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if self._is_route_decorator(decorator):
                        api_info = {
                            'path': self._extract_route_path(decorator),
                            'method': self._extract_http_method(decorator),
                            'function': node.name,
                            'file': file_path,
                            'line': node.lineno,
                            'docstring': ast.get_docstring(node),
                            'parameters': [arg.arg for arg in node.args.args if arg.arg != 'self']
                        }
                        apis.append(api_info)
        
        return apis
    
    def _extract_python_configs(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Extract configuration patterns from Python code."""
        configs = []
        
        # Look for configuration classes or dictionaries
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and 'config' in node.name.lower():
                config_info = {
                    'type': 'class',
                    'name': node.name,
                    'line': node.lineno,
                    'attributes': []
                }
                
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if hasattr(target, 'id'):
                                config_info['attributes'].append(target.id)
                
                configs.append(config_info)
        
        return configs
    
    def _calculate_python_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """Calculate complexity metrics for Python code."""
        metrics = {
            'total_functions': 0,
            'total_classes': 0,
            'total_lines': 0,
            'cyclomatic_complexity': 0,
            'max_function_complexity': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics['total_functions'] += 1
                func_complexity = self._calculate_function_complexity(node)
                metrics['cyclomatic_complexity'] += func_complexity
                metrics['max_function_complexity'] = max(metrics['max_function_complexity'], func_complexity)
            elif isinstance(node, ast.ClassDef):
                metrics['total_classes'] += 1
        
        return metrics
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _is_route_decorator(self, decorator) -> bool:
        """Check if decorator is a route decorator."""
        if hasattr(decorator, 'attr'):
            return decorator.attr in ['route', 'get', 'post', 'put', 'delete', 'patch']
        elif hasattr(decorator, 'id'):
            return decorator.id in ['app', 'router']
        return False
    
    def _extract_route_path(self, decorator) -> str:
        """Extract route path from decorator."""
        if hasattr(decorator, 'args') and decorator.args:
            first_arg = decorator.args[0]
            if hasattr(first_arg, 's'):
                return first_arg.s
            elif hasattr(first_arg, 'value'):
                return first_arg.value
        return "/"
    
    def _extract_http_method(self, decorator) -> str:
        """Extract HTTP method from decorator."""
        if hasattr(decorator, 'attr'):
            method = decorator.attr.upper()
            if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                return method
        return "GET"
    
    def _analyze_javascript(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze JavaScript file (basic implementation)."""
        # For now, return empty analysis - can be enhanced with JS AST parser
        return ASTAnalysis([], [], {}, [], [], {})
    
    def _analyze_typescript(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze TypeScript file (basic implementation)."""
        # For now, return empty analysis - can be enhanced with TS AST parser
        return ASTAnalysis([], [], {}, [], [], {})
    
    def _analyze_java(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Java file (basic implementation)."""
        # For now, return empty analysis - can be enhanced with Java AST parser
        return ASTAnalysis([], [], {}, [], [], {})
    
    def _analyze_go(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Go file (basic implementation)."""
        # For now, return empty analysis - can be enhanced with Go AST parser
        return ASTAnalysis([], [], {}, [], [], {})
    
    def _analyze_cpp(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze C++ file (basic implementation)."""
        # For now, return empty analysis - can be enhanced with C++ AST parser
        return ASTAnalysis([], [], {}, [], [], {})
    
    def _analyze_c(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze C file (basic implementation)."""
        # For now, return empty analysis - can be enhanced with C AST parser
        return ASTAnalysis([], [], {}, [], [], {})

class DocumentationGenerator:
    """Generate structured documentation from AST analysis."""
    
    def __init__(self, llama_client: LlamaClient):
        self.llama_client = llama_client
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load documentation templates."""
        return {
            'readme': """# {repo_name}

{overview}

## Architecture

{architecture}

## Getting Started

{getting_started}

## API Documentation

{api_summary}

## Development

{development_info}
""",
            'api': """# API Documentation

## Overview
{overview}

## Endpoints

{endpoints}

## Authentication
{auth_info}

## Examples
{examples}
""",
            'architecture': """# Architecture Documentation

## System Overview
{overview}

## Components
{components}

## Data Flow
{data_flow}

## Dependencies
{dependencies}
""",
            'development': """# Development Guide

## Setup
{setup}

## Building
{building}

## Testing
{testing}

## Contributing
{contributing}
"""
        }
    
    def generate_documentation(
        self, 
        repo_path: str, 
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate comprehensive documentation."""
        
        docs = {}
        
        # Generate README
        docs['README.md'] = self._generate_readme(repo_path, repo_metadata, ast_analysis, file_contents)
        
        # Generate API documentation if APIs found
        if self._has_apis(ast_analysis):
            docs['API.md'] = self._generate_api_docs(repo_path, ast_analysis)
        
        # Generate architecture documentation
        docs['ARCHITECTURE.md'] = self._generate_architecture_docs(repo_path, ast_analysis, repo_metadata)
        
        # Generate development guide
        docs['DEVELOPMENT.md'] = self._generate_development_docs(repo_path, repo_metadata, ast_analysis)
        
        # Generate component documentation
        docs['COMPONENTS.md'] = self._generate_component_docs(repo_path, ast_analysis)
        
        return docs
    
    def _generate_readme(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Generate focused README for project overview and getting started."""
        
        repo_name = Path(repo_path).name
        
        # Prepare focused context for README
        context = self._prepare_readme_context(repo_path, repo_metadata, ast_analysis, file_contents)
        
        prompt = f"""You are a technical documentation expert. Generate a focused README.md for the repository: {repo_name}

IMPORTANT: Create a concise, user-focused README that helps users understand what this project is and how to get started. Do NOT include detailed API documentation, architecture details, or component lists - those belong in separate files.

Repository Context:
{context}

Create a professional README that includes ONLY:

1. **Project Title and Brief Description**: 1-2 sentences explaining what this project does
2. **Key Features**: 3-5 bullet points of main functionality (high-level, not technical details)
3. **Installation & Setup**: Step-by-step installation instructions with prerequisites
4. **Quick Start**: Basic usage example to get users started immediately
5. **Configuration**: Essential configuration options users need to know
6. **Links to Other Documentation**: References to ARCHITECTURE.md, API.md, DEVELOPMENT.md, etc.

REQUIREMENTS:
- Keep it concise and user-focused
- Focus on getting users started quickly
- Avoid technical implementation details
- Maximum 100 lines
- Include actual project-specific information, not generic templates
- Reference other documentation files for detailed information

README Content:"""

        try:
            readme_content = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000
            )
            return readme_content
        except Exception as e:
            return f"# {repo_name}\n\nFailed to generate README: {str(e)}"
    
    def _generate_api_docs(self, repo_path: str, ast_analysis: Dict[str, ASTAnalysis]) -> str:
        """Generate API documentation."""
        
        all_apis = []
        for file_path, analysis in ast_analysis.items():
            all_apis.extend(analysis.apis)
        
        if not all_apis:
            return "# API Documentation\n\nNo API endpoints found in this repository."
        
        endpoints_table = "| Method | Path | Function | Description |\n|--------|------|----------|-------------|\n"
        detailed_endpoints = ""
        
        for api in all_apis:
            endpoints_table += f"| {api['method']} | {api['path']} | {api['function']} | {api.get('docstring', 'No description')} |\n"
            
            detailed_endpoints += f"""
## {api['method']} {api['path']}

**Function:** `{api['function']}`
**File:** {api['file']}:{api['line']}

{api.get('docstring', 'No description available.')}

**Parameters:**
{', '.join(api.get('parameters', [])) if api.get('parameters') else 'None'}

---
"""
        
        return self.templates['api'].format(
            overview="This document describes the API endpoints available in this repository.",
            endpoints=endpoints_table + "\n" + detailed_endpoints,
            auth_info="Authentication information not detected automatically. Please refer to the code for details.",
            examples="Please refer to the individual endpoint documentation above for usage examples."
        )
    
    def _generate_architecture_docs(
        self,
        repo_path: str,
        ast_analysis: Dict[str, ASTAnalysis],
        repo_metadata: Dict[str, Any]
    ) -> str:
        """Generate focused architecture documentation."""
        
        repo_name = Path(repo_path).name
        
        # Prepare architecture-focused context
        context = self._prepare_architecture_context(repo_path, repo_metadata, ast_analysis)
        
        prompt = f"""You are a software architect. Generate focused architecture documentation for: {repo_name}

IMPORTANT: Create architecture documentation that explains the system design, not detailed code listings. Focus on high-level structure, patterns, and relationships.

Repository Context:
{context}

Create architecture documentation that includes:

1. **System Overview**: High-level description of the system architecture and design patterns used
2. **Core Components**: Main architectural components and their responsibilities (not individual classes)
3. **Data Flow**: How data moves through the system
4. **Technology Stack**: Key technologies, frameworks, and libraries used
5. **Design Patterns**: Architectural patterns and design decisions
6. **Integration Points**: How different parts of the system interact

REQUIREMENTS:
- Focus on architecture and design, not implementation details
- Explain the "why" behind architectural decisions
- Use diagrams or ASCII art where helpful
- Keep it focused on system design
- Maximum 150 lines
- Avoid listing every single class and function

Architecture Documentation:"""

        try:
            arch_content = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            return arch_content
        except Exception as e:
            return f"# Architecture Documentation\n\nFailed to generate architecture docs: {str(e)}"
    
    def _generate_development_docs(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis]
    ) -> str:
        """Generate comprehensive development documentation."""
        
        repo_name = Path(repo_path).name
        
        # Prepare development-focused context
        context = self._prepare_development_context(repo_path, repo_metadata, ast_analysis)
        
        prompt = f"""You are a development team lead. Generate comprehensive development documentation for: {repo_name}

IMPORTANT: Create practical development documentation that helps developers contribute to this project. Focus on setup, workflows, and development practices.

Repository Context:
{context}

Create development documentation that includes:

1. **Development Setup**: Detailed setup instructions for developers
2. **Project Structure**: Explanation of how the codebase is organized
3. **Development Workflow**: How to develop, test, and contribute
4. **Build Process**: How to build and run the project
5. **Testing**: How to run tests and add new tests
6. **Code Standards**: Coding conventions and best practices
7. **Debugging**: How to debug and troubleshoot issues
8. **Contributing**: Guidelines for contributing to the project

REQUIREMENTS:
- Provide specific, actionable instructions
- Include actual commands and file paths where relevant
- Focus on developer productivity
- Include troubleshooting tips
- Maximum 200 lines
- Be practical and developer-focused

Development Guide:"""

        try:
            dev_content = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000
            )
            return dev_content
        except Exception as e:
            return f"# Development Guide\n\nFailed to generate development docs: {str(e)}"
    
    def _generate_component_docs(self, repo_path: str, ast_analysis: Dict[str, ASTAnalysis]) -> str:
        """Generate detailed component documentation."""
        
        content = f"# Component Documentation\n\n"
        
        for file_path, analysis in ast_analysis.items():
            if analysis.classes or analysis.functions:
                content += f"## {file_path}\n\n"
                
                if analysis.classes:
                    content += "### Classes\n\n"
                    for cls in analysis.classes:
                        content += f"#### {cls['name']}\n"
                        if cls.get('docstring'):
                            content += f"{cls['docstring']}\n\n"
                        
                        if cls.get('bases'):
                            content += f"**Inherits from:** {', '.join(cls['bases'])}\n\n"
                        
                        if cls.get('methods'):
                            content += "**Methods:**\n"
                            for method in cls['methods']:
                                content += f"- `{method['name']}()`: {method.get('docstring', 'No description')}\n"
                            content += "\n"
                
                if analysis.functions:
                    content += "### Functions\n\n"
                    for func in analysis.functions:
                        content += f"#### {func['name']}()\n"
                        if func.get('docstring'):
                            content += f"{func['docstring']}\n\n"
                        
                        if func.get('parameters'):
                            content += "**Parameters:**\n"
                            for param in func['parameters']:
                                param_type = param.get('type', 'Any')
                                content += f"- `{param['name']}` ({param_type})\n"
                            content += "\n"
                        
                        if func.get('return_annotation'):
                            content += f"**Returns:** {func['return_annotation']}\n\n"
                
                content += "---\n\n"
        
        return content
    
    def _has_apis(self, ast_analysis: Dict[str, ASTAnalysis]) -> bool:
        """Check if any APIs were found."""
        return any(analysis.apis for analysis in ast_analysis.values())
    
    def _prepare_context(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Prepare comprehensive context for AI generation."""
        
        repo_name = Path(repo_path).name
        context = f"""
# Repository Analysis: {repo_name}

## Basic Information
- **Repository**: {repo_name}
- **Primary Language**: {repo_metadata.get('primary_language', 'Unknown')}
- **Total Files**: {repo_metadata.get('file_count', 0)}
- **Total Size**: {repo_metadata.get('total_size', 0):,} bytes
- **Configuration Files**: {', '.join(repo_metadata.get('config_files', [])[:5])}

## Git Information
"""
        
        # Add Git information if available
        if repo_metadata.get('git_branch'):
            context += f"- **Branch**: {repo_metadata.get('git_branch')}\n"
        if repo_metadata.get('last_commit'):
            context += f"- **Last Commit**: {repo_metadata.get('last_commit')}\n"
        if repo_metadata.get('author'):
            context += f"- **Author**: {repo_metadata.get('author')}\n"
        
        # Add existing documentation content
        context += "\n## Existing Documentation\n"
        doc_files_found = False
        for file_info in file_contents:
            if file_info.get('extension') in ['.md', '.txt', '.rst']:
                doc_files_found = True
                context += f"\n### {file_info['path']}\n"
                context += f"```\n{file_info['content']}\n```\n"
        
        if not doc_files_found:
            context += "No existing documentation files found.\n"
        
        # Add detailed code analysis
        context += "\n## Code Structure Analysis\n"
        
        # Collect all components
        all_classes = []
        all_functions = []
        all_apis = []
        all_imports = {}
        
        for file_path, analysis in ast_analysis.items():
            all_classes.extend(analysis.classes)
            all_functions.extend(analysis.functions)
            all_apis.extend(analysis.apis)
            if analysis.imports:
                all_imports[file_path] = analysis.imports
        
        # Add class details
        if all_classes:
            context += f"\n### Classes ({len(all_classes)} total)\n"
            for cls in all_classes[:15]:  # Show more classes
                context += f"- **{cls['name']}**"
                if cls.get('bases'):
                    context += f" (extends {', '.join(cls['bases'])})"
                if cls.get('docstring'):
                    context += f": {cls['docstring'][:200]}..."
                context += f" [{cls.get('line_number', 'unknown')} lines]\n"
                
                # Add method details
                if cls.get('methods'):
                    methods = [m['name'] for m in cls['methods'][:5]]
                    context += f"  - Methods: {', '.join(methods)}\n"
        
        # Add function details
        if all_functions:
            context += f"\n### Functions ({len(all_functions)} total)\n"
            for func in all_functions[:15]:  # Show more functions
                context += f"- **{func['name']}()**"
                if func.get('parameters'):
                    params = [p['name'] for p in func['parameters'][:3]]
                    context += f" ({', '.join(params)}{'...' if len(func['parameters']) > 3 else ''})"
                if func.get('docstring'):
                    context += f": {func['docstring'][:150]}..."
                if func.get('complexity'):
                    context += f" [complexity: {func['complexity']}]"
                context += "\n"
        
        # Add API details
        if all_apis:
            context += f"\n### API Endpoints ({len(all_apis)} total)\n"
            for api in all_apis:
                context += f"- **{api['method']} {api['path']}** → {api['function']}()\n"
                if api.get('docstring'):
                    context += f"  - {api['docstring'][:100]}...\n"
        
        # Add dependency analysis
        if all_imports:
            context += "\n### Dependencies\n"
            all_third_party = set()
            all_standard = set()
            
            for file_imports in all_imports.values():
                all_third_party.update(file_imports.get('third_party', []))
                all_standard.update(file_imports.get('standard_library', []))
            
            if all_third_party:
                context += f"**Third-party libraries**: {', '.join(sorted(list(all_third_party)[:10]))}\n"
            if all_standard:
                context += f"**Standard library**: {', '.join(sorted(list(all_standard)[:10]))}\n"
        
        # Add file structure overview
        context += "\n## File Structure Overview\n"
        file_categories = repo_metadata.get('file_categories', {})
        context += f"- **Code files**: {file_categories.get('code', 0)}\n"
        context += f"- **Configuration files**: {file_categories.get('config', 0)}\n"
        context += f"- **Documentation files**: {file_categories.get('documentation', 0)}\n"
        context += f"- **Test files**: {file_categories.get('test', 0)}\n"
        
        # Add key file samples
        context += "\n## Key File Samples\n"
        for file_info in file_contents[:5]:  # Show first 5 files
            if file_info.get('extension') in ['.py', '.js', '.ts', '.java']:
                context += f"\n### {file_info['path']} ({file_info['size']} bytes)\n"
                context += f"```{file_info.get('extension', '').replace('.', '')}\n{file_info['content'][:1000]}...\n```\n"
        
        return context
    
    def _prepare_readme_context(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Prepare focused context for README generation."""
        
        repo_name = Path(repo_path).name
        context = f"""
# Repository: {repo_name}

## Basic Information
- **Primary Language**: {repo_metadata.get('primary_language', 'Unknown')}
- **Total Files**: {repo_metadata.get('file_count', 0)}
- **Configuration Files**: {', '.join(repo_metadata.get('config_files', [])[:3])}

## Key Features (from code analysis)
"""
        
        # Add key features based on APIs and main classes
        all_apis = []
        key_classes = []
        
        for file_path, analysis in ast_analysis.items():
            all_apis.extend(analysis.apis)
            # Get main classes (not utility classes)
            for cls in analysis.classes:
                if not any(word in cls['name'].lower() for word in ['util', 'helper', 'test']):
                    key_classes.append(cls['name'])
        
        if all_apis:
            context += f"- REST API with {len(all_apis)} endpoints\n"
        if key_classes:
            context += f"- Core components: {', '.join(key_classes[:5])}\n"
        
        # Add existing documentation content if available
        for file_info in file_contents:
            if file_info.get('extension') in ['.md', '.txt'] and 'readme' in file_info['path'].lower():
                context += f"\n## Existing README Content\n{file_info['content'][:500]}...\n"
                break
        
        return context
    
    def _prepare_architecture_context(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis]
    ) -> str:
        """Prepare architecture-focused context."""
        
        repo_name = Path(repo_path).name
        context = f"""
# Architecture Analysis: {repo_name}

## Technology Stack
- **Primary Language**: {repo_metadata.get('primary_language', 'Unknown')}
- **Configuration Files**: {', '.join(repo_metadata.get('config_files', []))}

## System Components
"""
        
        # Analyze architectural patterns
        all_classes = []
        all_apis = []
        patterns = set()
        
        for file_path, analysis in ast_analysis.items():
            all_classes.extend(analysis.classes)
            all_apis.extend(analysis.apis)
            
            # Detect patterns
            for cls in analysis.classes:
                name = cls['name'].lower()
                if 'manager' in name:
                    patterns.add('Manager Pattern')
                elif 'agent' in name:
                    patterns.add('Agent Pattern')
                elif 'client' in name:
                    patterns.add('Client Pattern')
                elif 'generator' in name:
                    patterns.add('Generator Pattern')
        
        context += f"- **Total Classes**: {len(all_classes)}\n"
        context += f"- **API Endpoints**: {len(all_apis)}\n"
        context += f"- **Design Patterns**: {', '.join(patterns) if patterns else 'Standard OOP'}\n"
        
        # Add key architectural components
        key_components = []
        for cls in all_classes:
            if any(word in cls['name'].lower() for word in ['manager', 'agent', 'client', 'generator', 'service']):
                key_components.append(cls['name'])
        
        if key_components:
            context += f"\n## Key Components\n"
            for comp in key_components[:10]:
                context += f"- {comp}\n"
        
        return context
    
    def _prepare_development_context(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis]
    ) -> str:
        """Prepare development-focused context."""
        
        repo_name = Path(repo_path).name
        context = f"""
# Development Context: {repo_name}

## Project Structure
- **Primary Language**: {repo_metadata.get('primary_language', 'Unknown')}
- **Total Files**: {repo_metadata.get('file_count', 0)}
- **Code Files**: {repo_metadata.get('code_files', 0)}
- **Test Files**: {repo_metadata.get('test_files', 0)}

## Configuration Files Found
{chr(10).join(f'- {config}' for config in repo_metadata.get('config_files', [])[:10])}

## Development Tools Detected
"""
        
        # Detect development tools from config files
        config_files = repo_metadata.get('config_files', [])
        tools = []
        
        for config in config_files:
            if 'requirements.txt' in config or 'pyproject.toml' in config:
                tools.append('Python pip/poetry')
            elif 'package.json' in config:
                tools.append('Node.js/npm')
            elif 'Dockerfile' in config:
                tools.append('Docker')
            elif 'Makefile' in config:
                tools.append('Make build system')
        
        if tools:
            context += '\n'.join(f'- {tool}' for tool in tools)
        else:
            context += '- Standard development setup'
        
        # Add complexity info
        total_functions = sum(len(analysis.functions) for analysis in ast_analysis.values())
        context += f"\n\n## Codebase Complexity\n"
        context += f"- **Total Functions**: {total_functions}\n"
        context += f"- **Total Classes**: {sum(len(analysis.classes) for analysis in ast_analysis.values())}\n"
        
        return context
    
    def _format_classes_list(self, classes: List[Dict[str, Any]]) -> str:
        """Format classes list for documentation."""
        if not classes:
            return "No classes found."
        
        result = ""
        for cls in classes:
            result += f"- **{cls['name']}**"
            if cls.get('bases'):
                result += f" (extends {', '.join(cls['bases'])})"
            if cls.get('docstring'):
                result += f": {cls['docstring'][:100]}..."
            result += "\n"
        
        return result
    
    def _format_functions_list(self, functions: List[Dict[str, Any]]) -> str:
        """Format functions list for documentation."""
        if not functions:
            return "No functions found."
        
        result = ""
        for func in functions:
            result += f"- **{func['name']}()**"
            if func.get('docstring'):
                result += f": {func['docstring'][:100]}..."
            result += "\n"
        
        return result
    
    def _format_dependencies(self, dependencies: Dict[str, Dict[str, Any]]) -> str:
        """Format dependencies for documentation."""
        all_third_party = set()
        all_standard = set()
        
        for file_deps in dependencies.values():
            all_third_party.update(file_deps.get('third_party', []))
            all_standard.update(file_deps.get('standard_library', []))
        
        result = ""
        if all_third_party:
            result += f"**Third-party libraries:** {', '.join(sorted(all_third_party))}\n\n"
        
        if all_standard:
            result += f"**Standard library modules:** {', '.join(sorted(all_standard))}\n\n"
        
        return result or "No external dependencies detected."

class IndexRepoAgent:
    """Enhanced LangGraph-based agent for indexing repositories with AST analysis."""
    
    def __init__(
        self,
        llama_client: Optional[LlamaClient] = None,
        chroma_manager: Optional[ChromaManager] = None,
        max_file_size: int = 100000,
        excluded_dirs: Optional[Set[str]] = None,
        excluded_extensions: Optional[Set[str]] = None,
        output_dir: Optional[str] = None,
        respect_gitignore: bool = True
    ):
        """Initialize enhanced index repository agent."""
        self.llama_client = llama_client or LlamaClient()
        self.chroma_manager = chroma_manager or ChromaManager()
        self.max_file_size = max_file_size
        self.output_dir = output_dir
        self.respect_gitignore = respect_gitignore
        self.gitignore_parser = None
        
        self.excluded_dirs = excluded_dirs or {
            ".git", ".svn", ".hg",
            "node_modules", "__pycache__", ".pytest_cache",
            "venv", "env", ".env", "virtualenv",
            "build", "dist", "target", "out",
            ".idea", ".vscode", ".vs"
        }
        
        self.excluded_extensions = excluded_extensions or {
            ".pyc", ".pyo", ".class", ".o", ".so", ".dll",
            ".exe", ".bin", ".jar", ".war",
            ".log", ".tmp", ".temp", ".cache",
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico",
            ".mp3", ".mp4", ".wav", ".avi", ".mov",
            ".zip", ".tar", ".gz", ".rar", ".7z"
        }
        
        self.ast_analyzer = ASTAnalyzer()
        self.doc_generator = DocumentationGenerator(self.llama_client)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the enhanced LangGraph workflow."""
        workflow = StateGraph(IndexState)
        
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("scan_repo", self._scan_repository)
        workflow.add_node("analyze_ast", self._analyze_with_ast)
        workflow.add_node("generate_docs", self._generate_documentation)
        workflow.add_node("store_docs", self._store_documentation)
        workflow.add_node("write_files", self._write_documentation_files)
        workflow.add_node("next_repo", self._next_repo)
        workflow.add_node("generate_general_memo", self._generate_general_memo)
        workflow.add_node("finalize", self._finalize)
        workflow.add_node("handle_error", self._handle_error)
        
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "scan_repo")
        workflow.add_edge("scan_repo", "analyze_ast")
        workflow.add_edge("analyze_ast", "generate_docs")
        workflow.add_edge("generate_docs", "write_files")
        workflow.add_edge("write_files", "store_docs")
        workflow.add_edge("store_docs", "next_repo")
        workflow.add_edge("generate_general_memo", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        workflow.add_conditional_edges(
            "next_repo",
            self._should_continue,
            {
                "continue": "scan_repo",
                "generate_general": "generate_general_memo",
                "error": "handle_error"
            }
        )
        
        return workflow.compile()
    
    def index_repositories(self, repo_paths: List[str], output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Index multiple repositories and generate comprehensive documentation."""
        initial_state = IndexState(
            repo_paths=repo_paths,
            current_repo_index=0,
            current_repo_path="",
            repo_files=[],
            ast_analysis={},
            generated_docs={},
            repo_metadata={},
            all_docs=[],
            general_memo="",
            success=False,
            error=None,
            output_dir=output_dir or self.output_dir
        )
        
        result = self.graph.invoke(initial_state)
        
        return {
            "success": result["success"],
            "error": result.get("error"),
            "individual_memos": result["all_docs"],  # Changed from individual_docs to individual_memos for CLI compatibility
            "general_memo": result["general_memo"],
            "total_repos": len(repo_paths),
            "output_dir": result.get("output_dir")
        }
    
    def _initialize(self, state: IndexState) -> IndexState:
        """Initialize the indexing process with validation."""
        logger.info("Initializing enhanced indexing process for %d repositories", len(state["repo_paths"]))
        
        new_state = state.copy()
        new_state.update({
            "current_repo_index": 0,
            "all_docs": [],
            "success": False,
            "error": None
        })
        
        return new_state
    
    def _scan_repository(self, state: IndexState) -> IndexState:
        """Scan the current repository for relevant files."""
        try:
            repo_paths = state["repo_paths"]
            current_index = state["current_repo_index"]
            
            if current_index >= len(repo_paths):
                new_state = state.copy()
                new_state["error"] = "Index out of bounds"
                return new_state
            
            repo_path = repo_paths[current_index]
            repo_path_obj = Path(repo_path)
            
            if not repo_path_obj.exists():
                new_state = state.copy()
                new_state["error"] = f"Repository path does not exist: {repo_path}"
                return new_state
            
            logger.info(f"Scanning repository: {repo_path}")
            
            repo_metadata = self._get_repo_metadata(repo_path)
            repo_files = self._scan_files(repo_path_obj)
            
            new_state = state.copy()
            new_state.update({
                "current_repo_path": repo_path,
                "repo_files": repo_files,
                "repo_metadata": repo_metadata
            })
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to scan repository: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to scan repository: {str(e)}"
            return new_state
    
    def _analyze_with_ast(self, state: IndexState) -> IndexState:
        """Perform parallel AST analysis on repository files."""
        try:
            repo_files = state["repo_files"]
            repo_path = state["current_repo_path"]
            
            # Filter files for AST analysis with more aggressive filtering
            analyzable_files = []
            for file_info in repo_files:
                if (file_info["size"] < self.max_file_size and
                    self._should_analyze_file(file_info)):
                    analyzable_files.append(file_info)
                    logger.info(f"✓ ACCEPTING for analysis: {file_info['relative_path']} ({file_info['size']} bytes, {file_info['category']})")
                else:
                    if file_info["size"] >= self.max_file_size:
                        logger.info(f"✗ SKIPPING (too large): {file_info['relative_path']} ({file_info['size']} bytes)")
                    else:
                        logger.info(f"✗ SKIPPING (filtered): {file_info['relative_path']} ({file_info['size']} bytes, {file_info['category']})")
            
            logger.info(f"Performing parallel AST analysis on {len(analyzable_files)} files (filtered from {len(repo_files)} total)")
            
            ast_analysis = {}
            
            # Use parallel processing for AST analysis with optimizations
            max_workers = min(4, len(analyzable_files))  # Reduced workers for better performance
            
            # For very large repositories, limit the number of files analyzed
            if len(analyzable_files) > 5000:
                logger.info(f"Large repository detected ({len(analyzable_files)} files). Limiting analysis to top 5000 files.")
                # Sort by priority and take top files
                analyzable_files = sorted(analyzable_files, key=self._file_analysis_priority)[:5000]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit analysis jobs
                future_to_file = {
                    executor.submit(self._analyze_single_file, file_info): file_info
                    for file_info in analyzable_files
                }
                
                completed = 0
                for future in as_completed(future_to_file):
                    file_info = future_to_file[future]
                    try:
                        analysis = future.result()
                        if analysis:
                            ast_analysis[file_info["relative_path"]] = analysis
                        
                        completed += 1
                        if completed % 500 == 0:  # More frequent progress updates
                            logger.info(f"AST analysis progress: {completed}/{len(analyzable_files)} files")
                            
                    except Exception as e:
                        logger.warning(f"Failed to analyze {file_info['path']}: {str(e)}")
                        continue
            
            new_state = state.copy()
            new_state["ast_analysis"] = ast_analysis
            
            logger.info(f"AST analysis completed for {len(ast_analysis)} files")
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to perform AST analysis: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to perform AST analysis: {str(e)}"
            return new_state
    
    def _should_analyze_file(self, file_info: Dict[str, Any]) -> bool:
        """Determine if a file should be analyzed - includes both AST analysis and documentation files."""
        # AST-analyzable extensions for code files
        analyzable_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.scala', '.swift',
            '.vue', '.svelte', '.dart', '.r', '.jl', '.m', '.mm'
        }
        
        # Documentation extensions that provide valuable context
        documentation_extensions = {
            '.md', '.txt', '.rst', '.org', '.adoc'
        }
        
        # Skip files that are clearly not useful for documentation
        skip_patterns = [
            'test', 'spec', '__test__', '.test.', '.spec.',
            'mock', 'fixture', 'sample', 'example',
            'vendor', 'third_party', 'external',
            'generated', 'auto', 'build', 'dist',
            'min.js', 'min.css', 'bundle.js', 'bundle.css',
            'lock.json', 'package-lock.json', 'yarn.lock',
            'migration', 'seed', 'schema.sql'
        ]
        
        file_path = file_info["path"].lower()
        file_name = file_info["name"].lower()
        extension = file_info["extension"]
        category = file_info.get("category", "other")
        
        # Accept documentation files (they provide crucial context)
        if extension in documentation_extensions or category == "documentation":
            # Skip very large documentation files
            if file_info["size"] > 100000:  # 100KB limit for docs
                return False
            return True
        
        # Accept code files that can benefit from AST analysis
        if extension in analyzable_extensions:
            # Skip files with patterns that indicate they're not main source code
            for pattern in skip_patterns:
                if pattern in file_path or pattern in file_name:
                    return False
            
            # Skip very small files (likely empty or minimal)
            if file_info["size"] < 50:
                return False
            
            # Skip very large files (likely generated or data files)
            if file_info["size"] > 500000:  # 500KB
                return False
            
            # Prioritize files in common source directories
            priority_dirs = ['src', 'lib', 'app', 'components', 'pages', 'views', 'controllers', 'models', 'services']
            has_priority_dir = any(dir_name in file_path for dir_name in priority_dirs)
            
            # For large repositories, be more selective
            if not has_priority_dir and category != "code":
                return False
            
            return True
        
        return False
    
    def _file_analysis_priority(self, file_info: Dict[str, Any]) -> tuple:
        """Calculate priority for file analysis (lower number = higher priority)."""
        file_path = file_info["path"].lower()
        file_name = file_info["name"].lower()
        
        # Priority 0: Main entry points and important files
        important_files = ['main.py', 'app.py', 'index.js', 'main.js', 'server.js', '__init__.py']
        if file_name in important_files:
            return (0, -file_info["size"])
        
        # Priority 1: Files in src/lib/app directories
        priority_dirs = ['src/', 'lib/', 'app/', 'components/', 'pages/']
        if any(dir_name in file_path for dir_name in priority_dirs):
            return (1, -file_info["size"])
        
        # Priority 2: Code files
        if file_info["category"] == "code":
            return (2, -file_info["size"])
        
        # Priority 3: Config files
        if file_info["category"] == "config":
            return (3, -file_info["size"])
        
        # Priority 4: Everything else
        return (4, -file_info["size"])
    
    def _analyze_single_file(self, file_info: Dict[str, Any]) -> Optional[ASTAnalysis]:
        """Analyze a single file with AST - designed for parallel execution."""
        try:
            with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            return self.ast_analyzer.analyze_file(file_info["path"], content)
            
        except Exception as e:
            # Don't log here to avoid thread-unsafe logging
            return None
    
    def _generate_documentation(self, state: IndexState) -> IndexState:
        """Generate comprehensive documentation from AST analysis."""
        try:
            repo_path = state["current_repo_path"]
            repo_metadata = state["repo_metadata"]
            ast_analysis = state["ast_analysis"]
            repo_files = state["repo_files"]
            
            logger.info(f"Generating documentation for {repo_path}")
            
            # Prepare file contents for context - prioritize documentation and key files
            file_contents = []
            
            # First, add all documentation files (they provide crucial context)
            doc_files = [f for f in repo_files if f["category"] == "documentation"]
            for file_info in doc_files:
                if file_info["size"] < self.max_file_size:
                    try:
                        with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            file_contents.append({
                                "path": file_info["relative_path"],
                                "content": content[:5000],  # More content for docs
                                "size": file_info["size"],
                                "extension": file_info["extension"],
                                "category": file_info["category"]
                            })
                    except Exception:
                        continue
            
            # Then add key code files (main entry points, configs, etc.)
            priority_files = [f for f in repo_files if f["name"].lower() in [
                "main.py", "app.py", "index.js", "server.js", "__init__.py",
                "requirements.txt", "package.json", "setup.py", "pyproject.toml"
            ]]
            
            for file_info in priority_files:
                if file_info["size"] < self.max_file_size and file_info not in doc_files:
                    try:
                        with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            file_contents.append({
                                "path": file_info["relative_path"],
                                "content": content[:3000],  # More content for key files
                                "size": file_info["size"],
                                "extension": file_info["extension"],
                                "category": file_info["category"]
                            })
                    except Exception:
                        continue
            
            # Finally, add other important files up to a reasonable limit
            other_files = [f for f in repo_files if f not in doc_files and f not in priority_files]
            for file_info in other_files[:15]:  # Limit other files
                if file_info["size"] < self.max_file_size:
                    try:
                        with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            file_contents.append({
                                "path": file_info["relative_path"],
                                "content": content[:2000],  # Standard content for other files
                                "size": file_info["size"],
                                "extension": file_info["extension"],
                                "category": file_info["category"]
                            })
                    except Exception:
                        continue
            
            # Generate documentation using the enhanced generator
            generated_docs = self.doc_generator.generate_documentation(
                repo_path=repo_path,
                repo_metadata=repo_metadata,
                ast_analysis=ast_analysis,
                file_contents=file_contents
            )
            
            new_state = state.copy()
            new_state["generated_docs"] = generated_docs
            
            logger.info(f"Generated {len(generated_docs)} documentation files")
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to generate documentation: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to generate documentation: {str(e)}"
            return new_state
    
    def _store_documentation(self, state: IndexState) -> IndexState:
        """Store the generated documentation in ChromaDB."""
        try:
            repo_path = state["current_repo_path"]
            generated_docs = state["generated_docs"]
            repo_metadata = state["repo_metadata"]
            
            # Prepare metadata for ChromaDB (only primitive types allowed)
            chroma_metadata = self._prepare_chroma_metadata(repo_metadata)
            
            # Store each document in ChromaDB
            for doc_name, doc_content in generated_docs.items():
                doc_metadata = {**chroma_metadata, "document_type": doc_name}
                self.chroma_manager.add_repo_memo(
                    repo_path=f"{repo_path}/{doc_name}",
                    memo_content=doc_content,
                    repo_metadata=doc_metadata
                )
            
            # Add to all_docs for final summary with CLI-compatible structure
            doc_entry = {
                "repo_path": repo_path,
                "documents": generated_docs,
                "metadata": repo_metadata,
                "memo_content": "\n\n".join([f"# {doc_name}\n\n{doc_content}" for doc_name, doc_content in generated_docs.items()])
            }
            
            all_docs = state["all_docs"].copy()
            all_docs.append(doc_entry)
            
            new_state = state.copy()
            new_state["all_docs"] = all_docs
            
            logger.info(f"Stored {len(generated_docs)} documents in ChromaDB")
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to store documentation: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to store documentation: {str(e)}"
            return new_state
    
    def _prepare_chroma_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool, None]]:
        """Prepare metadata for ChromaDB by converting complex types to strings."""
        chroma_metadata = {}
        
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                chroma_metadata[key] = value
            elif isinstance(value, dict):
                # Convert dict to JSON string
                chroma_metadata[key] = json.dumps(value)
            elif isinstance(value, list):
                # Convert list to comma-separated string
                chroma_metadata[key] = ", ".join(str(item) for item in value)
            else:
                # Convert other types to string
                chroma_metadata[key] = str(value)
        
        return chroma_metadata
    
    def _write_documentation_files(self, state: IndexState) -> IndexState:
        """Write documentation files to disk."""
        try:
            repo_path = state["current_repo_path"]
            generated_docs = state["generated_docs"]
            
            # Determine output directory
            if state.get("output_dir"):
                # Use specified output directory
                output_dir = Path(state["output_dir"])
                repo_name = Path(repo_path).name
                repo_output_dir = output_dir / repo_name
                repo_output_dir.mkdir(parents=True, exist_ok=True)
            else:
                # Write directly to the repository directory
                repo_output_dir = Path(repo_path)
            
            # Write each documentation file
            for doc_name, doc_content in generated_docs.items():
                doc_path = repo_output_dir / doc_name
                with open(doc_path, "w", encoding="utf-8") as f:
                    f.write(doc_content)
                
                logger.info(f"Written documentation file: {doc_path}")
            
            logger.info(f"All documentation files written to {repo_output_dir}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to write documentation files: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to write documentation files: {str(e)}"
            return new_state
    
    def _next_repo(self, state: IndexState) -> IndexState:
        """Move to the next repository."""
        current_index = state["current_repo_index"]
        new_state = state.copy()
        new_state.update({
            "current_repo_index": current_index + 1,
            "current_repo_path": "",
            "repo_files": [],
            "ast_analysis": {},
            "generated_docs": {},
            "repo_metadata": {}
        })
        return new_state
    
    def _generate_general_memo(self, state: IndexState) -> IndexState:
        """Generate a general memo summarizing all repositories."""
        try:
            all_docs = state["all_docs"]
            
            if not all_docs:
                new_state = state.copy()
                new_state["general_memo"] = "No repositories were successfully indexed."
                return new_state
            
            # Create comprehensive summary
            repo_summaries = []
            total_functions = 0
            total_classes = 0
            total_apis = 0
            languages = set()
            
            for doc_entry in all_docs:
                repo_name = Path(doc_entry["repo_path"]).name
                metadata = doc_entry["metadata"]
                
                languages.add(metadata.get('primary_language', 'Unknown'))
                
                summary = f"**{repo_name}**\n"
                summary += f"- Language: {metadata.get('primary_language', 'Unknown')}\n"
                summary += f"- Files: {metadata.get('file_count', 0)}\n"
                summary += f"- Size: {metadata.get('total_size', 0)} bytes\n"
                summary += f"- Documentation: {len(doc_entry['documents'])} files generated\n"
                
                repo_summaries.append(summary)
            
            general_memo_prompt = f"""Create a comprehensive overview memo for this collection of repositories:

Repository Collection Summary:
{chr(10).join(repo_summaries)}

Collection Statistics:
- Total Repositories: {len(all_docs)}
- Languages Used: {', '.join(languages)}
- Documentation Files Generated: {sum(len(doc['documents']) for doc in all_docs)}

Please create a general memo that includes:
1. Executive summary of the entire codebase collection
2. Technology stack and architecture patterns
3. Key insights and recommendations
4. Development workflow suggestions
5. Integration opportunities between repositories

General Collection Memo:"""

            general_memo = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": general_memo_prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            
            new_state = state.copy()
            new_state["general_memo"] = general_memo
            
            logger.info("Generated general collection memo")
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to generate general memo: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to generate general memo: {str(e)}"
            return new_state
    
    def _finalize(self, state: IndexState) -> IndexState:
        """Finalize the indexing process."""
        new_state = state.copy()
        new_state["success"] = True
        
        logger.info("Enhanced indexing process completed successfully")
        return new_state
    
    def _handle_error(self, state: IndexState) -> IndexState:
        """Handle errors gracefully."""
        new_state = state.copy()
        new_state["success"] = False
        
        logger.error(f"Indexing process failed: {new_state.get('error', 'Unknown error')}")
        return new_state
    
    def _should_continue(self, state: IndexState) -> str:
        """Determine if we should continue processing repos."""
        if state.get("error"):
            return "error"
        
        current_index = state["current_repo_index"]
        total_repos = len(state["repo_paths"])
        
        if current_index >= total_repos:
            return "generate_general"
        else:
            return "continue"
    
    def _get_repo_metadata(self, repo_path: str) -> Dict[str, Any]:
        """Extract enhanced metadata from a repository."""
        metadata = {
            "repo_path": repo_path,
            "repo_name": Path(repo_path).name
        }
        
        # Git information
        try:
            repo = Repo(repo_path)
            if not repo.bare:
                metadata["git_branch"] = repo.active_branch.name
                metadata["last_commit"] = repo.head.commit.hexsha[:8]
                metadata["author"] = repo.head.commit.author.name
                metadata["commit_date"] = repo.head.commit.committed_datetime.isoformat()
        except Exception:
            pass
        
        # File statistics
        file_stats = self._analyze_file_types(repo_path)
        metadata.update(file_stats)
        
        # Configuration files detection
        config_files = self._detect_config_files(repo_path)
        metadata["config_files"] = config_files
        
        return metadata
    
    def _detect_config_files(self, repo_path: str) -> List[str]:
        """Detect common configuration files."""
        config_patterns = [
            "requirements.txt", "package.json", "Cargo.toml", "go.mod",
            "pom.xml", "build.gradle", "Makefile", "CMakeLists.txt",
            "Dockerfile", "docker-compose.yml", ".env", "config.yml",
            "pyproject.toml", "setup.py", "tsconfig.json"
        ]
        
        found_configs = []
        repo_path_obj = Path(repo_path)
        
        for pattern in config_patterns:
            config_files = list(repo_path_obj.rglob(pattern))
            if config_files:
                found_configs.extend([str(f.relative_to(repo_path_obj)) for f in config_files])
        
        return found_configs
    
    def _scan_files(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Enhanced file scanning with better categorization and gitignore support."""
        files = []
        
        # Initialize gitignore parser if enabled
        if self.respect_gitignore:
            self.gitignore_parser = GitignoreParser(str(repo_path))
        
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                # Skip files ignored by gitignore
                if self.respect_gitignore and self.gitignore_parser and self.gitignore_parser.is_ignored(file_path):
                    continue
                
                if any(excluded in file_path.parts for excluded in self.excluded_dirs):
                    continue
                
                if file_path.suffix.lower() in self.excluded_extensions:
                    continue
                
                try:
                    file_info = {
                        "path": str(file_path),
                        "relative_path": str(file_path.relative_to(repo_path)),
                        "name": file_path.name,
                        "extension": file_path.suffix.lower(),
                        "size": file_path.stat().st_size,
                        "category": self._categorize_file(file_path)
                    }
                    files.append(file_info)
                except Exception:
                    continue
        
        # Enhanced sorting by category and importance
        def file_priority(file_info):
            category_priority = {
                "code": 0,
                "config": 1,
                "documentation": 2,
                "test": 3,
                "other": 4
            }
            
            category = file_info.get("category", "other")
            priority = category_priority.get(category, 4)
            
            # Prioritize important files within categories
            important_files = {
                "main.py", "app.py", "index.js", "main.js", "server.js",
                "README.md", "requirements.txt", "package.json", "Dockerfile"
            }
            
            importance = 0 if file_info["name"] in important_files else 1
            
            return (priority, importance, -file_info["size"])
        
        files.sort(key=file_priority)
        return files
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on extension and name."""
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        
        code_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs", ".php", ".rb", ".go", ".rs"}
        config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}
        doc_extensions = {".md", ".txt", ".rst", ".org"}
        test_patterns = {"test", "spec", "__test__"}
        
        if any(pattern in name for pattern in test_patterns):
            return "test"
        elif ext in code_extensions:
            return "code"
        elif ext in config_extensions or name in {"dockerfile", "makefile", "requirements.txt"}:
            return "config"
        elif ext in doc_extensions:
            return "documentation"
        else:
            return "other"
    
    def _analyze_file_types(self, repo_path: str) -> Dict[str, Any]:
        """Enhanced file type analysis with gitignore support."""
        repo_path_obj = Path(repo_path)
        extensions = {}
        categories = {"code": 0, "config": 0, "documentation": 0, "test": 0, "other": 0}
        total_files = 0
        total_size = 0
        
        # Initialize gitignore parser if enabled
        gitignore_parser = None
        if self.respect_gitignore:
            gitignore_parser = GitignoreParser(repo_path)
        
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file():
                # Skip files ignored by gitignore
                if self.respect_gitignore and gitignore_parser and gitignore_parser.is_ignored(file_path):
                    continue
                
                if any(excluded in file_path.parts for excluded in self.excluded_dirs):
                    continue
                
                ext = file_path.suffix.lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
                
                category = self._categorize_file(file_path)
                categories[category] += 1
                
                try:
                    total_size += file_path.stat().st_size
                    total_files += 1
                except Exception:
                    continue
        
        # Determine primary language
        code_extensions = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".java": "Java", ".cpp": "C++", ".c": "C", ".cs": "C#",
            ".php": "PHP", ".rb": "Ruby", ".go": "Go", ".rs": "Rust"
        }
        
        primary_language = "Unknown"
        max_count = 0
        for ext, count in extensions.items():
            if ext in code_extensions and count > max_count:
                max_count = count
                primary_language = code_extensions[ext]
        
        return {
            "file_count": total_files,
            "total_size": total_size,
            "primary_language": primary_language,
            "file_extensions": dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]),
            "file_categories": categories,
            "code_files": categories["code"],
            "config_files": categories["config"],
            "doc_files": categories["documentation"],
            "test_files": categories["test"]
        }
