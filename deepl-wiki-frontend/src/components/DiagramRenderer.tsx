'use client';

import React, { useEffect, useState } from 'react';
import mermaid from 'mermaid';
import { ReactFlow, Background, Controls, Node, Edge, Position, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { WikiDocument } from './WikiBrowser';
import { Network, GitBranch, FileText, Folder, ExternalLink, Copy, Download, X } from 'lucide-react';

interface DiagramRendererProps {
  type: 'mermaid' | 'network' | 'wizard';
  content?: string;
  documents?: WikiDocument[];
  onNodeClick?: (nodeId: string, document?: WikiDocument) => void;
  isDarkMode?: boolean;
  onExpand?: (diagramData: { type: 'mermaid' | 'network' | 'wizard'; content?: string; svg?: string; nodes?: Node[]; edges?: Edge[] }) => void;
}

// Initialize Mermaid with chat-friendly settings
mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  themeVariables: {
    primaryColor: '#8B5CF6',
    primaryTextColor: '#1F2937',
    primaryBorderColor: '#8B5CF6',
    lineColor: '#6B7280',
    sectionBkgColor: '#F9FAFB',
    altSectionBkgColor: '#F3F4F6',
    gridColor: '#E5E7EB',
    secondaryColor: '#F59E0B',
    tertiaryColor: '#10B981',
  },
  flowchart: {
    useMaxWidth: true,
    htmlLabels: true,
    curve: 'basis',
  },
  gitGraph: {
    mainBranchName: 'main',
    showCommitLabel: true,
  },
});

const nodeTypes = {
  repo: ({ data }: { data: { label: string; fileCount: number } }) => (
    <div className="px-3 py-2 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg border border-purple-400 shadow-sm min-w-[80px]">
      <div className="flex items-center gap-2">
        <GitBranch className="w-3 h-3 text-white" />
        <span className="text-white font-medium text-xs">{data.label}</span>
      </div>
      <div className="text-xs text-white/70">{data.fileCount} files</div>
    </div>
  ),
  folder: ({ data }: { data: { label: string; fileCount: number } }) => (
    <div className="px-2 py-1 bg-gradient-to-br from-orange-400 to-orange-500 rounded border border-orange-300 shadow-sm min-w-[60px]">
      <div className="flex items-center gap-1">
        <Folder className="w-2 h-2 text-white" />
        <span className="text-white font-medium text-xs">{data.label}</span>
      </div>
      <div className="text-xs text-white/70">{data.fileCount}</div>
    </div>
  ),
  file: ({ data }: { data: { label: string; hasConnections: boolean; connectionCount: number } }) => (
    <div className="px-2 py-1 bg-gradient-to-br from-green-400 to-green-500 rounded border border-green-300 shadow-sm min-w-[50px]">
      <div className="flex items-center gap-1">
        <FileText className="w-2 h-2 text-white" />
        <span className="text-white font-medium text-xs truncate">{data.label}</span>
      </div>
      {data.hasConnections && (
        <div className="text-xs text-white/70 flex items-center gap-1">
          <ExternalLink className="w-1 h-1" />
          {data.connectionCount}
        </div>
      )}
    </div>
  ),
};

