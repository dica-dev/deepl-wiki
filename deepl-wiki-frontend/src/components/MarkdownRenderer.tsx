'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  isDarkMode?: boolean;
}

export default function MarkdownRenderer({ content, className = "", isDarkMode = false }: MarkdownRendererProps) {
  const isChatMessage = className.includes('chat-message');
  
  return (
    <div className={`prose prose-gray max-w-none ${className} ${isDarkMode ? 'prose-invert hljs-dark' : ''} ${isChatMessage ? 'prose-sm' : ''}`}>
      <style jsx>{`
        .hljs-dark .hljs {
          background: #0f172a !important;
          color: #e2e8f0 !important;
          border: 1px solid #334155 !important;
        }
        .hljs-dark .hljs-keyword,
        .hljs-dark .hljs-selector-tag,
        .hljs-dark .hljs-literal,
        .hljs-dark .hljs-doctag,
        .hljs-dark .hljs-title,
        .hljs-dark .hljs-section,
        .hljs-dark .hljs-type,
        .hljs-dark .hljs-name,
        .hljs-dark .hljs-strong {
          color: #fbbf24 !important;
          font-weight: 600 !important;
        }
        .hljs-dark .hljs-string,
        .hljs-dark .hljs-number,
        .hljs-dark .hljs-quote,
        .hljs-dark .hljs-template-tag,
        .hljs-dark .hljs-deletion {
          color: #34d399 !important;
        }
        .hljs-dark .hljs-comment,
        .hljs-dark .hljs-meta {
          color: #94a3b8 !important;
          font-style: italic !important;
        }
        .hljs-dark .hljs-variable,
        .hljs-dark .hljs-template-variable,
        .hljs-dark .hljs-attr,
        .hljs-dark .hljs-attribute,
        .hljs-dark .hljs-builtin-name,
        .hljs-dark .hljs-addition {
          color: #60a5fa !important;
        }
        .hljs-dark .hljs-function,
        .hljs-dark .hljs-class,
        .hljs-dark .hljs-built_in {
          color: #c084fc !important;
          font-weight: 500 !important;
        }
        .hljs-dark .hljs-params {
          color: #fca5a5 !important;
        }
        .hljs-dark .hljs-operator,
        .hljs-dark .hljs-punctuation {
          color: #f1f5f9 !important;
        }
        .hljs-dark .hljs-tag {
          color: #fb7185 !important;
        }
        .hljs-dark .hljs-symbol,
        .hljs-dark .hljs-bullet,
        .hljs-dark .hljs-link {
          color: #fde047 !important;
        }
      `}</style>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          h1: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text
              .toLowerCase()
              .replace(/[^\w\s-]/g, '')
              .replace(/\s+/g, '-')
              .trim();
            
            return (
              <h1 
                id={isChatMessage ? undefined : id}
                className={isChatMessage 
                  ? "text-lg font-bold mb-2 mt-2 first:mt-0" 
                  : isDarkMode 
                    ? "text-3xl font-bold text-white mb-6 mt-8 first:mt-0 scroll-mt-20"
                    : "text-3xl font-bold text-gray-900 mb-6 mt-8 first:mt-0 scroll-mt-20"
                }
              >
                {children}
              </h1>
            );
          },
          h2: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text
              .toLowerCase()
              .replace(/[^\w\s-]/g, '')
              .replace(/\s+/g, '-')
              .trim();
            
            return (
              <h2 
                id={isChatMessage ? undefined : id}
                className={isChatMessage 
                  ? "text-base font-semibold mb-2 mt-3" 
                  : isDarkMode
                    ? "text-2xl font-semibold text-gray-100 mb-4 mt-8 scroll-mt-20"
                    : "text-2xl font-semibold text-gray-800 mb-4 mt-8 scroll-mt-20"
                }
              >
                {children}
              </h2>
            );
          },
          h3: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text
              .toLowerCase()
              .replace(/[^\w\s-]/g, '')
              .replace(/\s+/g, '-')
              .trim();
            
            return (
              <h3 
                id={isChatMessage ? undefined : id}
                className={isChatMessage 
                  ? "text-sm font-medium mb-1 mt-2" 
                  : isDarkMode
                    ? "text-xl font-medium text-gray-200 mb-3 mt-6 scroll-mt-20"
                    : "text-xl font-medium text-gray-700 mb-3 mt-6 scroll-mt-20"
                }
              >
                {children}
              </h3>
            );
          },
          h4: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text
              .toLowerCase()
              .replace(/[^\w\s-]/g, '')
              .replace(/\s+/g, '-')
              .trim();
            
            return (
              <h4 
                id={isChatMessage ? undefined : id}
                className={isChatMessage 
                  ? "text-sm font-medium mb-1 mt-2" 
                  : isDarkMode
                    ? "text-lg font-medium text-gray-200 mb-2 mt-4 scroll-mt-20"
                    : "text-lg font-medium text-gray-700 mb-2 mt-4 scroll-mt-20"
                }
              >
                {children}
              </h4>
            );
          },
          h5: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text
              .toLowerCase()
              .replace(/[^\w\s-]/g, '')
              .replace(/\s+/g, '-')
              .trim();
            
            return (
              <h5 
                id={isChatMessage ? undefined : id}
                className={isChatMessage 
                  ? "text-sm font-medium mb-1 mt-2" 
                  : isDarkMode
                    ? "text-base font-medium text-gray-200 mb-2 mt-4 scroll-mt-20"
                    : "text-base font-medium text-gray-700 mb-2 mt-4 scroll-mt-20"
                }
              >
                {children}
              </h5>
            );
          },
          h6: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text
              .toLowerCase()
              .replace(/[^\w\s-]/g, '')
              .replace(/\s+/g, '-')
              .trim();
            
            return (
              <h6 
                id={isChatMessage ? undefined : id}
                className={isChatMessage 
                  ? "text-sm font-medium mb-1 mt-2" 
                  : isDarkMode
                    ? "text-sm font-medium text-gray-200 mb-2 mt-4 scroll-mt-20"
                    : "text-sm font-medium text-gray-700 mb-2 mt-4 scroll-mt-20"
                }
              >
                {children}
              </h6>
            );
          },
          p: ({ children }) => (
            <p className={isChatMessage 
              ? "mb-2 leading-relaxed" 
              : isDarkMode
                ? "text-gray-300 mb-4 leading-relaxed"
                : "text-gray-700 mb-4 leading-relaxed"
            }>
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className={isChatMessage 
              ? "list-disc list-inside mb-2 space-y-1" 
              : isDarkMode
                ? "list-disc list-inside mb-4 space-y-2 text-gray-300"
                : "list-disc list-inside mb-4 space-y-2 text-gray-700"
            }>
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className={isChatMessage 
              ? "list-decimal list-inside mb-2 space-y-1" 
              : isDarkMode
                ? "list-decimal list-inside mb-4 space-y-2 text-gray-300"
                : "list-decimal list-inside mb-4 space-y-2 text-gray-700"
            }>
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className={isChatMessage 
              ? "leading-relaxed" 
              : isDarkMode
                ? "text-gray-300 leading-relaxed"
                : "text-gray-700 leading-relaxed"
            }>
              {children}
            </li>
          ),
          blockquote: ({ children }) => (
            <blockquote className={isChatMessage 
              ? "border-l-2 border-gray-400 pl-2 py-1 mb-2 italic opacity-80" 
              : isDarkMode
                ? "border-l-4 border-gray-600 pl-4 py-2 mb-4 italic text-gray-400 bg-gray-800 rounded-r"
                : "border-l-4 border-gray-300 pl-4 py-2 mb-4 italic text-gray-600 bg-gray-50 rounded-r"
            }>
              {children}
            </blockquote>
          ),
          code: ({ children, className }) => {
            const inline = !className;
            if (inline) {
              return (
                <code className={isChatMessage 
                  ? "bg-black/10 px-1 py-0.5 rounded text-xs font-mono" 
                  : isDarkMode
                    ? "bg-slate-800 text-emerald-300 px-2 py-1 rounded text-sm font-mono border border-slate-600"
                    : "bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono"
                }>
                  {children}
                </code>
              );
            }
            return (
              <code className={className}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className={isChatMessage 
              ? "bg-black/10 rounded p-2 mb-2 overflow-x-auto text-xs" 
              : isDarkMode
                ? "bg-slate-900 border border-slate-600 rounded-lg p-4 mb-4 overflow-x-auto text-sm shadow-lg"
                : "bg-gray-100 border border-gray-200 rounded-lg p-4 mb-4 overflow-x-auto text-sm"
            }>
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto mb-4">
              <table className={`min-w-full border rounded-lg ${
                isDarkMode ? 'border-gray-700' : 'border-gray-200'
              }`}>
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className={isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}>
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className={`divide-y ${isDarkMode ? 'divide-gray-700' : 'divide-gray-200'}`}>
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className={isDarkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-50'}>
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className={`px-4 py-3 text-left text-sm font-medium border-b ${
              isDarkMode 
                ? 'text-gray-300 border-gray-700' 
                : 'text-gray-700 border-gray-200'
            }`}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className={`px-4 py-3 text-sm ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              {children}
            </td>
          ),
          a: ({ children, href }) => (
            <a 
              href={href} 
              className={isDarkMode 
                ? "text-blue-400 hover:text-blue-300 underline" 
                : "text-blue-400 hover:text-blue-300 underline"
              }
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          strong: ({ children }) => (
            <strong className={`font-semibold ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className={`italic ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              {children}
            </em>
          ),
          hr: () => (
            <hr className={`my-6 ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}