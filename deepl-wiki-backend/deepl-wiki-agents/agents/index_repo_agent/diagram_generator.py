"""
Enhanced diagram generator for visual documentation using Mermaid, D2, and PlantUML.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from .models import ASTAnalysis

logger = logging.getLogger(__name__)

class DiagramGenerator:
    """Generate visual diagrams for repository documentation."""
    
    def __init__(self):
        self.supported_formats = ['mermaid', 'd2', 'plantuml']
    
    def generate_architecture_diagram(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]],
        format_type: str = 'mermaid'
    ) -> str:
        """Generate high-level architecture diagram."""
        
        if format_type not in self.supported_formats:
            format_type = 'mermaid'
        
        repo_name = Path(repo_path).name
        
        # Analyze components and relationships
        components = self._extract_components(ast_analysis)
        relationships = self._extract_relationships(ast_analysis, file_contents)
        
        if format_type == 'mermaid':
            return self._generate_mermaid_architecture(repo_name, components, relationships)
        elif format_type == 'd2':
            return self._generate_d2_architecture(repo_name, components, relationships)
        elif format_type == 'plantuml':
            return self._generate_plantuml_architecture(repo_name, components, relationships)
        
        return self._generate_mermaid_architecture(repo_name, components, relationships)
    
    def generate_component_diagram(
        self,
        components: List[Dict[str, Any]],
        format_type: str = 'mermaid'
    ) -> str:
        """Generate detailed component interaction diagram."""
        
        if format_type == 'mermaid':
            return self._generate_mermaid_components(components)
        elif format_type == 'd2':
            return self._generate_d2_components(components)
        elif format_type == 'plantuml':
            return self._generate_plantuml_components(components)
        
        return self._generate_mermaid_components(components)
    
    def generate_data_flow_diagram(
        self,
        ast_analysis: Dict[str, ASTAnalysis],
        apis: List[Dict[str, Any]],
        format_type: str = 'mermaid'
    ) -> str:
        """Generate data/request flow diagram."""
        
        if format_type == 'mermaid':
            return self._generate_mermaid_dataflow(ast_analysis, apis)
        elif format_type == 'd2':
            return self._generate_d2_dataflow(ast_analysis, apis)
        elif format_type == 'plantuml':
            return self._generate_plantuml_dataflow(ast_analysis, apis)
        
        return self._generate_mermaid_dataflow(ast_analysis, apis)
    
    def generate_class_diagram(
        self,
        classes: List[Dict[str, Any]],
        format_type: str = 'mermaid'
    ) -> str:
        """Generate class relationship diagram."""
        
        if format_type == 'mermaid':
            return self._generate_mermaid_classes(classes)
        elif format_type == 'd2':
            return self._generate_d2_classes(classes)
        elif format_type == 'plantuml':
            return self._generate_plantuml_classes(classes)
        
        return self._generate_mermaid_classes(classes)
    
    def _extract_components(self, ast_analysis: Dict[str, ASTAnalysis]) -> List[Dict[str, Any]]:
        """Extract high-level components from AST analysis."""
        components = []
        component_patterns = {
            'agent': ['agent', 'worker', 'processor'],
            'manager': ['manager', 'controller', 'coordinator'],
            'service': ['service', 'provider', 'handler'],
            'client': ['client', 'connector', 'adapter'],
            'model': ['model', 'schema', 'entity'],
            'util': ['util', 'helper', 'tool'],
            'config': ['config', 'setting', 'option'],
            'api': ['api', 'router', 'endpoint'],
            'database': ['db', 'database', 'storage', 'repository']
        }
        
        for file_path, analysis in ast_analysis.items():
            for cls in analysis.classes:
                cls_name = cls['name'].lower()
                component_type = 'component'
                
                # Determine component type
                for comp_type, patterns in component_patterns.items():
                    if any(pattern in cls_name for pattern in patterns):
                        component_type = comp_type
                        break
                
                components.append({
                    'name': cls['name'],
                    'type': component_type,
                    'file': file_path,
                    'methods': len(cls.get('methods', [])),
                    'properties': len(cls.get('properties', [])),
                    'bases': cls.get('bases', [])
                })
        
        return components
    
    def _extract_relationships(
        self, 
        ast_analysis: Dict[str, ASTAnalysis], 
        file_contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract relationships between components."""
        relationships = []
        
        # Extract import relationships
        for file_path, analysis in ast_analysis.items():
            for import_module, imported_items in analysis.imports.get('from_imports', {}).items():
                if import_module and not import_module.startswith('.'):
                    relationships.append({
                        'from': Path(file_path).stem,
                        'to': import_module.split('.')[0],
                        'type': 'imports',
                        'items': imported_items
                    })
        
        # Extract inheritance relationships
        for file_path, analysis in ast_analysis.items():
            for cls in analysis.classes:
                for base in cls.get('bases', []):
                    relationships.append({
                        'from': cls['name'],
                        'to': base,
                        'type': 'inherits',
                        'file': file_path
                    })
        
        return relationships
    
    def _generate_mermaid_architecture(
        self, 
        repo_name: str, 
        components: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ) -> str:
        """Generate Mermaid architecture diagram."""
        
        mermaid = f"""```mermaid
graph TB
    subgraph "{repo_name} Architecture"
"""
        
        # Group components by type
        component_groups = {}
        for comp in components:
            comp_type = comp['type']
            if comp_type not in component_groups:
                component_groups[comp_type] = []
            component_groups[comp_type].append(comp)
        
        # Add component groups
        for comp_type, comps in component_groups.items():
            if len(comps) > 1:
                mermaid += f'        subgraph "{comp_type.title()} Layer"\n'
                for comp in comps:
                    mermaid += f'            {comp["name"]}["{comp["name"]}"]\n'
                mermaid += '        end\n'
            else:
                comp = comps[0]
                mermaid += f'        {comp["name"]}["{comp["name"]}"]\n'
        
        # Add relationships
        mermaid += '\n'
        for rel in relationships:
            if rel['type'] == 'imports':
                mermaid += f'        {rel["from"]} --> {rel["to"]}\n'
            elif rel['type'] == 'inherits':
                mermaid += f'        {rel["to"]} <|-- {rel["from"]}\n'
        
        mermaid += '    end\n```'
        return mermaid
    
    def _generate_mermaid_components(self, components: List[Dict[str, Any]]) -> str:
        """Generate Mermaid component diagram."""
        
        mermaid = """```mermaid
graph LR
    subgraph "Component Interactions"
"""
        
        for comp in components:
            mermaid += f'        {comp["name"]}["{comp["name"]}<br/>Methods: {comp["methods"]}<br/>Properties: {comp["properties"]}"]\n'
        
        mermaid += '    end\n```'
        return mermaid
    
    def _generate_mermaid_dataflow(
        self, 
        ast_analysis: Dict[str, ASTAnalysis], 
        apis: List[Dict[str, Any]]
    ) -> str:
        """Generate Mermaid data flow diagram."""
        
        mermaid = """```mermaid
sequenceDiagram
    participant User
    participant API
    participant Service
    participant Database
"""
        
        # Add API interactions
        for api in apis:
            method = api.get('method', 'GET')
            path = api.get('path', '/')
            mermaid += f'    User->>API: {method} {path}\n'
            mermaid += f'    API->>Service: Process Request\n'
            
            if 'database' in api.get('function', '').lower():
                mermaid += f'    Service->>Database: Query/Update\n'
                mermaid += f'    Database->>Service: Result\n'
            
            mermaid += f'    Service->>API: Response\n'
            mermaid += f'    API->>User: JSON Response\n'
        
        mermaid += '```'
        return mermaid
    
    def _generate_mermaid_classes(self, classes: List[Dict[str, Any]]) -> str:
        """Generate Mermaid class diagram."""
        
        mermaid = """```mermaid
classDiagram
"""
        
        for cls in classes:
            class_name = cls['name']
            mermaid += f'    class {class_name} {{\n'
            
            # Add methods
            for method in cls.get('methods', []):
                method_name = method.get('name', 'unknown')
                mermaid += f'        +{method_name}()\n'
            
            # Add properties
            for prop in cls.get('properties', []):
                prop_name = prop.get('name', 'unknown')
                mermaid += f'        -{prop_name}\n'
            
            mermaid += '    }\n'
            
            # Add inheritance
            for base in cls.get('bases', []):
                mermaid += f'    {base} <|-- {class_name}\n'
        
        mermaid += '```'
        return mermaid
    
    def _generate_d2_architecture(
        self, 
        repo_name: str, 
        components: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ) -> str:
        """Generate D2 architecture diagram."""
        
        d2 = f"""```d2
title: {repo_name} Architecture

# Components
"""
        
        # Add components
        for comp in components:
            d2 += f'{comp["name"]}: {comp["name"]} ({comp["type"]})\n'
        
        d2 += '\n# Relationships\n'
        
        # Add relationships
        for rel in relationships:
            if rel['type'] == 'imports':
                d2 += f'{rel["from"]} -> {rel["to"]}: imports\n'
            elif rel['type'] == 'inherits':
                d2 += f'{rel["to"]} -> {rel["from"]}: inherits\n'
        
        d2 += '```'
        return d2
    
    def _generate_d2_components(self, components: List[Dict[str, Any]]) -> str:
        """Generate D2 component diagram."""
        
        d2 = """```d2
title: Component Details

"""
        
        for comp in components:
            d2 += f"""{comp["name"]}: {{
    shape: class
    Methods: {comp["methods"]}
    Properties: {comp["properties"]}
}}

"""
        
        d2 += '```'
        return d2
    
    def _generate_d2_dataflow(
        self, 
        ast_analysis: Dict[str, ASTAnalysis], 
        apis: List[Dict[str, Any]]
    ) -> str:
        """Generate D2 data flow diagram."""
        
        d2 = """```d2
title: Data Flow

User -> API: HTTP Request
API -> Service: Process
Service -> Database: Query
Database -> Service: Result
Service -> API: Response
API -> User: JSON Response
```"""
        
        return d2
    
    def _generate_d2_classes(self, classes: List[Dict[str, Any]]) -> str:
        """Generate D2 class diagram."""
        
        d2 = """```d2
title: Class Relationships

"""
        
        for cls in classes:
            d2 += f"""{cls["name"]}: {{
    shape: class
}}

"""
            
            # Add inheritance
            for base in cls.get('bases', []):
                d2 += f'{base} -> {cls["name"]}: inherits\n'
        
        d2 += '```'
        return d2
    
    def _generate_plantuml_architecture(
        self, 
        repo_name: str, 
        components: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ) -> str:
        """Generate PlantUML architecture diagram."""
        
        plantuml = f"""```plantuml
@startuml {repo_name}_Architecture
!theme plain

title {repo_name} Architecture

"""
        
        # Add components
        for comp in components:
            plantuml += f'component [{comp["name"]}] as {comp["name"]}\n'
        
        plantuml += '\n'
        
        # Add relationships
        for rel in relationships:
            if rel['type'] == 'imports':
                plantuml += f'{rel["from"]} --> {rel["to"]} : imports\n'
            elif rel['type'] == 'inherits':
                plantuml += f'{rel["to"]} <|-- {rel["from"]} : inherits\n'
        
        plantuml += '\n@enduml\n```'
        return plantuml
    
    def _generate_plantuml_components(self, components: List[Dict[str, Any]]) -> str:
        """Generate PlantUML component diagram."""
        
        plantuml = """```plantuml
@startuml Components
!theme plain

title Component Details

"""
        
        for comp in components:
            plantuml += f"""package "{comp["name"]}" {{
    [Methods: {comp["methods"]}]
    [Properties: {comp["properties"]}]
}}

"""
        
        plantuml += '@enduml\n```'
        return plantuml
    
    def _generate_plantuml_dataflow(
        self, 
        ast_analysis: Dict[str, ASTAnalysis], 
        apis: List[Dict[str, Any]]
    ) -> str:
        """Generate PlantUML data flow diagram."""
        
        plantuml = """```plantuml
@startuml DataFlow
!theme plain

title Data Flow Diagram

actor User
participant API
participant Service
participant Database

"""
        
        # Add API interactions
        for api in apis:
            method = api.get('method', 'GET')
            path = api.get('path', '/')
            plantuml += f'User -> API: {method} {path}\n'
            plantuml += f'API -> Service: Process Request\n'
            
            if 'database' in api.get('function', '').lower():
                plantuml += f'Service -> Database: Query/Update\n'
                plantuml += f'Database -> Service: Result\n'
            
            plantuml += f'Service -> API: Response\n'
            plantuml += f'API -> User: JSON Response\n'
        
        plantuml += '\n@enduml\n```'
        return plantuml
    
    def _generate_plantuml_classes(self, classes: List[Dict[str, Any]]) -> str:
        """Generate PlantUML class diagram."""
        
        plantuml = """```plantuml
@startuml Classes
!theme plain

title Class Diagram

"""
        
        for cls in classes:
            plantuml += f'class {cls["name"]} {{\n'
            
            # Add methods
            for method in cls.get('methods', []):
                method_name = method.get('name', 'unknown')
                plantuml += f'  +{method_name}()\n'
            
            # Add properties
            for prop in cls.get('properties', []):
                prop_name = prop.get('name', 'unknown')
                prop_name = prop.get('name', 'unknown')
                plantuml += f'  -{prop_name}\n'
            
            plantuml += '}\n\n'
            
            # Add inheritance
            for base in cls.get('bases', []):
                plantuml += f'{base} <|-- {cls["name"]}\n'
        
        plantuml += '\n@enduml\n```'
        return plantuml
