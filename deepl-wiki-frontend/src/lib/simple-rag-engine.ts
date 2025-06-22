/**
 * Simple RAG engine with mock embeddings for development
 */

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface RAGConfig {
  llamaApiKey: string;
  llamaApiUrl?: string;
  embeddingModel?: string;
  chatModel?: string;
  chunkSize?: number;
  chunkOverlap?: number;
}

interface DocumentChunk {
  text: string;
  metadata: {
    filePath: string;
    fileName: string;
    source: string;
  };
  embedding?: number[];
}

export class SimpleRAGEngine {
  private config: RAGConfig;
  private chunks: DocumentChunk[] = [];
  private isIndexed = false;

  constructor(config: RAGConfig) {
    this.config = {
      llamaApiUrl: 'https://api.llama-api.com/v1',
      embeddingModel: 'llama-embed',
      chatModel: 'llama-3.1-8b-instruct',
      chunkSize: 1024,
      chunkOverlap: 200,
      ...config,
    };
  }

  async indexDocuments(markdownFiles: Array<{ path: string; content: string }>) {
    console.log(`Indexing ${markdownFiles.length} markdown files...`);
    
    this.chunks = [];
    
    // Split documents into chunks
    for (const file of markdownFiles) {
      const chunks = this.splitIntoChunks(file.content, this.config.chunkSize!);
      
      for (const chunk of chunks) {
        this.chunks.push({
          text: chunk,
          metadata: {
            filePath: file.path,
            fileName: file.path.split('/').pop() || 'unknown',
            source: 'memo-repo',
          },
          embedding: this.generateMockEmbedding(chunk), // Mock embedding
        });
      }
    }

    this.isIndexed = true;
    console.log(`Documents indexed successfully: ${this.chunks.length} chunks created`);
  }

  async query(question: string): Promise<string> {
    if (!this.isIndexed) {
      throw new Error('RAG engine not initialized. Please index documents first.');
    }

    try {
      console.log(`Processing query: ${question}`);
      
      // Get relevant chunks using simple similarity
      const relevantChunks = this.getRelevantChunks(question, 3);
      
      // Build context from relevant chunks
      const context = relevantChunks
        .map(chunk => `From ${chunk.metadata.fileName}:\n${chunk.text}`)
        .join('\n\n---\n\n');

      // Generate response using mock LLM (in production, this would call Llama API)
      const response = await this.generateResponse(question, context);
      
      return response;
    } catch (error) {
      console.error('Error processing query:', error);
      throw error;
    }
  }

  async chat(messages: ChatMessage[]): Promise<string> {
    if (!this.isIndexed) {
      throw new Error('RAG engine not initialized. Please index documents first.');
    }

    try {
      // Get the latest user message
      const latestMessage = messages[messages.length - 1];
      if (latestMessage.role !== 'user') {
        throw new Error('Latest message must be from user');
      }

      // For simplicity, just use the latest message for now
      return await this.query(latestMessage.content);
    } catch (error) {
      console.error('Error processing chat:', error);
      throw error;
    }
  }

  async getRelevantDocuments(query: string, topK: number = 3): Promise<Array<{
    content: string;
    metadata: unknown;
    score?: number;
  }>> {
    if (!this.isIndexed) {
      throw new Error('Index not initialized. Please index documents first.');
    }

    const relevantChunks = this.getRelevantChunks(query, topK);
    
    return relevantChunks.map(chunk => ({
      content: chunk.text,
      metadata: chunk.metadata,
      score: this.calculateSimilarity(query, chunk.text),
    }));
  }

  private splitIntoChunks(text: string, chunkSize: number): string[] {
    const chunks: string[] = [];
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    
    let currentChunk = '';
    
    for (const sentence of sentences) {
      if (currentChunk.length + sentence.length > chunkSize && currentChunk.length > 0) {
        chunks.push(currentChunk.trim());
        currentChunk = sentence;
      } else {
        currentChunk += (currentChunk ? '. ' : '') + sentence.trim();
      }
    }
    
    if (currentChunk.trim()) {
      chunks.push(currentChunk.trim());
    }
    
    return chunks.length > 0 ? chunks : [text]; // Fallback to original text if splitting fails
  }

  private generateMockEmbedding(text: string): number[] {
    // Simple mock embedding based on text characteristics
    const words = text.toLowerCase().split(/\s+/);
    const embedding = new Array(384).fill(0); // Mock 384-dimensional embedding
    
    // Generate pseudo-random but consistent embedding based on text content
    for (let i = 0; i < words.length && i < 384; i++) {
      const word = words[i];
      const hash = this.simpleHash(word);
      embedding[i % 384] += Math.sin(hash) * 0.1;
    }
    
    // Normalize
    const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
    return embedding.map(val => magnitude > 0 ? val / magnitude : 0);
  }

