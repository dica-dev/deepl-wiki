'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState,
  Edge,
  Node,
  Position,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { WikiDocument } from './WikiBrowser';
import { Network, GitBranch, FileText, Folder, ExternalLink, Download, Zap } from 'lucide-react';

interface DiagramVisualizationProps {
  documents: WikiDocument[];
  onNodeClick?: (nodeId: string, document?: WikiDocument) => void;
}


const nodeTypes = {
  repo: ({ data }: { data: { label: string; fileCount: number } }) => (
    <div className="px-4 py-3 bg-gradient-to-br from-llama-purple to-llama-blue rounded-xl border border-llama-purple/30 shadow-lg min-w-[120px]">
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4 text-white" />
        <span className="text-white font-semibold text-sm">{data.label}</span>
      </div>
      <div className="text-xs text-white/70 mt-1">{data.fileCount} files</div>
    </div>
  ),
  folder: ({ data }: { data: { label: string; fileCount: number } }) => (
    <div className="px-3 py-2 bg-gradient-to-br from-llama-accent to-llama-accent-light rounded-lg border border-llama-accent/30 shadow-md min-w-[100px]">
      <div className="flex items-center gap-2">
        <Folder className="w-3 h-3 text-white" />
        <span className="text-white font-medium text-xs">{data.label}</span>
      </div>
      <div className="text-xs text-white/70">{data.fileCount} files</div>
    </div>
  ),
  file: ({ data }: { data: { label: string; hasConnections: boolean; connectionCount: number } }) => (
    <div className="px-3 py-2 bg-gradient-to-br from-llama-green to-llama-green-light rounded-lg border border-llama-green/30 shadow-sm min-w-[80px]">
      <div className="flex items-center gap-2">
        <FileText className="w-3 h-3 text-white" />
        <span className="text-white font-medium text-xs truncate">{data.label}</span>
      </div>
      {data.hasConnections && (
        <div className="text-xs text-white/70 flex items-center gap-1">
          <ExternalLink className="w-2 h-2" />
          {data.connectionCount}
        </div>
      )}
    </div>
  ),
};

