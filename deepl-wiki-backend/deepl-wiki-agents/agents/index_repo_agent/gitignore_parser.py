"""
GitIgnore parser for filtering out ignored files during repository indexing.
"""

import os
import fnmatch
import logging
from pathlib import Path
from typing import Dict, List, Any, Set

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
