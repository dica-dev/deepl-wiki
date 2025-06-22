'use client';

import React, { useState, useEffect } from 'react';
import { Keyboard, X } from 'lucide-react';

interface KeyboardShortcutsProps {
  isDarkMode?: boolean;
  onToggleChat?: () => void;
  onToggleTheme?: () => void;
  onToggleFullscreen?: () => void;
  onFocusSearch?: () => void;
}

export default function KeyboardShortcuts({
  isDarkMode = false,
  onToggleChat,
  onToggleTheme,
  onToggleFullscreen,
  onFocusSearch
}: KeyboardShortcutsProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Show shortcuts with Ctrl/Cmd + ?
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setIsVisible(!isVisible);
        return;
      }

      // Hide shortcuts on Escape
      if (e.key === 'Escape' && isVisible) {
        setIsVisible(false);
        return;
      }

      // Don't handle shortcuts if modal is open or user is typing
      if (isVisible || e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      // Keyboard shortcuts
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'k':
            e.preventDefault();
            onFocusSearch?.();
            break;
          case 'j':
            e.preventDefault();
            onToggleChat?.();
            break;
          case 'd':
            e.preventDefault();
            onToggleTheme?.();
            break;
          case 'f':
            e.preventDefault();
            onToggleFullscreen?.();
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, onToggleChat, onToggleTheme, onToggleFullscreen, onFocusSearch]);

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className={`fixed bottom-4 left-4 z-40 p-2 rounded-full transition-all duration-200 hover:scale-110 ${
          isDarkMode 
            ? 'bg-gray-800/80 text-gray-300 hover:bg-gray-700' 
            : 'bg-white/80 text-gray-600 hover:bg-gray-100'
        } backdrop-blur-sm border ${
          isDarkMode ? 'border-gray-600/50' : 'border-gray-200/50'
        }`}
        title="Keyboard shortcuts (Ctrl+/)"
      >
        <Keyboard className="w-4 h-4" />
      </button>
    );
  }

  const shortcuts = [
    { key: 'Ctrl+K', description: 'Focus search', available: !!onFocusSearch },
    { key: 'Ctrl+J', description: 'Toggle chat', available: !!onToggleChat },
    { key: 'Ctrl+D', description: 'Toggle dark mode', available: !!onToggleTheme },
    { key: 'Ctrl+F', description: 'Toggle fullscreen', available: !!onToggleFullscreen },
    { key: 'Ctrl+/', description: 'Show/hide shortcuts', available: true },
    { key: 'Escape', description: 'Close modals', available: true },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className={`w-full max-w-md rounded-xl border shadow-2xl ${
        isDarkMode 
          ? 'bg-gray-800 border-gray-600' 
          : 'bg-white border-gray-200'
      }`}>
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b ${
          isDarkMode ? 'border-gray-600' : 'border-gray-200'
        }`}>
          <div className="flex items-center gap-2">
            <Keyboard className={`w-5 h-5 ${
              isDarkMode ? 'text-blue-400' : 'text-blue-600'
            }`} />
            <h2 className={`text-lg font-semibold ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            onClick={() => setIsVisible(false)}
            className={`p-1 rounded transition-colors ${
              isDarkMode 
                ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Shortcuts list */}
        <div className="p-4 space-y-3">
          {shortcuts.filter(s => s.available).map((shortcut, index) => (
            <div key={index} className="flex items-center justify-between">
              <span className={`text-sm ${
                isDarkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {shortcut.description}
              </span>
              <div className={`px-2 py-1 rounded text-xs font-mono ${
                isDarkMode 
                  ? 'bg-gray-700 text-gray-300 border border-gray-600' 
                  : 'bg-gray-100 text-gray-700 border border-gray-300'
              }`}>
                {shortcut.key}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className={`p-4 border-t text-center ${
          isDarkMode ? 'border-gray-600' : 'border-gray-200'
        }`}>
          <p className={`text-xs ${
            isDarkMode ? 'text-gray-400' : 'text-gray-500'
          }`}>
            Press <kbd className={`px-1 py-0.5 rounded text-xs ${
              isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'
            }`}>Ctrl+/</kbd> to toggle this panel
          </p>
        </div>
      </div>
    </div>
  );
}