export default function DiagramVisualization({ documents, onNodeClick }: DiagramVisualizationProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedLayout, setSelectedLayout] = useState<'hierarchy' | 'force' | 'circular'>('hierarchy');
  const [showMiniMap, setShowMiniMap] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const processDocuments = useCallback(() => {
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

    // Create nodes and edges
    const processedNodes: Node[] = [];
    const processedEdges: Edge[] = [];
    let yOffset = 0;

    repoMap.forEach((repoData, repoName) => {
      const repoId = `repo-${repoName}`;
      const xOffset = 0;
      
      // Create repo node
      processedNodes.push({
        id: repoId,
        type: 'repo',
        position: { x: xOffset, y: yOffset },
        data: { 
          label: repoName, 
          fileCount: repoData.files.length,
          type: 'repo'
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });

      // Create folder nodes
      const folderNodes = Array.from(repoData.folders).map((folderPath, index) => {
        const folderId = `folder-${folderPath}`;
        const folderName = folderPath.split('/').pop() || 'unknown';
        const folderFiles = repoData.files.filter(f => f.path.startsWith(folderPath + '/'));
        
        processedNodes.push({
          id: folderId,
          type: 'folder',
          position: { x: xOffset + 200, y: yOffset + (index * 80) },
          data: { 
            label: folderName, 
            fileCount: folderFiles.length,
            type: 'folder',
            path: folderPath
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        });

        // Connect repo to folder
        processedEdges.push({
          id: `${repoId}-${folderId}`,
          source: repoId,
          target: folderId,
          type: 'smoothstep',
          animated: false,
          style: { stroke: '#8B5CF6', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#8B5CF6' },
        });

        return { folderId, folderPath, folderFiles };
      });

      // Create file nodes
      repoData.files.forEach((doc, fileIndex) => {
        const fileId = `file-${doc.path}`;
        const fileName = doc.path.split('/').pop() || 'unknown';
        const parentFolder = folderNodes.find(f => doc.path.startsWith(f.folderPath + '/'));
        
        // Find connections in document content
        const connections = documents.filter(otherDoc => 
          otherDoc.path !== doc.path && 
          (doc.content.includes(otherDoc.path) || doc.content.includes(otherDoc.path.split('/').pop() || ''))
        );

        processedNodes.push({
          id: fileId,
          type: 'file',
          position: { 
            x: xOffset + (parentFolder ? 400 : 200), 
            y: yOffset + (fileIndex * 60) + (parentFolder ? folderNodes.indexOf(parentFolder) * 80 : 0)
          },
          data: { 
            label: fileName, 
            hasConnections: connections.length > 0,
            connectionCount: connections.length,
            type: 'file',
            path: doc.path,
            document: doc
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        });

        // Connect folder to file or repo to file
        const sourceId = parentFolder ? parentFolder.folderId : repoId;
        processedEdges.push({
          id: `${sourceId}-${fileId}`,
          source: sourceId,
          target: fileId,
          type: 'smoothstep',
          animated: false,
          style: { stroke: parentFolder ? '#10B981' : '#F59E0B', strokeWidth: 1 },
          markerEnd: { type: MarkerType.ArrowClosed, color: parentFolder ? '#10B981' : '#F59E0B' },
        });

        // Create connections between files
        connections.forEach(connectedDoc => {
          const connectedFileId = `file-${connectedDoc.path}`;
          if (processedNodes.some(n => n.id === connectedFileId)) {
            processedEdges.push({
              id: `connection-${fileId}-${connectedFileId}`,
              source: fileId,
              target: connectedFileId,
              type: 'straight',
              animated: true,
              style: { stroke: '#EC4899', strokeWidth: 1, strokeDasharray: '5,5' },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#EC4899' },
            });
          }
        });
      });

      yOffset += Math.max(200, repoData.files.length * 60 + Array.from(repoData.folders).length * 80);
    });

    return { nodes: processedNodes, edges: processedEdges };
  }, [documents]);

  const applyLayout = useCallback((nodes: Node[], edges: Edge[], layout: string) => {
    if (layout === 'circular') {
      const center = { x: 400, y: 300 };
      const radius = 200;
      const angle = (2 * Math.PI) / nodes.length;
      
      return nodes.map((node, index) => ({
        ...node,
        position: {
          x: center.x + radius * Math.cos(index * angle),
          y: center.y + radius * Math.sin(index * angle),
        },
      }));
    } else if (layout === 'force') {
      // Simple force-directed layout simulation
      const centerX = 400;
      const centerY = 300;
      const spread = 100;
      
      return nodes.map((node) => ({
        ...node,
        position: {
          x: centerX + (Math.random() - 0.5) * spread * 4,
          y: centerY + (Math.random() - 0.5) * spread * 4,
        },
      }));
    }
    
    return nodes; // Keep hierarchy layout as default
  }, []);

  useEffect(() => {
    if (!documents || documents.length === 0) return;

    setIsLoading(true);
    const { nodes: newNodes, edges: newEdges } = processDocuments();
    const layoutNodes = applyLayout(newNodes, newEdges, selectedLayout);
    
    setNodes(layoutNodes);
    setEdges(newEdges);
    setIsLoading(false);
  }, [documents, selectedLayout, processDocuments, applyLayout, setNodes, setEdges]);

  const onNodeClickHandler = useCallback((event: React.MouseEvent, node: Node) => {
    if (onNodeClick) {
      onNodeClick(node.id, node.data.document);
    }
  }, [onNodeClick]);

  const onConnect = useCallback(() => {
    // Optional: handle manual connections
  }, []);

  const downloadDiagram = useCallback(() => {
    // Simple download functionality - in a real app, you'd use a library like html2canvas
    const diagramData = {
      nodes: nodes.map(n => ({ id: n.id, type: n.type, data: n.data, position: n.position })),
      edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target, type: e.type })),
      layout: selectedLayout,
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(diagramData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'repository-diagram.json';
    a.click();
    URL.revokeObjectURL(url);
  }, [nodes, edges, selectedLayout]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-llama-purple border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-text-secondary">Generating diagram...</p>
        </div>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Network className="w-16 h-16 text-text-tertiary mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-text-primary mb-2">No Data Available</h3>
          <p className="text-text-secondary">Load some documents to see the repository diagram</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative bg-gray-50 rounded-xl overflow-hidden border border-gray-200">
      {/* Compact Controls Header */}
      <div className="absolute top-2 left-2 right-2 z-10 flex items-center justify-between bg-white/95 backdrop-blur-xl border border-gray-200 rounded-lg p-2 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <Network className="w-4 h-4 text-llama-purple" />
            <span className="font-semibold text-gray-900 text-sm">Network</span>
          </div>
          <div className="text-xs text-gray-500">
            {nodes.length} nodes • {edges.length} connections
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Compact Layout Selector */}
          <select
            value={selectedLayout}
            onChange={(e) => setSelectedLayout(e.target.value as 'hierarchy' | 'force' | 'circular')}
            className="text-xs bg-white border border-gray-200 rounded px-2 py-1 text-gray-700 focus:outline-none focus:ring-1 focus:ring-llama-purple"
          >
            <option value="hierarchy">Hierarchy</option>
            <option value="force">Force</option>
            <option value="circular">Circular</option>
          </select>

          {/* Compact Controls */}
          <button
            onClick={() => setShowMiniMap(!showMiniMap)}
            className={`p-1 rounded transition-colors ${
              showMiniMap ? 'bg-llama-purple/10 text-llama-purple' : 'bg-gray-100 text-gray-400'
            }`}
            title="Toggle minimap"
          >
            <Zap className="w-3 h-3" />
          </button>

          <button
            onClick={downloadDiagram}
            className="p-1 bg-gray-100 text-gray-400 rounded hover:bg-gray-200 transition-colors"
            title="Download diagram data"
          >
            <Download className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* React Flow Diagram */}
      <div className="h-full w-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClickHandler}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          className="bg-bg-primary"
          proOptions={{ hideAttribution: true }}
        >
          <Background 
            color="#8B5CF6" 
            gap={16} 
            size={1} 
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            variant={'dots' as any} 
          />
          <Controls 
            className="bg-bg-secondary/90 border border-border-primary rounded-lg"
            showInteractive={false}
          />
          {showMiniMap && (
            <MiniMap
              className="bg-bg-secondary/90 border border-border-primary rounded-lg"
              nodeColor={(node: { type?: string }) => {
                switch (node.type) {
                  case 'repo': return '#8B5CF6';
                  case 'folder': return '#F59E0B';
                  case 'file': return '#10B981';
                  default: return '#6B7280';
                }
              }}
              maskColor="rgba(0, 0, 0, 0.1)"
              pannable
              zoomable
            />
          )}
        </ReactFlow>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-bg-secondary/90 backdrop-blur-xl border border-border-primary rounded-xl p-3 z-10">
        <div className="text-xs font-semibold text-text-primary mb-2">Legend</div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gradient-to-br from-llama-purple to-llama-blue rounded"></div>
            <span className="text-xs text-text-secondary">Repository</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gradient-to-br from-llama-accent to-llama-accent-light rounded"></div>
            <span className="text-xs text-text-secondary">Folder</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gradient-to-br from-llama-green to-llama-green-light rounded"></div>
            <span className="text-xs text-text-secondary">File</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-llama-pink" style={{background: 'linear-gradient(to right, #EC4899 0%, #EC4899 50%, transparent 50%, transparent 100%)', backgroundSize: '6px 1px'}}></div>
            <span className="text-xs text-text-secondary">Reference</span>
          </div>
        </div>
      </div>
    </div>
  );
}