'use client';

import React, { useState, useEffect, useMemo } from 'react';
import ChatInterface from '@/components/ChatInterface';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import { WikiDocument } from '@/components/WikiBrowser';
import { MarkdownMonitor, MarkdownFile } from '@/lib/markdown-monitor';
import { SimpleRAGEngine } from '@/lib/simple-rag-engine';
import { mockDocuments, MockRAGEngine } from '@/lib/mock-data';
import { BookOpen, Settings, Loader2, AlertCircle, Play, Search, FileText, Folder, Moon, Sun, X, Network, Copy, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { ReactFlow, Background, Controls, Node as FlowNode, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

export default function Home() {
  const [documents, setDocuments] = useState<WikiDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<WikiDocument | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ragEngine, setRagEngine] = useState<SimpleRAGEngine | null>(null);
  const [monitor, setMonitor] = useState<MarkdownMonitor | null>(null);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const [config, setConfig] = useState({
    githubToken: '',
    llamaApiKey: '',
    repoOwner: '',
    repoName: '',
  });
  const [useMockData, setUseMockData] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [chatPosition, setChatPosition] = useState<'bottom' | 'right'>('bottom');
  const [expandedDiagram, setExpandedDiagram] = useState<{
    type: 'mermaid' | 'network' | 'wizard';
    content?: string;
    svg?: string;
    nodes?: FlowNode[];
    edges?: Edge[];
  } | null>(null);


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
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
        const savedMockMode = localStorage.getItem('javi-wiki-mock-mode');
        if (savedMockMode === 'true') {
          setUseMockData(true);
          await initializeMockData();
          return;
        }

        // Load config from environment or localStorage
        const savedConfig = localStorage.getItem('javi-wiki-config');
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Intentionally empty - initialization should only run once

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


  const saveConfig = () => {
    localStorage.setItem('javi-wiki-config', JSON.stringify(config));
    localStorage.removeItem('javi-wiki-mock-mode');
    // Reload page to reinitialize with new config
    window.location.reload();
  };

  const enableMockMode = () => {
    localStorage.setItem('javi-wiki-mock-mode', 'true');
    localStorage.removeItem('javi-wiki-config');
    window.location.reload();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Initializing JAVI Wiki...</p>
        </div>
      </div>
    );
  }

  if (error && !config.githubToken && !useMockData) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-6">
        <div className="max-w-lg w-full">
          <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="flex justify-center mb-6">
                <Settings className="w-16 h-16 text-gray-600" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-3">
                Setup Required
              </h1>
              <p className="text-gray-600">
                Configure your JAVI Wiki to get started
              </p>
            </div>

            {/* Configuration Form */}
            <div className="space-y-6">
              <div className="group">
                <label className="block text-sm font-bold text-white mb-2">
                  GitHub Token
                </label>
                <input
                  type="password"
                  value={config.githubToken}
                  onChange={(e) => setConfig(prev => ({ ...prev, githubToken: e.target.value }))}
                  placeholder="ghp_xxxxxxxxxxxx"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300"
                />
              </div>

              <div className="group">
                <label className="block text-sm font-bold text-white mb-2">
                  Llama API Key
                </label>
                <input
                  type="password"
                  value={config.llamaApiKey}
                  onChange={(e) => setConfig(prev => ({ ...prev, llamaApiKey: e.target.value }))}
                  placeholder="Enter your Llama API key"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300"
                />
              </div>

              <div className="group">
                <label className="block text-sm font-bold text-white mb-2">
                  Repository Owner
                </label>
                <input
                  type="text"
                  value={config.repoOwner}
                  onChange={(e) => setConfig(prev => ({ ...prev, repoOwner: e.target.value }))}
                  placeholder="github-username"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300"
                />
              </div>

              <div className="group">
                <label className="block text-sm font-bold text-white mb-2">
                  Repository Name
                </label>
                <input
                  type="text"
                  value={config.repoName}
                  onChange={(e) => setConfig(prev => ({ ...prev, repoName: e.target.value }))}
                  placeholder="memo-repo"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300"
                />
              </div>

              <button
                onClick={saveConfig}
                disabled={!config.githubToken || !config.llamaApiKey || !config.repoOwner || !config.repoName}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-4 px-6 rounded-xl font-bold text-lg hover:from-purple-500 hover:to-blue-500 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group relative overflow-hidden shadow-lg"
              >
                <span className="relative z-10">Save Configuration</span>
              </button>

              {/* Divider */}
              <div className="relative py-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-600"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-gray-800 text-gray-400 font-medium">or</span>
                </div>
              </div>

              {/* Demo Button */}
              <button
                onClick={enableMockMode}
                className="w-full bg-gradient-to-r from-blue-600 to-green-600 text-white py-4 px-6 rounded-xl font-bold text-lg hover:from-blue-500 hover:to-green-500 transition-all duration-300 flex items-center justify-center gap-3 group relative overflow-hidden shadow-lg"
              >
                <Play className="w-5 h-5 group-hover:scale-110 transition-transform" />
                <span className="relative z-10">Try Demo with Mock Data</span>
              </button>
              
              <p className="text-xs text-gray-400 text-center leading-relaxed">
                Demo mode includes sample documentation from{' '}
                <span className="text-purple-400 font-semibold">3 repositories</span> with{' '}
                <span className="text-blue-400 font-semibold">JAVI chat functionality</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen transition-colors duration-200 ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
      {/* Main Content */}
      <div className="h-screen flex flex-col">
        {/* Clean Top Bar */}
        <div className={`flex items-center justify-between p-4 border-b transition-colors duration-200 ${
          isDarkMode 
            ? 'border-gray-700 bg-gray-900' 
            : 'border-gray-200 bg-white'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isDarkMode ? 'bg-white' : 'bg-black'
            }`}>
              <BookOpen className={`w-4 h-4 ${isDarkMode ? 'text-black' : 'text-white'}`} />
            </div>
            <span className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              JAVI Wiki
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 rounded-full px-3 py-1 ${
              isDarkMode ? 'bg-gray-800' : 'bg-gray-100'
            }`}>
              {ragEngine?.isReady() ? (
                <>
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className={`text-xs font-medium ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                    {ragEngine?.getIndexedDocumentCount()} docs
                  </span>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-1">
                    <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse" style={{animationDelay: '0ms'}}></div>
                    <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '150ms'}}></div>
                    <div className="w-1 h-1 bg-blue-300 rounded-full animate-pulse" style={{animationDelay: '300ms'}}></div>
                  </div>
                  <span className={`text-xs font-medium ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                    Indexing docs...
                  </span>
                </>
              )}
            </div>
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'text-gray-400 hover:text-white hover:bg-gray-800' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className={`p-3 border-b flex items-center gap-2 ${
            isDarkMode 
              ? 'bg-red-900/20 border-red-800 text-red-300' 
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            <AlertCircle className={`w-4 h-4 flex-shrink-0 ${
              isDarkMode ? 'text-red-400' : 'text-red-600'
            }`} />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Main Documentation Interface */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Show Sidebar Button - when sidebar is hidden */}
          {!sidebarVisible && (
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10">
              <button
                onClick={() => setSidebarVisible(true)}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-110 ${
                  isDarkMode 
                    ? 'bg-gray-800 border border-gray-600 text-gray-400 hover:text-white hover:bg-gray-700' 
                    : 'bg-white border border-gray-300 text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                } shadow-sm`}
                title="Show sidebar"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
          
          {/* Left Sidebar - Navigation */}
          <div className={`relative ${sidebarVisible ? 'w-80 lg:w-80 md:w-64 sm:w-60' : 'w-0'} ${sidebarVisible ? 'md:w-80 lg:w-80' : 'md:w-0'} border-r flex flex-col transition-all duration-300 overflow-hidden ${
            isDarkMode 
              ? 'border-gray-700 bg-gray-800' 
              : 'border-gray-200 bg-gray-50'
          }`}>
            
            {/* Sidebar Toggle Button */}
            {sidebarVisible && (
              <div className="absolute -right-4 top-1/2 transform -translate-y-1/2 z-10">
                <button
                  onClick={() => setSidebarVisible(!sidebarVisible)}
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-110 ${
                    isDarkMode 
                      ? 'bg-gray-800 border border-gray-600 text-gray-400 hover:text-white hover:bg-gray-700' 
                      : 'bg-white border border-gray-300 text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  } shadow-sm`}
                  title="Hide sidebar"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              </div>
            )}
            {/* Search Header */}
            <div className={`p-4 border-b transition-colors duration-200 ${
              isDarkMode ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <div className="relative">
                <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-400'
                }`} />
                <input
                  type="text"
                  placeholder="Search documentation..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg text-sm transition-colors duration-200 focus:outline-none focus:ring-1 ${
                    isDarkMode 
                      ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-blue-500 focus:ring-blue-500' 
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-blue-500'
                  }`}
                />
                {searchTerm && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs bg-blue-500 text-white px-2 py-1 rounded">
                    {filteredDocuments.length}
                  </div>
                )}
              </div>
            </div>

            {/* Document Tree */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
              {Object.entries(filteredDocuments.reduce((tree: { [key: string]: typeof filteredDocuments }, doc) => {
                const folder = doc.path.split('/')[0] || 'Root';
                if (!tree[folder]) tree[folder] = [];
                tree[folder].push(doc);
                return tree;
              }, {})).map(([folder, docs]) => (
                <div key={folder} className="group">
                  <div className={`flex items-center gap-2 p-2 text-sm font-medium transition-colors duration-200 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    <Folder className={`w-4 h-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                    <span>{folder}</span>
                    <span className={`ml-auto text-xs px-2 py-1 rounded transition-colors duration-200 ${
                      isDarkMode 
                        ? 'bg-gray-700 text-gray-300' 
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {docs.length}
                    </span>
                  </div>
                  <div className="ml-6 space-y-1">
                    {docs.map((doc) => (
                      <button
                        key={doc.path}
                        onClick={() => {
                          setSelectedDocument(doc);
                          setExpandedDiagram(null); // Clear any expanded diagram when selecting a document
                        }}
                        className={`flex items-center gap-2 w-full p-2 text-left rounded transition-all duration-200 text-sm ${
                          selectedDocument?.path === doc.path
                            ? isDarkMode 
                              ? 'bg-blue-900/30 text-blue-300 font-medium border border-blue-700/50'
                              : 'bg-blue-50 text-blue-700 font-medium border border-blue-200'
                            : isDarkMode
                              ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'
                              : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        <FileText className="w-3 h-3" />
                        <span className="truncate">{doc.path.split('/').pop()?.replace(/\.md$/, '') || 'Document'}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Main Content Area */}
          <div className={`flex-1 flex flex-col transition-colors duration-200 ${
            isDarkMode ? 'bg-gray-900' : 'bg-white'
          } ${chatPosition === 'right' && isChatExpanded ? 'mr-96' : ''}`}>
            {expandedDiagram ? (
              <>
                {/* Expanded Diagram Header */}
                <div className={`p-4 border-b transition-colors duration-200 ${
                  isDarkMode 
                    ? 'border-gray-700 bg-gray-900' 
                    : 'border-gray-200 bg-white'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        isDarkMode ? 'bg-white' : 'bg-black'
                      }`}>
                        <Network className={`w-4 h-4 ${isDarkMode ? 'text-black' : 'text-white'}`} />
                      </div>
                      <div>
                        <h1 className={`text-lg font-semibold transition-colors duration-200 ${
                          isDarkMode ? 'text-white' : 'text-gray-900'
                        }`}>
                          {expandedDiagram.type === 'mermaid' ? 'Repository Structure' : 
                           expandedDiagram.type === 'wizard' ? 'Analysis Workflow' : 
                           'Network Diagram'}
                        </h1>
                        <p className={`text-xs transition-colors duration-200 ${
                          isDarkMode ? 'text-gray-400' : 'text-gray-500'
                        }`}>
                          Interactive diagram view
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          if (expandedDiagram.content) {
                            navigator.clipboard.writeText(expandedDiagram.content);
                          }
                        }}
                        className={`p-2 rounded-lg transition-colors ${
                          isDarkMode 
                            ? 'text-gray-400 hover:text-white hover:bg-gray-800' 
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                        }`}
                        title="Copy diagram"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          if (expandedDiagram.svg) {
                            const blob = new Blob([expandedDiagram.svg], { type: 'image/svg+xml' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `${expandedDiagram.type}-diagram.svg`;
                            a.click();
                            URL.revokeObjectURL(url);
                          }
                        }}
                        className={`p-2 rounded-lg transition-colors ${
                          isDarkMode 
                            ? 'text-gray-400 hover:text-white hover:bg-gray-800' 
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                        }`}
                        title="Download diagram"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setExpandedDiagram(null)}
                        className={`p-2 rounded-lg transition-colors ${
                          isDarkMode 
                            ? 'text-gray-400 hover:text-white hover:bg-gray-800' 
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                        }`}
                        title="Close diagram"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Diagram Content */}
                <div className="flex-1 overflow-hidden">
                  {(expandedDiagram.type === 'mermaid' || expandedDiagram.type === 'wizard') && expandedDiagram.svg && (
                    <div 
                      className={`w-full h-full flex items-center justify-center overflow-auto p-4 ${
                        isDarkMode ? 'bg-gray-900' : 'bg-white'
                      }`}
                      dangerouslySetInnerHTML={{ __html: expandedDiagram.svg }}
                    />
                  )}
                  
                  {expandedDiagram.type === 'network' && expandedDiagram.nodes && expandedDiagram.edges && (
                    <div className="w-full h-full">
                      <ReactFlow
                        nodes={expandedDiagram.nodes}
                        edges={expandedDiagram.edges}
                        fitView
                        fitViewOptions={{ padding: 0.1 }}
                        className={isDarkMode ? 'bg-gray-900' : 'bg-white'}
                        proOptions={{ hideAttribution: true }}
                      >
                        <Background 
                          color={isDarkMode ? '#374151' : '#e5e7eb'} 
                          gap={25} 
                          size={2} 
                        />
                        <Controls className={`rounded-lg ${
                          isDarkMode 
                            ? 'bg-gray-800 border border-gray-600 [&>button]:text-gray-300 [&>button]:border-gray-600 [&>button:hover]:bg-gray-700' 
                            : 'bg-white border border-gray-300 [&>button]:text-gray-600 [&>button]:border-gray-300 [&>button:hover]:bg-gray-100'
                        }`} />
                      </ReactFlow>
                    </div>
                  )}
                </div>
              </>
            ) : selectedDocument ? (
              <>
                {/* Document Header */}
                <div className={`p-4 border-b transition-colors duration-200 ${
                  isDarkMode 
                    ? 'border-gray-700 bg-gray-900' 
                    : 'border-gray-200 bg-white'
                }`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      isDarkMode ? 'bg-white' : 'bg-black'
                    }`}>
                      <FileText className={`w-4 h-4 ${isDarkMode ? 'text-black' : 'text-white'}`} />
                    </div>
                    <div>
                      <h1 className={`text-lg font-semibold transition-colors duration-200 ${
                        isDarkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        {selectedDocument.path.split('/').pop()?.replace(/\.md$/, '') || 'Document'}
                      </h1>
                      <p className={`text-xs transition-colors duration-200 ${
                        isDarkMode ? 'text-gray-400' : 'text-gray-500'
                      }`}>
                        {selectedDocument.path.replace(/\.md$/, '')}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Document Content */}
                <div className="flex-1 overflow-y-auto p-6 pb-32">
                  <div className="max-w-4xl mx-auto">
                    <MarkdownRenderer content={selectedDocument.content} isDarkMode={isDarkMode} />
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className={`w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4 ${
                    isDarkMode ? 'bg-white' : 'bg-black'
                  }`}>
                    <BookOpen className={`w-8 h-8 ${isDarkMode ? 'text-black' : 'text-white'}`} />
                  </div>
                  <h2 className={`text-xl font-semibold mb-2 transition-colors duration-200 ${
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    Select Documentation
                  </h2>
                  <p className={`text-sm transition-colors duration-200 ${
                    isDarkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Choose a document from the sidebar to start reading
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Enhanced Chat Interface */}
          <ChatInterface
            onSendMessage={handleChatMessage}
            isLoading={!ragEngine?.isReady()}
            documents={documents}
            selectedDocument={selectedDocument}
            onDocumentSelect={setSelectedDocument}
            isExpanded={isChatExpanded}
            onToggleExpanded={setIsChatExpanded}
            isDarkMode={isDarkMode}
            onDiagramExpand={setExpandedDiagram}
            position={chatPosition}
            onPositionToggle={() => setChatPosition(chatPosition === 'bottom' ? 'right' : 'bottom')}
          />

        </div>
      </div>
    </div>
  );
}
