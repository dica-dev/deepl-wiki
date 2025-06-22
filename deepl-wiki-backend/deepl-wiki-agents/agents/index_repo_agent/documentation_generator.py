"""
Enhanced documentation generator that creates folder-based documentation structure
with recursive section generation, intelligent structure analysis, visual diagrams, and examples.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from .models import (
    ASTAnalysis, 
    DocumentationSection, 
    DocumentationFolder, 
    DocumentationStructure
)
from .intelligent_structure_analyzer import IntelligentStructureAnalyzer
from .diagram_generator import DiagramGenerator
from .example_extractor import ExampleExtractor

logger = logging.getLogger(__name__)

class DocumentationGenerator:
    """Generate structured documentation with folders and sections using intelligent analysis."""
    
    def __init__(self, llama_client):
        self.llama_client = llama_client
        self.structure_analyzer = IntelligentStructureAnalyzer()
        self.diagram_generator = DiagramGenerator()
        self.example_extractor = ExampleExtractor()
    
    def generate_documentation_structure(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> DocumentationStructure:
        """Generate intelligent documentation structure using AI and pattern analysis."""
        
        repo_name = Path(repo_path).name
        
        try:
            # Use intelligent structure analyzer first
            intelligent_folders = self.structure_analyzer.analyze_repository_structure(
                repo_path, repo_metadata, ast_analysis, file_contents
            )
            
            # Generate README content with enhanced analysis
            readme_content = self._generate_enhanced_readme(
                repo_path, repo_metadata, ast_analysis, file_contents
            )
            
            return DocumentationStructure(
                readme=readme_content,
                folders=intelligent_folders
            )
            
        except Exception as e:
            logger.error(f"Failed to generate intelligent structure: {e}")
            # Fallback to AI-based generation
            return self._generate_ai_fallback_structure(
                repo_path, repo_metadata, ast_analysis, file_contents
            )
    
    def _generate_ai_fallback_structure(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> DocumentationStructure:
        """Fallback AI-based structure generation."""
        
        repo_name = Path(repo_path).name
        context = self._prepare_analysis_context(repo_path, repo_metadata, ast_analysis, file_contents)
        
        # Generate structure using AI
        structure_prompt = f"""You are a technical documentation architect. Analyze this repository and create a structured documentation plan.

Repository: {repo_name}
Context: {context}

Create a comprehensive documentation structure with the following folders and their sections:

1. **architecture/** - System design and high-level structure
2. **components/** - Detailed component documentation  
3. **development/** - Development guides and processes

For each folder, define specific sections that should be created. Return your response in this EXACT JSON format:

{{
    "folders": [
        {{
            "name": "architecture",
            "title": "Architecture Documentation",
            "description": "System design and architectural decisions",
            "sections": [
                {{
                    "name": "overview",
                    "title": "System Overview", 
                    "description": "High-level system architecture and design patterns"
                }},
                {{
                    "name": "components",
                    "title": "Core Components",
                    "description": "Main architectural components and their relationships"
                }}
            ]
        }},
        {{
            "name": "components", 
            "title": "Component Documentation",
            "description": "Detailed documentation for each system component",
            "sections": [
                {{
                    "name": "core",
                    "title": "Core Components",
                    "description": "Essential system components"
                }}
            ]
        }},
        {{
            "name": "development",
            "title": "Development Guide", 
            "description": "Development setup, workflows, and guidelines",
            "sections": [
                {{
                    "name": "setup",
                    "title": "Development Setup",
                    "description": "How to set up the development environment"
                }}
            ]
        }}
    ]
}}

Analyze the repository contents and customize the sections based on what you find. Include only sections that are relevant to this specific codebase."""

        try:
            structure_response = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": structure_prompt}],
                temperature=0,
                max_tokens=2000
            )
            
            # Parse the JSON response
            try:
                structure_data = json.loads(structure_response)
                folders = []
                
                for folder_data in structure_data.get('folders', []):
                    sections = []
                    for section_data in folder_data.get('sections', []):
                        section = DocumentationSection(
                            name=section_data['name'],
                            title=section_data['title'],
                            description=section_data['description']
                        )
                        sections.append(section)
                    
                    folder = DocumentationFolder(
                        name=folder_data['name'],
                        title=folder_data['title'],
                        description=folder_data['description'],
                        sections=sections
                    )
                    folders.append(folder)
                
                # Generate README content
                readme_content = self._generate_readme(repo_path, repo_metadata, ast_analysis, file_contents)
                
                return DocumentationStructure(
                    readme=readme_content,
                    folders=folders
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse structure JSON: {e}")
                # Return default structure
                return self._create_default_structure(repo_path, repo_metadata, ast_analysis, file_contents)
                
        except Exception as e:
            logger.error(f"Failed to generate documentation structure: {e}")
            return self._create_default_structure(repo_path, repo_metadata, ast_analysis, file_contents)
    
    def _create_default_structure(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> DocumentationStructure:
        """Create a default documentation structure when AI generation fails."""
        
        # Default architecture sections
        arch_sections = [
            DocumentationSection("overview", "System Overview", "High-level system architecture"),
            DocumentationSection("components", "Core Components", "Main architectural components"),
            DocumentationSection("data-flow", "Data Flow", "How data moves through the system"),
            DocumentationSection("patterns", "Design Patterns", "Architectural patterns used")
        ]
        
        # Default component sections based on detected components
        comp_sections = [
            DocumentationSection("core", "Core Components", "Essential system components"),
            DocumentationSection("utilities", "Utility Components", "Helper and utility components")
        ]
        
        # Add API section if APIs detected
        if self._has_apis(ast_analysis):
            comp_sections.append(
                DocumentationSection("api", "API Components", "API endpoints and handlers")
            )
        
        # Default development sections
        dev_sections = [
            DocumentationSection("setup", "Development Setup", "How to set up the development environment"),
            DocumentationSection("workflow", "Development Workflow", "Development process and best practices"),
            DocumentationSection("testing", "Testing Guide", "How to test the application"),
            DocumentationSection("contributing", "Contributing", "Guidelines for contributing to the project")
        ]
        
        folders = [
            DocumentationFolder("architecture", "Architecture Documentation", 
                              "System design and architectural decisions", arch_sections),
            DocumentationFolder("components", "Component Documentation", 
                              "Detailed documentation for each system component", comp_sections), 
            DocumentationFolder("development", "Development Guide",
                              "Development setup, workflows, and guidelines", dev_sections)
        ]
        
        readme_content = self._generate_readme(repo_path, repo_metadata, ast_analysis, file_contents)
        
        return DocumentationStructure(readme=readme_content, folders=folders)
    
    def generate_section_content(
        self,
        section: DocumentationSection,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Generate enhanced content for a specific documentation section with diagrams and examples."""
        
        repo_name = Path(repo_path).name
        
        # Generate base content with AI
        base_content = self._generate_base_section_content(
            section, folder, repo_path, repo_metadata, ast_analysis, file_contents
        )
        
        # Enhance with diagrams and examples
        enhanced_content = self._enhance_section_with_visuals_and_examples(
            base_content, section, folder, repo_path, repo_metadata, ast_analysis, file_contents
        )
        
        return enhanced_content
    
    def _generate_base_section_content(
        self,
        section: DocumentationSection,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Generate base content using AI."""
        
        repo_name = Path(repo_path).name
        context = self._prepare_enhanced_section_context(
            section, folder, repo_path, repo_metadata, ast_analysis, file_contents
        )
        
        prompt = f"""You are a technical documentation expert. Generate focused content for this documentation section:

Repository: {repo_name}
Folder: {folder.title}
Section: {section.title}
Description: {section.description}

Context:
{context}

Generate comprehensive content for this specific section. Focus ONLY on the topic indicated by the section title and description. 

Requirements:
- Write in clear, professional markdown
- Include practical examples where relevant
- Focus specifically on the section topic - don't include content that belongs in other sections
- Maximum 800 words unless more detail is specifically needed
- Use appropriate markdown headers (start with ##)
- Include code examples if relevant to this section
- Leave space for diagrams with placeholder comments like <!-- DIAGRAM_PLACEHOLDER -->

Section Content:"""

        try:
            content = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=3000
            )
            return content.strip()
        except Exception as e:
            logger.error(f"Failed to generate content for section {section.name}: {e}")
            return f"## {section.title}\n\n{section.description}\n\n*Content generation failed. Please update manually.*"
    
    def _enhance_section_with_visuals_and_examples(
        self,
        base_content: str,
        section: DocumentationSection,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Enhance section content with diagrams, examples, and visual elements."""
        
        enhanced_content = base_content
        
        # Add appropriate diagrams based on section type
        diagram_content = self._generate_section_diagrams(
            section, folder, repo_path, repo_metadata, ast_analysis, file_contents
        )
        
        # Add relevant examples
        examples_content = self._generate_section_examples(
            section, folder, repo_path, repo_metadata, ast_analysis, file_contents
        )
        
        # Insert diagrams at appropriate locations
        if diagram_content:
            if "<!-- DIAGRAM_PLACEHOLDER -->" in enhanced_content:
                enhanced_content = enhanced_content.replace("<!-- DIAGRAM_PLACEHOLDER -->", diagram_content)
            else:
                # Insert after the first heading
                lines = enhanced_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('##'):
                        lines.insert(i + 2, diagram_content)
                        break
                enhanced_content = '\n'.join(lines)
        
        # Append examples at the end
        if examples_content:
            enhanced_content += "\n\n" + examples_content
        
        return enhanced_content
    
    def _generate_section_diagrams(
        self,
        section: DocumentationSection,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Generate appropriate diagrams for the section."""
        
        diagrams = []
        
        try:
            if folder.name == "architecture":
                if section.name in ["overview", "components"]:
                    # Generate architecture diagram
                    arch_diagram = self.diagram_generator.generate_architecture_diagram(
                        repo_path, repo_metadata, ast_analysis, file_contents, 'mermaid'
                    )
                    diagrams.append(f"### System Architecture\n\n{arch_diagram}")
                
                elif section.name == "data-flow":
                    # Generate data flow diagram
                    all_apis = []
                    for analysis in ast_analysis.values():
                        all_apis.extend(analysis.apis)
                    
                    if all_apis:
                        flow_diagram = self.diagram_generator.generate_data_flow_diagram(
                            ast_analysis, all_apis, 'mermaid'
                        )
                        diagrams.append(f"### Data Flow\n\n{flow_diagram}")
            
            elif folder.name == "components":
                # Generate component diagram
                components = []
                for analysis in ast_analysis.values():
                    for cls in analysis.classes:
                        components.append({
                            'name': cls['name'],
                            'methods': len(cls.get('methods', [])),
                            'properties': len(cls.get('properties', []))
                        })
                
                if components:
                    comp_diagram = self.diagram_generator.generate_component_diagram(
                        components, 'mermaid'
                    )
                    diagrams.append(f"### Component Overview\n\n{comp_diagram}")
            
            elif folder.name == "apis":
                # Generate API flow diagram
                all_apis = []
                for analysis in ast_analysis.values():
                    all_apis.extend(analysis.apis)
                
                if all_apis:
                    api_diagram = self.diagram_generator.generate_data_flow_diagram(
                        ast_analysis, all_apis, 'mermaid'
                    )
                    diagrams.append(f"### API Request Flow\n\n{api_diagram}")
        
        except Exception as e:
            logger.warning(f"Failed to generate diagrams for {section.name}: {e}")
        
        return "\n\n".join(diagrams) if diagrams else ""
    
    def _generate_section_examples(
        self,
        section: DocumentationSection,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Generate relevant examples for the section."""
        
        examples = []
        
        try:
            # Extract examples based on section type
            if folder.name == "development" and section.name == "setup":
                # Setup examples
                config_examples = self.example_extractor.extract_configuration_usage(
                    repo_metadata.get('config_files', []), file_contents
                )
                if config_examples:
                    examples.append("## Configuration Examples\n")
                    for example in config_examples[:3]:
                        examples.append(f"### {example['description']}\n")
                        examples.append(f"```{example['config_type']}\n{example['content'][:500]}...\n```\n")
            
            elif folder.name == "apis":
                # API examples
                all_apis = []
                for analysis in ast_analysis.values():
                    all_apis.extend(analysis.apis)
                
                api_examples = self.example_extractor.extract_api_examples(all_apis, file_contents)
                if api_examples:
                    examples.append("## API Usage Examples\n")
                    for example in api_examples[:5]:
                        examples.append(f"### {example['description']}\n")
                        if example['type'] == 'api_curl':
                            examples.append(f"```bash\n{example['curl']}\n```\n")
                        else:
                            examples.append(f"```javascript\n{example['usage']}\n```\n")
            
            elif folder.name == "cli":
                # CLI examples
                usage_examples = self.example_extractor.extract_usage_examples(ast_analysis, file_contents)
                cli_examples = usage_examples.get('cli_examples', [])
                
                if cli_examples:
                    examples.append("## CLI Usage Examples\n")
                    for example in cli_examples[:3]:
                        examples.append(f"### {example['description']}\n")
                        examples.append(f"```bash\n{example['usage']}\n```\n")
            
            elif folder.name == "components":
                # Component usage examples
                usage_examples = self.example_extractor.extract_usage_examples(ast_analysis, file_contents)
                code_examples = usage_examples.get('code_examples', [])
                
                if code_examples:
                    examples.append("## Component Usage Examples\n")
                    for example in code_examples[:3]:
                        if example['type'] == 'initialization':
                            examples.append(f"### {example['class']} Initialization\n")
                            examples.append(f"```python\n{example['example']}\n```\n")
        
        except Exception as e:
            logger.warning(f"Failed to generate examples for {section.name}: {e}")
        
        return "".join(examples) if examples else ""
    
    def generate_folder_structure(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate the complete folder-based documentation structure."""
        
        # First, generate the structure
        doc_structure = self.generate_documentation_structure(
            repo_path, repo_metadata, ast_analysis, file_contents
        )
        
        # Then generate content for each section
        result = {
            "README.md": doc_structure.readme,
            "folders": {}
        }
        
        for folder in doc_structure.folders:
            folder_content = {}
            
            # Generate an index file for the folder
            folder_index = self._generate_folder_index(folder, repo_path, repo_metadata, ast_analysis, file_contents)
            folder_content["README.md"] = folder_index
            
            # Generate content for each section
            for section in folder.sections:
                section_content = self.generate_section_content(
                    section, folder, repo_path, repo_metadata, ast_analysis, file_contents
                )
                folder_content[f"{section.name}.md"] = section_content
            
            result["folders"][folder.name] = folder_content
        
        return result
    
    def _generate_folder_index(
        self,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Generate an index/README file for a documentation folder."""
        
        repo_name = Path(repo_path).name
        
        content = f"""# {folder.title}

{folder.description}

## Sections

"""
        
        for section in folder.sections:
            content += f"- **[{section.title}]({section.name}.md)**: {section.description}\n"
        
        content += f"\n---\n\n*Documentation for {repo_name}*"
        
        return content
    
    def _prepare_analysis_context(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Prepare comprehensive context for structure analysis."""
        
        repo_name = Path(repo_path).name
        context = f"""
# Repository Analysis: {repo_name}

## Basic Information
- **Repository**: {repo_name}
- **Primary Language**: {repo_metadata.get('primary_language', 'Unknown')}
- **Total Files**: {repo_metadata.get('file_count', 0)}
- **Configuration Files**: {', '.join(repo_metadata.get('config_files', [])[:5])}

## Code Analysis Summary
"""
        
        # Collect analysis summary
        all_classes = []
        all_functions = []
        all_apis = []
        
        for file_path, analysis in ast_analysis.items():
            all_classes.extend(analysis.classes)
            all_functions.extend(analysis.functions)
            all_apis.extend(analysis.apis)
        
        context += f"- **Total Classes**: {len(all_classes)}\n"
        context += f"- **Total Functions**: {len(all_functions)}\n"
        context += f"- **API Endpoints**: {len(all_apis)}\n"
        
        # Add key components
        if all_classes:
            key_classes = [cls['name'] for cls in all_classes[:10]]
            context += f"- **Key Classes**: {', '.join(key_classes)}\n"
        
        # Add existing documentation
        doc_files = [f for f in file_contents if f.get('extension') in ['.md', '.txt', '.rst']]
        if doc_files:
            context += f"\n## Existing Documentation\n"
            for doc in doc_files[:3]:
                context += f"- {doc['name']}\n"
        
        return context
    
    def _generate_enhanced_readme(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Generate enhanced README with diagrams and examples."""
        
        # Generate base README
        base_readme = self._generate_readme(repo_path, repo_metadata, ast_analysis, file_contents)
        
        # Add architecture diagram at the beginning
        try:
            arch_diagram = self.diagram_generator.generate_architecture_diagram(
                repo_path, repo_metadata, ast_analysis, file_contents, 'mermaid'
            )
            
            # Insert diagram after the description
            lines = base_readme.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('##') and ('feature' in line.lower() or 'overview' in line.lower()):
                    lines.insert(i, f"\n## Architecture Overview\n\n{arch_diagram}\n")
                    break
            base_readme = '\n'.join(lines)
            
        except Exception as e:
            logger.warning(f"Failed to add architecture diagram to README: {e}")
        
        # Add quick start examples
        try:
            usage_examples = self.example_extractor.extract_usage_examples(ast_analysis, file_contents)
            
            # Add CLI examples if available
            cli_examples = usage_examples.get('cli_examples', [])
            if cli_examples:
                example_content = "\n\n## Quick Start Examples\n\n"
                for example in cli_examples[:2]:
                    example_content += f"### {example['description']}\n```bash\n{example['usage']}\n```\n\n"
                
                # Insert before the last section
                lines = base_readme.split('\n')
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].startswith('##'):
                        lines.insert(i, example_content)
                        break
                base_readme = '\n'.join(lines)
                
        except Exception as e:
            logger.warning(f"Failed to add examples to README: {e}")
        
        return base_readme
    
    def _prepare_enhanced_section_context(
        self,
        section: DocumentationSection,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Prepare enhanced context with examples and patterns for section content generation."""
        
        context = f"Section Type: {folder.name}/{section.name}\n\n"
        
        # Add relevant context based on folder/section type
        if folder.name == "architecture":
            context += self._get_enhanced_architecture_context(section, repo_metadata, ast_analysis, file_contents)
        elif folder.name == "components":
            context += self._get_enhanced_components_context(section, ast_analysis, file_contents)
        elif folder.name == "development":
            context += self._get_enhanced_development_context(section, repo_metadata, file_contents)
        elif folder.name == "apis":
            context += self._get_enhanced_api_context(section, ast_analysis, file_contents)
        elif folder.name == "cli":
            context += self._get_enhanced_cli_context(section, ast_analysis, file_contents)
        else:
            context += self._get_development_context(section, repo_metadata, file_contents)
        
        return context
    
    def _get_enhanced_architecture_context(
        self,
        section: DocumentationSection,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Get enhanced architecture-specific context with patterns and examples."""
        
        context = "Enhanced Architecture Context:\n"
        context += f"- Primary Language: {repo_metadata.get('primary_language')}\n"
        context += f"- Config Files: {', '.join(repo_metadata.get('config_files', [])[:5])}\n"
        
        # Add component analysis with patterns
        all_classes = []
        patterns = set()
        component_types = {}
        
        for analysis in ast_analysis.values():
            all_classes.extend(analysis.classes)
            for cls in analysis.classes:
                name_lower = cls['name'].lower()
                if 'manager' in name_lower:
                    patterns.add('Manager Pattern')
                    component_types['managers'] = component_types.get('managers', 0) + 1
                elif 'agent' in name_lower:
                    patterns.add('Agent Pattern')
                    component_types['agents'] = component_types.get('agents', 0) + 1
                elif 'client' in name_lower:
                    patterns.add('Client Pattern')
                    component_types['clients'] = component_types.get('clients', 0) + 1
                elif 'service' in name_lower:
                    patterns.add('Service Layer Pattern')
                    component_types['services'] = component_types.get('services', 0) + 1
        
        context += f"- Detected Patterns: {', '.join(patterns)}\n"
        context += f"- Component Distribution: {', '.join([f'{k}: {v}' for k, v in component_types.items()])}\n"
        context += f"- Key Components: {', '.join([cls['name'] for cls in all_classes[:5]])}\n"
        
        # Add architectural indicators
        has_api = any(analysis.apis for analysis in ast_analysis.values())
        has_database = any('db' in f['path'].lower() or 'database' in f['path'].lower() for f in file_contents)
        has_cli = any('cli' in f['path'].lower() or 'command' in f['path'].lower() for f in file_contents)
        
        context += f"- Architecture Type: "
        arch_types = []
        if has_api:
            arch_types.append("REST API")
        if has_database:
            arch_types.append("Database Layer")
        if has_cli:
            arch_types.append("CLI Application")
        context += ", ".join(arch_types) if arch_types else "Monolithic"
        context += "\n"
        
        return context
    
    def _get_enhanced_components_context(
        self,
        section: DocumentationSection,
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Get enhanced component-specific context with usage patterns."""
        
        context = "Enhanced Component Context:\n"
        
        all_classes = []
        all_functions = []
        
        for file_path, analysis in ast_analysis.items():
            all_classes.extend([{**cls, 'file': file_path} for cls in analysis.classes])
            all_functions.extend([{**func, 'file': file_path} for func in analysis.functions])
        
        # Group by file/module with more detail
        context += "Components by Module:\n"
        module_components = {}
        for cls in all_classes:
            module = Path(cls['file']).stem
            if module not in module_components:
                module_components[module] = []
            module_components[module].append(cls)
        
        for module, components in list(module_components.items())[:5]:
            context += f"- {module}: {', '.join([c['name'] for c in components])}\n"
        
        # Add component relationships
        inheritance_relationships = []
        for cls in all_classes:
            if cls.get('bases'):
                for base in cls['bases']:
                    inheritance_relationships.append(f"{base} -> {cls['name']}")
        
        if inheritance_relationships:
            context += f"- Inheritance Relationships: {', '.join(inheritance_relationships[:3])}\n"
        
        return context
    
    def _get_enhanced_development_context(
        self,
        section: DocumentationSection,
        repo_metadata: Dict[str, Any],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Get enhanced development-specific context with setup patterns."""
        
        context = "Enhanced Development Context:\n"
        context += f"- Primary Language: {repo_metadata.get('primary_language')}\n"
        context += f"- Configuration Files: {', '.join(repo_metadata.get('config_files', [])[:5])}\n"
        
        # Analyze setup and dependency patterns
        setup_files = {}
        for f in file_contents:
            name_lower = f['name'].lower()
            if name_lower in ['requirements.txt', 'package.json', 'dockerfile', 'makefile', 'setup.py', 'pyproject.toml']:
                setup_files[name_lower] = f.get('content', '')[:200]
        
        if setup_files:
            context += "Setup Files Analysis:\n"
            for filename, content in setup_files.items():
                # Detect key dependencies
                if filename == 'requirements.txt':
                    deps = [line.split('==')[0].split('>=')[0] for line in content.split('\n') if line.strip()]
                    context += f"- Python dependencies: {', '.join(deps[:5])}\n"
                elif filename == 'package.json':
                    context += f"- Node.js project with package.json\n"
                elif filename == 'dockerfile':
                    context += f"- Docker containerized application\n"
        
        # Detect development patterns
        has_tests = any('test' in f['path'].lower() for f in file_contents)
        has_ci = any('.github' in f['path'] or '.gitlab' in f['path'] for f in file_contents)
        has_docs = any(f['extension'] in ['.md', '.rst'] for f in file_contents)
        
        context += f"- Development Features: "
        features = []
        if has_tests:
            features.append("Testing")
        if has_ci:
            features.append("CI/CD")
        if has_docs:
            features.append("Documentation")
        context += ", ".join(features) if features else "Basic"
        context += "\n"
        
        return context
    
    def _get_enhanced_api_context(
        self,
        section: DocumentationSection,
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Get enhanced API-specific context with endpoint analysis."""
        
        context = "Enhanced API Context:\n"
        
        all_apis = []
        for analysis in ast_analysis.values():
            all_apis.extend(analysis.apis)
        
        context += f"- Total API Endpoints: {len(all_apis)}\n"
        
        # Group by HTTP method
        method_counts = {}
        for api in all_apis:
            method = api.get('method', 'GET')
            method_counts[method] = method_counts.get(method, 0) + 1
        
        context += f"- HTTP Methods: {', '.join([f'{k}: {v}' for k, v in method_counts.items()])}\n"
        
        # Group by path prefix
        path_groups = {}
        for api in all_apis:
            path = api.get('path', '/')
            if path.startswith('/api/'):
                group = path.split('/')[2] if len(path.split('/')) > 2 else 'general'
            else:
                group = 'general'
            path_groups[group] = path_groups.get(group, 0) + 1
        
        context += f"- API Groups: {', '.join([f'{k}: {v}' for k, v in path_groups.items()])}\n"
        
        return context
    
    def _get_enhanced_cli_context(
        self,
        section: DocumentationSection,
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Get enhanced CLI-specific context with command analysis."""
        
        context = "Enhanced CLI Context:\n"
        
        # Look for CLI frameworks
        cli_frameworks = []
        for f in file_contents:
            content = f.get('content', '').lower()
            if 'click' in content:
                cli_frameworks.append('Click')
            if 'argparse' in content:
                cli_frameworks.append('Argparse')
            if 'typer' in content:
                cli_frameworks.append('Typer')
        
        if cli_frameworks:
            context += f"- CLI Frameworks: {', '.join(set(cli_frameworks))}\n"
        
        # Look for command patterns
        command_files = [f for f in file_contents if 'cli' in f['path'].lower() or 'command' in f['path'].lower()]
        context += f"- CLI Files Found: {len(command_files)}\n"
        
        return context
    
    def _prepare_section_context(
        self,
        section: DocumentationSection,
        folder: DocumentationFolder,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Prepare focused context for section content generation."""
        
        context = f"Section Type: {folder.name}/{section.name}\n\n"
        
        # Add relevant context based on folder/section type
        if folder.name == "architecture":
            context += self._get_architecture_context(section, repo_metadata, ast_analysis)
        elif folder.name == "components":
            context += self._get_components_context(section, ast_analysis)
        elif folder.name == "development":
            context += self._get_development_context(section, repo_metadata, file_contents)
        
        return context
    
    def _get_architecture_context(
        self,
        section: DocumentationSection,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis]
    ) -> str:
        """Get architecture-specific context."""
        context = "Architecture Context:\n"
        context += f"- Primary Language: {repo_metadata.get('primary_language')}\n"
        context += f"- Config Files: {', '.join(repo_metadata.get('config_files', [])[:5])}\n"
        
        # Add component analysis
        all_classes = []
        patterns = set()
        
        for analysis in ast_analysis.values():
            all_classes.extend(analysis.classes)
            for cls in analysis.classes:
                name_lower = cls['name'].lower()
                if 'manager' in name_lower:
                    patterns.add('Manager Pattern')
                elif 'agent' in name_lower:
                    patterns.add('Agent Pattern')
                elif 'client' in name_lower:
                    patterns.add('Client Pattern')
        
        context += f"- Detected Patterns: {', '.join(patterns)}\n"
        context += f"- Key Components: {', '.join([cls['name'] for cls in all_classes[:5]])}\n"
        
        return context
    
    def _get_components_context(
        self,
        section: DocumentationSection,
        ast_analysis: Dict[str, ASTAnalysis]
    ) -> str:
        """Get component-specific context."""
        context = "Component Context:\n"
        
        all_classes = []
        all_functions = []
        
        for file_path, analysis in ast_analysis.items():
            all_classes.extend([{**cls, 'file': file_path} for cls in analysis.classes])
            all_functions.extend([{**func, 'file': file_path} for func in analysis.functions])
        
        # Group by file/module
        context += "Classes by Module:\n"
        for cls in all_classes[:10]:
            context += f"- {cls['name']} ({Path(cls['file']).name})\n"
        
        return context
    
    def _get_development_context(
        self,
        section: DocumentationSection,
        repo_metadata: Dict[str, Any],
        file_contents: List[Dict[str, Any]]
    ) -> str:
        """Get development-specific context."""
        context = "Development Context:\n"
        context += f"- Primary Language: {repo_metadata.get('primary_language')}\n"
        context += f"- Configuration Files: {', '.join(repo_metadata.get('config_files', [])[:5])}\n"
        
        # Add setup-relevant files
        setup_files = [f for f in file_contents if f['name'].lower() in [
            'requirements.txt', 'package.json', 'dockerfile', 'makefile', 'setup.py'
        ]]
        
        if setup_files:
            context += "Setup Files Found:\n"
            for f in setup_files:
                context += f"- {f['name']}\n"
        
        return context
    
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
6. **Links to Other Documentation**: References to architecture/, components/, development/ folders

REQUIREMENTS:
- Keep it concise and user-focused
- Focus on getting users started quickly
- Avoid technical implementation details
- Maximum 100 lines
- Include actual project-specific information, not generic templates
- Reference other documentation folders for detailed information

README Content:"""

        try:
            readme_content = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=4000
            )
            return readme_content
        except Exception as e:
            return f"# {repo_name}\n\nFailed to generate README: {str(e)}"
    
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
    
    def _has_apis(self, ast_analysis: Dict[str, ASTAnalysis]) -> bool:
        """Check if any APIs were found."""
        return any(analysis.apis for analysis in ast_analysis.values())