export default function DiagramRenderer({ type, content, documents = [], onNodeClick, isDarkMode = false, onExpand }: DiagramRendererProps) {
  const [mermaidSvg, setMermaidSvg] = useState<string>('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [diagramId] = useState(() => `diagram-${Math.random().toString(36).substr(2, 9)}`);

  // Generate network diagram data from documents
  const generateNetworkDiagram = () => {
    if (!documents || documents.length === 0) return { nodes: [], edges: [] };

    const repoMap = new Map<string, { files: WikiDocument[], folders: Set<string> }>();

    // Group documents by repository
    documents.forEach(doc => {
      const pathParts = doc.path.split('/');
      const repoName = pathParts[0] || 'root';
      
      if (!repoMap.has(repoName)) {
        repoMap.set(repoName, { files: [], folders: new Set() });
      }
      
      const repo = repoMap.get(repoName)!;
      repo.files.push(doc);
      
      // Track folders
      for (let i = 1; i < pathParts.length - 1; i++) {
        const folderPath = pathParts.slice(0, i + 1).join('/');
        repo.folders.add(folderPath);
      }
    });

    const processedNodes: Node[] = [];
    const processedEdges: Edge[] = [];
    let yOffset = 0;

    repoMap.forEach((repoData, repoName) => {
      const repoId = `repo-${repoName}`;
      const xOffset = 0;
      
      // Create compact repo node
      processedNodes.push({
        id: repoId,
        type: 'repo',
        position: { x: xOffset, y: yOffset },
        data: { 
          label: repoName, 
          fileCount: repoData.files.length,
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });

      // Create compact file nodes (skip folders for simplicity in chat)
      repoData.files.slice(0, 8).forEach((doc, fileIndex) => { // Limit to 8 files for chat view
        const fileId = `file-${doc.path}`;
        const fileName = doc.path.split('/').pop() || 'unknown';
        
        // Find connections in document content
        const connections = documents.filter(otherDoc => 
          otherDoc.path !== doc.path && 
          (doc.content.includes(otherDoc.path) || doc.content.includes(otherDoc.path.split('/').pop() || ''))
        );

        processedNodes.push({
          id: fileId,
          type: 'file',
          position: { 
            x: xOffset + 120 + (fileIndex % 4) * 80, 
            y: yOffset + Math.floor(fileIndex / 4) * 40
          },
          data: { 
            label: fileName.length > 10 ? fileName.substring(0, 10) + '...' : fileName, 
            hasConnections: connections.length > 0,
            connectionCount: connections.length,
            document: doc
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        });

        // Connect repo to file
        processedEdges.push({
          id: `${repoId}-${fileId}`,
          source: repoId,
          target: fileId,
          type: 'smoothstep',
          animated: false,
          style: { stroke: '#8B5CF6', strokeWidth: 1 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#8B5CF6' },
        });

        // Create connections between files (limited for clarity)
        connections.slice(0, 2).forEach(connectedDoc => {
          const connectedFileId = `file-${connectedDoc.path}`;
          if (processedNodes.some(n => n.id === connectedFileId)) {
            processedEdges.push({
              id: `connection-${fileId}-${connectedFileId}`,
              source: fileId,
              target: connectedFileId,
              type: 'straight',
              animated: true,
              style: { stroke: '#EC4899', strokeWidth: 1, strokeDasharray: '3,3' },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#EC4899' },
            });
          }
        });
      });

      yOffset += 120;
    });

    return { nodes: processedNodes, edges: processedEdges };
  };

  // Generate Mermaid diagram for repository structure
  const generateMermaidDiagram = () => {
    if (!documents || documents.length === 0) {
      return `graph TD
        A[No Documents Available] --> B[Load documents to see structure]
        style A fill:#f9f,stroke:#333,stroke-width:2px
        style B fill:#bbf,stroke:#333,stroke-width:2px`;
    }

    const repoMap = new Map<string, WikiDocument[]>();
    documents.forEach(doc => {
      const repoName = doc.path.split('/')[0] || 'root';
      if (!repoMap.has(repoName)) {
        repoMap.set(repoName, []);
      }
      repoMap.get(repoName)!.push(doc);
    });

    let diagram = 'graph TD\n';
    let nodeCounter = 0;
    const nodeMap = new Map<string, string>();

    repoMap.forEach((files, repoName) => {
      const repoNodeId = `R${nodeCounter++}`;
      nodeMap.set(repoName, repoNodeId);
      diagram += `    ${repoNodeId}["🗂️ ${repoName}<br/>${files.length} files"]\n`;
      
      // Group files by folder
      const folderMap = new Map<string, WikiDocument[]>();
      files.forEach(file => {
        const pathParts = file.path.split('/');
        if (pathParts.length > 1) {
          const folderName = pathParts[1] || 'root';
          if (!folderMap.has(folderName)) {
            folderMap.set(folderName, []);
          }
          folderMap.get(folderName)!.push(file);
        }
      });

      // Add folders and files (limit for readability)
      let folderCount = 0;
      folderMap.forEach((folderFiles, folderName) => {
        if (folderCount >= 3) return; // Limit folders for chat view
        
        const folderNodeId = `F${nodeCounter++}`;
        diagram += `    ${folderNodeId}["📁 ${folderName}<br/>${folderFiles.length} files"]\n`;
        diagram += `    ${repoNodeId} --> ${folderNodeId}\n`;
        
        // Add a few representative files
        folderFiles.slice(0, 3).forEach(file => {
          const fileName = file.path.split('/').pop() || 'unknown';
          const fileNodeId = `File${nodeCounter++}`;
          const fileIcon = fileName.endsWith('.md') ? '📄' : fileName.endsWith('.js') || fileName.endsWith('.ts') ? '📜' : '📋';
          diagram += `    ${fileNodeId}["${fileIcon} ${fileName}"]\n`;
          diagram += `    ${folderNodeId} --> ${fileNodeId}\n`;
        });
        
        folderCount++;
      });
    });

    // Add styling
    diagram += `
    classDef repoClass fill:#8B5CF6,stroke:#333,stroke-width:2px,color:#fff;
    classDef folderClass fill:#F59E0B,stroke:#333,stroke-width:2px,color:#fff;
    classDef fileClass fill:#10B981,stroke:#333,stroke-width:2px,color:#fff;
    `;

    return diagram;
  };

  // Generate wizard-style step diagram
  const generateWizardDiagram = () => {
    return `graph LR
    A["🎯 Start<br/>Repository Analysis"] --> B["📊 Scan Documents<br/>${documents.length} files found"]
    B --> C["🔍 Analyze Structure<br/>Detect patterns"]
    C --> D["🌐 Map Connections<br/>Find relationships"]
    D --> E["📈 Generate Insights<br/>Create visualizations"]
    E --> F["✅ Complete<br/>Ready for exploration"]
    
    style A fill:#8B5CF6,stroke:#333,stroke-width:2px,color:#fff
    style B fill:#F59E0B,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#10B981,stroke:#333,stroke-width:2px,color:#fff
    style D fill:#EC4899,stroke:#333,stroke-width:2px,color:#fff
    style E fill:#3B82F6,stroke:#333,stroke-width:2px,color:#fff
    style F fill:#059669,stroke:#333,stroke-width:2px,color:#fff`;
  };

  useEffect(() => {
    const renderDiagram = async () => {
      if (type === 'mermaid') {
        try {
          setIsLoading(true);
          const diagramContent = content || generateMermaidDiagram();
          
          const { svg } = await mermaid.render(`${diagramId}-mermaid`, diagramContent);
          setMermaidSvg(svg);
        } catch (error) {
          console.error('Error rendering Mermaid diagram:', error);
          setMermaidSvg(`<div class="flex items-center justify-center h-32 text-gray-500"><p>Failed to render diagram</p></div>`);
        } finally {
          setIsLoading(false);
        }
      } else if (type === 'wizard') {
        try {
          setIsLoading(true);
          const wizardContent = generateWizardDiagram();
          
          const { svg } = await mermaid.render(`${diagramId}-wizard`, wizardContent);
          setMermaidSvg(svg);
        } catch (error) {
          console.error('Error rendering wizard diagram:', error);
          setMermaidSvg(`<div class="flex items-center justify-center h-32 text-gray-500"><p>Failed to render diagram</p></div>`);
        } finally {
          setIsLoading(false);
        }
      } else if (type === 'network') {
        try {
          setIsLoading(true);
          const { nodes: networkNodes, edges: networkEdges } = generateNetworkDiagram();
          setNodes(networkNodes);
          setEdges(networkEdges);
        } catch (error) {
          console.error('Error generating network diagram:', error);
          setNodes([]);
          setEdges([]);
        } finally {
          setIsLoading(false);
        }
      }
    };

    renderDiagram();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, content, documents, diagramId]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isExpanded) {
        setIsExpanded(false);
      }
    };

    if (isExpanded) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scroll when expanded
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isExpanded]);

  const handleCopyDiagram = () => {
    if (type === 'mermaid' || type === 'wizard') {
      const diagramText = type === 'mermaid' ? (content || generateMermaidDiagram()) : generateWizardDiagram();
      navigator.clipboard.writeText(diagramText);
    }
  };

  const handleDownloadDiagram = () => {
    if (type === 'mermaid' || type === 'wizard') {
      const blob = new Blob([mermaidSvg], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}-diagram.svg`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleNodeClick = (event: React.MouseEvent, node: Node) => {
    if (onNodeClick && node.data.document) {
      onNodeClick(node.id, node.data.document);
    }
  };

  return (
    <>
      {/* Full-screen backdrop */}
      {isExpanded && (
        <div className="fixed inset-0 bg-black/80 z-50">
          <div className={`w-screen h-screen overflow-hidden relative ${
            isDarkMode 
              ? 'bg-gray-900' 
              : 'bg-white'
          }`}>
            {/* Full-screen header */}
            <div className={`absolute top-0 left-0 right-0 z-10 flex items-center justify-between backdrop-blur-xl border-b px-6 py-4 ${
              isDarkMode 
                ? 'bg-gray-900/95 border-gray-600' 
                : 'bg-white/95 border-gray-200'
            }`}>
              <div className="flex items-center gap-3">
                <Network className={`w-5 h-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
                <span className={`font-semibold text-lg ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  {type === 'mermaid' ? 'Repository Structure' : 
                   type === 'wizard' ? 'Analysis Workflow' : 
                   'Network Diagram'}
                </span>
                {type === 'network' && (
                  <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {nodes.length} nodes • {edges.length} connections
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyDiagram}
                  className={`p-2 rounded-lg transition-colors ${
                    isDarkMode 
                      ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                      : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                  }`}
                  title="Copy diagram"
                >
                  <Copy className="w-5 h-5" />
                </button>
                <button
                  onClick={handleDownloadDiagram}
                  className={`p-2 rounded-lg transition-colors ${
                    isDarkMode 
                      ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                      : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                  }`}
                  title="Download diagram"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setIsExpanded(false)}
                  className={`p-2 rounded-lg transition-colors ${
                    isDarkMode 
                      ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                      : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                  }`}
                  title="Exit full screen"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Full-screen diagram content */}
            <div className="w-screen h-screen pt-20 relative">
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-20">
                  <div className={`flex items-center gap-3 px-4 py-2 rounded-lg ${
                    isDarkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'
                  }`}>
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span>Loading diagram...</span>
                  </div>
                </div>
              )}
              
              {(type === 'mermaid' || type === 'wizard') && (
                <div 
                  className={`w-full h-full overflow-auto flex items-center justify-center ${
                    isDarkMode ? 'bg-gray-900' : 'bg-white'
                  }`}
                  dangerouslySetInnerHTML={{ __html: mermaidSvg }}
                />
              )}
              
              {type === 'network' && (
                <div className="w-full h-full">
                  <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodeClick={handleNodeClick}
                    nodeTypes={nodeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.05 }}
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
          </div>
        </div>
      )}

      {/* Regular embedded view */}
      <div 
        className={`border rounded-lg overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-sm ${
          isDarkMode 
            ? 'bg-gray-800 border-gray-600 hover:border-gray-500' 
            : 'bg-white border-gray-200 hover:border-gray-300'
        } ${isExpanded ? 'hidden' : 'w-full'}`}
        onClick={() => {
          if (onExpand) {
            onExpand({
              type,
              content: type === 'mermaid' ? (content || generateMermaidDiagram()) : type === 'wizard' ? generateWizardDiagram() : content,
              svg: mermaidSvg,
              nodes,
              edges
            });
          } else {
            setIsExpanded(true);
          }
        }}
      >
        {/* Header */}
        <div className={`flex items-center justify-between p-3 border-b transition-colors duration-200 ${
          isDarkMode 
            ? 'border-gray-600 bg-gray-700' 
            : 'border-gray-200 bg-gray-50'
        }`}>
          <div className="flex items-center gap-2">
            <Network className={`w-4 h-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
            <span className={`font-medium text-sm ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              {type === 'mermaid' ? 'Repository Structure' : 
               type === 'wizard' ? 'Analysis Workflow' : 
               'Network Diagram'}
            </span>
            {type === 'network' && (
              <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {nodes.length} nodes • {edges.length} connections
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleCopyDiagram();
              }}
              className={`p-1 rounded transition-colors ${
                isDarkMode 
                  ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}
              title="Copy diagram"
            >
              <Copy className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDownloadDiagram();
              }}
              className={`p-1 rounded transition-colors ${
                isDarkMode 
                  ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}
              title="Download diagram"
            >
              <Download className="w-3 h-3" />
            </button>
            <span className={`text-xs px-2 py-1 rounded ${
              isDarkMode 
                ? 'text-blue-400 bg-blue-900/30' 
                : 'text-blue-600 bg-blue-50'
            }`}>
              Click to expand
            </span>
          </div>
        </div>

        {/* Diagram Content */}
        <div className="h-64 relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/10 z-10">
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-900'
              } shadow-sm`}>
                <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm">Loading...</span>
              </div>
            </div>
          )}
          
          {(type === 'mermaid' || type === 'wizard') && (
            <div 
              className={`w-full h-full p-4 overflow-auto flex items-center justify-center ${
                isDarkMode ? 'bg-gray-800' : 'bg-white'
              }`}
              dangerouslySetInnerHTML={{ __html: mermaidSvg }}
            />
          )}
          
          {type === 'network' && (
            <div className="w-full h-full">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodeClick={handleNodeClick}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.1 }}
                className={isDarkMode ? 'bg-gray-800' : 'bg-white'}
                proOptions={{ hideAttribution: true }}
              >
                <Background 
                  color={isDarkMode ? '#374151' : '#e5e7eb'} 
                  gap={16} 
                  size={1} 
                />
                <Controls className={`rounded ${
                  isDarkMode 
                    ? 'bg-gray-700 border border-gray-600 [&>button]:text-gray-300 [&>button]:border-gray-600 [&>button:hover]:bg-gray-600' 
                    : 'bg-white border border-gray-300 [&>button]:text-gray-600 [&>button]:border-gray-300 [&>button:hover]:bg-gray-100'
                }`} />
              </ReactFlow>
            </div>
          )}
        </div>
      </div>
    </>
  );
}