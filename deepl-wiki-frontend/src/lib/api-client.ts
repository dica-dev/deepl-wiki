// API Client for DeepL Wiki Backend
export interface ApiRepository {
  id: number;
  path: string;
  name: string;
  description: string;
  status: string;
  indexed_at: string | null;
}

export interface ApiChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ApiChatSession {
  session_id: string;
  created_at: string;
  messages: ApiChatMessage[];
}

export interface ApiChatResponse {
  response: string;
  session_id: string;
  message_id: string;
}

export interface ApiFileContent {
  path: string;
  content: string;
  encoding: string;
  size: number;
}

export interface ApiFileSearchResult {
  path: string;
  name: string;
  size: number;
  repository_id: number;
  repository_name: string;
}

export interface ApiHealthStatus {
  status: string;
  version: string;
  components: {
    database: {
      status: string;
      path: string;
      size: string;
    };
    vector_db: {
      status: string;
      path: string;
      collections: number;
    };
    environment: {
      status: string;
      missing_variables: string[];
    };
    agents: {
      status: string;
      available: string[];
    };
  };
}

export interface ApiStats {
  total_repositories: number;
  total_files_indexed: number;
  database_size: string;
  vector_db_size: string;
  last_index_time: string;
}

export class ApiClient {
  private baseUrl: string;
  private sessionId: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // Helper method for making API requests
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      headers: { ...defaultHeaders, ...options.headers },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error: Unable to connect to the backend API. Please ensure the backend is running.');
      }
      throw error;
    }
  }

  // Health & System Routes
  async getHealth(): Promise<ApiHealthStatus> {
    return this.request<ApiHealthStatus>('/health');
  }

  async getStats(): Promise<ApiStats> {
    return this.request<ApiStats>('/stats');
  }

  async getVersion(): Promise<{ version: string; api_version: string; python_version: string; platform: string }> {
    return this.request<{ version: string; api_version: string; python_version: string; platform: string }>('/version');
  }

  // Chat Routes
  async sendChatMessage(message: string, sessionId?: string): Promise<ApiChatResponse> {
    const body = {
      message,
      ...(sessionId && { session_id: sessionId })
    };

    const response = await this.request<ApiChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(body),
    });

    // Store session ID for future requests
    this.sessionId = response.session_id;
    return response;
  }

  async getChatSessions(): Promise<ApiChatSession[]> {
    return this.request<ApiChatSession[]>('/chat/sessions');
  }

  async getChatSession(sessionId: string): Promise<ApiChatSession> {
    return this.request<ApiChatSession>(`/chat/sessions/${sessionId}`);
  }

  async deleteChatSession(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async clearAllChatSessions(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/chat/sessions', {
      method: 'DELETE',
    });
  }

  // Repository Management Routes
  async getRepositories(): Promise<ApiRepository[]> {
    return this.request<ApiRepository[]>('/repositories');
  }

  async addRepository(path: string, name: string, description: string): Promise<ApiRepository> {
    return this.request<ApiRepository>('/repositories', {
      method: 'POST',
      body: JSON.stringify({ path, name, description }),
    });
  }

  async getRepository(repositoryId: number): Promise<ApiRepository> {
    return this.request<ApiRepository>(`/repositories/${repositoryId}`);
  }

  async deleteRepository(repositoryId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/repositories/${repositoryId}`, {
      method: 'DELETE',
    });
  }

  async indexRepositories(repositoryIds?: number[]): Promise<{ message: string; repositories_indexed: number[]; status: string }> {
    const body = repositoryIds ? { repository_ids: repositoryIds } : {};
    return this.request<{ message: string; repositories_indexed: number[]; status: string }>('/repositories/index', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async getIndexingStatus(): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>('/repositories/index/status');
  }

  // File System Routes
  async getMonoRepoStructure(): Promise<{
    mono_repo_path: string;
    structure: Record<string, unknown>;
    total_files: number;
    total_size: number;
  }> {
    return this.request<{
      mono_repo_path: string;
      structure: Record<string, unknown>;
      total_files: number;
      total_size: number;
    }>('/files/mono-repo');
  }

  async generateMonoRepo(): Promise<{
    message: string;
    mono_repo_path: string;
    repositories_included: number;
  }> {
    return this.request<{
      message: string;
      mono_repo_path: string;
      repositories_included: number;
    }>('/files/mono-repo/generate');
  }

  async getFileContent(filePath: string): Promise<ApiFileContent> {
    const encodedPath = encodeURIComponent(filePath);
    return this.request<ApiFileContent>(`/files/content?file_path=${encodedPath}`);
  }

  async searchFiles(
    query: string,
    fileType?: string,
    repositoryId?: number
  ): Promise<{
    query: string;
    results: ApiFileSearchResult[];
    total: number;
  }> {
    const params = new URLSearchParams({ query });
    if (fileType) params.append('file_type', fileType);
    if (repositoryId) params.append('repository_id', repositoryId.toString());

    return this.request<{
      query: string;
      results: ApiFileSearchResult[];
      total: number;
    }>(`/files/search?${params.toString()}`);
  }

  async getMarkdownFilesTree(): Promise<{
    tree: Array<{
      name: string;
      path: string;
      type: 'repository';
      repository_id: number;
      children: Array<{
        name: string;
        path: string;
        relative_path: string;
        type: 'file';
        size: number;
        repository_id: number;
        repository_name: string;
      }>;
    }>;
    total_files: number;
    repositories_count: number;
  }> {
    return this.request<{
      tree: Array<{
        name: string;
        path: string;
        type: 'repository';
        repository_id: number;
        children: Array<{
          name: string;
          path: string;
          relative_path: string;
          type: 'file';
          size: number;
          repository_id: number;
          repository_name: string;
        }>;
      }>;
      total_files: number;
      repositories_count: number;
    }>('/files/markdown-tree');
  }

  // Utility methods
  getCurrentSessionId(): string | null {
    return this.sessionId;
  }

  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  clearSessionId(): void {
    this.sessionId = null;
  }

  // Check if backend is available
  async isAvailable(): Promise<boolean> {
    try {
      await this.getHealth();
      return true;
    } catch {
      return false;
    }
  }
}

// Create a singleton instance
export const apiClient = new ApiClient();

// Helper function to convert API data to frontend format
export function convertApiRepositoryToWikiDocument(repo: ApiRepository, fileContent?: string): {path: string; content: string; lastModified: string; sha: string} {
  return {
    path: repo.name,
    content: fileContent || `# ${repo.name}\n\n${repo.description}\n\nRepository Path: ${repo.path}`,
    lastModified: repo.indexed_at || new Date().toISOString(),
    sha: repo.id.toString(),
  };
}

export function convertApiChatMessageToFrontend(apiMessage: ApiChatMessage): {id: string; role: string; content: string; timestamp: Date} {
  return {
    id: apiMessage.id,
    role: apiMessage.role,
    content: apiMessage.content,
    timestamp: new Date(apiMessage.timestamp),
  };
}