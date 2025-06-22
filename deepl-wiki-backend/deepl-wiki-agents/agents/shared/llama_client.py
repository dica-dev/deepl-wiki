"""Llama API client using OpenAI SDK compatibility."""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

class LlamaClient:
    """Client for interacting with Llama API using OpenAI SDK."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"):
        """Initialize Llama client.
        
        Args:
            api_key: Llama API key. If None, reads from LLAMA_API_KEY env var.
            model: Model name to use for completions.
        """
        self.api_key = api_key or os.environ.get("LLAMA_API_KEY")
        if not self.api_key:
            raise ValueError("LLAMA_API_KEY environment variable or api_key parameter required")
            
        self.model = model
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.llama.com/compat/v1/"
        )
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Generated text response
        """
        completion_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        
        if max_tokens:
            completion_kwargs["max_tokens"] = max_tokens
            
        completion = self.client.chat.completions.create(**completion_kwargs)
        
        if stream:
            return completion  # Return generator for streaming
        else:
            return completion.choices[0].message.content
    
    def generate_system_prompt(self, role: str, context: str = "") -> str:
        """Generate a system prompt for a specific agent role.
        
        Args:
            role: The agent role (chat, push, index)
            context: Additional context to include
            
        Returns:
            Formatted system prompt
        """
        base_prompts = {
            "chat": """You are a helpful documentation chat assistant. You help users find information about their codebase by answering questions based on indexed documentation and code memos. 

Key capabilities:
- Answer questions about code structure, functionality, and documentation
- Provide relevant code examples and explanations  
- Help users navigate complex codebases
- Maintain conversational context across interactions

Always be helpful, accurate, and cite your sources when possible.""",

            "push": """You are a repository management agent responsible for pushing documentation updates to GitHub repositories.

Key responsibilities:
- Create and manage branches in memo repositories
- Push generated documentation to appropriate locations
- Handle GitHub API operations safely and efficiently
- Manage version control workflows for documentation

Always verify operations before executing and handle errors gracefully.""",

            "index": """You are a repository indexing agent that analyzes codebases and generates comprehensive documentation memos.

Key responsibilities:  
- Scan repository contents and identify important files
- Extract key information about code structure and functionality
- Generate detailed memos that capture essential codebase knowledge
- Create vector embeddings for efficient search and retrieval
- Handle multiple repository formats and languages

Focus on creating comprehensive, searchable documentation that helps users understand codebases quickly."""
        }
        
        prompt = base_prompts.get(role, "You are a helpful AI assistant.")
        
        if context:
            prompt += f"\n\nAdditional context:\n{context}"
            
        return prompt