  private simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  private calculateSimilarity(query: string, text: string): number {
    const queryWords = new Set(query.toLowerCase().split(/\s+/));
    const textWords = text.toLowerCase().split(/\s+/);
    
    let matches = 0;
    for (const word of textWords) {
      if (queryWords.has(word)) {
        matches++;
      }
    }
    
    return matches / Math.max(queryWords.size, textWords.length);
  }

  private getRelevantChunks(query: string, topK: number): DocumentChunk[] {
    const scores = this.chunks.map(chunk => ({
      chunk,
      score: this.calculateSimilarity(query, chunk.text),
    }));
    
    return scores
      .sort((a, b) => b.score - a.score)
      .slice(0, topK)
      .map(item => item.chunk);
  }

  private async generateResponse(question: string, context: string): Promise<string> {
    // Mock response generation - in production this would call Llama API
    const lowerQuestion = question.toLowerCase();
    
    // Extract key topics from context
    const contextLower = context.toLowerCase();
    
    if (lowerQuestion.includes('auth') || lowerQuestion.includes('login') || contextLower.includes('auth')) {
      return `Based on the authentication documentation, our system provides comprehensive authentication features including JWT tokens, OAuth integration, and role-based access control. The system uses bcrypt for password hashing and includes rate limiting for security.

Key endpoints:
- POST /auth/login for user authentication
- POST /auth/register for user registration
- JWT tokens with 24-hour expiration

Security features include password hashing with 12 salt rounds and protection against brute force attacks.`;
    }
    
    if (lowerQuestion.includes('database') || lowerQuestion.includes('schema') || contextLower.includes('database')) {
      return `The database schema uses PostgreSQL with a well-structured design:

**Main Tables:**
- **users**: Stores account information with UUID primary keys
- **posts**: Contains content with author references
- **sessions**: Tracks user sessions and tokens

**Key Features:**
- UUID primary keys for security
- Optimized indexes for performance
- Foreign key relationships for data integrity
- Flyway for migration management

The schema is designed for scalability and includes proper indexing on frequently queried fields.`;
    }
    
    if (lowerQuestion.includes('deploy') || lowerQuestion.includes('production') || contextLower.includes('deploy')) {
      return `Deployment is supported through multiple approaches:

**Docker Deployment:**
- Complete containerization with Docker Compose
- Environment variable configuration
- Health checks for all services

**Kubernetes:**
- Production-ready with 3 replicas
- Secret management for sensitive data
- Rolling updates support

**Requirements:**
- PostgreSQL 14+, Redis 6+, Node.js 18+
- Monitoring with Prometheus metrics
- Error tracking with Sentry integration

All deployments include comprehensive health checks and monitoring capabilities.`;
    }
    
    if (lowerQuestion.includes('frontend') || lowerQuestion.includes('react') || contextLower.includes('react')) {
      return `The frontend architecture follows modern React best practices:

**Technology Stack:**
- React 18 with TypeScript for type safety
- Vite for fast development and building
- React Query for server state management
- Zustand for client-side state

**Architecture Patterns:**
- Component composition over prop drilling
- Custom hooks for reusable logic
- Separation of concerns between UI and business logic

**Performance Optimizations:**
- Code splitting with React.lazy
- Bundle optimization and analysis
- Image optimization strategies

The codebase maintains high TypeScript coverage and follows established React patterns.`;
    }
    
    if (lowerQuestion.includes('test') || lowerQuestion.includes('testing') || contextLower.includes('test')) {
      return `Our testing strategy follows the testing pyramid:

**Unit Tests (70%):**
- Jest with React Testing Library
- Component behavior testing
- MSW for API mocking

**Integration Tests (20%):**
- API endpoint testing with Supertest
- Database testing with containers
- Full request/response validation

**End-to-End Tests (10%):**
- Playwright for browser automation
- Critical user journey validation
- Cross-browser compatibility

**Coverage Requirements:**
- 80% minimum overall coverage
- 100% for critical authentication and payment flows
- Automated reporting and CI integration`;
    }
    
    // Default response using context
    if (context.trim()) {
      return `Based on the available documentation, here's what I found relevant to your question:

${context.substring(0, 800)}${context.length > 800 ? '...' : ''}

Would you like me to elaborate on any specific aspect of this information?`;
    }
    
    return `I found some information related to your question in the documentation, but I'd need more specific details to provide a comprehensive answer. Could you clarify what specific aspect you're interested in regarding: ${question}?`;
  }

  getIndexedDocumentCount(): number {
    return this.chunks.length;
  }

  isReady(): boolean {
    return this.isIndexed;
  }

  async updateDocuments(markdownFiles: Array<{ path: string; content: string }>) {
    console.log('Updating document index...');
    await this.indexDocuments(markdownFiles);
  }
}