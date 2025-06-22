"""SQLite database manager for chat history and repository tracking."""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class DatabaseManager:
    """Manages SQLite database for chat history and repository data."""
    
    def __init__(self, db_path: str = "./deepl_wiki.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Chat history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Repository tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_path TEXT UNIQUE NOT NULL,
                    repo_name TEXT NOT NULL,
                    primary_language TEXT,
                    file_count INTEGER,
                    total_size INTEGER,
                    last_indexed DATETIME,
                    status TEXT DEFAULT 'pending',
                    metadata TEXT
                )
            """)
            
            # Indexing sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS indexing_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    repo_count INTEGER,
                    success_count INTEGER,
                    error_count INTEGER,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    status TEXT DEFAULT 'running'
                )
            """)
            
            conn.commit()
    
    def add_chat_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a chat message to history.
        
        Args:
            session_id: Chat session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO chat_history (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, metadata_json))
            
            conn.commit()
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session.
        
        Args:
            session_id: Chat session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of chat messages
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role, content, timestamp, metadata
                FROM chat_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                role, content, timestamp, metadata_json = row
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                messages.append({
                    "role": role,
                    "content": content,
                    "timestamp": timestamp,
                    "metadata": metadata
                })
            
            return list(reversed(messages))  # Return in chronological order
    
    def add_repository(self, repo_path: str, repo_metadata: Dict[str, Any]) -> None:
        """Add or update repository information.
        
        Args:
            repo_path: Path to repository
            repo_metadata: Repository metadata dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO repositories 
                (repo_path, repo_name, primary_language, file_count, total_size, last_indexed, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repo_path,
                repo_metadata.get("repo_name", Path(repo_path).name),
                repo_metadata.get("primary_language", "Unknown"),
                repo_metadata.get("file_count", 0),
                repo_metadata.get("total_size", 0),
                datetime.now().isoformat(),
                "indexed",
                json.dumps(repo_metadata)
            ))
            
            conn.commit()
    
    def get_repositories(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of repositories.
        
        Args:
            status: Optional status filter (pending, indexed, error)
            
        Returns:
            List of repository information
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT repo_path, repo_name, primary_language, file_count, 
                           total_size, last_indexed, status, metadata
                    FROM repositories
                    WHERE status = ?
                    ORDER BY last_indexed DESC
                """, (status,))
            else:
                cursor.execute("""
                    SELECT repo_path, repo_name, primary_language, file_count,
                           total_size, last_indexed, status, metadata
                    FROM repositories
                    ORDER BY last_indexed DESC
                """)
            
            repositories = []
            for row in cursor.fetchall():
                repo_path, repo_name, primary_language, file_count, total_size, last_indexed, status, metadata_json = row
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                repositories.append({
                    "repo_path": repo_path,
                    "repo_name": repo_name,
                    "primary_language": primary_language,
                    "file_count": file_count,
                    "total_size": total_size,
                    "last_indexed": last_indexed,
                    "status": status,
                    "metadata": metadata
                })
            
            return repositories
    
    def start_indexing_session(self, session_id: str, repo_count: int) -> None:
        """Start a new indexing session.
        
        Args:
            session_id: Unique session identifier
            repo_count: Number of repositories to index
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO indexing_sessions 
                (session_id, repo_count, success_count, error_count, status)
                VALUES (?, ?, 0, 0, 'running')
            """, (session_id, repo_count))
            
            conn.commit()
    
    def complete_indexing_session(self, session_id: str, success_count: int, error_count: int) -> None:
        """Complete an indexing session.
        
        Args:
            session_id: Session identifier
            success_count: Number of successfully indexed repositories
            error_count: Number of failed repositories
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE indexing_sessions 
                SET success_count = ?, error_count = ?, completed_at = ?, status = 'completed'
                WHERE session_id = ?
            """, (success_count, error_count, datetime.now().isoformat(), session_id))
            
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Repository stats
            cursor.execute("SELECT COUNT(*) FROM repositories")
            total_repos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM repositories WHERE status = 'indexed'")
            indexed_repos = cursor.fetchone()[0]
            
            # Chat stats
            cursor.execute("SELECT COUNT(*) FROM chat_history")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM chat_history")
            total_sessions = cursor.fetchone()[0]
            
            return {
                "total_repositories": total_repos,
                "indexed_repositories": indexed_repos,
                "pending_repositories": total_repos - indexed_repos,
                "total_chat_messages": total_messages,
                "total_chat_sessions": total_sessions,
                "database_path": self.db_path
            }
