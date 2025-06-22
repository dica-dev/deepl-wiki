'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Bot, User, Loader2, MessageSquare, Minimize2, PanelRightOpen, PanelBottomOpen, Maximize2, ArrowLeft } from 'lucide-react';
import { Node as FlowNode, Edge } from 'reactflow';
import DiagramRenderer from './DiagramRenderer';
import MarkdownRenderer from './MarkdownRenderer';
import AdvancedTypingIndicator from './AdvancedTypingIndicator';
import { WikiDocument } from './WikiBrowser';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  diagram?: {
    type: 'mermaid' | 'network' | 'wizard';
    content?: string;
  };
}

interface ChatInterfaceProps {
  onSendMessage: (message: string) => Promise<string>;
  isLoading?: boolean;
  documents?: WikiDocument[];
  selectedDocument?: WikiDocument | null;
  onDocumentSelect?: (document: WikiDocument) => void;
  isExpanded?: boolean;
  onToggleExpanded?: (expanded: boolean) => void;
  isDarkMode?: boolean;
  onDiagramExpand?: (diagramData: { type: 'mermaid' | 'network' | 'wizard'; content?: string; svg?: string; nodes?: FlowNode[]; edges?: Edge[] }) => void;
  position?: 'bottom-middle' | 'bottom-right';
  onPositionToggle?: () => void;
  isFullscreen?: boolean;
  onToggleFullscreen?: (fullscreen: boolean) => void;
}

