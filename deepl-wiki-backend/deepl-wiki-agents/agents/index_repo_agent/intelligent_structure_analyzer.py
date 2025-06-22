"""
Intelligent structure analyzer for automatically inferring documentation sections
based on file types, folder hierarchy, and code structure.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict
from .models import ASTAnalysis, DocumentationSection, DocumentationFolder

logger = logging.getLogger(__name__)

class IntelligentStructureAnalyzer:
    """Analyze repository structure and intelligently infer documentation sections."""
    
    def __init__(self):
        self.section_patterns = {
            'getting_started': {
                'triggers': ['main.py', 'app.py', 'cli.py', '__main__.py', 'setup.py'],
                'keywords': ['install', 'setup', 'start', 'init', 'bootstrap'],
                'priority': 1
            },
            'core_modules': {
                'triggers': ['core/', 'lib/', 'src/', 'main/'],
                'keywords': ['engine', 'processor', 'manager', 'handler', 'service'],
                'priority': 2
            },
            'data_models': {
                'triggers': ['models/', 'schema/', 'entities/', 'types/'],
                'keywords': ['model', 'schema', 'entity', 'type', 'data'],
                'priority': 3
            },
            'apis_services': {
                'triggers': ['api/', 'routes/', 'endpoints/', 'services/'],
                'keywords': ['api', 'endpoint', 'route', 'service', 'handler'],
                'priority': 4
            },
            'cli_tooling': {
                'triggers': ['cli/', 'bin/', 'scripts/', 'tools/'],
                'keywords': ['cli', 'command', 'script', 'tool', 'utility'],
                'priority': 5
            },
            'tests': {
                'triggers': ['test/', 'tests/', 'spec/', '__tests__/'],
                'keywords': ['test', 'spec', 'mock', 'fixture'],
                'priority': 6
            },
            'deployment_ci': {
                'triggers': ['.github/', '.gitlab/', 'deploy/', 'ci/', 'docker'],
                'keywords': ['deploy', 'ci', 'cd', 'docker', 'k8s', 'workflow'],
                'priority': 7
            },
            'contributing': {
                'triggers': ['CONTRIBUTING.md', '.github/CONTRIBUTING.md'],
                'keywords': ['contribute', 'guidelines', 'development'],
                'priority': 8
            }
        }
        
        self.component_patterns = {
            'agents': ['agent', 'worker', 'processor'],
            'managers': ['manager', 'controller', 'coordinator', 'supervisor'],
            'services': ['service', 'provider', 'handler', 'gateway'],
            'clients': ['client', 'connector', 'adapter', 'driver'],
            'models': ['model', 'schema', 'entity', 'dto'],
            'utilities': ['util', 'helper', 'tool', 'common'],
            'configurations': ['config', 'setting', 'option', 'env'],
            'databases': ['db', 'database', 'storage', 'repository', 'dao'],
            'apis': ['api', 'router', 'endpoint', 'route'],
            'ui_components': ['component', 'widget', 'view', 'page']
        }
    
    def analyze_repository_structure(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> List[DocumentationFolder]:
        """Analyze repository and generate intelligent documentation structure."""
        
        # Analyze directory structure
        directory_analysis = self._analyze_directories(file_contents)
        
        # Analyze code components
        component_analysis = self._analyze_components(ast_analysis)
        
        # Analyze file patterns
        file_pattern_analysis = self._analyze_file_patterns(file_contents)
        
        # Analyze technology stack
        tech_stack_analysis = self._analyze_technology_stack(repo_metadata, file_contents)
        
        # Generate intelligent sections
        folders = self._generate_intelligent_folders(
            directory_analysis,
            component_analysis,
            file_pattern_analysis,
            tech_stack_analysis,
            repo_metadata
        )
        
        return folders
    
    def _analyze_directories(self, file_contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze directory structure to understand project organization."""
        
        directories = defaultdict(list)
        dir_stats = defaultdict(lambda: {'files': 0, 'code_files': 0, 'size': 0})
        
        for file_info in file_contents:
            file_path = Path(file_info['path'])
            dir_name = str(file_path.parent)
            
            directories[dir_name].append(file_info)
            dir_stats[dir_name]['files'] += 1
            dir_stats[dir_name]['size'] += file_info.get('size', 0)
            
            if file_info.get('category') == 'code':
                dir_stats[dir_name]['code_files'] += 1
        
        # Find important directories
        important_dirs = {}
        for dir_name, stats in dir_stats.items():
            if stats['code_files'] > 2 or stats['files'] > 5:
                importance = stats['code_files'] * 2 + stats['files']
                important_dirs[dir_name] = {
                    'importance': importance,
                    'stats': stats,
                    'files': directories[dir_name]
                }
        
        return {
            'all_directories': directories,
            'directory_stats': dir_stats,
            'important_directories': important_dirs
        }
    
    def _analyze_components(self, ast_analysis: Dict[str, ASTAnalysis]) -> Dict[str, Any]:
        """Analyze code components to understand architecture patterns."""
        
        component_types = defaultdict(list)
        inheritance_graph = defaultdict(list)
        api_endpoints = []
        
        for file_path, analysis in ast_analysis.items():
            # Categorize classes by patterns
            for cls in analysis.classes:
                cls_name = cls['name'].lower()
                component_type = 'other'
                
                for comp_type, patterns in self.component_patterns.items():
                    if any(pattern in cls_name for pattern in patterns):
                        component_type = comp_type
                        break
                
                component_types[component_type].append({
                    'name': cls['name'],
                    'file': file_path,
                    'methods': len(cls.get('methods', [])),
                    'properties': len(cls.get('properties', []))
                })
                
                # Build inheritance graph
                for base in cls.get('bases', []):
                    inheritance_graph[base].append(cls['name'])
            
            # Collect API endpoints
            api_endpoints.extend(analysis.apis)
        
        return {
            'component_types': dict(component_types),
            'inheritance_graph': dict(inheritance_graph),
            'api_endpoints': api_endpoints,
            'total_classes': sum(len(analysis.classes) for analysis in ast_analysis.values()),
            'total_functions': sum(len(analysis.functions) for analysis in ast_analysis.values())
        }
    
    def _analyze_file_patterns(self, file_contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze file patterns to understand project type and structure."""
        
        patterns = {
            'has_web_framework': False,
            'has_cli': False,
            'has_tests': False,
            'has_database': False,
            'has_api': False,
            'has_frontend': False,
            'has_docker': False,
            'has_ci_cd': False
        }
        
        web_frameworks = ['flask', 'django', 'fastapi', 'express', 'react', 'vue', 'angular']
        cli_indicators = ['click', 'argparse', 'commander', 'yargs']
        test_indicators = ['pytest', 'unittest', 'jest', 'mocha']
        db_indicators = ['sqlalchemy', 'mongoose', 'prisma', 'sequelize']
        
        for file_info in file_contents:
            content_lower = file_info.get('content', '').lower()
            file_name = file_info['name'].lower()
            
            # Check for web frameworks
            if any(fw in content_lower for fw in web_frameworks):
                patterns['has_web_framework'] = True
            
            # Check for CLI tools
            if any(cli in content_lower for cli in cli_indicators):
                patterns['has_cli'] = True
            
            # Check for tests
            if (any(test in content_lower for test in test_indicators) or
                'test' in file_info['path'].lower()):
                patterns['has_tests'] = True
            
            # Check for database
            if any(db in content_lower for db in db_indicators):
                patterns['has_database'] = True
            
            # Check for API
            if ('api' in file_info['path'].lower() or
                'endpoint' in content_lower or
                'route' in content_lower):
                patterns['has_api'] = True
            
            # Check for frontend
            if file_info['extension'] in ['.jsx', '.tsx', '.vue', '.html', '.css', '.scss']:
                patterns['has_frontend'] = True
            
            # Check for Docker
            if 'dockerfile' in file_name or 'docker-compose' in file_name:
                patterns['has_docker'] = True
            
            # Check for CI/CD
            if ('.github' in file_info['path'] or
                '.gitlab' in file_info['path'] or
                'ci' in file_name):
                patterns['has_ci_cd'] = True
        
        return patterns
    
    def _analyze_technology_stack(
        self,
        repo_metadata: Dict[str, Any],
        file_contents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze technology stack and project characteristics."""
        
        primary_language = repo_metadata.get('primary_language', 'Unknown')
        
        tech_stack = {
            'primary_language': primary_language,
            'frameworks': [],
            'databases': [],
            'deployment_tools': [],
            'testing_frameworks': [],
            'build_tools': []
        }
        
        # Framework detection patterns
        framework_patterns = {
            'Python': ['flask', 'django', 'fastapi', 'pyramid', 'tornado'],
            'JavaScript': ['express', 'koa', 'hapi', 'react', 'vue', 'angular'],
            'TypeScript': ['nest', 'angular', 'react', 'vue'],
            'Go': ['gin', 'echo', 'fiber', 'gorilla'],
            'Java': ['spring', 'struts', 'jersey'],
            'C#': ['asp.net', 'mvc', 'webapi']
        }
        
        # Analyze package files for dependencies
        for file_info in file_contents:
            if file_info['name'] in ['package.json', 'requirements.txt', 'go.mod', 'pom.xml']:
                content = file_info.get('content', '').lower()
                
                # Check for frameworks
                if primary_language in framework_patterns:
                    for framework in framework_patterns[primary_language]:
                        if framework in content:
                            tech_stack['frameworks'].append(framework)
        
        return tech_stack
    
    def _generate_intelligent_folders(
        self,
        directory_analysis: Dict[str, Any],
        component_analysis: Dict[str, Any],
        file_pattern_analysis: Dict[str, Any],
        tech_stack_analysis: Dict[str, Any],
        repo_metadata: Dict[str, Any]
    ) -> List[DocumentationFolder]:
        """Generate intelligent documentation folders based on analysis."""
        
        folders = []
        
        # Always include architecture folder
        arch_sections = self._generate_architecture_sections(
            directory_analysis, component_analysis, tech_stack_analysis
        )
        folders.append(DocumentationFolder(
            name="architecture",
            title="Architecture Documentation",
            description="System design, components, and architectural decisions",
            sections=arch_sections
        ))
        
        # Generate component-specific folders
        component_folders = self._generate_component_folders(component_analysis)
        folders.extend(component_folders)
        
        # Generate API documentation if APIs exist
        if component_analysis['api_endpoints']:
            api_sections = self._generate_api_sections(component_analysis['api_endpoints'])
            folders.append(DocumentationFolder(
                name="apis",
                title="API Documentation",
                description="REST API endpoints and usage",
                sections=api_sections
            ))
        
        # Generate CLI documentation if CLI detected
        if file_pattern_analysis['has_cli']:
            cli_sections = self._generate_cli_sections()
            folders.append(DocumentationFolder(
                name="cli",
                title="Command Line Interface",
                description="CLI commands and usage",
                sections=cli_sections
            ))
        
        # Generate deployment documentation if Docker/CI detected
        if file_pattern_analysis['has_docker'] or file_pattern_analysis['has_ci_cd']:
            deploy_sections = self._generate_deployment_sections(file_pattern_analysis)
            folders.append(DocumentationFolder(
                name="deployment",
                title="Deployment & CI/CD",
                description="Deployment processes and continuous integration",
                sections=deploy_sections
            ))
        
        # Always include development folder
        dev_sections = self._generate_development_sections(
            file_pattern_analysis, tech_stack_analysis
        )
        folders.append(DocumentationFolder(
            name="development",
            title="Development Guide",
            description="Development setup, workflows, and guidelines",
            sections=dev_sections
        ))
        
        return folders
    
    def _generate_architecture_sections(
        self,
        directory_analysis: Dict[str, Any],
        component_analysis: Dict[str, Any],
        tech_stack_analysis: Dict[str, Any]
    ) -> List[DocumentationSection]:
        """Generate architecture-specific sections."""
        
        sections = [
            DocumentationSection(
                name="overview",
                title="System Overview",
                description="High-level system architecture and design principles"
            ),
            DocumentationSection(
                name="components",
                title="Core Components",
                description="Main architectural components and their responsibilities"
            )
        ]
        
        # Add data flow if we have APIs or complex components
        if component_analysis['api_endpoints'] or component_analysis['total_classes'] > 10:
            sections.append(DocumentationSection(
                name="data-flow",
                title="Data Flow",
                description="How data moves through the system"
            ))
        
        # Add design patterns if we have inheritance or complex structure
        if component_analysis['inheritance_graph'] or component_analysis['total_classes'] > 5:
            sections.append(DocumentationSection(
                name="patterns",
                title="Design Patterns",
                description="Architectural patterns and design decisions"
            ))
        
        return sections
    
    def _generate_component_folders(
        self,
        component_analysis: Dict[str, Any]
    ) -> List[DocumentationFolder]:
        """Generate component-specific folders."""
        
        folders = []
        component_types = component_analysis['component_types']
        
        # Group related components
        if any(comp_type in component_types for comp_type in ['agents', 'managers', 'services']):
            business_sections = []
            
            if 'agents' in component_types:
                business_sections.append(DocumentationSection(
                    name="agents",
                    title="Agent Components",
                    description="Autonomous agent components and their capabilities"
                ))
            
            if 'managers' in component_types:
                business_sections.append(DocumentationSection(
                    name="managers",
                    title="Manager Components",
                    description="Management and coordination components"
                ))
            
            if 'services' in component_types:
                business_sections.append(DocumentationSection(
                    name="services",
                    title="Service Components",
                    description="Business logic and service layer components"
                ))
            
            if business_sections:
                folders.append(DocumentationFolder(
                    name="components",
                    title="Business Components",
                    description="Core business logic and processing components",
                    sections=business_sections
                ))
        
        # Data and infrastructure components
        if any(comp_type in component_types for comp_type in ['models', 'databases', 'clients']):
            data_sections = []
            
            if 'models' in component_types:
                data_sections.append(DocumentationSection(
                    name="models",
                    title="Data Models",
                    description="Data structures and model definitions"
                ))
            
            if 'databases' in component_types:
                data_sections.append(DocumentationSection(
                    name="databases",
                    title="Database Components",
                    description="Database access and storage components"
                ))
            
            if 'clients' in component_types:
                data_sections.append(DocumentationSection(
                    name="clients",
                    title="Client Components",
                    description="External service clients and adapters"
                ))
            
            if data_sections:
                folders.append(DocumentationFolder(
                    name="data",
                    title="Data & Infrastructure",
                    description="Data models, storage, and external integrations",
                    sections=data_sections
                ))
        
        return folders
    
    def _generate_api_sections(self, api_endpoints: List[Dict[str, Any]]) -> List[DocumentationSection]:
        """Generate API-specific sections."""
        
        sections = [
            DocumentationSection(
                name="overview",
                title="API Overview",
                description="REST API overview and authentication"
            ),
            DocumentationSection(
                name="endpoints",
                title="Endpoints",
                description="Available API endpoints and their usage"
            )
        ]
        
        # Group endpoints by functionality
        endpoint_groups = defaultdict(list)
        for endpoint in api_endpoints:
            path = endpoint.get('path', '/')
            if path.startswith('/api/'):
                group = path.split('/')[2] if len(path.split('/')) > 2 else 'general'
            else:
                group = 'general'
            endpoint_groups[group].append(endpoint)
        
        # Add sections for different endpoint groups
        for group in endpoint_groups:
            if group != 'general' and len(endpoint_groups[group]) > 1:
                sections.append(DocumentationSection(
                    name=f"{group}-endpoints",
                    title=f"{group.title()} Endpoints",
                    description=f"API endpoints for {group} functionality"
                ))
        
        return sections
    
    def _generate_cli_sections(self) -> List[DocumentationSection]:
        """Generate CLI-specific sections."""
        
        return [
            DocumentationSection(
                name="overview",
                title="CLI Overview",
                description="Command line interface overview and installation"
            ),
            DocumentationSection(
                name="commands",
                title="Available Commands",
                description="All available CLI commands and their usage"
            ),
            DocumentationSection(
                name="examples",
                title="Usage Examples",
                description="Common CLI usage patterns and examples"
            )
        ]
    
    def _generate_deployment_sections(
        self,
        file_pattern_analysis: Dict[str, Any]
    ) -> List[DocumentationSection]:
        """Generate deployment-specific sections."""
        
        sections = []
        
        if file_pattern_analysis['has_docker']:
            sections.append(DocumentationSection(
                name="docker",
                title="Docker Deployment",
                description="Docker containerization and deployment"
            ))
        
        if file_pattern_analysis['has_ci_cd']:
            sections.append(DocumentationSection(
                name="ci-cd",
                title="CI/CD Pipeline",
                description="Continuous integration and deployment pipeline"
            ))
        
        sections.append(DocumentationSection(
            name="production",
            title="Production Deployment",
            description="Production deployment guidelines and best practices"
        ))
        
        return sections
    
    def _generate_development_sections(
        self,
        file_pattern_analysis: Dict[str, Any],
        tech_stack_analysis: Dict[str, Any]
    ) -> List[DocumentationSection]:
        """Generate development-specific sections."""
        
        sections = [
            DocumentationSection(
                name="setup",
                title="Development Setup",
                description="Setting up the development environment"
            ),
            DocumentationSection(
                name="workflow",
                title="Development Workflow",
                description="Development process and best practices"
            )
        ]
        
        if file_pattern_analysis['has_tests']:
            sections.append(DocumentationSection(
                name="testing",
                title="Testing Guide",
                description="Running tests and testing guidelines"
            ))
        
        sections.append(DocumentationSection(
            name="contributing",
            title="Contributing",
            description="Guidelines for contributing to the project"
        ))
        
        return sections
