"""
Enhanced multi-language AST analyzer for deep code understanding.
"""

import ast
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from .models import ASTAnalysis

logger = logging.getLogger(__name__)

class ASTAnalyzer:
    """Multi-language AST analyzer for deep code understanding."""
    
    def __init__(self):
        self.supported_extensions = {
            '.py': self._analyze_python,
            '.js': self._analyze_javascript,
            '.jsx': self._analyze_javascript,
            '.ts': self._analyze_typescript,
            '.tsx': self._analyze_typescript,
            '.java': self._analyze_java,
            '.go': self._analyze_go,
            '.cpp': self._analyze_cpp,
            '.c': self._analyze_c,
            '.cs': self._analyze_csharp,
            '.php': self._analyze_php,
            '.rb': self._analyze_ruby,
            '.rs': self._analyze_rust,
            '.kt': self._analyze_kotlin,
            '.swift': self._analyze_swift,
            '.vue': self._analyze_vue,
            '.py': self._analyze_python,
            '.r': self._analyze_r,
            '.sql': self._analyze_sql,
            '.sh': self._analyze_shell,
            '.bash': self._analyze_shell,
            '.ps1': self._analyze_powershell,
            '.yaml': self._analyze_yaml,
            '.yml': self._analyze_yaml,
            '.json': self._analyze_json,
            '.xml': self._analyze_xml,
            '.html': self._analyze_html,
            '.css': self._analyze_css,
            '.scss': self._analyze_scss,
            '.sass': self._analyze_sass,
            '.less': self._analyze_less
        }
    
    def analyze_file(self, file_path: str, content: str) -> Optional[ASTAnalysis]:
        """Analyze a file using appropriate analyzer."""
        ext = Path(file_path).suffix.lower()
        analyzer = self.supported_extensions.get(ext, self._analyze_generic)
        
        try:
            return analyzer(file_path, content)
        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {str(e)}")
            return self._analyze_generic(file_path, content)
    
    def _analyze_python(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {str(e)}")
            return self._analyze_generic(file_path, content)
        
        functions = self._extract_python_functions(tree)
        classes = self._extract_python_classes(tree)
        imports = self._extract_python_imports(tree)
        apis = self._extract_python_apis(tree, file_path)
        configs = self._extract_python_configs(tree, content)
        complexity = self._calculate_python_complexity(tree)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_javascript(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze JavaScript/JSX file using regex patterns."""
        functions = self._extract_js_functions(content)
        classes = self._extract_js_classes(content)
        imports = self._extract_js_imports(content)
        apis = self._extract_js_apis(content, file_path)
        configs = self._extract_js_configs(content)
        complexity = self._calculate_js_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_typescript(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze TypeScript file using regex patterns."""
        # Similar to JavaScript but with type annotations
        functions = self._extract_ts_functions(content)
        classes = self._extract_ts_classes(content)
        imports = self._extract_ts_imports(content)
        apis = self._extract_ts_apis(content, file_path)
        configs = self._extract_ts_configs(content)
        complexity = self._calculate_ts_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_java(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Java file using regex patterns."""
        functions = self._extract_java_methods(content)
        classes = self._extract_java_classes(content)
        imports = self._extract_java_imports(content)
        apis = self._extract_java_apis(content, file_path)
        configs = self._extract_java_configs(content)
        complexity = self._calculate_java_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_go(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Go file using regex patterns."""
        functions = self._extract_go_functions(content)
        classes = self._extract_go_structs(content)  # Go uses structs instead of classes
        imports = self._extract_go_imports(content)
        apis = self._extract_go_apis(content, file_path)
        configs = self._extract_go_configs(content)
        complexity = self._calculate_go_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_cpp(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze C++ file using regex patterns."""
        functions = self._extract_cpp_functions(content)
        classes = self._extract_cpp_classes(content)
        imports = self._extract_cpp_includes(content)
        apis = []  # C++ doesn't typically have REST APIs
        configs = self._extract_cpp_configs(content)
        complexity = self._calculate_cpp_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_c(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze C file using regex patterns."""
        functions = self._extract_c_functions(content)
        classes = []  # C doesn't have classes
        imports = self._extract_c_includes(content)
        apis = []
        configs = self._extract_c_configs(content)
        complexity = self._calculate_c_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_csharp(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze C# file using regex patterns."""
        functions = self._extract_csharp_methods(content)
        classes = self._extract_csharp_classes(content)
        imports = self._extract_csharp_usings(content)
        apis = self._extract_csharp_apis(content, file_path)
        configs = self._extract_csharp_configs(content)
        complexity = self._calculate_csharp_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_php(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze PHP file using regex patterns."""
        functions = self._extract_php_functions(content)
        classes = self._extract_php_classes(content)
        imports = self._extract_php_includes(content)
        apis = self._extract_php_apis(content, file_path)
        configs = self._extract_php_configs(content)
        complexity = self._calculate_php_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_ruby(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Ruby file using regex patterns."""
        functions = self._extract_ruby_methods(content)
        classes = self._extract_ruby_classes(content)
        imports = self._extract_ruby_requires(content)
        apis = self._extract_ruby_apis(content, file_path)
        configs = self._extract_ruby_configs(content)
        complexity = self._calculate_ruby_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_rust(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Rust file using regex patterns."""
        functions = self._extract_rust_functions(content)
        classes = self._extract_rust_structs(content)
        imports = self._extract_rust_uses(content)
        apis = self._extract_rust_apis(content, file_path)
        configs = self._extract_rust_configs(content)
        complexity = self._calculate_rust_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_kotlin(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Kotlin file using regex patterns."""
        functions = self._extract_kotlin_functions(content)
        classes = self._extract_kotlin_classes(content)
        imports = self._extract_kotlin_imports(content)
        apis = self._extract_kotlin_apis(content, file_path)
        configs = self._extract_kotlin_configs(content)
        complexity = self._calculate_kotlin_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_swift(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Swift file using regex patterns."""
        functions = self._extract_swift_functions(content)
        classes = self._extract_swift_classes(content)
        imports = self._extract_swift_imports(content)
        apis = self._extract_swift_apis(content, file_path)
        configs = self._extract_swift_configs(content)
        complexity = self._calculate_swift_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_vue(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze Vue file by extracting script section."""
        # Extract script section from Vue file
        script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        if script_match:
            script_content = script_match.group(1)
            # Analyze as JavaScript/TypeScript
            if 'lang="ts"' in content or 'lang="typescript"' in content:
                return self._analyze_typescript(file_path, script_content)
            else:
                return self._analyze_javascript(file_path, script_content)
        
        return ASTAnalysis()
    
    def _analyze_r(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze R file using regex patterns."""
        functions = self._extract_r_functions(content)
        classes = []  # R doesn't have traditional classes
        imports = self._extract_r_libraries(content)
        apis = self._extract_r_apis(content, file_path)
        configs = self._extract_r_configs(content)
        complexity = self._calculate_r_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_sql(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze SQL file using regex patterns."""
        functions = self._extract_sql_procedures(content)
        classes = []  # SQL doesn't have classes
        imports = []  # SQL doesn't have imports
        apis = []
        configs = self._extract_sql_configs(content)
        complexity = self._calculate_sql_complexity(content)
        
        return ASTAnalysis(functions, classes, {}, apis, configs, complexity)
    
    def _analyze_shell(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze shell script using regex patterns."""
        functions = self._extract_shell_functions(content)
        classes = []  # Shell doesn't have classes
        imports = self._extract_shell_sources(content)
        apis = []
        configs = self._extract_shell_configs(content)
        complexity = self._calculate_shell_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_powershell(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze PowerShell script using regex patterns."""
        functions = self._extract_powershell_functions(content)
        classes = self._extract_powershell_classes(content)
        imports = self._extract_powershell_modules(content)
        apis = []
        configs = self._extract_powershell_configs(content)
        complexity = self._calculate_powershell_complexity(content)
        
        return ASTAnalysis(functions, classes, imports, apis, configs, complexity)
    
    def _analyze_yaml(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze YAML configuration file."""
        configs = self._extract_yaml_configs(content)
        return ASTAnalysis([], [], {}, [], configs, {})
    
    def _analyze_json(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze JSON configuration file."""
        configs = self._extract_json_configs(content)
        return ASTAnalysis([], [], {}, [], configs, {})
    
    def _analyze_xml(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze XML configuration file."""
        configs = self._extract_xml_configs(content)
        return ASTAnalysis([], [], {}, [], configs, {})
    
    def _analyze_html(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze HTML file for structure."""
        # Extract any embedded JavaScript
        js_scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        all_functions = []
        for script in js_scripts:
            js_analysis = self._analyze_javascript(file_path, script)
            all_functions.extend(js_analysis.functions)
        
        return ASTAnalysis(all_functions, [], {}, [], [], {})
    
    def _analyze_css(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze CSS file for classes and rules."""
        classes = self._extract_css_classes(content)
        return ASTAnalysis([], classes, {}, [], [], {})
    
    def _analyze_scss(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze SCSS file for classes and mixins."""
        classes = self._extract_scss_classes(content)
        functions = self._extract_scss_mixins(content)
        return ASTAnalysis(functions, classes, {}, [], [], {})
    
    def _analyze_sass(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze SASS file for classes and mixins."""
        classes = self._extract_sass_classes(content)
        functions = self._extract_sass_mixins(content)
        return ASTAnalysis(functions, classes, {}, [], [], {})
    
    def _analyze_less(self, file_path: str, content: str) -> ASTAnalysis:
        """Analyze LESS file for classes and mixins."""
        classes = self._extract_less_classes(content)
        functions = self._extract_less_mixins(content)
        return ASTAnalysis(functions, classes, {}, [], [], {})
    
    def _analyze_generic(self, file_path: str, content: str) -> ASTAnalysis:
        """Generic analysis for unsupported file types."""
        # Basic analysis using regex patterns
        functions = self._extract_generic_functions(content)
        classes = self._extract_generic_classes(content)
        imports = self._extract_generic_imports(content)
        
        # Try to detect configuration patterns
        configs = []
        if any(keyword in content.lower() for keyword in ['config', 'setting', 'option', 'parameter']):
            configs = [{'type': 'generic', 'content': content[:500]}]
        
        return ASTAnalysis(functions, classes, imports, [], configs, {})
    
    # Python-specific extraction methods (keeping the original ones)
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
    
    # JavaScript-specific extraction methods
    def _extract_js_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript functions using regex."""
        functions = []
        
        # Function declarations
        func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*{'
        matches = re.finditer(func_pattern, content)
        for match in matches:
            functions.append({
                'name': match.group(1),
                'type': 'function',
                'line_number': content[:match.start()].count('\n') + 1
            })
        
        # Arrow functions
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])*=>'
        matches = re.finditer(arrow_pattern, content)
        for match in matches:
            functions.append({
                'name': match.group(1),
                'type': 'arrow_function',
                'line_number': content[:match.start()].count('\n') + 1
            })
        
        return functions
    
    def _extract_js_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript classes using regex."""
        classes = []
        
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{'
        matches = re.finditer(class_pattern, content)
        for match in matches:
            class_info = {
                'name': match.group(1),
                'line_number': content[:match.start()].count('\n') + 1,
                'extends': match.group(2) if match.group(2) else None
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_js_imports(self, content: str) -> Dict[str, Any]:
        """Extract JavaScript imports using regex."""
        imports = {'modules': [], 'requires': []}
        
        # ES6 imports
        import_pattern = r'import\s+(?:(?:\{[^}]*\}|\w+|\*\s+as\s+\w+)(?:\s*,\s*(?:\{[^}]*\}|\w+))?\s+from\s+)?[\'"]([^\'"]+)[\'"]'
        matches = re.finditer(import_pattern, content)
        for match in matches:
            imports['modules'].append(match.group(1))
        
        # CommonJS requires
        require_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        matches = re.finditer(require_pattern, content)
        for match in matches:
            imports['requires'].append(match.group(1))
        
        return imports
    
    def _extract_js_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from JavaScript code."""
        apis = []
        
        # Express.js routes
        route_pattern = r'app\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
        matches = re.finditer(route_pattern, content)
        for match in matches:
            apis.append({
                'method': match.group(1).upper(),
                'path': match.group(2),
                'file': file_path,
                'line': content[:match.start()].count('\n') + 1
            })
        
        return apis
    
    def _extract_js_configs(self, content: str) -> List[Dict[str, Any]]:
        """Extract configuration from JavaScript code."""
        configs = []
        
        # Look for config objects
        if 'config' in content.lower():
            configs.append({
                'type': 'config_object',
                'content': content[:500]
            })
        
        return configs
    
    def _calculate_js_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate basic complexity metrics for JavaScript."""
        return {
            'lines': len(content.split('\n')),
            'functions': len(re.findall(r'function\s+\w+', content)),
            'classes': len(re.findall(r'class\s+\w+', content))
        }
    
    # TypeScript-specific methods (similar to JavaScript with type info)
    def _extract_ts_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract TypeScript functions with type information."""
        functions = self._extract_js_functions(content)
        
        # Add type information
        for func in functions:
            # Look for function with return type
            type_pattern = rf'function\s+{func["name"]}\s*\([^)]*\)\s*:\s*(\w+)'
            match = re.search(type_pattern, content)
            if match:
                func['return_type'] = match.group(1)
        
        return functions
    
    def _extract_ts_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract TypeScript classes with interface information."""
        classes = self._extract_js_classes(content)
        
        # Add interfaces
        interface_pattern = r'interface\s+(\w+)\s*(?:extends\s+([^{]+))?\s*{'
        matches = re.finditer(interface_pattern, content)
        for match in matches:
            classes.append({
                'name': match.group(1),
                'type': 'interface',
                'extends': match.group(2).strip() if match.group(2) else None,
                'line_number': content[:match.start()].count('\n') + 1
            })
        
        return classes
    
    def _extract_ts_imports(self, content: str) -> Dict[str, Any]:
        """Extract TypeScript imports including type imports."""
        imports = self._extract_js_imports(content)
        
        # Type-only imports
        type_import_pattern = r'import\s+type\s+(?:\{[^}]*\}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        matches = re.finditer(type_import_pattern, content)
        type_imports = [match.group(1) for match in matches]
        
        imports['type_imports'] = type_imports
        return imports
    
    def _extract_ts_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from TypeScript code."""
        return self._extract_js_apis(content, file_path)
    
    def _extract_ts_configs(self, content: str) -> List[Dict[str, Any]]:
        """Extract configuration from TypeScript code."""
        return self._extract_js_configs(content)
    
    def _calculate_ts_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate complexity metrics for TypeScript."""
        complexity = self._calculate_js_complexity(content)
        complexity['interfaces'] = len(re.findall(r'interface\s+\w+', content))
        complexity['types'] = len(re.findall(r'type\s+\w+', content))
        return complexity
    
    # Generic extraction methods for other languages
    def _extract_generic_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function-like patterns from any language."""
        functions = []
        
        # Common function patterns
        patterns = [
            r'def\s+(\w+)\s*\(',  # Python
            r'function\s+(\w+)\s*\(',  # JavaScript
            r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*{',  # Java/C#
            r'func\s+(\w+)\s*\(',  # Go
            r'fn\s+(\w+)\s*\(',  # Rust
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                functions.append({
                    'name': match.group(1),
                    'line_number': content[:match.start()].count('\n') + 1,
                    'type': 'function'
                })
        
        return functions
    
    def _extract_generic_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class-like patterns from any language."""
        classes = []
        
        # Common class patterns
        patterns = [
            r'class\s+(\w+)',  # Most languages
            r'struct\s+(\w+)',  # C/C++/Go/Rust
            r'interface\s+(\w+)',  # TypeScript/Java/C#
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                classes.append({
                    'name': match.group(1),
                    'line_number': content[:match.start()].count('\n') + 1,
                    'type': 'class'
                })
        
        return classes
    
    def _extract_generic_imports(self, content: str) -> Dict[str, Any]:
        """Extract import-like patterns from any language."""
        imports = {'modules': []}
        
        # Common import patterns
        patterns = [
            r'import\s+[\'"]([^\'"]+)[\'"]',  # Python/JavaScript
            r'#include\s+[<"]([^>"]+)[>"]',  # C/C++
            r'using\s+(\w+(?:\.\w+)*)',  # C#
            r'package\s+(\w+(?:\.\w+)*)',  # Java
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                imports['modules'].append(match.group(1))
        
        return imports
    
    # Placeholder methods for languages not yet fully implemented
    def _extract_java_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java methods."""
        return self._extract_generic_functions(content)
    
    def _extract_java_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java classes."""
        return self._extract_generic_classes(content)
    
    def _extract_java_imports(self, content: str) -> Dict[str, Any]:
        """Extract Java imports."""
        return self._extract_generic_imports(content)
    
    def _extract_java_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Java API endpoints."""
        return []
    
    def _extract_java_configs(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java configuration."""
        return []
    
    def _calculate_java_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate Java complexity."""
        return {'lines': len(content.split('\n'))}
    
    # Similar placeholder methods for other languages...
    # For brevity, I'll implement a few more and use similar patterns for the rest
    
    def _extract_go_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract Go functions."""
        functions = []
        func_pattern = r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\([^)]*\)'
        matches = re.finditer(func_pattern, content)
        for match in matches:
            functions.append({
                'name': match.group(1),
                'line_number': content[:match.start()].count('\n') + 1,
                'type': 'function'
            })
        return functions
    
    def _extract_go_structs(self, content: str) -> List[Dict[str, Any]]:
        """Extract Go structs."""
        structs = []
        struct_pattern = r'type\s+(\w+)\s+struct\s*{'
        matches = re.finditer(struct_pattern, content)
        for match in matches:
            structs.append({
                'name': match.group(1),
                'line_number': content[:match.start()].count('\n') + 1,
                'type': 'struct'
            })
        return structs
    
    def _extract_go_imports(self, content: str) -> Dict[str, Any]:
        """Extract Go imports."""
        imports = {'modules': []}
        
        # Single import
        single_pattern = r'import\s+"([^"]+)"'
        matches = re.finditer(single_pattern, content)
        for match in matches:
            imports['modules'].append(match.group(1))
        
        # Multi-line imports
        multi_pattern = r'import\s*\(\s*([^)]+)\s*\)'
        matches = re.finditer(multi_pattern, content, re.DOTALL)
        for match in matches:
            import_block = match.group(1)
            import_lines = re.findall(r'"([^"]+)"', import_block)
            imports['modules'].extend(import_lines)
        
        return imports
    
    def _extract_go_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Go API endpoints."""
        apis = []
        
        # Gin framework routes
        gin_pattern = r'r\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*"([^"]+)"'
        matches = re.finditer(gin_pattern, content)
        for match in matches:
            apis.append({
                'method': match.group(1),
                'path': match.group(2),
                'file': file_path,
                'line': content[:match.start()].count('\n') + 1
            })
        
        return apis
    
    def _extract_go_configs(self, content: str) -> List[Dict[str, Any]]:
        """Extract Go configuration."""
        configs = []
        if 'config' in content.lower():
            configs.append({
                'type': 'config_struct',
                'content': content[:500]
            })
        return configs
    
    def _calculate_go_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate Go complexity."""
        return {
            'lines': len(content.split('\n')),
            'functions': len(re.findall(r'func\s+\w+', content)),
            'structs': len(re.findall(r'type\s+\w+\s+struct', content))
        }
    
    # Add placeholder methods for other languages to avoid errors
    def _extract_cpp_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_cpp_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_cpp_includes(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_cpp_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_cpp_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_c_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_c_includes(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_c_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_c_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    # Add similar placeholder methods for all other languages
    def _extract_csharp_methods(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_csharp_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_csharp_usings(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_csharp_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_csharp_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_csharp_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    # Continue with other languages...
    def _extract_php_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_php_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_php_includes(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_php_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_php_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_php_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_ruby_methods(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_ruby_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_ruby_requires(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_ruby_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_ruby_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_ruby_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_rust_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_rust_structs(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_rust_uses(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_rust_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_rust_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_rust_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_kotlin_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_kotlin_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_kotlin_imports(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_kotlin_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_kotlin_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_kotlin_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_swift_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_swift_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_swift_imports(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_swift_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_swift_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_swift_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_r_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_r_libraries(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_r_apis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_r_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_r_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_sql_procedures(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_sql_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_sql_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_shell_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_shell_sources(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_shell_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_shell_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_powershell_functions(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_functions(content)
    
    def _extract_powershell_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_generic_classes(content)
    
    def _extract_powershell_modules(self, content: str) -> Dict[str, Any]:
        return self._extract_generic_imports(content)
    
    def _extract_powershell_configs(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_powershell_complexity(self, content: str) -> Dict[str, Any]:
        return {'lines': len(content.split('\n'))}
    
    def _extract_yaml_configs(self, content: str) -> List[Dict[str, Any]]:
        configs = []
        try:
            import yaml
            data = yaml.safe_load(content)
            configs.append({
                'type': 'yaml',
                'data': data
            })
        except Exception:
            configs.append({
                'type': 'yaml',
                'content': content[:500]
            })
        return configs
    
    def _extract_json_configs(self, content: str) -> List[Dict[str, Any]]:
        configs = []
        try:
            data = json.loads(content)
            configs.append({
                'type': 'json',
                'data': data
            })
        except Exception:
            configs.append({
                'type': 'json',
                'content': content[:500]
            })
        return configs
    
    def _extract_xml_configs(self, content: str) -> List[Dict[str, Any]]:
        return [{'type': 'xml', 'content': content[:500]}]
    
    def _extract_css_classes(self, content: str) -> List[Dict[str, Any]]:
        classes = []
        class_pattern = r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)\s*{'
        matches = re.finditer(class_pattern, content)
        for match in matches:
            classes.append({
                'name': match.group(1),
                'type': 'css_class',
                'line_number': content[:match.start()].count('\n') + 1
            })
        return classes
    
    def _extract_scss_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_css_classes(content)
    
    def _extract_scss_mixins(self, content: str) -> List[Dict[str, Any]]:
        mixins = []
        mixin_pattern = r'@mixin\s+([a-zA-Z_-][a-zA-Z0-9_-]*)'
        matches = re.finditer(mixin_pattern, content)
        for match in matches:
            mixins.append({
                'name': match.group(1),
                'type': 'scss_mixin',
                'line_number': content[:match.start()].count('\n') + 1
            })
        return mixins
    
    def _extract_sass_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_css_classes(content)
    
    def _extract_sass_mixins(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_scss_mixins(content)
    
    def _extract_less_classes(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_css_classes(content)
    
    def _extract_less_mixins(self, content: str) -> List[Dict[str, Any]]:
        return self._extract_scss_mixins(content)
