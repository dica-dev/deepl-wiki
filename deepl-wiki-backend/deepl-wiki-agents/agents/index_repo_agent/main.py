"""
Enhanced Index Repository Agent with folder-based documentation structure.
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Any, Optional, Set, Union
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import git
from git import Repo
from langgraph.graph import StateGraph, END

from ..shared.llama_client import LlamaClient
from ..shared.chroma_manager import ChromaManager
from .models import IndexState, ASTAnalysis
from .ast_analyzer import ASTAnalyzer
from .documentation_generator import DocumentationGenerator
from .gitignore_parser import GitignoreParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexRepoAgent:
    """Enhanced LangGraph-based agent for indexing repositories with folder-based documentation."""
    
    def __init__(
        self,
        llama_client: Optional[LlamaClient] = None,
        chroma_manager: Optional[ChromaManager] = None,
        max_file_size: int = 100000,
        excluded_dirs: Optional[Set[str]] = None,
        excluded_extensions: Optional[Set[str]] = None,
        output_dir: Optional[str] = None,
        respect_gitignore: bool = True,
        enhanced_features: Optional[Dict[str, Any]] = None
    ):
        """Initialize enhanced index repository agent with additional features."""
        self.llama_client = llama_client or LlamaClient()
        self.chroma_manager = chroma_manager or ChromaManager()
        self.max_file_size = max_file_size
        self.output_dir = output_dir
        self.respect_gitignore = respect_gitignore
        self.gitignore_parser = None
        # Ensure enhanced_features is always set
        self.enhanced_features = enhanced_features or {
            "include_diagrams": False,
            "diagram_format": "mermaid",
            "include_examples": False,
            "intelligent_structure": True
        }
        
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
        self.graph = self._build_graph().compile()
    
    def _build_graph(self):
        workflow = StateGraph(IndexState)
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("scan_repo", self._scan_repository)
        workflow.add_node("analyze_ast", self._analyze_with_ast)
        workflow.add_node("generate_structure", self._generate_structure)
        workflow.add_node("generate_folder_docs", self._generate_folder_docs)
        workflow.add_node("write_docs", self._write_documentation_files)
        workflow.add_node("store_docs", self._store_documentation)
        workflow.add_node("next_repo", self._next_repo)
        workflow.add_node("generate_general_memo", self._generate_general_memo)
        workflow.add_node("finalize", self._finalize)
        workflow.add_node("handle_error", self._handle_error)

        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "scan_repo")
        workflow.add_edge("scan_repo", "analyze_ast")
        workflow.add_edge("analyze_ast", "generate_structure")
        workflow.add_edge("generate_structure", "generate_folder_docs")
        workflow.add_edge("generate_folder_docs", "write_docs")
        workflow.add_edge("write_docs", "store_docs")
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
        return workflow
    
    def get_output_dir(self) -> str:
        """Get the output directory for documentation files."""
        if self.output_dir:
            return str(Path(self.output_dir).resolve())
        else:
            return str(Path.cwd() / "documentation")
    
    def index_repositories(self, repo_paths: List[str], output_dir: Optional[str] = None, enhanced_features: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Index multiple repositories and generate comprehensive folder-based documentation."""
        # Update enhanced features if provided
        if enhanced_features:
            self.enhanced_features.update(enhanced_features)
        
        initial_state = IndexState(
            repo_paths=repo_paths,
            current_repo_index=0,
            current_repo_path="",
            repo_files=[],
            ast_analysis={},
            generated_docs={},
            documentation_structure=None,
            current_folder_index=0,
            current_section_index=0,
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
            "individual_memos": result["all_docs"],
            "general_memo": result["general_memo"],
            "total_repos": len(repo_paths),
            "output_dir": result.get("output_dir")
        }
    
    def _initialize(self, state: IndexState) -> IndexState:
        """Initialize the indexing process with validation."""
        logger.info("Initializing enhanced folder-based indexing process for %d repositories", len(state["repo_paths"]))
        
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
            
            # Filter files for AST analysis
            analyzable_files = []
            for file_info in repo_files:
                if (file_info["size"] < self.max_file_size and
                    self._should_analyze_file(file_info)):
                    analyzable_files.append(file_info)
            
            logger.info(f"Performing parallel AST analysis on {len(analyzable_files)} files (filtered from {len(repo_files)} total)")
            
            ast_analysis = {}
            
            # Use parallel processing for AST analysis
            max_workers = min(4, len(analyzable_files))
            
            # For very large repositories, limit the number of files analyzed
            if len(analyzable_files) > 5000:
                logger.info(f"Large repository detected ({len(analyzable_files)} files). Limiting analysis to top 5000 files.")
                analyzable_files = sorted(analyzable_files, key=self._file_analysis_priority)[:5000]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
                        if completed % 500 == 0:
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
    
    def _generate_structure(self, state: IndexState) -> IndexState:
        """Generate the documentation structure (first scan)."""
        try:
            repo_path = state["current_repo_path"]
            repo_metadata = state["repo_metadata"]
            ast_analysis = state["ast_analysis"]
            repo_files = state["repo_files"]
            
            logger.info(f"Generating documentation structure for {repo_path}")
            
            # Prepare file contents for context
            file_contents = self._prepare_file_contents(repo_files)
            
            # Generate documentation structure
            doc_structure = self.doc_generator.generate_documentation_structure(
                repo_path=repo_path,
                repo_metadata=repo_metadata,
                ast_analysis=ast_analysis,
                file_contents=file_contents
            )
            
            new_state = state.copy()
            new_state["documentation_structure"] = doc_structure
            new_state["current_folder_index"] = 0
            new_state["current_section_index"] = 0
            
            logger.info(f"Generated structure with {len(doc_structure.folders)} folders")
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to generate documentation structure: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to generate documentation structure: {str(e)}"
            return new_state
    
    def _generate_folder_docs(self, state: IndexState) -> IndexState:
        """Generate complete folder-based documentation with detailed file analysis."""
        try:
            repo_path = state["current_repo_path"]
            repo_metadata = state["repo_metadata"]
            ast_analysis = state["ast_analysis"]
            repo_files = state["repo_files"]
            doc_structure = state["documentation_structure"]
            
            logger.info(f"Generating comprehensive folder-based documentation for {repo_path}")
            
            # Prepare ALL file contents for comprehensive analysis
            file_contents = self._prepare_file_contents(repo_files)
              # Generate detailed file documentation using AI for each file
            try:
                detailed_file_docs = self._generate_detailed_file_docs(file_contents, repo_path, repo_metadata)
            except Exception as e:
                logger.warning(f"Failed to generate detailed file docs: {str(e)}, using fallback")
                detailed_file_docs = "# File Documentation\n\n*Detailed file documentation generation failed.*"
            
            # Generate complete folder structure
            try:
                folder_docs = self.doc_generator.generate_folder_structure(
                    repo_path=repo_path,
                    repo_metadata=repo_metadata,
                    ast_analysis=ast_analysis,
                    file_contents=file_contents
                )
                
                # Validate that the structure contains required keys
                if not isinstance(folder_docs, dict) or "README.md" not in folder_docs:
                    logger.warning("Generated folder docs missing README.md, using fallback")
                    folder_docs = self._create_fallback_documentation(repo_path, state)
                    
            except Exception as e:
                logger.warning(f"Failed to generate folder structure: {str(e)}, using fallback")
                folder_docs = self._create_fallback_documentation(repo_path, state)
              # Add detailed file documentation to the components folder
            if "folders" not in folder_docs:
                folder_docs["folders"] = {}
            
            if "components" not in folder_docs["folders"]:
                folder_docs["folders"]["components"] = {}
            
            # Add detailed file documentation safely
            try:
                folder_docs["folders"]["components"]["file-documentation.md"] = detailed_file_docs
            except Exception as e:
                logger.warning(f"Failed to add detailed file docs: {str(e)}")
                # Ensure the structure exists even if we can't add the detailed docs
                if "components" not in folder_docs["folders"]:
                    folder_docs["folders"]["components"] = {"README.md": "# Components\n\n*Component documentation unavailable.*"}
            
            new_state = state.copy()
            new_state["generated_docs"] = folder_docs
            
            # Count total sections generated
            total_sections = sum(len(folder_data) for folder_data in folder_docs.get("folders", {}).values())
            logger.info(f"Generated {len(folder_docs.get('folders', {}))} folders with {total_sections} total sections")
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to generate folder documentation: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to generate folder documentation: {str(e)}"
            return new_state
    
    def _write_documentation_files(self, state: IndexState) -> IndexState:
        """Write documentation files to disk in folder structure."""
        try:
            # Skip file writing if no output directory is specified
            # This allows mono-repo generators to handle file writing
            if not state.get("output_dir"):
                logger.info("No output directory specified, skipping file writing (likely mono-repo mode)")
                new_state = state.copy()
                return new_state
            
            repo_path = state["current_repo_path"]
            generated_docs = state["generated_docs"]
            
            # Validate generated_docs structure
            if not generated_docs:
                logger.warning("No generated documentation found, creating basic structure")
                generated_docs = self._create_fallback_documentation(repo_path, state)
            
            # Determine output directory with better path handling
            output_dir = Path(state["output_dir"]).resolve()
            repo_name = Path(repo_path).name
            
            # Check if we should create a subdirectory or use the output dir directly
            # For mono-repo mode or when output_dir is specifically provided, 
            # we should be more careful about directory structure
            total_repos = len(state.get("repo_paths", []))
            
            if total_repos == 1:
                # Single repository - use output directory directly
                repo_output_dir = output_dir
                logger.info(f"Creating documentation in specified directory: {repo_output_dir}")
            else:
                # Multiple repositories - create subdirectory for each
                repo_output_dir = output_dir / repo_name
                logger.info(f"Creating documentation in subdirectory: {repo_output_dir}")
            
            # Ensure output directory exists
            repo_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write README.md with fallback
            readme_path = repo_output_dir / "README.md"
            readme_content = generated_docs.get("README.md")
            if not readme_content:
                logger.warning("README.md not found in generated docs, creating fallback")
                readme_content = self._create_fallback_readme(repo_path, state)
            
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            logger.info(f"Written: {readme_path}")
            
            # Write folder structure
            folders_data = generated_docs.get("folders", {})
            for folder_name, folder_content in folders_data.items():
                folder_dir = repo_output_dir / folder_name
                folder_dir.mkdir(parents=True, exist_ok=True)
                
                # Write each file in the folder
                for file_name, file_content in folder_content.items():
                    file_path = folder_dir / file_name
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(file_content)
                    logger.info(f"Written: {file_path}")
            
            # Create an index file for navigation
            index_content = self._generate_index_file(generated_docs, Path(repo_path).name)
            index_path = repo_output_dir / "index.md"
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)
            logger.info(f"Written navigation index: {index_path}")
            
            logger.info(f"All documentation files written to {repo_output_dir}")
            
            # Update state with actual output directory for reference
            new_state = state.copy()
            new_state["actual_output_dir"] = str(repo_output_dir)
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to write documentation files: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to write documentation files: {str(e)}"
            return new_state
    
    def _generate_index_file(self, generated_docs: Dict[str, Any], repo_name: str) -> str:
        """Generate a navigation index file for the documentation."""
        
        index_content = f"""# {repo_name} Documentation Index

Welcome to the comprehensive documentation for the **{repo_name}** repository.

## Quick Navigation

### 📋 [Main README](README.md)
Overview and getting started guide for the project.

### 📁 Documentation Sections

"""
        
        folders_data = generated_docs.get("folders", {})
        for folder_name, folder_content in folders_data.items():
            # Capitalize and format folder name
            folder_title = folder_name.replace("_", " ").replace("-", " ").title()
            index_content += f"\n#### 📂 {folder_title}\n"
            
            for file_name, _ in folder_content.items():
                # Create readable title from filename
                file_title = file_name.replace(".md", "").replace("_", " ").replace("-", " ").title()
                index_content += f"- [{file_title}]({folder_name}/{file_name})\n"
        
        index_content += f"""

---

## About This Documentation

This documentation was automatically generated using the DeepL Wiki system, which provides:

- **Comprehensive Analysis**: Every file in the repository has been analyzed
- **AI-Generated Insights**: Technical documentation created by AI analysis
- **Searchable Content**: All content is indexed for chat-based queries
- **Structured Organization**: Documentation organized by purpose and component type

### Usage

- Browse the sections above to explore different aspects of the codebase
- Use the chat interface to ask specific questions about the code
- Refer to individual file documentation for detailed technical information

*Generated on: {str(Path().absolute().parent)}*
*Repository: {repo_name}*
"""
        
        return index_content
    
    def _store_documentation(self, state: IndexState) -> IndexState:
        """Store the generated documentation and ALL individual files in ChromaDB."""
        try:
            repo_path = state["current_repo_path"]
            generated_docs = state["generated_docs"]
            repo_metadata = state["repo_metadata"]
            repo_files = state["repo_files"]
              # Prepare metadata for ChromaDB (only primitive types allowed)
            chroma_metadata = self._prepare_chroma_metadata(repo_metadata)
            
            logger.info(f"Storing documentation and indexing {len(repo_files)} individual files into ChromaDB")
            
            # Store README with fallback
            readme_content = generated_docs.get("README.md")
            if not readme_content:
                logger.warning("README.md not found in generated docs, creating fallback")
                readme_content = self._create_fallback_readme(repo_path, state)
            
            readme_metadata = {**chroma_metadata, "document_type": "README"}
            self.chroma_manager.add_repo_memo(
                repo_path=f"{repo_path}/README.md",
                memo_content=readme_content,
                repo_metadata=readme_metadata
            )
            
            # Store each folder and its sections
            folders_data = generated_docs.get("folders", {})
            for folder_name, folder_content in folders_data.items():
                for file_name, file_content in folder_content.items():
                    doc_metadata = {
                        **chroma_metadata, 
                        "document_type": f"{folder_name}/{file_name}",
                        "folder": folder_name,
                        "section": file_name
                    }
                    self.chroma_manager.add_repo_memo(
                        repo_path=f"{repo_path}/{folder_name}/{file_name}",
                        memo_content=file_content,
                        repo_metadata=doc_metadata
                    )
            
            # Store ALL individual source files for chat reference
            for file_info in repo_files:
                if self._should_index_file(file_info):
                    try:
                        with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                            file_content = f.read()
                        
                        file_metadata = {
                            **chroma_metadata,
                            "document_type": "source_file",
                            "file_path": file_info["relative_path"],
                            "file_name": file_info["name"],
                            "file_extension": file_info["extension"],
                            "file_category": file_info["category"],
                            "file_size": file_info["size"]
                        }
                        
                        # Create a comprehensive memo for each file
                        file_memo = f"""# File: {file_info['relative_path']}

**Type**: {file_info['category'].title()} File ({file_info['extension']})
**Size**: {file_info['size']:,} bytes
**Path**: {file_info['relative_path']}

## Content

```{file_info['extension'].replace('.', '')}
{file_content}
```

---
*This file is part of {Path(repo_path).name} repository*
"""
                        
                        self.chroma_manager.add_repo_memo(
                            repo_path=f"{repo_path}/{file_info['relative_path']}",
                            memo_content=file_memo,
                            repo_metadata=file_metadata
                        )
                        
                    except Exception as e:
                        logger.warning(f"Failed to index file {file_info['path']}: {str(e)}")
                        continue
              # Create combined memo for CLI compatibility
            readme_content = generated_docs.get("README.md", "")
            if not readme_content:
                readme_content = self._create_fallback_readme(repo_path, state)
            
            combined_memo = readme_content + "\n\n"
            for folder_name, folder_content in folders_data.items():
                for file_name, file_content in folder_content.items():
                    combined_memo += f"\n\n# {folder_name}/{file_name}\n\n{file_content}"
            
            # Add to all_docs for final summary
            doc_entry = {
                "repo_path": repo_path,
                "documents": generated_docs,
                "metadata": repo_metadata,
                "memo_content": combined_memo
            }
            
            all_docs = state["all_docs"].copy()
            all_docs.append(doc_entry)
            
            new_state = state.copy()
            new_state["all_docs"] = all_docs
            
            # Count total stored documents
            indexed_files = len([f for f in repo_files if self._should_index_file(f)])
            total_docs = 1 + sum(len(folder_content) for folder_content in folders_data.values()) + indexed_files
            logger.info(f"Stored {total_docs} documents in ChromaDB ({indexed_files} source files + documentation)")
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to store documentation: {str(e)}")
            new_state = state.copy()
            new_state["error"] = f"Failed to store documentation: {str(e)}"
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
            "documentation_structure": None,
            "current_folder_index": 0,
            "current_section_index": 0,
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
            total_folders = 0
            total_sections = 0
            languages = set()
            
            for doc_entry in all_docs:
                repo_name = Path(doc_entry["repo_path"]).name
                metadata = doc_entry["metadata"]
                documents = doc_entry["documents"]
                
                languages.add(metadata.get('primary_language', 'Unknown'))
                
                folders_count = len(documents.get("folders", {}))
                sections_count = sum(len(folder_content) for folder_content in documents.get("folders", {}).values())
                
                total_folders += folders_count
                total_sections += sections_count
                
                summary = f"**{repo_name}**\n"
                summary += f"- Language: {metadata.get('primary_language', 'Unknown')}\n"
                summary += f"- Files: {metadata.get('file_count', 0)}\n"
                summary += f"- Size: {metadata.get('total_size', 0)} bytes\n"
                summary += f"- Documentation Folders: {folders_count}\n"
                summary += f"- Documentation Sections: {sections_count}\n"
                
                repo_summaries.append(summary)
            
            general_memo_prompt = f"""Create a comprehensive overview memo for this collection of repositories:

Repository Collection Summary:
{chr(10).join(repo_summaries)}

Collection Statistics:
- Total Repositories: {len(all_docs)}
- Languages Used: {', '.join(languages)}
- Documentation Folders Generated: {total_folders}
- Documentation Sections Generated: {total_sections}

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
        
        logger.info("Enhanced folder-based indexing process completed successfully")
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
    
    def _prepare_file_contents(self, repo_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare ALL file contents for comprehensive documentation generation."""
        file_contents = []
        
        logger.info(f"Processing {len(repo_files)} files for documentation generation")
        
        # Process ALL files in the repository (not just a subset)
        for file_info in repo_files:
            if file_info["size"] < self.max_file_size and self._should_analyze_file(file_info):
                try:
                    with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        # Determine content length based on file type and size
                        if file_info["category"] == "documentation":
                            max_content = min(20000, len(content))  # Up to 20KB for docs
                        elif file_info["category"] == "code":
                            max_content = min(15000, len(content))  # Up to 15KB for code
                        elif file_info["category"] == "config":
                            max_content = min(10000, len(content))  # Up to 10KB for config
                        else:
                            max_content = min(8000, len(content))   # Up to 8KB for other files
                        
                        file_contents.append({
                            "path": file_info["relative_path"],
                            "content": content[:max_content],
                            "full_content": content,  # Keep full content for indexing
                            "size": file_info["size"],
                            "extension": file_info["extension"],
                            "category": file_info["category"],
                            "name": file_info["name"]
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to read file {file_info['path']}: {str(e)}")
                    continue
        
        logger.info(f"Successfully processed {len(file_contents)} files for documentation")
        return file_contents
    
    def _generate_detailed_file_docs(
        self, 
        file_contents: List[Dict[str, Any]], 
        repo_path: str, 
        repo_metadata: Dict[str, Any]
    ) -> str:
        """Generate detailed documentation for each file using AI."""
        
        repo_name = Path(repo_path).name
        logger.info(f"Generating detailed file documentation for {len(file_contents)} files")
        
        # Group files by category for better organization
        files_by_category = {
            "code": [],
            "config": [],
            "documentation": [],
            "other": []
        }
        
        for file_info in file_contents:
            category = file_info.get("category", "other")
            files_by_category[category].append(file_info)
        
        detailed_docs = f"""# Comprehensive File Documentation

This document provides detailed analysis and documentation for all files in the {repo_name} repository.

## Repository Overview

- **Primary Language**: {repo_metadata.get('primary_language', 'Unknown')}
- **Total Files Analyzed**: {len(file_contents)}
- **Repository Path**: {repo_path}

---

"""
        
        # Process each category
        for category, files in files_by_category.items():
            if not files:
                continue
                
            detailed_docs += f"\n## {category.title()} Files ({len(files)} files)\n\n"
            
            # Process files in batches to avoid overwhelming the AI
            batch_size = 5
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                batch_docs = self._generate_file_batch_docs(batch, category, repo_name)
                detailed_docs += batch_docs + "\n\n"
        
        return detailed_docs
    
    def _generate_file_batch_docs(
        self, 
        file_batch: List[Dict[str, Any]], 
        category: str, 
        repo_name: str
    ) -> str:
        """Generate documentation for a batch of files."""
        
        # Prepare context for the batch
        batch_context = f"Repository: {repo_name}\nFile Category: {category}\n\nFiles to analyze:\n\n"
        
        for file_info in file_batch:
            batch_context += f"""### {file_info['path']}
- **Size**: {file_info['size']:,} bytes
- **Extension**: {file_info['extension']}
- **Category**: {file_info['category']}

**Content Preview:**
```{file_info['extension'].replace('.', '')}
{file_info['content'][:2000]}{'...' if len(file_info['content']) > 2000 else ''}
```

---

"""
        
        prompt = f"""You are a technical documentation expert. Analyze these {category} files and create comprehensive documentation for each.

{batch_context}

For each file, provide:

1. **Purpose & Role**: What this file does and its role in the project
2. **Key Components**: Main functions, classes, or configuration items
3. **Dependencies**: What this file imports or depends on
4. **Usage**: How this file is used or called by other parts of the system
5. **Technical Notes**: Important implementation details or patterns

Format each file as a markdown subsection with clear headers. Be detailed but concise.

File Documentation:"""

        try:
            batch_docs = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            return batch_docs.strip()
        except Exception as e:
            logger.warning(f"Failed to generate batch documentation: {str(e)}")
            # Fallback to basic documentation
            fallback_docs = ""
            for file_info in file_batch:
                fallback_docs += f"""### {file_info['path']}

**Type**: {file_info['category'].title()} File ({file_info['extension']})
**Size**: {file_info['size']:,} bytes

*AI documentation generation failed. File indexed for search but detailed analysis unavailable.*

---

"""
            return fallback_docs
    
    def _should_index_file(self, file_info: Dict[str, Any]) -> bool:
        """Determine if a file should be indexed into ChromaDB for chat reference."""
        
        # Index all files that we can analyze, plus some additional types
        indexable_extensions = {
            # Code files
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.scala', '.swift',
            '.vue', '.svelte', '.dart', '.r', '.jl', '.m', '.mm',
            
            # Documentation
            '.md', '.txt', '.rst', '.org', '.adoc',
            
            # Configuration
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.xml', '.env', '.properties',
            
            # Web files
            '.html', '.css', '.scss', '.sass', '.less',
            
            # Data files
            '.sql', '.csv',
            
            # Scripts
            '.sh', '.bash', '.ps1', '.bat', '.cmd'
        }
        
        skip_patterns = [
            # Skip test and build artifacts
            'test', 'spec', '__test__', '.test.', '.spec.',
            'mock', 'fixture', 'sample', 'example',
            'vendor', 'third_party', 'external',
            'generated', 'auto', 'build', 'dist',
            'min.js', 'min.css', 'bundle.js', 'bundle.css',
            'lock.json', 'package-lock.json', 'yarn.lock',
            '.pyc', '.pyo', '.class', '.o', '.so'
        ]
        
        file_path = file_info["path"].lower()
        file_name = file_info["name"].lower()
        extension = file_info["extension"]
        
        # Check extension
        if extension not in indexable_extensions:
            return False
        
        # Skip if file size is too large
        if file_info["size"] > 1000000:  # 1MB limit
            return False
        
        # Skip if file size is too small (likely empty or generated)
        if file_info["size"] < 10:
            return False
        
        # Skip based on patterns
        for pattern in skip_patterns:
            if pattern in file_path or pattern in file_name:
                return False
        
        return True
    
    def _prepare_chroma_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool, None]]:
        """Prepare metadata for ChromaDB by converting complex types to strings."""
        chroma_metadata = {}
        
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                chroma_metadata[key] = value
            elif isinstance(value, dict):
                chroma_metadata[key] = json.dumps(value)
            elif isinstance(value, list):
                chroma_metadata[key] = ", ".join(str(item) for item in value)
            else:
                chroma_metadata[key] = str(value)
        
        return chroma_metadata
    
    def _should_analyze_file(self, file_info: Dict[str, Any]) -> bool:
        """Determine if a file should be analyzed."""
        analyzable_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.scala', '.swift',
            '.vue', '.svelte', '.dart', '.r', '.jl', '.m', '.mm'
        }
        
        documentation_extensions = {
            '.md', '.txt', '.rst', '.org', '.adoc'
        }
        
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
        
        # Accept documentation files
        if extension in documentation_extensions or category == "documentation":
            if file_info["size"] > 100000:  # 100KB limit for docs
                return False
            return True
        
        # Accept code files
        if extension in analyzable_extensions:
            for pattern in skip_patterns:
                if pattern in file_path or pattern in file_name:
                    return False
            
            if file_info["size"] < 50 or file_info["size"] > 500000:
                return False
            
            priority_dirs = ['src', 'lib', 'app', 'components', 'pages', 'views', 'controllers', 'models', 'services']
            has_priority_dir = any(dir_name in file_path for dir_name in priority_dirs)
            
            if not has_priority_dir and category != "code":
                return False
            
            return True
        
        return False
    
    def _file_analysis_priority(self, file_info: Dict[str, Any]) -> tuple:
        """Calculate priority for file analysis."""
        file_path = file_info["path"].lower()
        file_name = file_info["name"].lower()
        
        important_files = ['main.py', 'app.py', 'index.js', 'main.js', 'server.js', '__init__.py']
        if file_name in important_files:
            return (0, -file_info["size"])
        
        priority_dirs = ['src/', 'lib/', 'app/', 'components/', 'pages/']
        if any(dir_name in file_path for dir_name in priority_dirs):
            return (1, -file_info["size"])
        
        if file_info["category"] == "code":
            return (2, -file_info["size"])
        
        if file_info["category"] == "config":
            return (3, -file_info["size"])
        
        return (4, -file_info["size"])
    
    def _analyze_single_file(self, file_info: Dict[str, Any]) -> Optional[ASTAnalysis]:
        """Analyze a single file with AST."""
        try:
            with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            return self.ast_analyzer.analyze_file(file_info["path"], content)
            
        except Exception:
            return None
    
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
    
    def _create_fallback_documentation(self, repo_path: str, state: IndexState) -> Dict[str, Any]:
        """Create basic fallback documentation when AI generation fails."""
        repo_name = Path(repo_path).name
        repo_metadata = state.get("repo_metadata", {})
        
        readme_content = self._create_fallback_readme(repo_path, state)
        
        # Create proper folder structure matching the expected format
        fallback_docs = {
            "README.md": readme_content,
            "folders": {
                "architecture": {
                    "README.md": f"# Architecture Documentation\n\nSystem design and architectural decisions for {repo_name}.\n\n## Sections\n\n- **[Overview](overview.md)**: High-level system architecture\n- **[Components](components.md)**: Core system components\n- **[Structure](structure.md)**: Repository structure analysis\n\n---\n\n*Documentation for {repo_name}*",
                    "overview.md": f"## System Overview\n\n{repo_name} is built using {repo_metadata.get('primary_language', 'Unknown')} with {repo_metadata.get('file_count', 0)} total files.\n\n*Detailed architecture analysis unavailable in fallback mode.*",
                    "components.md": f"## Core Components\n\nMain components detected in {repo_name}:\n\n*Component analysis unavailable in fallback mode.*",
                    "structure.md": self._create_basic_structure_doc(repo_path, state)
                },
                "components": {
                    "README.md": f"# Component Documentation\n\nDetailed documentation for each system component in {repo_name}.\n\n## Sections\n\n- **[Core Components](core.md)**: Essential system components\n- **[Utilities](utilities.md)**: Helper and utility components\n\n---\n\n*Documentation for {repo_name}*",
                    "core.md": f"## Core Components\n\n*Component documentation unavailable in fallback mode.*",
                    "utilities.md": f"## Utility Components\n\n*Utility documentation unavailable in fallback mode.*"
                },
                "development": {
                    "README.md": f"# Development Guide\n\nDevelopment setup, workflows, and guidelines for {repo_name}.\n\n## Sections\n\n- **[Setup](setup.md)**: Development environment setup\n- **[Workflow](workflow.md)**: Development process\n- **[Contributing](contributing.md)**: Contribution guidelines\n\n---\n\n*Documentation for {repo_name}*",
                    "setup.md": f"## Development Setup\n\nSetup instructions for {repo_name}.\n\n*Setup documentation unavailable in fallback mode.*",
                    "workflow.md": f"## Development Workflow\n\nDevelopment process for {repo_name}.\n\n*Workflow documentation unavailable in fallback mode.*",
                    "contributing.md": f"## Contributing\n\nContribution guidelines for {repo_name}.\n\n*Contributing guidelines unavailable in fallback mode.*"
                }
            }
        }
        
        return fallback_docs
    
    def _create_fallback_readme(self, repo_path: str, state: IndexState) -> str:
        """Create a basic README when full generation fails."""
        repo_name = Path(repo_path).name
        repo_metadata = state.get("repo_metadata", {})
        repo_files = state.get("repo_files", [])
        
        primary_language = repo_metadata.get("primary_language", "Unknown")
        file_count = len(repo_files)
        total_size = sum(f.get("size", 0) for f in repo_files)
        
        readme_content = f"""# {repo_name}

## Repository Information

- **Primary Language**: {primary_language}
- **Total Files**: {file_count:,}
- **Repository Size**: {total_size:,} bytes
- **Path**: {repo_path}

## Overview

This repository contains {file_count} files primarily written in {primary_language}.

## File Categories

"""
        
        # Add file category breakdown
        categories = {}
        for file_info in repo_files:
            category = file_info.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        
        for category, count in sorted(categories.items()):
            readme_content += f"- **{category.title()}**: {count} files\n"
        
        readme_content += f"""

## Configuration Files

"""
        
        config_files = repo_metadata.get("config_files", [])
        if config_files:
            for config_file in config_files[:10]:  # Show first 10
                readme_content += f"- `{config_file}`\n"
        else:
            readme_content += "No configuration files detected.\n"
        
        readme_content += f"""

---

*This documentation was generated automatically by DeepL Wiki system.*
*Full documentation generation failed, showing basic repository analysis.*
"""
        
        return readme_content
    
    def _create_basic_structure_doc(self, repo_path: str, state: IndexState) -> str:
        """Create basic structure documentation."""
        repo_name = Path(repo_path).name
        repo_files = state.get("repo_files", [])
        
        # Group files by directory
        directories = {}
        for file_info in repo_files:
            rel_path = file_info.get("relative_path", "")
            dir_name = str(Path(rel_path).parent) if Path(rel_path).parent != Path(".") else "root"
            
            if dir_name not in directories:
                directories[dir_name] = []
            directories[dir_name].append(file_info)
        
        structure_content = f"""# {repo_name} Structure

## Directory Layout

"""
        
        # Show directory structure
        for dir_name, files in sorted(directories.items()):
            if dir_name == "root":
                structure_content += f"### Root Directory ({len(files)} files)\n\n"
            else:
                structure_content += f"### `{dir_name}/` ({len(files)} files)\n\n"
            
            # Show important files in each directory
            important_files = [f for f in files if f.get("name", "").lower() in [
                "readme.md", "main.py", "app.py", "index.js", "package.json", 
                "requirements.txt", "dockerfile", "makefile"
            ]]
            
            if important_files:
                structure_content += "**Key Files:**\n"
                for file_info in important_files:
                    structure_content += f"- `{file_info.get('name', '')}` ({file_info.get('size', 0):,} bytes)\n"
                structure_content += "\n"
            
            # Show file type breakdown
            file_types = {}
            for file_info in files:
                ext = file_info.get("extension", "")
                if ext:
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            if file_types:
                structure_content += "**File Types:**\n"
                for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                    structure_content += f"- `{ext}`: {count} files\n"
                structure_content += "\n"
        
        structure_content += """
---

*Basic structure analysis generated in fallback mode.*
"""
        
        return structure_content
