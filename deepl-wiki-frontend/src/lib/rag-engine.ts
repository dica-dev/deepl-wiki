/**
 * RAG (Retrieval Augmented Generation) engine using LlamaIndex with Llama models
 */

import { Document, VectorStoreIndex, Settings, serviceContextFromDefaults } from 'llamaindex';

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

export class RAGEngine {
  private config: RAGConfig;
  private index: VectorStoreIndex | null = null;
  private queryEngine: any = null;
  private documents: Document[] = [];
  private serviceContext: any = null;

  constructor(config: RAGConfig) {
    this.config = {
      llamaApiUrl: 'https://api.llama-api.com/v1',
      embeddingModel: 'llama-embed',
      chatModel: 'llama-3.1-8b-instruct',
      chunkSize: 1024,
      chunkOverlap: 200,
      ...config,
    };

    // Configure service context for Llama models
    this.serviceContext = serviceContextFromDefaults({
      chunkSize: this.config.chunkSize,
      chunkOverlap: this.config.chunkOverlap,
    });
  }

  async indexDocuments(markdownFiles: Array<{ path: string; content: string }>) {
    console.log(`Indexing ${markdownFiles.length} markdown files...`);
    
    // Convert markdown files to LlamaIndex documents
    this.documents = markdownFiles.map(file => {
      const doc = new Document({
        text: file.content,
        metadata: {
          filePath: file.path,
          fileName: file.path.split('/').pop() || 'unknown',
          source: 'memo-repo',
        },
      });
      return doc;
    });

    try {
      // Create vector store index with service context
      this.index = await VectorStoreIndex.fromDocuments(
        this.documents,
        { serviceContext: this.serviceContext }
      );
      
      // Create query engine with retrieval
      this.queryEngine = this.index.asQueryEngine({
        similarityTopK: 5, // Retrieve top 5 most similar chunks
      });

      console.log('Documents indexed successfully');
    } catch (error) {
      console.error('Error indexing documents:', error);
      throw error;
    }
  }

  async query(question: string): Promise<string> {
    if (!this.queryEngine) {
      throw new Error('RAG engine not initialized. Please index documents first.');
    }

    try {
      console.log(`Processing query: ${question}`);
      
      const response = await this.queryEngine.query({
        query: question,
      });

      return response.response || 'I apologize, but I could not generate a response to your question.';
    } catch (error) {
      console.error('Error processing query:', error);
      throw error;
    }
  }

  async chat(messages: ChatMessage[]): Promise<string> {
    if (!this.queryEngine) {
      throw new Error('RAG engine not initialized. Please index documents first.');
    }

    try {
      // Get the latest user message
      const latestMessage = messages[messages.length - 1];
      if (latestMessage.role !== 'user') {
        throw new Error('Latest message must be from user');
      }

      // Build context from conversation history
      const conversationContext = messages
        .slice(-5) // Last 5 messages for context
        .map(msg => `${msg.role}: ${msg.content}`)
        .join('\n');

      const enhancedQuery = `Context from conversation:
${conversationContext}

Current question: ${latestMessage.content}

Please provide a helpful response based on the documentation and conversation context.`;

      const response = await this.queryEngine.query({
        query: enhancedQuery,
      });

      return response.response || 'I apologize, but I could not generate a response to your question.';
    } catch (error) {
      console.error('Error processing chat:', error);
      throw error;
    }
  }

  async getRelevantDocuments(query: string, topK: number = 3): Promise<Array<{
    content: string;
    metadata: any;
    score?: number;
  }>> {
    if (!this.index) {
      throw new Error('Index not initialized. Please index documents first.');
    }

    try {
      const retriever = this.index.asRetriever({
        similarityTopK: topK,
      });

      const nodes = await retriever.retrieve(query);
      
      return nodes.map(node => ({
        content: node.node.getContent(),
        metadata: node.node.metadata,
        score: node.score,
      }));
    } catch (error) {
      console.error('Error retrieving relevant documents:', error);
      throw error;
    }
  }

  getIndexedDocumentCount(): number {
    return this.documents.length;
  }

  isReady(): boolean {
    return this.index !== null && this.queryEngine !== null;
  }

  async updateDocuments(markdownFiles: Array<{ path: string; content: string }>) {
    console.log('Updating document index...');
    await this.indexDocuments(markdownFiles);
  }
}