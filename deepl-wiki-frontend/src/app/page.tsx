'use client';

import React, { useState, useEffect, useMemo } from 'react';
import ChatInterface from '@/components/ChatInterface';
import WikiBrowser, { WikiDocument } from '@/components/WikiBrowser';
import { MarkdownMonitor, MarkdownFile } from '@/lib/markdown-monitor';
import { SimpleRAGEngine } from '@/lib/simple-rag-engine';
import { mockDocuments, MockRAGEngine } from '@/lib/mock-data';
import { MessageSquare, BookOpen, Settings, Loader2, AlertCircle, Play, Search, FileText, Folder, Bot, Send } from 'lucide-react';

export default function Home() {
  const [documents, setDocuments] = useState<WikiDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<WikiDocument | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ragEngine, setRagEngine] = useState<SimpleRAGEngine | null>(null);
  const [monitor, setMonitor] = useState<MarkdownMonitor | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'wiki'>('chat');
  const [config, setConfig] = useState({
    githubToken: '',
    llamaApiKey: '',
    repoOwner: '',
    repoName: '',
  });
  const [useMockData, setUseMockData] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
  }>>([]);
  const [chatInput, setChatInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Handle click outside chat to minimize
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const chatElement = document.getElementById('chat-overlay');
      if (chatElement && !chatElement.contains(event.target as Node)) {
        setIsChatExpanded(false);
      }
    };

    if (isChatExpanded) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isChatExpanded]);

  // Filter documents based on search
  const filteredDocuments = useMemo(() => {
    if (!searchTerm.trim()) return documents;
    return documents.filter(doc => 
      doc.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.content.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [documents, searchTerm]);

  // Initialize mock data
  const initializeMockData = async () => {
    try {
      console.log('Initializing with mock data...');
      setIsLoading(true);
      
      // Set up mock documents
      const wikiDocs: WikiDocument[] = mockDocuments.map(doc => ({
        path: doc.path,
        content: doc.content,
        lastModified: doc.lastModified,
        sha: doc.sha,
      }));
      
      setDocuments(wikiDocs);
      
      // Initialize mock RAG engine
      const mockRag = new MockRAGEngine();
      setRagEngine(mockRag as any);
      
      console.log('Mock data initialized successfully');
    } catch (err) {
      console.error('Mock initialization error:', err);
      setError('Failed to initialize mock data');
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize system
  useEffect(() => {
    const initializeSystem = async () => {
      try {
        // Check for mock mode first
        const savedMockMode = localStorage.getItem('deepl-wiki-mock-mode');
        if (savedMockMode === 'true') {
          setUseMockData(true);
          await initializeMockData();
          return;
        }

        // Load config from environment or localStorage
        const savedConfig = localStorage.getItem('deepl-wiki-config');
        if (savedConfig) {
          const parsedConfig = JSON.parse(savedConfig);
          setConfig(parsedConfig);
          
          // Initialize RAG engine
          const rag = new SimpleRAGEngine({
            llamaApiKey: parsedConfig.llamaApiKey,
          });
          setRagEngine(rag);

          // Initialize markdown monitor
          const markdownMonitor = new MarkdownMonitor(
            {
              owner: parsedConfig.repoOwner,
              repo: parsedConfig.repoName,
            },
            parsedConfig.githubToken
          );

          // Set up event listeners
          markdownMonitor.on('filesUpdated', handleFilesUpdated);
          markdownMonitor.on('error', handleMonitorError);

          setMonitor(markdownMonitor);
          
          // Start monitoring
          await markdownMonitor.start();
        } else {
          // Show config needed message
          setError('Configuration needed. Please set up your GitHub token, Llama API key, and repository details.');
        }
      } catch (err) {
        console.error('Initialization error:', err);
        setError('Failed to initialize system. Please check your configuration.');
      } finally {
        setIsLoading(false);
      }
    };

    initializeSystem();

    // Cleanup
    return () => {
      if (monitor) {
        monitor.stop();
      }
    };
  }, []);

  const handleFilesUpdated = async (files: MarkdownFile[]) => {
    try {
      console.log(`Received ${files.length} updated files`);
      
      // Convert to WikiDocument format
      const wikiDocs: WikiDocument[] = files.map(file => ({
        path: file.path,
        content: file.content,
        lastModified: file.lastModified,
        sha: file.sha,
      }));

      setDocuments(wikiDocs);

      // Update RAG engine with new documents
      if (ragEngine) {
        await ragEngine.updateDocuments(files.map(f => ({
          path: f.path,
          content: f.content,
        })));
        console.log('RAG engine updated with new documents');
      }
    } catch (err) {
      console.error('Error handling file updates:', err);
      setError('Failed to process document updates');
    }
  };

  const handleMonitorError = (err: Error) => {
    console.error('Monitor error:', err);
    setError(`Monitoring error: ${err.message}`);
  };

  const handleChatMessage = async (message: string): Promise<string> => {
    if (!ragEngine || !ragEngine.isReady()) {
      return 'Sorry, the system is not ready yet. Please wait for documents to be indexed.';
    }

    try {
      const response = await ragEngine.query(message);
      return response;
    } catch (err) {
      console.error('Chat error:', err);
      return 'I apologize, but I encountered an error processing your question. Please try again.';
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isProcessing || !ragEngine?.isReady()) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: chatInput.trim(),
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsProcessing(true);

    try {
      let contextualQuery = chatInput.trim();
      if (selectedDocument) {
        contextualQuery = `Based on the document "${selectedDocument.path.split('/').pop()}" (${selectedDocument.path}): ${chatInput.trim()}`;
      }

      const response = await handleChatMessage(contextualQuery);
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: response,
        timestamp: new Date(),
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const saveConfig = () => {
    localStorage.setItem('deepl-wiki-config', JSON.stringify(config));
    localStorage.removeItem('deepl-wiki-mock-mode');
    // Reload page to reinitialize with new config
    window.location.reload();
  };

  const enableMockMode = () => {
    localStorage.setItem('deepl-wiki-mock-mode', 'true');
    localStorage.removeItem('deepl-wiki-config');
    window.location.reload();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Initializing DeepL Wiki...</p>
        </div>
      </div>
    );
  }

  if (error && !config.githubToken && !useMockData) {
    return (
      <div className="min-h-screen bg-bg-primary relative overflow-hidden flex items-center justify-center p-6">
        {/* Animated Background */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-llama-purple rounded-full mix-blend-multiply filter blur-3xl animate-float"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-llama-accent rounded-full mix-blend-multiply filter blur-3xl animate-float" style={{animationDelay: '1s'}}></div>
        </div>

        <div className="relative z-10 max-w-lg w-full">
          <div className="glass-effect neon-border rounded-3xl p-8 shadow-2xl">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="flex justify-center mb-6">
                <div className="relative">
                  <Settings className="w-16 h-16 text-llama-purple animate-pulse-glow" />
                  <div className="absolute inset-0 w-16 h-16 bg-llama-purple rounded-full blur-xl opacity-30 animate-pulse"></div>
                </div>
              </div>
              <h1 className="text-4xl font-black gradient-text mb-3">
                Setup Required
              </h1>
              <p className="text-text-secondary text-lg font-medium">
                Configure your DeepL Wiki to get started
              </p>
            </div>

            {/* Configuration Form */}
            <div className="space-y-6">
              <div className="group">
                <label className="block text-sm font-bold text-text-primary mb-2">
                  GitHub Token
                </label>
                <input
                  type="password"
                  value={config.githubToken}
                  onChange={(e) => setConfig(prev => ({ ...prev, githubToken: e.target.value }))}
                  placeholder="ghp_xxxxxxxxxxxx"
                  className="w-full px-4 py-3 bg-bg-secondary border border-border-primary rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple focus:glow-purple transition-all duration-300"
                />
              </div>

              <div className="group">
                <label className="block text-sm font-bold text-text-primary mb-2">
                  Llama API Key
                </label>
                <input
                  type="password"
                  value={config.llamaApiKey}
                  onChange={(e) => setConfig(prev => ({ ...prev, llamaApiKey: e.target.value }))}
                  placeholder="Enter your Llama API key"
                  className="w-full px-4 py-3 bg-bg-secondary border border-border-primary rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple focus:glow-purple transition-all duration-300"
                />
              </div>

              <div className="group">
                <label className="block text-sm font-bold text-text-primary mb-2">
                  Repository Owner
                </label>
                <input
                  type="text"
                  value={config.repoOwner}
                  onChange={(e) => setConfig(prev => ({ ...prev, repoOwner: e.target.value }))}
                  placeholder="github-username"
                  className="w-full px-4 py-3 bg-bg-secondary border border-border-primary rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple focus:glow-purple transition-all duration-300"
                />
              </div>

              <div className="group">
                <label className="block text-sm font-bold text-text-primary mb-2">
                  Repository Name
                </label>
                <input
                  type="text"
                  value={config.repoName}
                  onChange={(e) => setConfig(prev => ({ ...prev, repoName: e.target.value }))}
                  placeholder="memo-repo"
                  className="w-full px-4 py-3 bg-bg-secondary border border-border-primary rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple focus:glow-purple transition-all duration-300"
                />
              </div>

              <button
                onClick={saveConfig}
                disabled={!config.githubToken || !config.llamaApiKey || !config.repoOwner || !config.repoName}
                className="w-full bg-gradient-to-r from-llama-purple to-llama-accent text-white py-4 px-6 rounded-xl font-bold text-lg hover:glow-purple transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group relative overflow-hidden"
              >
                <span className="relative z-10">Save Configuration</span>
                <div className="absolute inset-0 bg-gradient-to-r from-llama-purple-light to-llama-accent-light opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              </button>

              {/* Divider */}
              <div className="relative py-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border-primary"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-bg-card text-text-tertiary font-medium">or</span>
                </div>
              </div>

              {/* Demo Button */}
              <button
                onClick={enableMockMode}
                className="w-full bg-gradient-to-r from-llama-blue to-llama-green text-white py-4 px-6 rounded-xl font-bold text-lg hover:glow-blue transition-all duration-300 flex items-center justify-center gap-3 group relative overflow-hidden"
              >
                <Play className="w-5 h-5 group-hover:scale-110 transition-transform" />
                <span className="relative z-10">Try Demo with Mock Data</span>
                <div className="absolute inset-0 bg-gradient-to-r from-llama-blue-light to-llama-green-light opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              </button>
              
              <p className="text-xs text-text-tertiary text-center leading-relaxed">
                Demo mode includes sample documentation from{' '}
                <span className="text-llama-accent font-semibold">3 repositories</span> with{' '}
                <span className="text-llama-blue font-semibold">AI chat functionality</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 left-20 w-96 h-96 bg-llama-purple rounded-full mix-blend-multiply filter blur-3xl animate-float"></div>
        <div className="absolute top-40 right-20 w-96 h-96 bg-llama-accent rounded-full mix-blend-multiply filter blur-3xl animate-float" style={{animationDelay: '1s'}}></div>
        <div className="absolute bottom-20 left-1/2 w-96 h-96 bg-llama-blue rounded-full mix-blend-multiply filter blur-3xl animate-float" style={{animationDelay: '2s'}}></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 h-screen flex flex-col">
        {/* Top Bar */}
        <div className="flex items-center justify-between p-4 border-b border-border-primary/30 bg-bg-secondary/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-llama-purple to-llama-accent flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-text-primary">DeepL Wiki</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 glass-effect rounded-full px-3 py-1 border border-border-primary">
              {ragEngine?.isReady() ? (
                <>
                  <div className="w-2 h-2 bg-llama-green rounded-full animate-pulse"></div>
                  <span className="text-xs text-text-secondary font-medium">
                    {ragEngine?.getIndexedDocumentCount()} docs
                  </span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-llama-accent rounded-full animate-pulse"></div>
                  <span className="text-xs text-text-secondary font-medium">Indexing...</span>
                </>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-900/20 border-b border-red-500/30 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        )}

        {/* Main Documentation Interface */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Left Sidebar - Navigation */}
          <div className="w-80 border-r border-border-primary/30 bg-bg-secondary/20 flex flex-col">
            {/* Search Header */}
            <div className="p-4 border-b border-border-primary/30">
              <div className="relative group">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-tertiary w-4 h-4 group-focus-within:text-llama-purple transition-colors" />
                <input
                  type="text"
                  placeholder="Search documentation..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple transition-all duration-300 text-sm"
                />
                {searchTerm && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs bg-llama-purple text-white px-2 py-1 rounded">
                    {filteredDocuments.length}
                  </div>
                )}
              </div>
            </div>

            {/* Document Tree */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin scrollbar-thumb-llama-purple scrollbar-track-bg-tertiary">
              {Object.entries(filteredDocuments.reduce((tree: { [key: string]: typeof filteredDocuments }, doc) => {
                const folder = doc.path.split('/')[0] || 'Root';
                if (!tree[folder]) tree[folder] = [];
                tree[folder].push(doc);
                return tree;
              }, {})).map(([folder, docs]) => (
                <div key={folder} className="group">
                  <div className="flex items-center gap-2 p-2 text-sm font-semibold text-text-primary">
                    <Folder className="w-4 h-4 text-llama-blue" />
                    <span>{folder}</span>
                    <span className="ml-auto text-xs bg-llama-accent/20 text-llama-accent px-2 py-1 rounded">
                      {docs.length}
                    </span>
                  </div>
                  <div className="ml-6 space-y-1">
                    {docs.map((doc) => (
                      <button
                        key={doc.path}
                        onClick={() => setSelectedDocument(doc)}
                        className={`flex items-center gap-2 w-full p-2 text-left rounded transition-all duration-200 text-sm ${
                          selectedDocument?.path === doc.path
                            ? 'bg-llama-purple/20 text-llama-purple font-medium'
                            : 'hover:bg-bg-hover text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        <FileText className="w-3 h-3" />
                        <span className="truncate">{doc.path.split('/').pop()}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col">
            {selectedDocument ? (
              <>
                {/* Document Header */}
                <div className="p-4 border-b border-border-primary/30 bg-bg-secondary/20">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-llama-purple to-llama-blue rounded-lg flex items-center justify-center">
                      <FileText className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <h1 className="text-lg font-bold text-text-primary">
                        {selectedDocument.path.split('/').pop()}
                      </h1>
                      <p className="text-xs text-text-secondary">
                        {selectedDocument.path}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Document Content */}
                <div className="flex-1 overflow-y-auto p-6 pb-32">
                  <div className="max-w-4xl mx-auto">
                    {selectedDocument.content.split('\n').map((line, index) => {
                      if (line.startsWith('# ')) {
                        return <h1 key={index} className="text-3xl font-bold text-text-primary mb-6">{line.substring(2)}</h1>;
                      }
                      if (line.startsWith('## ')) {
                        return <h2 key={index} className="text-2xl font-semibold text-text-primary mb-4 mt-8">{line.substring(3)}</h2>;
                      }
                      if (line.startsWith('### ')) {
                        return <h3 key={index} className="text-xl font-medium text-text-primary mb-3 mt-6">{line.substring(4)}</h3>;
                      }
                      if (line.startsWith('```')) {
                        return <div key={index} className="bg-bg-tertiary border border-border-primary rounded-lg p-4 my-4 font-mono text-sm text-text-primary overflow-x-auto"></div>;
                      }
                      if (line.startsWith('- ')) {
                        return <li key={index} className="text-text-secondary mb-2 ml-4">{line.substring(2)}</li>;
                      }
                      if (line.trim() === '') {
                        return <br key={index} />;
                      }
                      return <p key={index} className="text-text-secondary mb-4 leading-relaxed">{line}</p>;
                    })}
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-llama-purple to-llama-blue rounded-xl flex items-center justify-center mx-auto mb-4">
                    <BookOpen className="w-8 h-8 text-white" />
                  </div>
                  <h2 className="text-xl font-bold text-text-primary mb-2">
                    Select Documentation
                  </h2>
                  <p className="text-text-secondary text-sm">
                    Choose a document from the sidebar to start reading
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Chat Interface - Minimized/Expanded States */}
          <div 
            id="chat-overlay"
            className={`fixed z-50 transition-all duration-300 ease-in-out ${
              isChatExpanded 
                ? 'bottom-4 left-4 right-4'
                : 'bottom-4 left-1/2 -translate-x-1/2'
            }`}
          >
            <div className={`bg-bg-secondary/98 backdrop-blur-xl border border-border-primary shadow-2xl transition-all duration-300 ${
              isChatExpanded 
                ? 'rounded-xl'
                : 'rounded-full w-64'
            }`}>
              
              {/* Minimized State */}
              {!isChatExpanded && (
                <button
                  onClick={() => setIsChatExpanded(true)}
                  className="flex items-center justify-center gap-3 w-full p-3 hover:bg-bg-hover/50 rounded-full transition-all duration-200"
                >
                  <div className="w-6 h-6 bg-gradient-to-br from-llama-purple to-llama-accent rounded-full flex items-center justify-center">
                    <MessageSquare className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm font-medium text-text-primary">
                    Ask AI Assistant
                  </span>
                  {ragEngine?.isReady() ? (
                    <div className="w-2 h-2 bg-llama-green rounded-full animate-pulse"></div>
                  ) : (
                    <div className="w-2 h-2 bg-llama-accent rounded-full animate-pulse"></div>
                  )}
                </button>
              )}

              {/* Expanded State */}
              {isChatExpanded && (
                <>
                  {/* Chat Header */}
                  <div className="flex items-center justify-between p-3 border-b border-border-primary/30">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-gradient-to-br from-llama-purple to-llama-accent rounded flex items-center justify-center">
                        <MessageSquare className="w-3 h-3 text-white" />
                      </div>
                      <span className="text-sm font-semibold text-text-primary">AI Assistant</span>
                      {selectedDocument && (
                        <span className="text-xs text-text-tertiary">
                          • {selectedDocument.path.split('/').pop()}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {ragEngine?.isReady() ? (
                        <div className="w-2 h-2 bg-llama-green rounded-full"></div>
                      ) : (
                        <div className="w-2 h-2 bg-llama-accent rounded-full animate-pulse"></div>
                      )}
                      <button
                        onClick={() => setIsChatExpanded(false)}
                        className="p-1 hover:bg-bg-hover rounded text-text-tertiary hover:text-text-primary transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Chat Messages */}
                  <div className="max-h-64 overflow-y-auto p-3 space-y-3 scrollbar-thin scrollbar-thumb-llama-purple scrollbar-track-bg-tertiary">
                    {chatMessages.length === 0 && (
                      <div className="text-center py-4">
                        <p className="text-sm text-text-tertiary">
                          {selectedDocument 
                            ? `Ask me anything about ${selectedDocument.path.split('/').pop()}`
                            : "Select a document to start chatting"
                          }
                        </p>
                      </div>
                    )}

                    {chatMessages.map((message) => (
                      <div key={message.id} className={`flex gap-2 ${
                        message.role === 'user' ? 'flex-row-reverse' : ''
                      }`}>
                        <div className={`w-6 h-6 rounded flex items-center justify-center flex-shrink-0 ${
                          message.role === 'user' 
                            ? 'bg-llama-accent/20'
                            : 'bg-llama-purple/20'
                        }`}>
                          {message.role === 'user' ? (
                            <div className="w-2 h-2 bg-llama-accent rounded-full"></div>
                          ) : (
                            <Bot className="w-3 h-3 text-llama-purple" />
                          )}
                        </div>
                        <div className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === 'user'
                            ? 'bg-llama-purple/10 border border-llama-purple/30'
                            : 'bg-bg-tertiary/50 border border-border-primary/30'
                        }`}>
                          <div className="text-sm text-text-primary whitespace-pre-wrap">
                            {message.content}
                          </div>
                        </div>
                      </div>
                    ))}

                    {isProcessing && (
                      <div className="flex gap-2">
                        <div className="w-6 h-6 rounded flex items-center justify-center bg-llama-purple/20">
                          <Bot className="w-3 h-3 text-llama-purple animate-pulse" />
                        </div>
                        <div className="bg-bg-tertiary/50 border border-border-primary/30 rounded-lg p-3">
                          <div className="flex items-center gap-2">
                            <div className="flex gap-1">
                              <div className="w-1 h-1 bg-llama-purple rounded-full animate-pulse"></div>
                              <div className="w-1 h-1 bg-llama-accent rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                              <div className="w-1 h-1 bg-llama-blue rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                            </div>
                            <span className="text-xs text-text-secondary">AI is thinking...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Chat Input */}
                  <div className="p-3 border-t border-border-primary/30">
                    <form onSubmit={handleChatSubmit} className="relative">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder={selectedDocument ? `Ask about ${selectedDocument.path.split('/').pop()}...` : "Select a document first..."}
                        disabled={!ragEngine?.isReady() || isProcessing}
                        className="w-full pl-4 pr-12 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple transition-all duration-300 text-sm disabled:opacity-50"
                        autoFocus
                      />
                      <button
                        type="submit"
                        disabled={!ragEngine?.isReady() || isProcessing || !chatInput.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 bg-gradient-to-r from-llama-purple to-llama-accent text-white rounded flex items-center justify-center hover:opacity-80 transition-all duration-300 disabled:opacity-30"
                      >
                        {isProcessing ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Send className="w-3 h-3" />
                        )}
                      </button>
                    </form>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
