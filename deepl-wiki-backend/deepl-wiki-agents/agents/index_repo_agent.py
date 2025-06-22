"""Index repository agent for scanning codebases and generating documentation using LangGraph."""

import os
import json
from typing import Dict, List, Any, Optional, TypedDict, Set
from pathlib import Path
import git
from git import Repo
from langgraph.graph import StateGraph, END

from .shared.llama_client import LlamaClient
from .shared.chroma_manager import ChromaManager

class IndexState(TypedDict):
    """State for the index agent."""
    repo_paths: List[str]
    current_repo_index: int
    current_repo_path: str
    repo_files: List[Dict[str, Any]]
    generated_memo: str
    repo_metadata: Dict[str, Any] 
    all_memos: List[Dict[str, Any]]
    general_memo: str
    success: bool
    error: Optional[str]

class IndexRepoAgent:
    """LangGraph-based agent for indexing repositories and generating documentation."""
    
    def __init__(
        self,
        llama_client: Optional[LlamaClient] = None,
        chroma_manager: Optional[ChromaManager] = None,
        max_file_size: int = 100000,
        excluded_dirs: Optional[Set[str]] = None,
        excluded_extensions: Optional[Set[str]] = None
    ):
        """Initialize index repository agent."""
        self.llama_client = llama_client or LlamaClient()
        self.chroma_manager = chroma_manager or ChromaManager()
        self.max_file_size = max_file_size
        
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
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(IndexState)
        
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("scan_repo", self._scan_repository)
        workflow.add_node("generate_memo", self._generate_repo_memo)
        workflow.add_node("store_memo", self._store_memo)
        workflow.add_node("next_repo", self._next_repo)
        workflow.add_node("generate_general_memo", self._generate_general_memo)
        workflow.add_node("finalize", self._finalize)
        workflow.add_node("handle_error", self._handle_error)
        
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "scan_repo")
        workflow.add_edge("scan_repo", "generate_memo")
        workflow.add_edge("generate_memo", "store_memo")
        workflow.add_edge("store_memo", "next_repo")
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
    
    def index_repositories(self, repo_paths: List[str]) -> Dict[str, Any]:
        """Index multiple repositories and generate documentation."""
        initial_state = IndexState(
            repo_paths=repo_paths,
            current_repo_index=0,
            current_repo_path="",
            repo_files=[],
            generated_memo="",
            repo_metadata={},
            all_memos=[],
            general_memo="",
            success=False,
            error=None
        )
        
        result = self.graph.invoke(initial_state)
        
        return {
            "success": result["success"],            "error": result.get("error"),
            "individual_memos": result["all_memos"],
            "general_memo": result["general_memo"],
            "total_repos": len(repo_paths)
        }
    
    def _initialize(self, state: IndexState) -> IndexState:
        """Initialize the indexing process."""
        new_state = state.copy()
        new_state.update({
            "current_repo_index": 0,            "all_memos": [],
            "success": False
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
            new_state = state.copy()
            new_state["error"] = f"Failed to scan repository: {str(e)}"
            return new_state
    
    def _generate_repo_memo(self, state: IndexState) -> IndexState:
        """Generate a comprehensive memo for the current repository."""
        try:
            repo_path = state["current_repo_path"]
            repo_files = state["repo_files"]
            repo_metadata = state["repo_metadata"]
            
            file_contents = []
            for file_info in repo_files[:50]:
                if file_info["size"] < self.max_file_size:
                    try:
                        with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            file_contents.append({
                                "path": file_info["relative_path"],
                                "content": content[:5000],
                                "size": file_info["size"],
                                "extension": file_info["extension"]
                            })
                    except Exception:
                        continue
            
            memo_content = self._create_repository_memo(
                repo_path=repo_path,
                repo_metadata=repo_metadata,
                file_contents=file_contents,
                all_files=repo_files
            )
            
            new_state = state.copy()
            new_state["generated_memo"] = memo_content
            return new_state            
        except Exception as e:
            new_state = state.copy()
            new_state["error"] = f"Failed to generate memo: {str(e)}"
            return new_state
    
    def _store_memo(self, state: IndexState) -> IndexState:
        """Store the generated memo in ChromaDB."""
        try:
            repo_path = state["current_repo_path"]
            memo_content = state["generated_memo"]
            repo_metadata = state["repo_metadata"]
            
            self.chroma_manager.add_repo_memo(
                repo_path=repo_path,
                memo_content=memo_content,
                repo_metadata=repo_metadata
            )
            
            memo_entry = {
                "repo_path": repo_path,
                "memo_content": memo_content,
                "metadata": repo_metadata
            }
            
            all_memos = state["all_memos"].copy()
            all_memos.append(memo_entry)
            
            new_state = state.copy()
            new_state["all_memos"] = all_memos
            return new_state            
        except Exception as e:
            new_state = state.copy()
            new_state["error"] = f"Failed to store memo: {str(e)}"
            return new_state
    
    def _next_repo(self, state: IndexState) -> IndexState:
        """Move to the next repository."""
        current_index = state["current_repo_index"]
        new_state = state.copy()
        new_state.update({
            "current_repo_index": current_index + 1,
            "current_repo_path": "",            "repo_files": [],
            "generated_memo": "",
            "repo_metadata": {}
        })
        return new_state
    
    def _generate_general_memo(self, state: IndexState) -> IndexState:
        """Generate a general memo summarizing all repositories."""
        try:
            all_memos = state["all_memos"]
            
            if not all_memos:
                new_state = state.copy()
                new_state["general_memo"] = "No repositories were successfully indexed."
                return new_state
            
            repo_summaries = []
            for memo_entry in all_memos:
                repo_name = Path(memo_entry["repo_path"]).name
                metadata = memo_entry["metadata"]
                
                summary = f"**{repo_name}**\n"
                summary += f"- Language: {metadata.get('primary_language', 'Unknown')}\n"
                summary += f"- Files: {metadata.get('file_count', 0)}\n"
                
                repo_summaries.append(summary)
            
            general_memo_prompt = f"""Create a comprehensive overview memo for this collection of repositories:

Repository Collection Summary:
{chr(10).join(repo_summaries)}

Please create a general memo that includes:
1. Overview of the entire codebase collection
2. Common patterns and technologies used
3. Key architectural insights
4. Recommended development practices

General Memo:"""

            general_memo = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": general_memo_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            new_state = state.copy()
            new_state["general_memo"] = general_memo
            return new_state            
        except Exception as e:
            new_state = state.copy()
            new_state["error"] = f"Failed to generate general memo: {str(e)}"
            return new_state
    
    def _finalize(self, state: IndexState) -> IndexState:
        """Finalize the indexing process."""
        new_state = state.copy()
        new_state["success"] = True
        return new_state
    
    def _handle_error(self, state: IndexState) -> IndexState:
        """Handle errors gracefully."""
        new_state = state.copy()
        new_state["success"] = False
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
        """Extract metadata from a repository."""
        metadata = {
            "repo_path": repo_path,
            "repo_name": Path(repo_path).name
        }
        
        try:
            repo = Repo(repo_path)
            if not repo.bare:
                metadata["git_branch"] = repo.active_branch.name
                metadata["last_commit"] = repo.head.commit.hexsha[:8]
                metadata["author"] = repo.head.commit.author.name
        except Exception:
            pass
        
        file_stats = self._analyze_file_types(repo_path)
        metadata.update(file_stats)
        
        return metadata
    
    def _scan_files(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Scan repository files and return file information."""
        files = []
        
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
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
                        "size": file_path.stat().st_size
                    }
                    files.append(file_info)
                except Exception:
                    continue
        
        code_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs", ".php", ".rb", ".go", ".rs"}
        config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}
        doc_extensions = {".md", ".txt", ".rst", ".org"}
        
        def file_priority(file_info):
            ext = file_info["extension"]
            if ext in code_extensions:
                return (0, -file_info["size"])
            elif ext in config_extensions:
                return (1, -file_info["size"])
            elif ext in doc_extensions:
                return (2, -file_info["size"])
            else:
                return (3, -file_info["size"])
        
        files.sort(key=file_priority)
        return files
    
    def _analyze_file_types(self, repo_path: str) -> Dict[str, Any]:
        """Analyze file types in the repository."""
        repo_path_obj = Path(repo_path)
        extensions = {}
        total_files = 0
        total_size = 0
        
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file():
                if any(excluded in file_path.parts for excluded in self.excluded_dirs):
                    continue
                
                ext = file_path.suffix.lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
                
                try:
                    total_size += file_path.stat().st_size
                    total_files += 1
                except Exception:
                    continue
        
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
            "file_extensions": str(dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]))
        }
    
    def _create_repository_memo(
        self,
        repo_path: str,
        repo_metadata: Dict[str, Any],
        file_contents: List[Dict[str, Any]],
        all_files: List[Dict[str, Any]]
    ) -> str:
        """Create a comprehensive repository memo using AI."""
        
        repo_name = Path(repo_path).name
        
        structure_summary = "\n".join([
            f"  {file_info['relative_path']} ({file_info['size']} bytes)"
            for file_info in all_files[:30]
        ])
        
        content_summary = ""
        for file_content in file_contents[:10]:
            content_summary += f"\n--- {file_content['path']} ---\n"
            content_summary += file_content['content'][:1000] + "\n"
        
        memo_prompt = f"""Create a comprehensive documentation memo for the repository: {repo_name}

Repository Metadata:
- Path: {repo_path}
- Primary Language: {repo_metadata.get('primary_language', 'Unknown')}
- Total Files: {repo_metadata.get('file_count', 0)}
- Git Branch: {repo_metadata.get('git_branch', 'N/A')}
- Last Commit: {repo_metadata.get('last_commit', 'N/A')}

File Structure (first 30 files):
{structure_summary}

Key File Contents:
{content_summary}

Please create a detailed memo that includes:

1. **Repository Overview**
   - Purpose and functionality of this repository
   - Main features and capabilities

2. **Architecture and Structure**
   - Key directories and their purposes
   - Important files and their roles
   - Dependencies and external libraries

3. **Development Information**
   - Programming languages and frameworks used
   - Build process and requirements
   - Testing approach (if evident)

4. **Key Components**
   - Main classes, functions, or modules
   - Configuration files and their purposes
   - Entry points and main execution flows

5. **Documentation and Notes**
   - Existing documentation found
   - Code patterns and conventions
   - Potential areas for improvement

6. **Integration Points**
   - APIs or interfaces exposed
   - External services or databases used
   - Inter-component communication

Please be thorough but concise, focusing on information that would be valuable for developers working with or integrating this codebase.

Repository Memo:"""

        try:
            memo = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": memo_prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            return memo
        except Exception as e:
            return f"Failed to generate comprehensive memo: {str(e)}\n\nBasic Info:\nRepository: {repo_name}\nLanguage: {repo_metadata.get('primary_language', 'Unknown')}\nFiles: {repo_metadata.get('file_count', 0)}"
