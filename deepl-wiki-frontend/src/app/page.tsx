'use client';

import React, { useState, useEffect, useMemo } from 'react';
import ChatInterface from '@/components/ChatInterface';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import TableOfContents from '@/components/TableOfContents';
import ParticleBackground from '@/components/ParticleBackground';
import KeyboardShortcuts from '@/components/KeyboardShortcuts';
import ErrorBoundary from '@/components/ErrorBoundary';
import LoadingSpinner from '@/components/LoadingSpinner';
import PathSelector from '@/components/PathSelector';
import { WikiDocument } from '@/components/WikiBrowser';
import { MarkdownMonitor } from '@/lib/markdown-monitor';
import { SimpleRAGEngine } from '@/lib/simple-rag-engine';
import { mockDocuments, MockRAGEngine } from '@/lib/mock-data';
import { apiClient } from '@/lib/api-client';
import { createFileSystemService, LocalFileTree, LocalMarkdownFile, FileSystemService } from '@/lib/local-file-system';
import { BookOpen, AlertCircle, Search, FileText, Folder, Moon, Sun, X, Network, Copy, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { ReactFlow, Background, Controls, Node as FlowNode, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

export default function Home() {
  const [documents, setDocuments] = useState<WikiDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<WikiDocument | null>(null);
  const [localFileTree, setLocalFileTree] = useState<LocalFileTree | null>(null);
  const [localFileService] = useState<FileSystemService>(() => createFileSystemService());
  const [showPathSelector, setShowPathSelector] = useState(false);
  const [useLocalFiles, setUseLocalFiles] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ragEngine, setRagEngine] = useState<SimpleRAGEngine | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [monitor] = useState<MarkdownMonitor | null>(null);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [chatPosition, setChatPosition] = useState<'bottom-middle' | 'bottom-right'>('bottom-middle');
  const [chatFullscreen, setChatFullscreen] = useState(false);
  const [expandedDiagram, setExpandedDiagram] = useState<{
    type: 'mermaid' | 'network' | 'wizard';
    content?: string;
    svg?: string;
    nodes?: FlowNode[];
    edges?: Edge[];
  } | null>(null);
  const [searchInputRef, setSearchInputRef] = useState<HTMLInputElement | null>(null);
  const [isOnline, setIsOnline] = useState(true);

  // Apply light mode class to body
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.remove('light-mode');
    } else {
      document.body.classList.add('light-mode');
    }
  }, [isDarkMode]);

  // Online/offline status tracking
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    setIsOnline(navigator.onLine);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Mouse tracking for dynamic chat positioning
  useEffect(() => {
    const handleMouseMove = () => {
      if (!isChatExpanded || chatFullscreen) return;
    };

    const handleClick = (e: MouseEvent) => {
      if (!isChatExpanded || chatFullscreen) return;
      
      // If user clicks on content area, move chat to avoid overlap
      const chatElement = document.getElementById('chat-interface');
      if (chatElement && !chatElement.contains(e.target as Node)) {
        const { innerWidth } = window;
        const { clientX } = e;
        
        // Determine best position based on click location
        // If clicking on the right side, move chat to bottom-middle
        // If clicking on the left/center, move chat to bottom-right
        const newPosition: typeof chatPosition = clientX > (innerWidth * 2) / 3 
          ? 'bottom-middle' 
          : 'bottom-right';
        
        setChatPosition(newPosition);
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('click', handleClick);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('click', handleClick);
    };
  }, [isChatExpanded, chatFullscreen]);

  // Filter documents based on search
  const filteredDocuments = useMemo(() => {
    if (!searchTerm.trim()) return documents;
    return documents.filter(doc => 
      doc.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.content.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [documents, searchTerm]);

  // Filter local files based on search
  const filteredLocalFiles = useMemo(() => {
    if (!localFileTree || !searchTerm.trim()) return localFileService.getAllMarkdownFiles();
    return localFileService.searchFiles(searchTerm);
  }, [localFileTree, searchTerm, localFileService]);

  // Check backend connectivity
  const checkBackendConnection = async (): Promise<boolean> => {
    try {
      await apiClient.getHealth();
      return true;
    } catch (error) {
      console.warn('Backend not available:', error);
      return false;
    }
  };

  // Handle local file system path selection
  const handlePathSelect = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Check backend connectivity first
      const connected = await checkBackendConnection();
      setBackendConnected(connected);
      
      if (!connected) {
        setError('Backend API is not available. Chat functionality will be limited.');
      }
      
      // Use the directory picker (browsers don't allow direct path access for security reasons)
      const fileTree = await localFileService.selectDirectory();
      setLocalFileTree(fileTree);
      
      // Convert to WikiDocument format for compatibility
      const allFiles = localFileService.getAllMarkdownFiles();
      const wikiDocs: WikiDocument[] = allFiles.map(file => ({
        path: file.relativePath,
        content: '', // Will be loaded when selected
        lastModified: new Date(file.lastModified).toISOString(),
        sha: file.relativePath,
      }));
      
      setDocuments(wikiDocs);
      setUseLocalFiles(true);
      
      console.log(`Loaded ${fileTree.totalFiles} local markdown files from ${fileTree.rootPath}`);
    } catch (err) {
      console.error('Failed to load local files:', err);
      setError('Failed to load local files: ' + (err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle local file selection and load content
  const handleLocalFileSelect = async (file: LocalMarkdownFile) => {
    try {
      const content = await localFileService.readFileContent(file.relativePath);
      const doc: WikiDocument = {
        path: file.relativePath,
        content: content,
        lastModified: new Date(file.lastModified).toISOString(),
        sha: file.relativePath,
      };
      setSelectedDocument(doc);
      setExpandedDiagram(null);
    } catch (error) {
      console.error('Failed to load local file:', error);
      setError('Failed to load file content');
    }
  };


  // Initialize demo data (fallback)
  const initializeDemoData = async () => {
    try {
      console.log('Initializing with demo data...');
      setIsLoading(true);
      setError(null);
      
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
      setUseLocalFiles(false);
      
      console.log('Demo data initialized successfully');
    } catch (err) {
      console.error('Demo initialization error:', err);
      setError('Failed to initialize demo data');
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize system - start with demo mode and show path selector
  useEffect(() => {
    const initializeSystem = async () => {
      try {
        // Start with demo data
        await initializeDemoData();
        
        // Show path selector for local files option
        setTimeout(() => {
          if (!useLocalFiles) {
            setShowPathSelector(true);
          }
        }, 1000);
      } catch (error) {
        console.error('System initialization failed:', error);
        setError('Failed to initialize system. Please refresh the page.');
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


  const handleChatMessage = async (message: string): Promise<string> => {
    try {
      // Check network connectivity
      if (!navigator.onLine) {
        return 'You appear to be offline. Please check your internet connection and try again.';
      }

      if (useLocalFiles) {
        // Use backend API for local files mode
        if (!backendConnected) {
          return 'Backend API is not available. Please ensure the backend server is running at http://localhost:8000 and try again.';
        }
        
        try {
          const response = await apiClient.sendChatMessage(message);
          return response.response;
        } catch (err) {
          console.error('Backend chat error:', err);
          setBackendConnected(false);
          return 'Failed to connect to the backend API. Please ensure the backend server is running and try again.';
        }
      } else {
        // Use local RAG engine for demo mode
        if (!ragEngine || !ragEngine.isReady()) {
          return 'Sorry, the system is not ready yet. Please wait for documents to be indexed.';
        }

        const response = await ragEngine.query(message);
        return response;
      }
    } catch (err) {
      console.error('Chat error:', err);
      
      // Handle different types of errors
      if (err instanceof TypeError && err.message.includes('fetch')) {
        return 'Network error: Unable to connect to the AI service. Please check your internet connection and try again.';
      }
      
      if (err instanceof Error && err.message.includes('timeout')) {
        return 'Request timeout: The AI service is taking too long to respond. Please try again with a shorter question.';
      }
      
      return 'I apologize, but I encountered an error processing your question. Please try again, and if the problem persists, try refreshing the page.';
    }
  };

  // Handle chat position toggle between two states
  const handleChatPositionToggle = () => {
    const newPosition = chatPosition === 'bottom-middle' ? 'bottom-right' : 'bottom-middle';
    setChatPosition(newPosition);
  };

  // Handle fullscreen toggle
  const handleChatFullscreenToggle = (fullscreen: boolean) => {
    setChatFullscreen(fullscreen);
    if (fullscreen) {
      setIsChatExpanded(true);
    }
  };

  // Keyboard shortcuts handlers
  const handleFocusSearch = () => {
    searchInputRef?.focus();
  };

  const handleToggleChat = () => {
    setIsChatExpanded(!isChatExpanded);
  };

  const handleToggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleToggleFullscreen = () => {
    handleChatFullscreenToggle(!chatFullscreen);
  };

  // Toggle between local files and demo mode
  const handleToggleMode = async () => {
    if (useLocalFiles) {
      // Switch to demo mode
      await initializeDemoData();
      localFileService.clear();
      setLocalFileTree(null);
    } else {
      // Switch to local files mode
      setShowPathSelector(true);
    }
  };



  if (isLoading) {
    return (
      <ErrorBoundary isDarkMode={isDarkMode}>
        <div className={`min-h-screen flex items-center justify-center transition-colors duration-200 ${
          isDarkMode ? 'bg-gray-900' : 'bg-white'
        }`}>
          <div className="text-center space-y-8">
            {/* Enhanced Loading Animation */}
            <LoadingSpinner 
              isDarkMode={isDarkMode} 
              size="xl" 
              type="indexing"
              message="Initializing JAVI Wiki"
            />

            {/* Title */}
            <div>
              <h1 className={`text-4xl font-black mb-2 transition-colors duration-200 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent animate-pulse">
                  JAVI Wiki
                </span>
              </h1>
              <p className={`text-lg font-medium transition-colors duration-200 ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Your AI-powered documentation assistant
              </p>
            </div>

            {/* Progress Indicator */}
            <div className="space-y-3">
              <div className={`w-80 h-2 rounded-full overflow-hidden mx-auto transition-colors duration-200 ${
                isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
              }`}>
                <div className={`h-full rounded-full indexing-progress transition-colors duration-200 ${
                  isDarkMode 
                    ? 'bg-gradient-to-r from-blue-400 to-purple-400' 
                    : 'bg-gradient-to-r from-blue-500 to-purple-500'
                }`}></div>
              </div>
              <p className={`text-sm transition-colors duration-200 ${
                isDarkMode ? 'text-gray-500' : 'text-gray-400'
              }`}>
                Indexing documents and setting up intelligent search...
              </p>
            </div>
          </div>
          
          {/* Particle Background for loading screen */}
          <ParticleBackground isDarkMode={isDarkMode} density={15} />
        </div>
      </ErrorBoundary>
    );
  }


  return (
    <ErrorBoundary isDarkMode={isDarkMode}>
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
            {/* Offline Indicator */}
            {!isOnline && (
              <div className={`flex items-center gap-2 rounded-full px-3 py-2 border ${
                isDarkMode 
                  ? 'bg-red-900/20 border-red-700/50 text-red-400' 
                  : 'bg-red-50 border-red-200/50 text-red-600'
              }`}>
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-xs font-medium">Offline</span>
              </div>
            )}
            
            {/* Local Files/Demo Mode Toggle */}
            <button
              onClick={handleToggleMode}
              className={`flex items-center gap-2 rounded-full px-3 py-2 border text-xs transition-colors ${
                useLocalFiles 
                  ? isDarkMode 
                    ? 'bg-purple-900/20 border-purple-700/50 text-purple-400 hover:bg-purple-900/30' 
                    : 'bg-purple-50 border-purple-200/50 text-purple-600 hover:bg-purple-100'
                  : isDarkMode 
                    ? 'bg-amber-900/20 border-amber-700/50 text-amber-400 hover:bg-amber-900/30' 
                    : 'bg-amber-50 border-amber-200/50 text-amber-600 hover:bg-amber-100'
              }`}
              title={useLocalFiles ? 'Switch to Demo Mode' : 'Load Local Files'}
            >
              <div className={`w-2 h-2 rounded-full ${
                useLocalFiles ? 'bg-purple-500' : 'bg-amber-500'
              } animate-pulse`}></div>
              <span className="font-medium">
                {useLocalFiles ? 'Local Files' : 'Demo Mode'}
              </span>
            </button>

            <div className={`flex items-center gap-3 rounded-full px-4 py-2 border transition-all duration-300 ${
              isDarkMode 
                ? 'bg-gray-800/80 border-gray-600/50' 
                : 'bg-white/80 border-gray-200/50'
            }`}>
              {useLocalFiles ? (
                <>
                  <div className="relative">
                    <div className={`w-3 h-3 ${backendConnected ? 'bg-purple-500' : 'bg-yellow-500'} rounded-full indexing-pulse`}></div>
                    <div className={`absolute inset-0 w-3 h-3 ${backendConnected ? 'bg-purple-400' : 'bg-yellow-400'} rounded-full animate-ping opacity-75`}></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-bold ${
                      backendConnected 
                        ? isDarkMode ? 'text-purple-400' : 'text-purple-600'
                        : isDarkMode ? 'text-yellow-400' : 'text-yellow-600'
                    }`}>
                      {localFileTree?.totalFiles || documents.length} local files
                    </span>
                    <div className={`w-2 h-2 rounded-full ${
                      backendConnected 
                        ? isDarkMode ? 'bg-purple-400' : 'bg-purple-500'
                        : isDarkMode ? 'bg-yellow-400' : 'bg-yellow-500'
                    }`}></div>
                    {!backendConnected && (
                      <span className={`text-xs ${
                        isDarkMode ? 'text-yellow-400' : 'text-yellow-600'
                      }`}>
                        (API offline)
                      </span>
                    )}
                  </div>
                </>
              ) : ragEngine?.isReady() ? (
                <>
                  <div className="relative">
                    <div className="w-3 h-3 bg-green-500 rounded-full indexing-pulse"></div>
                    <div className="absolute inset-0 w-3 h-3 bg-green-400 rounded-full animate-ping opacity-75"></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-bold ${
                      isDarkMode ? 'text-green-400' : 'text-green-600'
                    }`}>
                      {ragEngine?.getIndexedDocumentCount()} docs indexed
                    </span>
                    <div className={`w-2 h-2 rounded-full ${
                      isDarkMode ? 'bg-green-400' : 'bg-green-500'
                    }`}></div>
                  </div>
                </>
              ) : (
                <>
                  <div className="relative flex items-center">
                    <div className={`w-4 h-4 border-2 border-t-transparent rounded-full indexing-spin ${
                      isDarkMode ? 'border-blue-400' : 'border-blue-500'
                    }`}></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-bold ${
                      isDarkMode ? 'text-blue-400' : 'text-blue-600'
                    }`}>
                      Indexing docs
                    </span>
                    <div className="flex items-center gap-1">
                      <div className={`w-1.5 h-1.5 rounded-full indexing-dots ${
                        isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                      }`}></div>
                      <div className={`w-1.5 h-1.5 rounded-full indexing-dots ${
                        isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                      }`} style={{animationDelay: '0.3s'}}></div>
                      <div className={`w-1.5 h-1.5 rounded-full indexing-dots ${
                        isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                      }`} style={{animationDelay: '0.6s'}}></div>
                    </div>
                  </div>
                  <div className={`h-1 w-16 rounded-full overflow-hidden ${
                    isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
                  }`}>
                    <div className={`h-full rounded-full indexing-progress ${
                      isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                    }`}></div>
                  </div>
                </>
              )}
            </div>
            {useLocalFiles && (
              <button
                onClick={() => setShowPathSelector(true)}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode 
                    ? 'text-gray-400 hover:text-white hover:bg-gray-800' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="Select Different Path"
              >
                <Folder className="w-4 h-4" />
              </button>
            )}
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
                  ref={setSearchInputRef}
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
              {useLocalFiles && localFileTree ? (
                // Local files mode - show directory structure
                (() => {
                  const buildTreeFromFiles = (files: LocalMarkdownFile[]) => {
                    const tree: { [key: string]: LocalMarkdownFile[] } = {};
                    
                    files.forEach(file => {
                      const pathParts = file.relativePath.split('/');
                      const folder = pathParts.length > 1 ? pathParts[0] : 'Root';
                      if (!tree[folder]) tree[folder] = [];
                      tree[folder].push(file);
                    });
                    
                    return tree;
                  };

                  const fileTree = buildTreeFromFiles(filteredLocalFiles);
                  
                  return Object.entries(fileTree).map(([folder, files]) => (
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
                          {files.length}
                        </span>
                      </div>
                      <div className="ml-6 space-y-1">
                        {files.map((file) => (
                          <button
                            key={file.relativePath}
                            onClick={() => handleLocalFileSelect(file)}
                            className={`flex items-center gap-2 w-full p-2 text-left rounded transition-all duration-200 text-sm ${
                              selectedDocument?.sha === file.relativePath
                                ? isDarkMode 
                                  ? 'bg-blue-900/30 text-blue-300 font-medium border border-blue-700/50'
                                  : 'bg-blue-50 text-blue-700 font-medium border border-blue-200'
                                : isDarkMode
                                  ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'
                                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                            }`}
                          >
                            <FileText className="w-3 h-3" />
                            <span className="truncate" title={file.relativePath}>
                              {file.name.replace(/\.md$/, '')}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ));
                })()
              ) : (
                // Demo mode - use original structure
                Object.entries(filteredDocuments.reduce((tree: { [key: string]: typeof filteredDocuments }, doc) => {
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
                            setExpandedDiagram(null);
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
                ))
              )}
            </div>
          </div>

          {/* Main Content Area */}
          <div className={`flex-1 flex flex-col transition-colors duration-200 ${
            isDarkMode ? 'bg-gray-900' : 'bg-white'
          } ${chatPosition === 'bottom-right' && isChatExpanded && !chatFullscreen ? 'mr-96' : ''} ${
            chatFullscreen ? 'pointer-events-none' : ''
          }`}>
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
                <div className="flex-1 overflow-y-auto">
                  <div className="flex gap-8 p-6 pb-32">
                    {/* Main Content */}
                    <div className="flex-1 max-w-4xl">
                      <MarkdownRenderer content={selectedDocument.content} isDarkMode={isDarkMode} />
                    </div>
                    
                    {/* Table of Contents - Right Sidebar */}
                    <div className="hidden lg:block w-80 flex-shrink-0">
                      <TableOfContents 
                        content={selectedDocument.content} 
                        isDarkMode={isDarkMode}
                        className="w-full"
                      />
                    </div>
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
            isLoading={useLocalFiles ? false : !ragEngine?.isReady()}
            documents={documents}
            selectedDocument={selectedDocument}
            onDocumentSelect={setSelectedDocument}
            isExpanded={isChatExpanded}
            onToggleExpanded={setIsChatExpanded}
            isDarkMode={isDarkMode}
            onDiagramExpand={setExpandedDiagram}
            position={chatPosition}
            onPositionToggle={handleChatPositionToggle}
            isFullscreen={chatFullscreen}
            onToggleFullscreen={handleChatFullscreenToggle}
          />

        </div>
      </div>
      
      {/* Particle Background */}
      <ParticleBackground isDarkMode={isDarkMode} density={25} />
      
      {/* Keyboard Shortcuts */}
      <KeyboardShortcuts 
        isDarkMode={isDarkMode}
        onToggleChat={handleToggleChat}
        onToggleTheme={handleToggleTheme}
        onToggleFullscreen={handleToggleFullscreen}
        onFocusSearch={handleFocusSearch}
      />

      {/* Path Selector Modal */}
      <PathSelector
        isOpen={showPathSelector}
        onClose={() => setShowPathSelector(false)}
        onPathSelect={handlePathSelect}
        isDarkMode={isDarkMode}
      />
      </div>
    </ErrorBoundary>
  );
}
