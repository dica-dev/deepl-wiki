"""
Enhanced example extractor for generating usage examples from code analysis.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from .models import ASTAnalysis

logger = logging.getLogger(__name__)

class ExampleExtractor:
    """Extract usage examples and patterns from code analysis."""
    
    def __init__(self):
        self.test_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'tests/.*\.py$',
            r'spec/.*\.js$',
            r'.*\.spec\.js$',
            r'.*\.test\.js$',
            r'__tests__/.*\.js$'
        ]
        
        self.example_patterns = [
            r'examples?/.*',
            r'samples?/.*',
            r'demos?/.*',
            r'tutorial/.*'
        ]
        
        self.cli_patterns = [
            r'cli\.py$',
            r'main\.py$',
            r'__main__\.py$',
            r'bin/.*',
            r'scripts?/.*'
        ]
    
    def extract_usage_examples(
        self,
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract usage examples from various sources."""
        
        examples = {
            'test_examples': [],
            'cli_examples': [],
            'code_examples': [],
            'config_examples': [],
            'api_examples': []
        }
        
        # Extract test examples
        examples['test_examples'] = self._extract_test_examples(file_contents)
        
        # Extract CLI examples
        examples['cli_examples'] = self._extract_cli_examples(file_contents, ast_analysis)
        
        # Extract code usage patterns
        examples['code_examples'] = self._extract_code_patterns(ast_analysis)
        
        # Extract configuration examples
        examples['config_examples'] = self._extract_config_examples(file_contents)
        
        # Extract API examples
        examples['api_examples'] = self._extract_api_examples(ast_analysis)
        
        return examples
    
    def extract_function_examples(
        self,
        function_name: str,
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract specific examples for a function."""
        
        examples = []
        
        # Look for test cases
        for file_info in file_contents:
            if self._is_test_file(file_info['path']):
                function_examples = self._find_function_usage_in_content(
                    function_name, file_info['content'], file_info['path']
                )
                examples.extend(function_examples)
        
        # Look for usage in regular code
        for file_path, analysis in ast_analysis.items():
            if not self._is_test_file(file_path):
                function_examples = self._find_function_calls(function_name, file_path, analysis)
                examples.extend(function_examples)
        
        return examples
    
    def extract_class_examples(
        self,
        class_name: str,
        ast_analysis: Dict[str, ASTAnalysis],
        file_contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract usage examples for a class."""
        
        examples = []
        
        # Look for instantiation and usage
        for file_info in file_contents:
            class_examples = self._find_class_usage_in_content(
                class_name, file_info['content'], file_info['path']
            )
            examples.extend(class_examples)
        
        return examples
    
    def extract_api_examples(
        self,
        apis: List[Dict[str, Any]],
        file_contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract API usage examples."""
        
        examples = []
        
        for api in apis:
            # Create curl example
            curl_example = self._generate_curl_example(api)
            if curl_example:
                examples.append(curl_example)
            
            # Look for client usage examples
            client_examples = self._find_api_client_usage(api, file_contents)
            examples.extend(client_examples)
        
        return examples
    
    def extract_configuration_usage(
        self,
        config_files: List[str],
        file_contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract configuration usage examples."""
        
        examples = []
        
        for config_file in config_files:
            # Find the config file content
            config_content = None
            for file_info in file_contents:
                if file_info['path'].endswith(config_file):
                    config_content = file_info['content']
                    break
            
            if config_content:
                config_example = self._analyze_config_content(config_file, config_content)
                if config_example:
                    examples.append(config_example)
        
        return examples
    
    def _extract_test_examples(self, file_contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract examples from test files."""
        
        examples = []
        
        for file_info in file_contents:
            if self._is_test_file(file_info['path']):
                test_examples = self._parse_test_file(file_info)
                examples.extend(test_examples)
        
        return examples
    
    def _extract_cli_examples(
        self,
        file_contents: List[Dict[str, Any]],
        ast_analysis: Dict[str, ASTAnalysis]
    ) -> List[Dict[str, Any]]:
        """Extract CLI usage examples."""
        
        examples = []
        
        for file_info in file_contents:
            if self._is_cli_file(file_info['path']):
                cli_examples = self._parse_cli_file(file_info, ast_analysis)
                examples.extend(cli_examples)
        
        return examples
    
    def _extract_code_patterns(self, ast_analysis: Dict[str, ASTAnalysis]) -> List[Dict[str, Any]]:
        """Extract common code usage patterns."""
        
        patterns = []
        
        # Common initialization patterns
        for file_path, analysis in ast_analysis.items():
            for cls in analysis.classes:
                if cls.get('methods'):
                    init_method = next((m for m in cls['methods'] if m['name'] == '__init__'), None)
                    if init_method:
                        pattern = {
                            'type': 'initialization',
                            'class': cls['name'],
                            'file': file_path,
                            'parameters': init_method.get('parameters', []),
                            'example': self._generate_class_init_example(cls, init_method)
                        }
                        patterns.append(pattern)
        
        return patterns
    
    def _extract_config_examples(self, file_contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract configuration file examples."""
        
        examples = []
        
        config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.env'}
        
        for file_info in file_contents:
            if any(file_info['path'].endswith(ext) for ext in config_extensions):
                config_example = self._analyze_config_content(file_info['path'], file_info['content'])
                if config_example:
                    examples.append(config_example)
        
        return examples
    
    def _extract_api_examples(self, ast_analysis: Dict[str, ASTAnalysis]) -> List[Dict[str, Any]]:
        """Extract API endpoint examples."""
        
        examples = []
        
        for file_path, analysis in ast_analysis.items():
            for api in analysis.apis:
                curl_example = self._generate_curl_example(api)
                if curl_example:
                    examples.append(curl_example)
        
        return examples
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        return any(re.search(pattern, file_path) for pattern in self.test_patterns)
    
    def _is_example_file(self, file_path: str) -> bool:
        """Check if file is an example file."""
        return any(re.search(pattern, file_path) for pattern in self.example_patterns)
    
    def _is_cli_file(self, file_path: str) -> bool:
        """Check if file is a CLI file."""
        return any(re.search(pattern, file_path) for pattern in self.cli_patterns)
    
    def _parse_test_file(self, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse test file for usage examples."""
        
        examples = []
        content = file_info['content']
        
        # Extract test functions
        test_function_pattern = r'def\s+(test_\w+)\s*\([^)]*\):\s*\n((?:    .*\n)*)'
        matches = re.finditer(test_function_pattern, content, re.MULTILINE)
        
        for match in matches:
            test_name = match.group(1)
            test_body = match.group(2)
            
            # Clean up the test body
            test_body = '\n'.join(line[4:] if line.startswith('    ') else line 
                                for line in test_body.split('\n'))
            
            example = {
                'type': 'test',
                'name': test_name,
                'file': file_info['path'],
                'code': test_body.strip(),
                'description': f"Test case: {test_name}"
            }
            examples.append(example)
        
        return examples
    
    def _parse_cli_file(
        self,
        file_info: Dict[str, Any],
        ast_analysis: Dict[str, ASTAnalysis]
    ) -> List[Dict[str, Any]]:
        """Parse CLI file for usage examples."""
        
        examples = []
        content = file_info['content']
        
        # Look for Click commands
        click_command_pattern = r'@click\.command\(\)\s*\n@[^n]*\ndef\s+(\w+)\s*\([^)]*\):'
        matches = re.finditer(click_command_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            command_name = match.group(1)
            
            example = {
                'type': 'cli_command',
                'name': command_name,
                'file': file_info['path'],
                'usage': f"python -m module {command_name}",
                'description': f"CLI command: {command_name}"
            }
            examples.append(example)
        
        # Look for argparse usage
        argparse_pattern = r'parser\.add_argument\([^)]*[\'"]([^\'"]*)[\'"],[^)]*\)'
        matches = re.finditer(argparse_pattern, content)
        
        if matches:
            args = [match.group(1) for match in matches]
            example = {
                'type': 'cli_usage',
                'file': file_info['path'],
                'arguments': args,
                'usage': f"python {Path(file_info['path']).name} {' '.join(args)}",
                'description': "Command line usage"
            }
            examples.append(example)
        
        return examples
    
    def _find_function_usage_in_content(
        self,
        function_name: str,
        content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Find function usage in content."""
        
        examples = []
        
        # Simple function call pattern
        pattern = rf'{function_name}\s*\([^)]*\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            # Get surrounding context
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end]
            
            example = {
                'type': 'function_call',
                'function': function_name,
                'file': file_path,
                'usage': match.group(0),
                'context': context.strip(),
                'description': f"Usage of {function_name}"
            }
            examples.append(example)
        
        return examples
    
    def _find_function_calls(
        self,
        function_name: str,
        file_path: str,
        analysis: ASTAnalysis
    ) -> List[Dict[str, Any]]:
        """Find function calls in AST analysis."""
        
        examples = []
        
        # This would require more sophisticated AST walking
        # For now, we'll use a simple approach
        for func in analysis.functions:
            if func['name'] == function_name:
                example = {
                    'type': 'function_definition',
                    'function': function_name,
                    'file': file_path,
                    'parameters': func.get('parameters', []),
                    'description': func.get('docstring', f"Definition of {function_name}")
                }
                examples.append(example)
        
        return examples
    
    def _find_class_usage_in_content(
        self,
        class_name: str,
        content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Find class usage in content."""
        
        examples = []
        
        # Class instantiation pattern
        pattern = rf'{class_name}\s*\([^)]*\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            # Get surrounding context
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end]
            
            example = {
                'type': 'class_instantiation',
                'class': class_name,
                'file': file_path,
                'usage': match.group(0),
                'context': context.strip(),
                'description': f"Instantiation of {class_name}"
            }
            examples.append(example)
        
        return examples
    
    def _generate_curl_example(self, api: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate curl example for API endpoint."""
        
        method = api.get('method', 'GET')
        path = api.get('path', '/')
        
        if method == 'GET':
            curl_cmd = f"curl -X GET http://localhost:8000{path}"
        elif method == 'POST':
            curl_cmd = f"curl -X POST http://localhost:8000{path} -H 'Content-Type: application/json' -d '{{}}'"
        elif method == 'PUT':
            curl_cmd = f"curl -X PUT http://localhost:8000{path} -H 'Content-Type: application/json' -d '{{}}'"
        elif method == 'DELETE':
            curl_cmd = f"curl -X DELETE http://localhost:8000{path}"
        else:
            curl_cmd = f"curl -X {method} http://localhost:8000{path}"
        
        return {
            'type': 'api_curl',
            'method': method,
            'path': path,
            'curl': curl_cmd,
            'description': f"{method} {path} API endpoint"
        }
    
    def _find_api_client_usage(
        self,
        api: Dict[str, Any],
        file_contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find client-side API usage."""
        
        examples = []
        path = api.get('path', '/')
        
        # Look for requests usage
        for file_info in file_contents:
            content = file_info['content']
            
            # Find requests calls to this path
            pattern = rf'requests\.\w+\s*\([^)]*[\'"].*{re.escape(path)}.*[\'"][^)]*\)'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                example = {
                    'type': 'api_client',
                    'path': path,
                    'file': file_info['path'],
                    'usage': match.group(0),
                    'description': f"Client usage of {path}"
                }
                examples.append(example)
        
        return examples
    
    def _analyze_config_content(self, file_path: str, content: str) -> Optional[Dict[str, Any]]:
        """Analyze configuration file content."""
        
        if not content.strip():
            return None
        
        config_type = 'unknown'
        parsed_content = content
        
        if file_path.endswith('.json'):
            config_type = 'json'
            try:
                import json
                parsed_content = json.loads(content)
            except:
                pass
        elif file_path.endswith(('.yaml', '.yml')):
            config_type = 'yaml'
        elif file_path.endswith('.toml'):
            config_type = 'toml'
        elif file_path.endswith(('.ini', '.cfg')):
            config_type = 'ini'
        elif file_path.endswith('.env'):
            config_type = 'env'
        
        return {
            'type': 'configuration',
            'file': file_path,
            'config_type': config_type,
            'content': content[:1000],  # Limit content size
            'description': f"Configuration file: {Path(file_path).name}"
        }
    
    def _generate_class_init_example(
        self,
        cls: Dict[str, Any],
        init_method: Dict[str, Any]
    ) -> str:
        """Generate class initialization example."""
        
        class_name = cls['name']
        parameters = init_method.get('parameters', [])
        
        if not parameters:
            return f"{class_name}()"
        
        # Generate example parameters
        param_examples = []
        for param in parameters:
            param_name = param.get('name', 'param')
            if param_name == 'self':
                continue
            
            param_type = param.get('type', '')
            if 'str' in param_type.lower():
                param_examples.append(f'{param_name}="example"')
            elif 'int' in param_type.lower():
                param_examples.append(f'{param_name}=1')
            elif 'bool' in param_type.lower():
                param_examples.append(f'{param_name}=True')
            else:
                param_examples.append(f'{param_name}=...')
        
        params_str = ', '.join(param_examples)
        return f"{class_name}({params_str})"
