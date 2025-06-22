"""ChromaDB manager for vector storage and retrieval."""

import os
import hashlib
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

class ChromaManager:
    """Manages ChromaDB operations for document storage and retrieval."""
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "deepl_wiki_docs"):
        """Initialize ChromaDB manager.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use default embedding function
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        batch_size: int = 4000
    ) -> None:
        """Add documents to the collection in batches to avoid size limits."""
        if ids is None:
            ids = [self._generate_id(doc) for doc in documents]
        
        assert len(documents) == len(metadatas) == len(ids)
        
        # Process documents in batches to avoid ChromaDB batch size limits
        total_docs = len(documents)
        for i in range(0, total_docs, batch_size):
            end_idx = min(i + batch_size, total_docs)
            
            batch_documents = documents[i:end_idx]
            batch_metadatas = metadatas[i:end_idx]
            batch_ids = ids[i:end_idx]
            
            try:
                self.collection.add(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                print(f"Successfully added batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} ({len(batch_documents)} documents)")
            except Exception as e:
                print(f"Failed to add batch {i//batch_size + 1}: {str(e)}")
                # Try with smaller batch size if this batch fails
                if batch_size > 100:
                    print(f"Retrying with smaller batch size...")
                    self.add_documents(
                        batch_documents,
                        batch_metadatas,
                        batch_ids,
                        batch_size=batch_size//2
                    )
                else:
                    raise e
    
    def search(
        self, 
        query: str, 
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }
    
    def add_repo_memo(
        self,
        repo_path: str,
        memo_content: str,
        repo_metadata: Dict[str, Any]
    ) -> None:
        """Add a repository memo to the collection."""
        chunks = self._split_memo(memo_content)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            
            metadata = repo_metadata.copy()
            metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks),
                'content_type': 'memo_chunk'
            })
            metadatas.append(metadata)
            
            chunk_id = f"{repo_path}_{i}_{self._generate_id(chunk)}"
            ids.append(chunk_id)
        
        # Use batched processing to avoid ChromaDB size limits
        print(f"Adding {len(documents)} document chunks for {repo_path}")
        self.add_documents(documents, metadatas, ids, batch_size=4000)
    
    def search_repos(
        self, 
        query: str, 
        repo_filter: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search across repository memos."""
        where_filter = {'content_type': 'memo_chunk'}
        if repo_filter:
            where_filter['repo_name'] = repo_filter
        
        results = self.search(query, n_results, where_filter)
        
        formatted_results = []
        for i in range(len(results['documents'])):
            formatted_results.append({
                'content': results['documents'][i],
                'similarity': 1 - results['distances'][i],
                'metadata': results['metadatas'][i],
                'id': results['ids'][i]
            })
        
        return formatted_results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        count = self.collection.count()
        return {
            'name': self.collection_name,
            'count': count,
            'persist_directory': self.persist_directory
        }
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID from content hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _split_memo(self, memo: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split memo into overlapping chunks for better search."""
        if len(memo) <= chunk_size:
            return [memo]
        
        chunks = []
        start = 0
        
        while start < len(memo):
            end = start + chunk_size
            chunk = memo[start:end]
            
            if end < len(memo):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = memo[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(memo):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]
