'use client';

import React, { useState, useMemo } from 'react';
import { Search, FileText, Folder, Clock, ExternalLink, ChevronRight, ChevronDown, BookOpen, Hash } from 'lucide-react';

export interface WikiDocument {
  path: string;
  content: string;
  lastModified: string;
  sha: string;
}

interface WikiBrowserProps {
  documents: WikiDocument[];
  onDocumentSelect?: (document: WikiDocument) => void;
  selectedDocument?: WikiDocument | null;
}

export default function WikiBrowser({ 
  documents, 
  onDocumentSelect,
  selectedDocument 
}: WikiBrowserProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  // Filter and organize documents
  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => 
      doc.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.content.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [documents, searchTerm]);

  // Organize documents by folder structure
  const documentTree = useMemo(() => {
    const tree: { [key: string]: WikiDocument[] } = {};
    
    filteredDocuments.forEach(doc => {
      const pathParts = doc.path.split('/');
      const folder = pathParts.length > 1 ? pathParts.slice(0, -1).join('/') : 'Root';
      
      if (!tree[folder]) {
        tree[folder] = [];
      }
      tree[folder].push(doc);
    });

    return tree;
  }, [filteredDocuments]);

  const toggleFolder = (folder: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folder)) {
      newExpanded.delete(folder);
    } else {
      newExpanded.add(folder);
    }
    setExpandedFolders(newExpanded);
  };

  const getFileName = (path: string) => {
    return path.split('/').pop() || path;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const renderMarkdown = (content: string) => {
    // Simple markdown rendering - in production you'd want a proper markdown parser
    return content
      .split('\n')
      .map((line, index) => {
        if (line.startsWith('# ')) {
          return <h1 key={index} className="text-2xl font-bold mb-4 text-white">{line.substring(2)}</h1>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={index} className="text-xl font-semibold mb-3 text-gray-100">{line.substring(3)}</h2>;
        }
        if (line.startsWith('### ')) {
          return <h3 key={index} className="text-lg font-medium mb-2 text-gray-200">{line.substring(4)}</h3>;
        }
        if (line.startsWith('- ')) {
          return <li key={index} className="ml-4 mb-1 text-gray-300">{line.substring(2)}</li>;
        }
        if (line.trim() === '') {
          return <br key={index} />;
        }
        return <p key={index} className="mb-2 text-gray-300">{line}</p>;
      });
  };

  return (
    <div className="flex h-full bg-bg-secondary/50 backdrop-blur-xl rounded-3xl overflow-hidden">
      {/* Sophisticated Sidebar */}
      <div className="w-96 border-r border-border-primary/50 flex flex-col bg-bg-tertiary/30">
        {/* Enhanced Search Header */}
        <div className="p-6 border-b border-border-primary/50">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-text-tertiary w-5 h-5 group-focus-within:text-llama-purple transition-colors" />
            <input
              type="text"
              placeholder="Search through your documentation..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-bg-secondary border border-border-primary rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple focus:glow-purple transition-all duration-300 font-medium"
            />
            {searchTerm && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs bg-llama-purple text-white px-2 py-1 rounded-md">
                {filteredDocuments.length}
              </div>
            )}
          </div>
        </div>

        {/* Document Tree */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {Object.entries(documentTree).map(([folder, docs]) => (
            <div key={folder} className="group">
              <button
                onClick={() => toggleFolder(folder)}
                className="flex items-center gap-3 w-full p-3 text-left hover:bg-bg-hover rounded-xl transition-all duration-200 group"
              >
                <div className="flex items-center gap-2 flex-1">
                  {expandedFolders.has(folder) ? (
                    <ChevronDown className="w-4 h-4 text-llama-purple" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-text-tertiary group-hover:text-llama-purple transition-colors" />
                  )}
                  <Folder className="w-5 h-5 text-llama-blue" />
                  <span className="font-bold text-text-primary">{folder}</span>
                </div>
                <div className="bg-llama-accent/20 text-llama-accent px-2 py-1 rounded-full text-xs font-semibold">
                  {docs.length}
                </div>
              </button>
              
              {expandedFolders.has(folder) && (
                <div className="ml-6 mt-2 space-y-1 border-l border-border-primary/30 pl-4">
                  {docs.map((doc) => (
                    <button
                      key={doc.path}
                      onClick={() => onDocumentSelect?.(doc)}
                      className={`group flex items-center gap-3 w-full p-3 text-left rounded-xl transition-all duration-200 ${
                        selectedDocument?.path === doc.path
                          ? 'bg-gradient-to-r from-llama-purple/20 to-llama-accent/20 border border-llama-purple/30 glow-purple'
                          : 'hover:bg-bg-hover'
                      }`}
                    >
                      <FileText className={`w-4 h-4 ${
                        selectedDocument?.path === doc.path ? 'text-llama-purple' : 'text-text-tertiary group-hover:text-llama-blue'
                      } transition-colors`} />
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm font-semibold truncate ${
                          selectedDocument?.path === doc.path ? 'text-llama-purple' : 'text-text-primary'
                        }`}>
                          {getFileName(doc.path)}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-text-tertiary mt-1">
                          <Clock className="w-3 h-3" />
                          {formatDate(doc.lastModified)}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {selectedDocument ? (
          <>
            {/* Sophisticated Header */}
            <div className="p-6 border-b border-border-primary/50 bg-bg-secondary/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-llama-purple to-llama-blue rounded-xl flex items-center justify-center shadow-lg">
                    <BookOpen className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-black text-text-primary mb-1">
                      {getFileName(selectedDocument.path)}
                    </h1>
                    <div className="flex items-center gap-4 text-sm text-text-secondary">
                      <div className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        <span className="font-medium">{selectedDocument.path}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{formatDate(selectedDocument.lastModified)}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <button className="p-3 text-text-tertiary hover:text-llama-purple hover:bg-bg-hover rounded-xl transition-all duration-200 group">
                  <ExternalLink className="w-5 h-5 group-hover:scale-110 transition-transform" />
                </button>
              </div>
            </div>

            {/* Enhanced Document Content */}
            <div className="flex-1 overflow-y-auto p-8 relative">
              {/* Background gradient */}
              <div className="absolute inset-0 bg-gradient-to-b from-bg-primary/50 to-bg-secondary/50 pointer-events-none"></div>
              
              <div className="relative max-w-4xl mx-auto">
                <div className="prose prose-lg prose-invert max-w-none">
                  <div className="space-y-6">
                    {renderMarkdown(selectedDocument.content)}
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center relative">
            {/* Background pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="w-full h-full bg-gradient-to-br from-llama-purple/20 via-transparent to-llama-blue/20"></div>
            </div>
            
            <div className="text-center relative z-10">
              <div className="relative mb-8">
                <div className="w-24 h-24 bg-gradient-to-br from-llama-purple to-llama-blue rounded-2xl flex items-center justify-center mx-auto shadow-2xl animate-float">
                  <FileText className="w-12 h-12 text-white" />
                </div>
                <div className="absolute inset-0 w-24 h-24 bg-llama-purple rounded-2xl blur-xl opacity-30 mx-auto animate-pulse"></div>
              </div>
              <h2 className="text-3xl font-black text-text-primary mb-4 gradient-text">
                Select Documentation
              </h2>
              <p className="text-text-secondary text-lg font-medium max-w-md mx-auto leading-relaxed">
                Choose a document from the sidebar to explore your{' '}
                <span className="text-llama-accent font-bold">AI-enhanced</span> documentation
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}