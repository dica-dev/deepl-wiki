'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { List, ChevronDown, ChevronRight } from 'lucide-react';

interface TOCItem {
  id: string;
  text: string;
  level: number;
  element?: HTMLElement;
}

interface TableOfContentsProps {
  content: string;
  isDarkMode?: boolean;
  className?: string;
}

export default function TableOfContents({ 
  content, 
  isDarkMode = false,
  className = ""
}: TableOfContentsProps) {
  const [tocItems, setTocItems] = useState<TOCItem[]>([]);
  const [activeId, setActiveId] = useState<string>('');
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Extract headings from markdown content
  const extractTOC = useMemo(() => {
    const headingRegex = /^(#{1,6})\s+(.+)$/gm;
    const items: TOCItem[] = [];
    let match;

    while ((match = headingRegex.exec(content)) !== null) {
      const level = match[1].length;
      const text = match[2].trim();
      const id = text
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-')
        .trim();

      items.push({
        id,
        text,
        level,
      });
    }

    return items;
  }, [content]);

  useEffect(() => {
    setTocItems(extractTOC);
  }, [extractTOC]);

  // Set up intersection observer for scroll tracking
  useEffect(() => {
    if (tocItems.length === 0) return;

    const headingElements: HTMLElement[] = [];
    
    // Wait for DOM to be ready, then find heading elements
    const findHeadings = () => {
      tocItems.forEach((item) => {
        const element = document.getElementById(item.id);
        if (element) {
          headingElements.push(element);
          item.element = element;
        }
      });
    };

    // Try to find headings immediately, and if not found, try again after a delay
    findHeadings();
    
    if (headingElements.length === 0) {
      const timeout = setTimeout(() => {
        findHeadings();
        if (headingElements.length === 0) return;
        setupObserver();
      }, 100);
      return () => clearTimeout(timeout);
    } else {
      setupObserver();
    }

    function setupObserver() {
      // Create intersection observer with better settings
      const observer = new IntersectionObserver(
        (entries) => {
          // Find the heading that's most visible
          const visibleEntries = entries.filter(entry => entry.isIntersecting);
          
          if (visibleEntries.length === 0) {
            // If no entries are intersecting, find the one closest to the top
            let closestEntry: IntersectionObserverEntry | null = null;
            let closestDistance = Infinity;
            
            entries.forEach((entry) => {
              const rect = entry.target.getBoundingClientRect();
              const distance = Math.abs(rect.top);
              if (distance < closestDistance) {
                closestDistance = distance;
                closestEntry = entry;
              }
            });
            
            if (closestEntry) {
              const target = closestEntry.target as HTMLElement;
              if (target.id) {
                setActiveId(target.id);
              }
            }
          } else {
            // Find the entry with the highest intersection ratio
            const bestEntry = visibleEntries.reduce((best, current) => 
              current.intersectionRatio > best.intersectionRatio ? current : best
            );
            
            const target = bestEntry.target as HTMLElement;
            if (target.id) {
              setActiveId(target.id);
            }
          }
        },
        {
          rootMargin: '-10% 0px -60% 0px', // Top 10% to bottom 40% of viewport
          threshold: [0, 0.1, 0.25, 0.5, 0.75, 1],
        }
      );

      // Observe all heading elements
      headingElements.forEach((element) => {
        observer.observe(element);
      });

      return () => {
        observer.disconnect();
      };
    }
  }, [tocItems]);

  // Additional scroll listener for better tracking
  useEffect(() => {
    if (tocItems.length === 0) return;

    const handleScroll = () => {
      const viewportHeight = window.innerHeight;
      const threshold = viewportHeight * 0.3; // 30% from top

      let activeHeading = '';
      let minDistance = Infinity;

      tocItems.forEach((item) => {
        const element = document.getElementById(item.id);
        if (element) {
          const rect = element.getBoundingClientRect();
          const distance = Math.abs(rect.top - threshold);
          
          if (rect.top <= threshold && distance < minDistance) {
            minDistance = distance;
            activeHeading = item.id;
          }
        }
      });

      if (activeHeading && activeHeading !== activeId) {
        setActiveId(activeHeading);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // Call once on mount

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [tocItems, activeId]);

  const scrollToHeading = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  };

  const getIndentClass = (level: number) => {
    const indents = {
      1: 'ml-0',
      2: 'ml-4',
      3: 'ml-8',
      4: 'ml-12',
      5: 'ml-16',
      6: 'ml-20',
    };
    return indents[level as keyof typeof indents] || 'ml-0';
  };

  const getTextSizeClass = (level: number) => {
    const sizes = {
      1: 'text-sm font-bold',
      2: 'text-sm font-semibold',
      3: 'text-xs font-medium',
      4: 'text-xs',
      5: 'text-xs',
      6: 'text-xs',
    };
    return sizes[level as keyof typeof sizes] || 'text-xs';
  };

  if (tocItems.length === 0) {
    return null;
  }

  return (
    <div className={`sticky top-4 ${className}`}>
      <div className={`rounded-xl border transition-all duration-200 ${
        isDarkMode 
          ? 'bg-gray-800/80 border-gray-600/50 backdrop-blur-sm' 
          : 'bg-white/80 border-gray-200/50 backdrop-blur-sm'
      }`}>
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b ${
          isDarkMode ? 'border-gray-600/50' : 'border-gray-200/50'
        }`}>
          <div className="flex items-center gap-2">
            <List className={`w-4 h-4 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`} />
            <h3 className={`font-semibold text-sm ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Overview
            </h3>
          </div>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={`p-1 rounded transition-all duration-200 hover:scale-110 ${
              isDarkMode 
                ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
            title={isCollapsed ? 'Expand overview' : 'Collapse overview'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* TOC Content */}
        {!isCollapsed && (
          <div className="max-h-96 overflow-y-auto p-2">
            <nav>
              <ul className="space-y-1">
                {tocItems.map((item, index) => (
                  <li key={index} className={getIndentClass(item.level)}>
                    <button
                      onClick={() => scrollToHeading(item.id)}
                      className={`w-full text-left p-2 rounded-lg transition-all duration-200 hover:scale-[1.02] transform ${
                        activeId === item.id
                          ? isDarkMode
                            ? 'bg-blue-900/30 text-blue-300 border border-blue-700/50 shadow-sm'
                            : 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm'
                          : isDarkMode
                            ? 'hover:bg-gray-700/50 text-gray-300 hover:text-gray-100'
                            : 'hover:bg-gray-100/50 text-gray-600 hover:text-gray-900'
                      } ${getTextSizeClass(item.level)}`}
                      title={item.text}
                    >
                      <div className="flex items-center gap-2">
                        {activeId === item.id && (
                          <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                            isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                          }`} />
                        )}
                        <span className="truncate leading-relaxed">
                          {item.text}
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        )}
      </div>
    </div>
  );
}