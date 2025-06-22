"""Push agent for managing GitHub repository operations using LangGraph."""

import os
import json
import tempfile
import shutil
from typing import Dict, List, Any, Optional, TypedDict
from pathlib import Path
import git
from git import Repo
from langgraph.graph import StateGraph, END

from .shared.llama_client import LlamaClient

class PushState(TypedDict):
    """State for the push agent."""
    memo_repo_url: str
    target_branch: str
    source_repo_name: str
    memo_content: str
    memo_metadata: Dict[str, Any]
    temp_dir: Optional[str]
    success: bool
    error: Optional[str]
    commit_hash: Optional[str]

class PushAgent:
    """LangGraph-based agent for pushing documentation to GitHub repositories."""
    
    def __init__(
        self,
        llama_client: Optional[LlamaClient] = None,
        github_token: Optional[str] = None
    ):
        """Initialize push agent."""
        self.llama_client = llama_client or LlamaClient()
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(PushState)
        
        workflow.add_node("clone_repo", self._clone_repo)
        workflow.add_node("create_branch", self._create_branch)
        workflow.add_node("update_memo", self._update_memo)
        workflow.add_node("commit_changes", self._commit_changes)
        workflow.add_node("push_changes", self._push_changes)
        workflow.add_node("cleanup", self._cleanup)
        workflow.add_node("handle_error", self._handle_error)
        
        workflow.set_entry_point("clone_repo")
        workflow.add_edge("clone_repo", "create_branch")
        workflow.add_edge("create_branch", "update_memo")
        workflow.add_edge("update_memo", "commit_changes")
        workflow.add_edge("commit_changes", "push_changes")
        workflow.add_edge("push_changes", "cleanup")
        workflow.add_edge("cleanup", END)
        workflow.add_edge("handle_error", "cleanup")
        
        # Add error handling
        for node in ["clone_repo", "create_branch", "update_memo", "commit_changes", "push_changes"]:
            workflow.add_conditional_edges(
                node,
                self._check_for_errors,
                {"error": "handle_error", "continue": {
                    "clone_repo": "create_branch",
                    "create_branch": "update_memo",
                    "update_memo": "commit_changes",
                    "commit_changes": "push_changes",
                    "push_changes": "cleanup"
                }[node]}
            )
        
        return workflow.compile()
    
    def push_memo(
        self,
        memo_repo_url: str,
        target_branch: str,
        source_repo_name: str,
        memo_content: str,
        memo_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Push a memo to the target repository."""
        initial_state = PushState(
            memo_repo_url=memo_repo_url,
            target_branch=target_branch,
            source_repo_name=source_repo_name,
            memo_content=memo_content,
            memo_metadata=memo_metadata,
            temp_dir=None,
            success=False,
            error=None,
            commit_hash=None
        )
        
        result = self.graph.invoke(initial_state)
        
        return {
            "success": result["success"],
            "error": result.get("error"),
            "commit_hash": result.get("commit_hash"),
            "branch": target_branch
        }
    
    def _clone_repo(self, state: PushState) -> PushState:
        """Clone the memo repository."""
        try:
            temp_dir = tempfile.mkdtemp(prefix="deepl_wiki_")
            
            repo_url = state["memo_repo_url"]
            if repo_url.startswith("https://github.com/"):
                auth_url = repo_url.replace(
                    "https://github.com/",
                    f"https://{self.github_token}@github.com/"
                )
            else:
                auth_url = repo_url
            
            Repo.clone_from(auth_url, temp_dir)
            
            return PushState(
                **state,
                temp_dir=temp_dir
            )
            
        except Exception as e:
            return PushState(
                **state,
                error=f"Failed to clone repository: {str(e)}"
            )
    
    def _create_branch(self, state: PushState) -> PushState:
        """Create or checkout the target branch."""
        try:
            repo = Repo(state["temp_dir"])
            target_branch = state["target_branch"]
            
            try:
                repo.git.checkout(f"origin/{target_branch}")
                repo.git.checkout("-b", target_branch)
            except Exception:
                try:
                    repo.git.checkout("main")
                except Exception:
                    repo.git.checkout("master")
                repo.git.checkout("-b", target_branch)
            
            return state
            
        except Exception as e:
            return PushState(
                **state,
                error=f"Failed to create/checkout branch: {str(e)}"
            )
    
    def _update_memo(self, state: PushState) -> PushState:
        """Update the memo file in the repository."""
        try:
            repo_path = Path(state["temp_dir"])
            source_repo_name = state["source_repo_name"]
            memo_content = state["memo_content"]
            memo_metadata = state["memo_metadata"]
            
            repo_dir = repo_path / source_repo_name
            repo_dir.mkdir(exist_ok=True)
            
            memo_file = repo_dir / "README.md"
            with open(memo_file, "w", encoding="utf-8") as f:
                f.write(memo_content)
            
            metadata_file = repo_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(memo_metadata, f, indent=2)
            
            summary = self._generate_memo_summary(memo_content)
            summary_file = repo_dir / "summary.md"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary)
            
            return state
            
        except Exception as e:
            return PushState(
                **state,
                error=f"Failed to update memo: {str(e)}"
            )
    
    def _commit_changes(self, state: PushState) -> PushState:
        """Commit changes to the repository."""
        try:
            repo = Repo(state["temp_dir"])
            
            repo.git.add(".")
            
            if not repo.index.diff("HEAD"):
                return PushState(
                    **state,
                    success=True,
                    commit_hash="no_changes"
                )
            
            source_repo = state["source_repo_name"]
            branch = state["target_branch"]
            commit_message = f"Update documentation for {source_repo} (branch: {branch})"
            
            metadata = state["memo_metadata"]
            if metadata.get("commit_hash"):
                commit_message += f"\n\nSource commit: {metadata['commit_hash']}"
            if metadata.get("author"):
                commit_message += f"\nAuthor: {metadata['author']}"
            
            commit = repo.index.commit(commit_message)
            
            return PushState(
                **state,
                commit_hash=commit.hexsha
            )
            
        except Exception as e:
            return PushState(
                **state,
                error=f"Failed to commit changes: {str(e)}"
            )
    
    def _push_changes(self, state: PushState) -> PushState:
        """Push changes to the remote repository."""
        try:
            repo = Repo(state["temp_dir"])
            target_branch = state["target_branch"]
            
            origin = repo.remote("origin")
            origin.push(target_branch)
            
            return PushState(
                **state,
                success=True
            )
            
        except Exception as e:
            return PushState(
                **state,
                error=f"Failed to push changes: {str(e)}"
            )
    
    def _cleanup(self, state: PushState) -> PushState:
        """Clean up temporary directory."""
        if state.get("temp_dir") and os.path.exists(state["temp_dir"]):
            try:
                shutil.rmtree(state["temp_dir"])
            except Exception:
                pass
        
        return state
    
    def _handle_error(self, state: PushState) -> PushState:
        """Handle errors gracefully."""
        return PushState(
            **state,
            success=False
        )
    
    def _check_for_errors(self, state: PushState) -> str:
        """Check if there are errors in the current state."""
        return "error" if state.get("error") else "continue"
    
    def _generate_memo_summary(self, memo_content: str) -> str:
        """Generate a summary of the memo using AI."""
        try:
            summary_prompt = f"""Create a concise summary of this repository documentation memo:

{memo_content[:2000]}...

Please provide:
1. A brief description of what this repository does
2. Key components and features
3. Main technologies used
4. Important notes for developers

Summary:"""

            summary = self.llama_client.chat_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return summary
            
        except Exception as e:
            return f"Summary generation failed: {str(e)}"
