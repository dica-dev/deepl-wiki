"""Chat agent for interactive documentation queries using LangGraph."""

from typing import Dict, List, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END

from .shared.llama_client import LlamaClient
from .shared.chroma_manager import ChromaManager

class ChatState(TypedDict):
    """State for the chat agent."""
    messages: List[Dict[str, str]]
    query: str
    search_results: List[Dict[str, Any]]
    response: str
    context: str
    error: Optional[str]

class ChatAgent:
    """LangGraph-based chat agent for documentation queries."""
    
    def __init__(
        self, 
        llama_client: Optional[LlamaClient] = None,
        chroma_manager: Optional[ChromaManager] = None,
        max_search_results: int = 5
    ):
        """Initialize chat agent."""
        self.llama_client = llama_client or LlamaClient()
        self.chroma_manager = chroma_manager or ChromaManager()
        self.max_search_results = max_search_results
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ChatState)
        
        workflow.add_node("search_docs", self._search_docs)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        
        workflow.set_entry_point("search_docs")
        workflow.add_edge("search_docs", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        workflow.add_conditional_edges(
            "search_docs",
            self._should_handle_error,
            {"error": "handle_error", "continue": "generate_response"}
        )
        
        return workflow.compile()
    
    def chat(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process a chat query."""
        initial_state = ChatState(
            messages=conversation_history or [],
            query=query,
            search_results=[],
            response="",
            context="",
            error=None
        )
        
        result = self.graph.invoke(initial_state)
        
        return {
            "response": result["response"],
            "search_results": result["search_results"],            "context": result["context"],
            "error": result.get("error")
        }
    
    def _search_docs(self, state: ChatState) -> ChatState:
        """Search documentation for relevant context."""
        try:
            query = state["query"]
            
            search_results = self.chroma_manager.search_repos(
                query=query,
                n_results=self.max_search_results
            )
            
            context_parts = []
            for result in search_results:
                metadata = result["metadata"]
                content = result["content"]
                similarity = result["similarity"]
                
                repo_info = f"Repository: {metadata.get('repo_name', 'Unknown')}"
                if metadata.get('file_path'):
                    repo_info += f" | File: {metadata['file_path']}"
                
                context_parts.append(
                    f"{repo_info} (Relevance: {similarity:.2f})\n{content}\n"
                )
            
            context = "\n---\n".join(context_parts)
            
            new_state = state.copy()
            new_state.update({
                "search_results": search_results,
                "context": context
            })
            return new_state            
        except Exception as e:
            new_state = state.copy()
            new_state["error"] = f"Search error: {str(e)}"
            return new_state
    
    def _generate_response(self, state: ChatState) -> ChatState:
        """Generate response using Llama API."""
        try:
            query = state["query"]
            context = state["context"]
            conversation_history = state["messages"]
            
            system_prompt = self.llama_client.generate_system_prompt(
                role="chat",
                context=f"Use the following documentation context to answer user questions:\n\n{context}"
            )
            
            messages = [{"role": "system", "content": system_prompt}]
            
            for msg in conversation_history[-10:]:
                messages.append(msg)
            
            messages.append({"role": "user", "content": query})
            
            response = self.llama_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            new_state = state.copy()
            new_state["response"] = response
            return new_state            
        except Exception as e:
            new_state = state.copy()
            new_state["error"] = f"Generation error: {str(e)}"
            return new_state
    
    def _handle_error(self, state: ChatState) -> ChatState:
        """Handle errors gracefully."""
        error = state.get("error", "Unknown error occurred")
        
        response = f"I apologize, but I encountered an error while processing your request: {error}"
        
        if "search" in error.lower():
            response += "\n\nThis might be because no documentation has been indexed yet. Please make sure repositories have been processed by the index agent."
        elif "generation" in error.lower():
            response += "\n\nThis might be a temporary issue with the AI service. Please try again in a moment."
        
        new_state = state.copy()
        new_state["response"] = response
        return new_state
    
    def _should_handle_error(self, state: ChatState) -> str:
        """Determine if we should handle an error."""
        return "error" if state.get("error") else "continue"
