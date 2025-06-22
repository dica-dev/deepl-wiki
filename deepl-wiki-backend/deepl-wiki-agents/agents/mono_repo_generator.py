"""Mono-repository documentation generator for creating structured documentation sites."""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import re
from datetime import datetime

class MonoRepoGenerator:
    """Generator for creating structured mono-repository documentation."""
    
    def __init__(self, include_diagrams: bool = True, output_format: str = "markdown"):
        """Initialize the mono-repo generator."""
        self.include_diagrams = include_diagrams
        self.output_format = output_format
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_mono_repo(
        self, 
        output_dir: str, 
        repositories: List[Dict[str, Any]], 
        general_memo: str
    ) -> str:
        """Generate a complete mono-repo documentation structure."""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        self._create_directory_structure(output_path)
        
        # Generate main README
        self._generate_main_readme(output_path, repositories, general_memo)
        
        # Generate individual repository documentation
        for repo_data in repositories:
            self._generate_repo_documentation(output_path, repo_data)
        
        # Generate global documentation
        self._generate_global_documentation(output_path, repositories, general_memo)
        
        # Generate diagrams if requested
        if self.include_diagrams:
            self._generate_diagrams(output_path, repositories)
        
        # Generate navigation and index files
        self._generate_navigation(output_path, repositories)
        
        return str(output_path)
    
    def _create_directory_structure(self, base_path: Path):
        """Create the basic directory structure."""
        directories = [
            "repos",
            "global", 
            "diagrams",
            "assets"
        ]
        
        for directory in directories:
            (base_path / directory).mkdir(exist_ok=True)
    
    def _generate_main_readme(self, base_path: Path, repositories: List[Dict[str, Any]], general_memo: str):
        """Generate the main README.md file."""
        
        repo_list = []
        for repo_data in repositories:
            repo_name = Path(repo_data["repo_path"]).name
            metadata = repo_data["metadata"]
            
            repo_list.append({
                "name": repo_name,
                "language": metadata.get("primary_language", "Unknown"),
                "files": metadata.get("file_count", 0),
                "path": f"repos/{repo_name}/README.md"
            })
        
        readme_content = f"""# Documentation Repository

*Generated on {self.timestamp}*

## Overview

This repository contains comprehensive documentation for {len(repositories)} codebases, automatically generated and structured for easy navigation and understanding.

{general_memo}

## Repository Index

| Repository | Language | Files | Documentation |
|------------|----------|--------|---------------|
"""

        for repo in repo_list:
            readme_content += f"| [{repo['name']}]({repo['path']}) | {repo['language']} | {repo['files']} | [View Docs]({repo['path']}) |\n"

        readme_content += f"""

## Navigation

- 📁 **[Repository Documentation](repos/)** - Individual repository documentation
- 🌐 **[System Overview](global/overview.md)** - Multi-repository system analysis  
- 🏗️ **[Architecture](global/architecture.md)** - System architecture and design
- 🔗 **[Integrations](global/integrations.md)** - Inter-repository connections
- 📊 **[Diagrams](diagrams/)** - Visual system representations

## Quick Links

### By Technology
"""

        # Group repositories by language
        tech_groups = {}
        for repo in repo_list:
            lang = repo["language"]
            if lang not in tech_groups:
                tech_groups[lang] = []
            tech_groups[lang].append(repo)
        
        for tech, repos in tech_groups.items():
            readme_content += f"\n#### {tech}\n"
            for repo in repos:
                readme_content += f"- [{repo['name']}]({repo['path']})\n"

        readme_content += f"""

### Quick Actions

- 🔍 **Search Documentation**: Use your browser's search (Ctrl+F) to find specific information
- 📋 **API Reference**: Check individual repository documentation for API details
- 🚀 **Getting Started**: Each repository has setup and development instructions
- 🔧 **Configuration**: Environment and configuration details in each repo

## Documentation Structure

```
docs/
├── README.md                 # This file - main entry point
├── repos/                    # Individual repository documentation
│   ├── repo1/
│   │   ├── README.md        # Main repository documentation
│   │   ├── api.md           # API documentation (if applicable)
│   │   ├── architecture.md  # Repository architecture
│   │   └── setup.md         # Setup and development guide
│   └── repo2/
│       └── ...
├── global/                   # System-wide documentation
│   ├── overview.md          # Complete system overview
│   ├── architecture.md      # System architecture
│   └── integrations.md      # Cross-repository integrations
└── diagrams/                 # Visual documentation
    ├── system-overview.mermaid
    ├── data-flow.mermaid
    └── component-diagram.mermaid
```

---

*Documentation automatically generated by DeepL Wiki Agents*
"""

        with open(base_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
    
    def _generate_repo_documentation(self, base_path: Path, repo_data: Dict[str, Any]):
        """Generate documentation for an individual repository."""
        
        repo_path = repo_data["repo_path"]
        repo_name = Path(repo_path).name
        memo_content = repo_data["memo_content"]
        metadata = repo_data["metadata"]
        
        repo_dir = base_path / "repos" / repo_name
        repo_dir.mkdir(exist_ok=True)
        
        # Parse the memo_content to extract individual documentation sections
        docs = self._parse_memo_content(memo_content)
        
        # Generate main README (focused and concise)
        repo_readme = f"""# {repo_name}

*Repository Documentation*

## Metadata

- **Path**: `{repo_path}`
- **Primary Language**: {metadata.get('primary_language', 'Unknown')}
- **File Count**: {metadata.get('file_count', 0)}
- **Total Size**: {self._format_size(metadata.get('total_size', 0))}
- **Git Branch**: {metadata.get('git_branch', 'N/A')}
- **Last Commit**: {metadata.get('last_commit', 'N/A')}

## Overview

{docs.get('README.md', 'No overview available.')}

## Documentation Files

- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Development Guide](DEVELOPMENT.md)** - Setup and contribution guidelines
- **[Component Reference](COMPONENTS.md)** - Detailed API documentation

## File Extensions

The repository contains the following file types:

"""

        # Parse file extensions from metadata
        file_extensions = metadata.get('file_extensions', '{}')
        if isinstance(file_extensions, str):
            try:
                # Convert string representation back to dict
                extensions_dict = eval(file_extensions)
                for ext, count in extensions_dict.items():
                    repo_readme += f"- `{ext}`: {count} files\n"
            except:
                repo_readme += "- File extension information not available\n"

        repo_readme += f"""

## Navigation

- [🏠 Back to Main Documentation](../../README.md)
- [🌐 System Overview](../../global/overview.md)
- [📊 System Diagrams](../../diagrams/)

---

*Last updated: {self.timestamp}*
"""

        # Write main README
        with open(repo_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(repo_readme)
        
        # Write separate documentation files
        for doc_name, doc_content in docs.items():
            if doc_name != 'README.md' and doc_content.strip():
                with open(repo_dir / doc_name, "w", encoding="utf-8") as f:
                    f.write(doc_content)
    
    def _generate_global_documentation(self, base_path: Path, repositories: List[Dict[str, Any]], general_memo: str):
        """Generate global system documentation."""
        
        global_dir = base_path / "global"
        
        # System overview
        overview_content = f"""# System Overview

*Multi-Repository System Analysis*

## General Analysis

{general_memo}

## Repository Summary

This system consists of {len(repositories)} repositories:

"""

        for repo_data in repositories:
            repo_name = Path(repo_data["repo_path"]).name
            metadata = repo_data["metadata"]
            
            overview_content += f"""### {repo_name}

- **Language**: {metadata.get('primary_language', 'Unknown')}
- **Files**: {metadata.get('file_count', 0)}
- **Size**: {self._format_size(metadata.get('total_size', 0))}
- **Documentation**: [View Details](../repos/{repo_name}/README.md)

"""

        overview_content += f"""

## Technology Stack

The system uses the following technologies:

"""

        # Aggregate technology information
        tech_stats = {}
        for repo_data in repositories:
            lang = repo_data["metadata"].get("primary_language", "Unknown")
            tech_stats[lang] = tech_stats.get(lang, 0) + 1

        for tech, count in sorted(tech_stats.items(), key=lambda x: x[1], reverse=True):
            overview_content += f"- **{tech}**: {count} repository/repositories\n"

        overview_content += f"""

## Navigation

- [🏠 Main Documentation](../README.md)
- [🏗️ System Architecture](architecture.md)
- [🔗 Integrations](integrations.md)

---

*Generated: {self.timestamp}*
"""

        with open(global_dir / "overview.md", "w", encoding="utf-8") as f:
            f.write(overview_content)
        
        # Architecture documentation
        arch_content = f"""# System Architecture

*Technical Architecture Overview*

## Architecture Summary

This multi-repository system follows modern software architecture principles with clear separation of concerns and modular design.

## Repository Architecture

"""

        for repo_data in repositories:
            repo_name = Path(repo_data["repo_path"]).name
            metadata = repo_data["metadata"]
            
            arch_content += f"""### {repo_name} Architecture

- **Type**: {self._determine_repo_type(metadata)}
- **Language**: {metadata.get('primary_language', 'Unknown')}
- **Scale**: {metadata.get('file_count', 0)} files, {self._format_size(metadata.get('total_size', 0))}

"""

        if self.include_diagrams:
            arch_content += """

## System Diagrams

- [System Overview Diagram](../diagrams/system-overview.mermaid)
- [Component Relationships](../diagrams/component-diagram.mermaid)
- [Data Flow](../diagrams/data-flow.mermaid)

"""

        arch_content += f"""

## Design Patterns

Based on the analysis, the following patterns are observed:

- **Microservices**: Multiple independent repositories suggest a microservices architecture
- **Language Diversity**: Multi-language approach for different concerns
- **Modular Design**: Clear separation between different functional areas

## Navigation

- [🏠 Main Documentation](../README.md)
- [🌐 System Overview](overview.md)
- [🔗 Integrations](integrations.md)

---

*Generated: {self.timestamp}*
"""

        with open(global_dir / "architecture.md", "w", encoding="utf-8") as f:
            f.write(arch_content)
        
        # Integrations documentation
        integrations_content = f"""# System Integrations

*Cross-Repository Connections and Interfaces*

## Integration Overview

This document outlines how the {len(repositories)} repositories in this system interact and integrate with each other.

## Repository Connections

"""

        # Analyze potential connections based on languages and patterns
        for repo_data in repositories:
            repo_name = Path(repo_data["repo_path"]).name
            metadata = repo_data["metadata"]
            
            integrations_content += f"""### {repo_name} Integrations

- **Primary Language**: {metadata.get('primary_language', 'Unknown')}
- **Potential Integration Points**: {self._identify_integration_points(metadata)}
- **Documentation**: [View Details](../repos/{repo_name}/README.md)

"""

        integrations_content += f"""

## Common Integration Patterns

Based on the repository analysis:

1. **API Interfaces**: RESTful APIs and service endpoints
2. **Shared Libraries**: Common utility and helper libraries  
3. **Data Sharing**: Database connections and data exchange
4. **Configuration**: Shared configuration and environment variables

## External Dependencies

The system likely integrates with external services and tools:

- **Databases**: Various database systems for data persistence
- **Cloud Services**: Cloud-based infrastructure and services
- **Third-party APIs**: External service integrations
- **Development Tools**: CI/CD, monitoring, and development tooling

## Navigation

- [🏠 Main Documentation](../README.md)
- [🌐 System Overview](overview.md)
- [🏗️ System Architecture](architecture.md)

---

*Generated: {self.timestamp}*
"""

        with open(global_dir / "integrations.md", "w", encoding="utf-8") as f:
            f.write(integrations_content)
    
    def _generate_diagrams(self, base_path: Path, repositories: List[Dict[str, Any]]):
        """Generate Mermaid diagrams for system visualization."""
        
        diagrams_dir = base_path / "diagrams"
        
        # System overview diagram
        system_overview = """# System Overview Diagram

```mermaid
graph TB
    subgraph "System Architecture"
"""

        # Add repositories as nodes
        for i, repo_data in enumerate(repositories):
            repo_name = Path(repo_data["repo_path"]).name
            lang = repo_data["metadata"].get("primary_language", "Unknown")
            system_overview += f'        {chr(65+i)}["{repo_name}<br/>({lang})"]'
            system_overview += "\n"

        # Add connections (simplified)
        if len(repositories) > 1:
            system_overview += "\n"
            for i in range(len(repositories)-1):
                system_overview += f"        {chr(65+i)} --> {chr(65+i+1)}\n"

        system_overview += """    end
```

*This diagram shows the high-level system structure and repository relationships.*
"""

        with open(diagrams_dir / "system-overview.mermaid", "w", encoding="utf-8") as f:
            f.write(system_overview)
        
        # Component diagram
        component_diagram = """# Component Diagram

```mermaid
classDiagram
"""

        for repo_data in repositories:
            repo_name = Path(repo_data["repo_path"]).name
            lang = repo_data["metadata"].get("primary_language", "Unknown")
            file_count = repo_data["metadata"].get("file_count", 0)
            
            component_diagram += f"""    class {repo_name.replace('-', '_')} {{
        +Language: {lang}
        +Files: {file_count}
        +getInfo()
        +initialize()
    }}
"""

        component_diagram += """```

*This diagram shows the main components and their relationships.*
"""

        with open(diagrams_dir / "component-diagram.mermaid", "w", encoding="utf-8") as f:
            f.write(component_diagram)
        
        # Data flow diagram
        data_flow = """# Data Flow Diagram

```mermaid
flowchart LR
    A[Input Data] --> B[Processing]
    B --> C[Storage]
    C --> D[Output]
    
    subgraph "Repository System"
"""

        for repo_data in repositories:
            repo_name = Path(repo_data["repo_path"]).name
            data_flow += f'        E{len(repo_name)}["{repo_name}"]\n'

        data_flow += """    end
    
    B --> E1
    E1 --> C
```

*This diagram illustrates the data flow through the system components.*
"""

        with open(diagrams_dir / "data-flow.mermaid", "w", encoding="utf-8") as f:
            f.write(data_flow)
    
    def _generate_navigation(self, base_path: Path, repositories: List[Dict[str, Any]]):
        """Generate navigation and index files."""
        
        # Create a simple sitemap
        sitemap_content = f"""# Site Map

## Documentation Structure

Generated on: {self.timestamp}

### Main Documentation
- [README.md](README.md) - Main entry point

### Repository Documentation
"""

        for repo_data in repositories:
            repo_name = Path(repo_data["repo_path"]).name
            sitemap_content += f"- [repos/{repo_name}/README.md](repos/{repo_name}/README.md)\n"

        sitemap_content += f"""

### Global Documentation
- [global/overview.md](global/overview.md)
- [global/architecture.md](global/architecture.md)  
- [global/integrations.md](global/integrations.md)

### Diagrams
- [diagrams/system-overview.mermaid](diagrams/system-overview.mermaid)
- [diagrams/component-diagram.mermaid](diagrams/component-diagram.mermaid)
- [diagrams/data-flow.mermaid](diagrams/data-flow.mermaid)

---

Total repositories: {len(repositories)}
"""

        with open(base_path / "sitemap.md", "w", encoding="utf-8") as f:
            f.write(sitemap_content)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _determine_repo_type(self, metadata: Dict[str, Any]) -> str:
        """Determine the type of repository based on metadata."""
        lang = metadata.get("primary_language", "").lower()
        file_count = metadata.get("file_count", 0)
        
        if "python" in lang:
            return "Python Application/Library"
        elif "javascript" in lang or "typescript" in lang:
            return "Web Application/Library"
        elif "java" in lang:
            return "Java Application/Library"
        elif file_count > 100:
            return "Large Application"
        elif file_count > 20:
            return "Medium Application"
        else:
            return "Small Library/Tool"
    
    def _identify_integration_points(self, metadata: Dict[str, Any]) -> str:
        """Identify potential integration points based on metadata."""
        lang = metadata.get("primary_language", "").lower()
        
        if "python" in lang:
            return "REST APIs, Database connections, CLI interfaces"
        elif "javascript" in lang:
            return "Web APIs, Frontend interfaces, NPM packages"
        elif "java" in lang:
            return "REST/SOAP APIs, Database connections, Maven dependencies"
        else:
            return "Configuration files, Command line interfaces, Data files"

    async def get_mono_repo_path(self) -> Optional[str]:
        """Get the path to the generated mono repository.
        
        Returns:
            Path to the mono repository if it exists, None otherwise
        """
        # Default mono repo path
        default_path = Path("./mono_repo_docs")
        
        if default_path.exists() and default_path.is_dir():
            return str(default_path.absolute())
        
        # Try alternative locations
        alternative_paths = [
            Path("../mono_repo_docs"),
            Path("./docs"),
            Path("../docs"),
            Path("./generated_docs")
        ]
        
        for path in alternative_paths:
            if path.exists() and path.is_dir():
                return str(path.absolute())
        
        return None

    async def generate_or_get_mono_repo(self, repositories: List[Dict[str, Any]], general_memo: str = "", output_dir: str = "./mono_repo_docs") -> str:
        """Generate a mono repo or return existing one.
        
        Args:
            repositories: List of repository data
            general_memo: General memo about the repositories
            output_dir: Output directory for the mono repo
            
        Returns:
            Path to the mono repository
        """
        output_path = Path(output_dir)
        
        # If mono repo already exists and is recent, return it
        if output_path.exists() and output_path.is_dir():
            # Check if it was generated recently (within last hour)
            try:
                stats = output_path.stat()
                import time
                if time.time() - stats.st_mtime < 3600:  # 1 hour
                    return str(output_path.absolute())
            except:
                pass
        
        # Generate new mono repo
        return self.generate_mono_repo(output_dir, repositories, general_memo)
    
    def _parse_memo_content(self, memo_content: str) -> Dict[str, str]:
        """Parse memo content to extract individual documentation sections."""
        docs = {}
        
        # Split content by markdown headers that indicate separate files
        sections = re.split(r'\n# ([A-Z_]+\.md)\n', memo_content)
        
        if len(sections) == 1:
            # No clear file separations found, try to extract by common patterns
            docs = self._extract_docs_by_pattern(memo_content)
        else:
            # Process sections found by file headers
            current_content = sections[0].strip()  # Content before first header
            
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    filename = sections[i]
                    content = sections[i + 1].strip()
                    docs[filename] = content
            
            # If there's initial content, treat it as README
            if current_content:
                docs['README.md'] = current_content
        
        return docs
    
    def _extract_docs_by_pattern(self, content: str) -> Dict[str, str]:
        """Extract documentation sections by common patterns when file headers aren't clear."""
        docs = {}
        
        # Try to find sections by common documentation patterns
        patterns = {
            'README.md': r'(?i)(?:^|\n)(?:#\s*)?(?:readme|overview|description|about).*?(?=\n#\s*(?:architecture|development|components|api)|$)',
            'ARCHITECTURE.md': r'(?i)(?:^|\n)(?:#\s*)?(?:architecture|system\s+overview|design).*?(?=\n#\s*(?:development|components|api|readme)|$)',
            'DEVELOPMENT.md': r'(?i)(?:^|\n)(?:#\s*)?(?:development|setup|installation|getting\s+started).*?(?=\n#\s*(?:architecture|components|api|readme)|$)',
            'COMPONENTS.md': r'(?i)(?:^|\n)(?:#\s*)?(?:components?|api|reference|classes?|functions?).*?(?=\n#\s*(?:architecture|development|readme)|$)'
        }
        
        for filename, pattern in patterns.items():
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if matches:
                # Take the longest match (most comprehensive)
                docs[filename] = max(matches, key=len).strip()
        
        # If no patterns matched, put everything in README
        if not docs:
            docs['README.md'] = content
        
        return docs
