'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Expand, Copy, Download } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
  isDarkMode?: boolean;
  onExpand?: (data: {
    type: 'mermaid';
    content: string;
    svg: string;
  }) => void;
}

// Initialize mermaid once globally
let mermaidInitialized = false;
let mermaidInstance: any = null;

const initializeMermaid = async () => {
  if (mermaidInitialized) return mermaidInstance;
  
  try {
    const mermaid = await import('mermaid');
    mermaidInstance = mermaid.default;
    
    mermaidInstance.initialize({
      startOnLoad: false,
      theme: 'base',
      securityLevel: 'loose',
      maxTextSize: 90000,
      maxEdges: 10000,
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
        nodeSpacing: 50,
        rankSpacing: 50
      },
      sequence: {
        useMaxWidth: true,
        diagramMarginX: 50,
        diagramMarginY: 10,
        boxTextMargin: 5,
        noteMargin: 10,
        messageMargin: 35
      },
      gantt: {
        useMaxWidth: true
      },
      journey: {
        useMaxWidth: true
      },
      gitGraph: {
        useMaxWidth: true
      }
    });
    
    mermaidInitialized = true;
    return mermaidInstance;
  } catch (error) {
    console.error('Failed to initialize Mermaid:', error);
    throw error;
  }
};

export default function MermaidDiagram({ chart, isDarkMode = false, onExpand }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isLoaded, setIsLoaded] = useState(false);
  const renderTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const renderDiagram = useCallback(async () => {
    if (!chart.trim()) return;

    try {
      setError('');
      setIsLoaded(false);

      const mermaid = await initializeMermaid();
      
      // Generate unique ID for this diagram
      const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      
      // Clean the chart text and validate syntax
      const cleanChart = chart.trim();
      
      // Count nodes/connections for timeout adjustment
      const nodeCount = (cleanChart.match(/-->/g) || []).length + (cleanChart.match(/---/g) || []).length;
      if (nodeCount > 200) {
        console.log(`Large diagram detected with ${nodeCount} connections. Using extended timeout.`);
      }
      
      // Basic syntax validation for common issues
      if (cleanChart.includes('<|--') && !cleanChart.startsWith('classDiagram')) {
        throw new Error('Class diagram syntax detected but missing "classDiagram" declaration');
      }
      
      // Render the diagram with timeout (much longer for complex diagrams)
      const timeoutMs = nodeCount > 500 ? 60000 : nodeCount > 200 ? 30000 : nodeCount > 100 ? 15000 : 10000;
      const renderPromise = mermaid.render(id, cleanChart);
      const timeoutPromise = new Promise((_, reject) => {
        renderTimeoutRef.current = setTimeout(() => reject(new Error(`Rendering timeout after ${timeoutMs/1000} seconds`)), timeoutMs);
      });
      
      const result = await Promise.race([renderPromise, timeoutPromise]) as { svg: string };
      
      if (renderTimeoutRef.current) {
        clearTimeout(renderTimeoutRef.current);
        renderTimeoutRef.current = null;
      }
      
      if (result && result.svg) {
        setSvg(result.svg);
        setIsLoaded(true);

        // Insert the SVG into the container
        if (ref.current) {
          ref.current.innerHTML = result.svg;
          
          // Style the SVG
          const svgElement = ref.current.querySelector('svg');
          if (svgElement) {
            svgElement.style.maxWidth = '100%';
            svgElement.style.height = 'auto';
            svgElement.style.display = 'block';
            
            // Apply theme-specific styling
            if (isDarkMode) {
              svgElement.style.filter = 'invert(0.9) hue-rotate(180deg)';
              svgElement.style.backgroundColor = 'transparent';
            } else {
              svgElement.style.filter = 'none';
              svgElement.style.backgroundColor = 'transparent';
            }
          }
        }
      } else {
        throw new Error('No SVG returned from Mermaid');
      }
    } catch (err) {
      console.error('Mermaid rendering error:', err);
      const errorMessage = (err as Error).message;
      
      // Provide more helpful error messages for common syntax issues
      let userFriendlyError = errorMessage;
      if (errorMessage.includes('Parse error') && errorMessage.includes('TAGSTART')) {
        userFriendlyError = 'Invalid diagram syntax. Check for missing diagram type declaration or incorrect arrow syntax.';
      } else if (errorMessage.includes('Parse error')) {
        userFriendlyError = 'Diagram syntax error. Please check the mermaid syntax.';
      } else if (errorMessage.includes('timeout')) {
        userFriendlyError = `Large diagram rendering timed out. Please wait and try again.`;
      }
      
      setError(userFriendlyError);
      setIsLoaded(true);
      
      if (renderTimeoutRef.current) {
        clearTimeout(renderTimeoutRef.current);
        renderTimeoutRef.current = null;
      }
    }
  }, [chart, isDarkMode, isLoaded]);

  useEffect(() => {
    // Debounce rendering to avoid rapid re-renders
    const timeoutId = setTimeout(() => {
      renderDiagram();
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      if (renderTimeoutRef.current) {
        clearTimeout(renderTimeoutRef.current);
        renderTimeoutRef.current = null;
      }
    };
  }, [renderDiagram]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(chart);
    } catch (err) {
      console.error('Failed to copy chart:', err);
    }
  };

  const handleDownload = () => {
    if (!svg) return;
    
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mermaid-diagram.svg';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExpand = () => {
    if (onExpand && svg) {
      onExpand({
        type: 'mermaid',
        content: chart,
        svg: svg
      });
    }
  };

  if (error) {
    return (
      <div className={`p-3 rounded-lg border text-sm ${
        isDarkMode 
          ? 'bg-red-900/20 border-red-700/50 text-red-300' 
          : 'bg-red-50 border-red-200 text-red-700'
      }`}>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="font-medium">Diagram Error</span>
        </div>
        <p className="text-xs opacity-90 mb-2">{error}</p>
        <div className="flex gap-2">
          <button
            onClick={() => renderDiagram()}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              isDarkMode 
                ? 'bg-red-800/50 hover:bg-red-800/70 text-red-200' 
                : 'bg-red-100 hover:bg-red-200 text-red-700'
            }`}
          >
            Retry
          </button>
          <button
            onClick={() => {
              if (ref.current) {
                ref.current.innerHTML = `<pre class="text-xs p-2 bg-gray-100 dark:bg-gray-800 rounded border overflow-x-auto"><code>${chart}</code></pre>`;
              }
            }}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              isDarkMode 
                ? 'bg-gray-700/50 hover:bg-gray-700/70 text-gray-300' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
            }`}
          >
            Show Source
          </button>
        </div>
      </div>
    );
  }


  if (!isLoaded) {
    const nodeCount = (chart.match(/-->/g) || []).length + (chart.match(/---/g) || []).length;
    const isLarge = nodeCount > 200;
    
    return (
      <div className={`flex flex-col items-center justify-center p-6 rounded-lg border min-h-[200px] ${
        isDarkMode 
          ? 'bg-gray-800/50 border-gray-600' 
          : 'bg-gray-50 border-gray-200'
      }`}>
        <div className="flex items-center gap-3 mb-2">
          <div className={`w-4 h-4 border-2 border-t-transparent rounded-full animate-spin ${
            isDarkMode ? 'border-blue-400' : 'border-blue-500'
          }`}></div>
          <span className={`text-sm font-medium ${
            isDarkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Rendering Diagram...
          </span>
        </div>
        {isLarge && (
          <p className={`text-xs text-center ${
            isDarkMode ? 'text-gray-500' : 'text-gray-500'
          }`}>
            Large diagram detected ({nodeCount} connections)<br/>
            This may take up to {nodeCount > 500 ? '60' : nodeCount > 200 ? '30' : '15'} seconds
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="group relative">
      {/* Diagram Container */}
      <div 
        ref={ref} 
        className={`mermaid-diagram overflow-auto max-w-full ${
          isDarkMode ? 'bg-gray-900' : 'bg-white'
        } rounded-lg p-4`}
        style={{ 
          minHeight: '200px',
          maxHeight: '80vh',
          scrollbarWidth: 'thin'
        }}
      />
      
      {/* Action Buttons */}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <div className={`flex items-center gap-1 rounded-lg p-1 ${
          isDarkMode 
            ? 'bg-gray-800/90 border border-gray-600' 
            : 'bg-white/90 border border-gray-300'
        } shadow-sm backdrop-blur-sm`}>
          <button
            onClick={handleCopy}
            className={`p-1.5 rounded transition-colors ${
              isDarkMode 
                ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
            title="Copy source"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            onClick={handleDownload}
            className={`p-1.5 rounded transition-colors ${
              isDarkMode 
                ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
            title="Download SVG"
          >
            <Download className="w-3 h-3" />
          </button>
          {onExpand && (
            <button
              onClick={handleExpand}
              className={`p-1.5 rounded transition-colors ${
                isDarkMode 
                  ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="Expand diagram"
            >
              <Expand className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}