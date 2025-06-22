import { ApiClient, ApiRepository, convertApiRepositoryToWikiDocument } from './api-client';

export interface BackendDocument {
  path: string;
  content: string;
}

export class BackendRAGEngine {
  private client: ApiClient;
  private isIndexing: boolean = false;
  private repositories: ApiRepository[] = [];
  private documents: BackendDocument[] = [];
  private ready: boolean = false;

  constructor(apiClient: ApiClient) {
    this.client = apiClient;
  }

  async initialize(): Promise<void> {
    try {
      // Check if backend is available
      const isAvailable = await this.client.isAvailable();
      if (!isAvailable) {
        throw new Error('Backend API is not available. Please ensure the backend server is running.');
      }

      // Get current repositories
      this.repositories = await this.client.getRepositories();
      
      // Load documents from repositories
      await this.loadDocuments();
      
      // Check indexing status
      const indexingStatus = await this.client.getIndexingStatus();
      this.isIndexing = indexingStatus.status === 'running';
      
      this.ready = true;
    } catch (error) {
      console.error('Failed to initialize BackendRAGEngine:', error);
      throw error;
    }
  }

  private async loadDocuments(): Promise<void> {
    try {
      // Get mono repo structure to understand what files are available
      const monoRepo = await this.client.getMonoRepoStructure();
      
      // Convert repositories to documents
      this.documents = this.repositories.map(repo => 
        convertApiRepositoryToWikiDocument(repo)
      );

      // Add some sample documents from the mono repo structure
      if (monoRepo.structure && monoRepo.structure.children) {
        this.addDocumentsFromStructure(monoRepo.structure, monoRepo.mono_repo_path);
      }
    } catch (error) {
      console.warn('Could not load mono repo structure, using repository data only:', error);
      // Fall back to just repository information
      this.documents = this.repositories.map(repo => 
        convertApiRepositoryToWikiDocument(repo)
      );
    }
  }

  private addDocumentsFromStructure(node: Record<string, unknown>, basePath: string, maxDepth: number = 2, currentDepth: number = 0): void {
    if (currentDepth >= maxDepth) return;

    if (node.type === 'file' && typeof node.name === 'string' && this.isDocumentFile(node.name)) {
      this.documents.push({
        path: (node.path as string).replace(basePath, '').replace(/^\//, ''),
        content: `# ${node.name}\n\nFile: ${node.path}\nSize: ${node.size} bytes\n\nThis file is part of the indexed codebase.`
      });
    } else if (node.type === 'directory' && Array.isArray(node.children)) {
      node.children.forEach((child: Record<string, unknown>) => {
        this.addDocumentsFromStructure(child, basePath, maxDepth, currentDepth + 1);
      });
    }
  }

  private isDocumentFile(filename: string): boolean {
    const documentExtensions = ['.md', '.txt', '.rst', '.adoc'];
    return documentExtensions.some(ext => filename.toLowerCase().endsWith(ext));
  }

  async query(message: string): Promise<string> {
    if (!this.ready) {
      throw new Error('RAG Engine is not ready. Please wait for initialization to complete.');
    }

    try {
      const response = await this.client.sendChatMessage(message);
      return response.response;
    } catch (error) {
      console.error('Query failed:', error);
      
      // Provide fallback responses based on error type
      if (error instanceof Error) {
        if (error.message.includes('Network error')) {
          return 'I apologize, but I cannot connect to the backend service right now. Please check that the backend server is running and try again.';
        }
        if (error.message.includes('timeout')) {
          return 'The request timed out. Please try asking a shorter or more specific question.';
        }
      }
      
      return 'I encountered an error while processing your question. Please try again or rephrase your question.';
    }
  }

  async updateDocuments(): Promise<void> {
    // This method would trigger re-indexing in the backend
    try {
      await this.client.indexRepositories();
      this.isIndexing = true;
      
      // Poll for completion
      this.pollIndexingStatus();
    } catch (error) {
      console.error('Failed to update documents:', error);
      throw error;
    }
  }

  private async pollIndexingStatus(): Promise<void> {
    const checkStatus = async () => {
      try {
        const status = await this.client.getIndexingStatus();
        if (status.status === 'available') {
          this.isIndexing = false;
          await this.loadDocuments(); // Reload documents after indexing
        } else {
          // Continue polling
          setTimeout(checkStatus, 2000);
        }
      } catch (error) {
        console.error('Error polling indexing status:', error);
        this.isIndexing = false;
      }
    };

    setTimeout(checkStatus, 1000);
  }

  isReady(): boolean {
    return this.ready && !this.isIndexing;
  }

  getIndexedDocumentCount(): number {
    return this.documents.length;
  }

  getDocuments(): BackendDocument[] {
    return this.documents;
  }

  getRepositories(): ApiRepository[] {
    return this.repositories;
  }

  async addRepository(path: string, name: string, description: string): Promise<ApiRepository> {
    try {
      const newRepo = await this.client.addRepository(path, name, description);
      this.repositories.push(newRepo);
      
      // Trigger indexing for the new repository
      await this.client.indexRepositories([newRepo.id]);
      this.isIndexing = true;
      this.pollIndexingStatus();
      
      return newRepo;
    } catch (error) {
      console.error('Failed to add repository:', error);
      throw error;
    }
  }

  async removeRepository(repositoryId: number): Promise<void> {
    try {
      await this.client.deleteRepository(repositoryId);
      this.repositories = this.repositories.filter(repo => repo.id !== repositoryId);
      await this.loadDocuments(); // Reload documents
    } catch (error) {
      console.error('Failed to remove repository:', error);
      throw error;
    }
  }

  async searchFiles(query: string, fileType?: string): Promise<Array<{path: string; name: string; size: number; repository: string}>> {
    try {
      const searchResult = await this.client.searchFiles(query, fileType);
      return searchResult.results.map(result => ({
        path: result.path,
        name: result.name,
        size: result.size,
        repository: result.repository_name
      }));
    } catch (error) {
      console.error('File search failed:', error);
      return [];
    }
  }

  async getFileContent(filePath: string): Promise<string> {
    try {
      const fileContent = await this.client.getFileContent(filePath);
      return fileContent.content;
    } catch (error) {
      console.error('Failed to get file content:', error);
      throw error;
    }
  }

  async getSystemStats(): Promise<Record<string, unknown> | null> {
    try {
      const [health, stats] = await Promise.all([
        this.client.getHealth(),
        this.client.getStats()
      ]);
      
      return {
        health,
        stats,
        repositories: this.repositories.length,
        documents: this.documents.length,
        isIndexing: this.isIndexing
      };
    } catch (error) {
      console.error('Failed to get system stats:', error);
      return null;
    }
  }

  // Chat session management
  async getChatSessions(): Promise<Array<{id: string; createdAt: Date; messageCount: number}>> {
    try {
      const sessions = await this.client.getChatSessions();
      return sessions.map(session => ({
        id: session.session_id,
        createdAt: new Date(session.created_at),
        messageCount: session.messages.length
      }));
    } catch (error) {
      console.error('Failed to get chat sessions:', error);
      return [];
    }
  }

  async clearChatHistory(): Promise<void> {
    try {
      await this.client.clearAllChatSessions();
      this.client.clearSessionId();
    } catch (error) {
      console.error('Failed to clear chat history:', error);
      throw error;
    }
  }
}