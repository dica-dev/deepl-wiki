"""Chat endpoints for DeepL Wiki API."""

import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# Add the agents directory to the path
AGENTS_DIR = Path(__file__).parent.parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))

try:
    from agents.chat_agent import ChatAgent
except ImportError:
    ChatAgent = None

router = APIRouter()

# In-memory session storage (in production, use Redis or database)
chat_sessions: Dict[str, dict] = {}


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str


class ChatSession(BaseModel):
    session_id: str
    created_at: str
    messages: List[dict]


def get_chat_agent():
    """Dependency to get chat agent instance."""
    if ChatAgent is None:
        raise HTTPException(
            status_code=500,
            detail="Chat agent not available. Please check your configuration."
        )
    return ChatAgent()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    chat_message: ChatMessage,
    chat_agent = Depends(get_chat_agent)
):
    """
    Send a message to the chat agent and get a response.
    Creates a new session if session_id is not provided.
    """
    try:
        # Generate session ID if not provided
        session_id = chat_message.session_id or str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        # Initialize session if it doesn't exist
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "session_id": session_id,
                "created_at": str(uuid.uuid4()),  # In production, use actual timestamp
                "messages": []
            }
        
        # Add user message to session
        user_message = {
            "id": message_id,
            "role": "user",
            "content": chat_message.message,
            "timestamp": str(uuid.uuid4())  # In production, use actual timestamp
        }
        chat_sessions[session_id]["messages"].append(user_message)
          # Get response from chat agent
        try:
            # Build conversation history for the agent
            conversation_history = []
            for msg in chat_sessions[session_id]["messages"]:
                if msg["role"] in ["user", "assistant"]:
                    conversation_history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Get response from chat agent
            chat_result = chat_agent.chat(
                query=chat_message.message,
                conversation_history=conversation_history
            )
            
            response = chat_result.get("response", "I couldn't generate a response.")
            
            # Handle any errors from the chat agent
            if chat_result.get("error"):
                response = f"I encountered an issue: {chat_result['error']}"
                
        except Exception as e:
            # Fallback response if agent fails
            response = f"I'm having trouble processing your request right now. Error: {str(e)}"
        
        # Add agent response to session
        agent_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": response,
            "timestamp": str(uuid.uuid4())  # In production, use actual timestamp
        }
        chat_sessions[session_id]["messages"].append(agent_message)
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            message_id=message_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/chat/sessions", response_model=List[ChatSession])
async def get_chat_sessions():
    """Get all chat sessions."""
    return list(chat_sessions.values())


@router.get("/chat/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    """Get a specific chat session by ID."""
    if session_id not in chat_sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    return chat_sessions[session_id]


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session."""
    if session_id not in chat_sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    del chat_sessions[session_id]
    return {"message": "Session deleted successfully"}


@router.delete("/chat/sessions")
async def clear_all_sessions():
    """Clear all chat sessions."""
    global chat_sessions
    chat_sessions = {}
    return {"message": "All sessions cleared successfully"}