export default function ChatInterface({ 
  onSendMessage, 
  isLoading = false,
  documents = [],
  selectedDocument = null,
  onDocumentSelect,
  isExpanded = false,
  onToggleExpanded,
  isDarkMode = false,
  onDiagramExpand,
  position = 'bottom-middle',
  onPositionToggle,
  isFullscreen = false,
  onToggleFullscreen
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m JAVI, your documentation assistant. I can help answer questions about your project documentation and generate interactive diagrams. Try asking me to "show a diagram" or "visualize the repository structure"!',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isMinimized, setIsMinimized] = useState(!isExpanded);
  const [isCompactMode, setIsCompactMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Determine if we should be in compact mode
    const shouldBeCompact = position === 'bottom-middle' && !isExpanded;
    setIsCompactMode(shouldBeCompact);
    setIsMinimized(!isExpanded && !shouldBeCompact);
    
    // Scroll to bottom when chat is expanded
    if (isExpanded) {
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }
  }, [isExpanded, position]);

  const handleToggleMinimized = useCallback(() => {
    const newMinimized = !isMinimized;
    setIsMinimized(newMinimized);
    onToggleExpanded?.(!newMinimized);
    
    // Scroll to bottom when expanding
    if (!newMinimized) {
      setTimeout(() => {
        scrollToBottom();
      }, 150);
    }
  }, [isMinimized, onToggleExpanded]);

  // Click outside to minimize
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const chatElement = document.getElementById('chat-interface');
      if (chatElement && !chatElement.contains(event.target as Node) && !isMinimized) {
        handleToggleMinimized();
      }
    };

    if (!isMinimized) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMinimized, handleToggleMinimized]);

  const handleDiagramNodeClick = (nodeId: string, document?: WikiDocument) => {
    if (document && onDocumentSelect) {
      onDocumentSelect(document);
    }
  };

  // Detect if user is asking for diagrams
  const shouldGenerateDiagram = (message: string): { type: 'mermaid' | 'network' | 'wizard' | null; content?: string } => {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('diagram') || lowerMessage.includes('visualize') || lowerMessage.includes('chart') || lowerMessage.includes('graph')) {
      if (lowerMessage.includes('workflow') || lowerMessage.includes('process') || lowerMessage.includes('step') || lowerMessage.includes('wizard')) {
        return { type: 'wizard' };
      } else if (lowerMessage.includes('network') || lowerMessage.includes('connection') || lowerMessage.includes('relationship')) {
        return { type: 'network' };
      } else {
        return { type: 'mermaid' };
      }
    }
    
    if (lowerMessage.includes('structure') || lowerMessage.includes('organization') || lowerMessage.includes('hierarchy')) {
      return { type: 'mermaid' };
    }
    
    if (lowerMessage.includes('flow') || lowerMessage.includes('workflow') || lowerMessage.includes('process')) {
      return { type: 'wizard' };
    }
    
    return { type: null };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input.trim();
    setInput('');
    setIsProcessing(true);
    
    // Auto-expand when starting to process (especially important for compact mode)
    if (isCompactMode || !isExpanded) {
      onToggleExpanded?.(true);
    }

    try {
      // Check if user is asking for a diagram
      const diagramRequest = shouldGenerateDiagram(currentInput);
      
      const response = await onSendMessage(currentInput);
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
        diagram: diagramRequest.type ? {
          type: diagramRequest.type,
          content: diagramRequest.content
        } : undefined,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If a diagram was requested, enhance the response
      if (diagramRequest.type) {
        const diagramExplanation: ChatMessage = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `I've generated a ${diagramRequest.type === 'wizard' ? 'workflow' : diagramRequest.type} diagram to visualize ${
            diagramRequest.type === 'mermaid' ? 'the repository structure' :
            diagramRequest.type === 'network' ? 'the connections between files' :
            'the analysis process'
          }. You can interact with it, expand it for a better view, or download it for your documentation.`,
          timestamp: new Date(),
        };
        
        // Add the explanation after a brief delay for better UX
        setTimeout(() => {
          setMessages(prev => [...prev, diagramExplanation]);
        }, 500);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
      inputRef.current?.focus();
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Get position classes based on position prop
  const getPositionClasses = () => {
    if (isFullscreen) {
      return 'fixed inset-0 z-50';
    }

    if (isMinimized) {
      switch (position) {
        case 'bottom-right':
          return 'fixed bottom-6 right-6 z-40';
        default: // bottom-middle
          return 'fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40';
      }
    }

    if (isCompactMode) {
      return 'fixed bottom-6 left-1/2 transform -translate-x-1/2 w-[95vw] sm:w-[90vw] max-w-2xl z-50';
    }

    // Expanded states
    switch (position) {
      case 'bottom-right':
        return 'fixed top-0 right-0 h-full w-96 z-50 animate-in slide-in-from-right-4';
      default: // bottom-middle
        return 'fixed bottom-6 left-1/2 transform -translate-x-1/2 w-[95vw] sm:w-[90vw] max-w-4xl z-50 animate-in slide-in-from-bottom-4';
    }
  };

  // Minimized state
  if (isMinimized) {
    return (
      <div className={`${getPositionClasses()} transition-all duration-300 ease-out`}>
        <div className={`backdrop-blur-md shadow-lg rounded-xl border transform flex items-center ${
          isDarkMode 
            ? 'bg-gray-800/60 border-gray-600/60 hover:bg-gray-800/80' 
            : 'bg-white/60 border-gray-200/60 hover:bg-white/80'
        }`}>
          <button
            onClick={handleToggleMinimized}
            className="px-4 py-3 flex items-center gap-3 hover:shadow-xl hover:scale-105 transition-all duration-300 ease-out flex-1"
            aria-label="Open chat interface"
          >
            <div className={`w-6 h-6 rounded-lg flex items-center justify-center ${
              isDarkMode ? 'bg-white' : 'bg-black'
            }`}>
              <MessageSquare className={`w-3 h-3 ${isDarkMode ? 'text-black' : 'text-white'}`} />
            </div>
            <div className="text-left">
              <div className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Ask JAVI
              </div>
              <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                Chat about your docs
              </div>
            </div>
            {isLoading && (
              <div className="relative">
                <div className={`w-2 h-2 border border-t-transparent rounded-full indexing-spin ${
                  isDarkMode ? 'border-blue-400' : 'border-blue-500'
                }`}></div>
              </div>
            )}
          </button>
          
          {/* Position toggle button in minimized state */}
          {onPositionToggle && (
            <button
              onClick={onPositionToggle}
              className={`p-2 rounded-r-xl transition-all duration-200 hover:scale-110 transform border-l ${
                isDarkMode 
                  ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700 border-gray-600' 
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 border-gray-200'
              }`}
              title={position === 'bottom-middle' ? 'Move to right corner' : 'Move to bottom center'}
            >
              {position === 'bottom-middle' ? (
                <PanelRightOpen className="w-4 h-4" />
              ) : (
                <PanelBottomOpen className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>
    );
  }

  // Compact input bar mode for bottom-middle position
  if (isCompactMode) {
    return (
      <div className={`${getPositionClasses()} transition-all duration-300 ease-out`}>
        <div className={`backdrop-blur-md shadow-xl border transition-all duration-300 flex items-center rounded-full ${
          isDarkMode 
            ? 'bg-gray-800/70 border-gray-600/60 hover:bg-gray-800/80' 
            : 'bg-white/70 border-gray-200/60 hover:bg-white/80'
        }`}>
          {/* Compact Input Form */}
          <form onSubmit={handleSubmit} className="flex items-center w-full" role="search" aria-label="Chat with JAVI">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedDocument ? `Ask about ${selectedDocument.path.split('/').pop()?.replace(/\.md$/, '') || 'document'}...` : "Ask about your docs..."}
                disabled={isProcessing || isLoading}
                aria-label="Type your message"
                className={`w-full pl-6 pr-4 py-4 rounded-full transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm border-none focus:outline-none bg-transparent ${
                  isDarkMode 
                    ? 'text-white placeholder-gray-400' 
                    : 'text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
            
            {/* Submit Button */}
            <button
              type="submit"
              disabled={!input.trim() || isProcessing || isLoading}
              className={`mr-2 w-10 h-10 rounded-full transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center hover:scale-110 transform ${
                isDarkMode 
                  ? 'bg-white text-black hover:bg-gray-200 disabled:hover:scale-100' 
                  : 'bg-black text-white hover:bg-gray-800 disabled:hover:scale-100'
              }`}
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>

            {/* Position toggle button */}
            {onPositionToggle && (
              <button
                type="button"
                onClick={onPositionToggle}
                className={`mr-2 w-8 h-8 rounded-full transition-all duration-200 hover:scale-110 transform flex items-center justify-center ${
                  isDarkMode 
                    ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                }`}
                title="Move to right corner"
              >
                <PanelRightOpen className="w-3 h-3" />
              </button>
            )}
          </form>
        </div>
      </div>
    );
  }

  return (
    <div id="chat-interface" className={`${getPositionClasses()} transition-all duration-500 ease-out`}>
      <div className={`backdrop-blur-md shadow-xl border transition-all duration-300 flex flex-col ${
        isFullscreen 
          ? 'rounded-none h-full' 
          : position === 'bottom-middle'
            ? 'rounded-xl overflow-hidden' 
            : 'rounded-none h-full'
      } ${
        isDarkMode 
          ? 'bg-gray-800/70 border-gray-600/60 hover:bg-gray-800/80' 
          : 'bg-white/70 border-gray-200/60 hover:bg-white/80'
      }`}>
        {/* Header */}
        <div className={`border-b ${
          isDarkMode 
            ? 'border-gray-600/60 bg-gray-800/30' 
            : 'border-gray-200/60 bg-white/30'
        }`}>
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <div className={`w-6 h-6 rounded-lg flex items-center justify-center ${
                isDarkMode ? 'bg-white' : 'bg-black'
              }`}>
                <Bot className={`w-3 h-3 ${isDarkMode ? 'text-black' : 'text-white'}`} />
              </div>
              <div>
                <h3 className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  JAVI
                </h3>
                <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {documents.length} docs indexed
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isLoading && !isFullscreen && (
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-300 indexing-glow ${
                  isDarkMode 
                    ? 'bg-blue-900/30 border-blue-700/50' 
                    : 'bg-blue-50 border-blue-200/50'
                }`}>
                  <div className="relative flex items-center">
                    <div className={`w-3 h-3 border border-t-transparent rounded-full indexing-spin ${
                      isDarkMode ? 'border-blue-400' : 'border-blue-500'
                    }`}></div>
                  </div>
                  <span className={`text-xs font-bold ${
                    isDarkMode ? 'text-blue-400' : 'text-blue-700'
                  }`}>
                    Indexing
                  </span>
                  <div className="flex items-center gap-0.5">
                    <div className={`w-1 h-1 rounded-full indexing-dots ${
                      isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                    }`}></div>
                    <div className={`w-1 h-1 rounded-full indexing-dots ${
                      isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                    }`} style={{animationDelay: '0.3s'}}></div>
                    <div className={`w-1 h-1 rounded-full indexing-dots ${
                      isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                    }`} style={{animationDelay: '0.6s'}}></div>
                  </div>
                </div>
              )}
              
              {isFullscreen ? (
                /* Large prominent return button for fullscreen */
                <button
                  onClick={() => onToggleFullscreen?.(false)}
                  className={`flex items-center gap-3 px-6 py-3 rounded-xl transition-all duration-200 hover:scale-105 transform shadow-lg font-semibold text-sm ${
                    isDarkMode 
                      ? 'bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-600 hover:to-gray-500 text-white border border-gray-500' 
                      : 'bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-900 border border-gray-300'
                  }`}
                  title="Return to normal view"
                >
                  <ArrowLeft className="w-5 h-5" />
                  Return
                </button>
              ) : (
                /* Normal mode buttons */
                <>
                  {onToggleFullscreen && (
                    <button
                      onClick={() => onToggleFullscreen?.(true)}
                      className={`p-1 rounded transition-all duration-200 hover:scale-110 transform ${
                        isDarkMode 
                          ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                          : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                      }`}
                      title="Enter fullscreen"
                    >
                      <Maximize2 className="w-4 h-4" />
                    </button>
                  )}
                  {onPositionToggle && (
                    <button
                      onClick={onPositionToggle}
                      className={`p-1 rounded transition-all duration-200 hover:scale-110 transform ${
                        isDarkMode 
                          ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                          : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                      }`}
                      title={position === 'bottom-middle' ? 'Move to right panel' : 'Move to bottom center'}
                    >
                      {position === 'bottom-middle' ? (
                        <PanelRightOpen className="w-4 h-4" />
                      ) : (
                        <PanelBottomOpen className="w-4 h-4" />
                      )}
                    </button>
                  )}
                  <button
                    onClick={handleToggleMinimized}
                    className={`p-1 rounded transition-all duration-200 hover:scale-110 transform ${
                      isDarkMode 
                        ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                        : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                    }`}
                    title="Minimize chat"
                  >
                    <Minimize2 className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Chat Messages - Improved scrolling */}
        <div className={`flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0 ${
          isFullscreen 
            ? "" 
            : position === 'bottom-middle'
              ? "max-h-60" 
              : ""
        }`}>
          {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start gap-3 ${
                    message.role === 'user' ? 'flex-row-reverse' : ''
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user' 
                      ? isDarkMode ? 'bg-white' : 'bg-black'
                      : isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
                  }`}>
                    {message.role === 'user' ? (
                      <User className={`w-3 h-3 ${isDarkMode ? 'text-black' : 'text-white'}`} />
                    ) : (
                      <Bot className={`w-3 h-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`} />
                    )}
                  </div>
                  
                  <div className={`max-w-[85%] space-y-3 ${message.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                    {/* Text Message */}
                    <div className={`rounded-lg px-3 py-2 ${
                      message.role === 'user'
                        ? isDarkMode ? 'bg-white text-black' : 'bg-black text-white'
                        : isDarkMode ? 'bg-gray-700 text-gray-100' : 'bg-gray-100 text-gray-900'
                    }`}>
                      {message.role === 'user' ? (
                        <div className="text-sm leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </div>
                      ) : (
                        <div className="text-sm leading-relaxed">
                          <MarkdownRenderer 
                            content={message.content} 
                            isDarkMode={isDarkMode}
                            className="chat-message"
                          />
                        </div>
                      )}
                      <div className={`text-xs mt-1 ${
                        message.role === 'user' 
                          ? isDarkMode ? 'text-black/70' : 'text-white/70'
                          : isDarkMode ? 'text-gray-400' : 'text-gray-500'
                      }`}>
                        {formatTimestamp(message.timestamp)}
                      </div>
                    </div>
                    
                    {/* Diagram (if present) */}
                    {message.diagram && (
                      <div className="w-full">
                        <DiagramRenderer
                          type={message.diagram.type}
                          content={message.diagram.content}
                          documents={documents}
                          onNodeClick={handleDiagramNodeClick}
                          isDarkMode={isDarkMode}
                          onExpand={onDiagramExpand}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isProcessing && (
                <AdvancedTypingIndicator 
                  isDarkMode={isDarkMode} 
                  userName="JAVI" 
                />
              )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Section - Positioned at bottom with no whitespace */}
        <div className={`border-t p-4 mt-auto ${
          isDarkMode 
            ? 'border-gray-600/60 bg-gray-800/30' 
            : 'border-gray-200/60 bg-white/30'
        }`}>
          <form onSubmit={handleSubmit} className="relative">
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedDocument ? `Ask about ${selectedDocument.path.split('/').pop()?.replace(/\.md$/, '') || 'document'}...` : "Ask about your docs..."}
                disabled={isProcessing || isLoading}
                className={`w-full pl-4 pr-12 py-3 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm border focus:outline-none focus:ring-1 ${
                  isDarkMode 
                    ? 'bg-gray-700/80 border-gray-600/60 text-white placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500' 
                    : 'bg-white/80 border-gray-300/60 text-gray-900 placeholder-gray-500 focus:ring-blue-500 focus:border-blue-500'
                }`}
              />
              <button
                type="submit"
                disabled={!input.trim() || isProcessing || isLoading}
                className={`absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center hover:scale-110 transform ${
                  isDarkMode 
                    ? 'bg-white text-black hover:bg-gray-200 disabled:hover:scale-100' 
                    : 'bg-black text-white hover:bg-gray-800 disabled:hover:scale-100'
                }`}
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}