'use client';

import React from 'react';
import { Loader2, Bot, BookOpen } from 'lucide-react';

interface LoadingSpinnerProps {
  isDarkMode?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  message?: string;
  type?: 'default' | 'chat' | 'indexing';
}

export default function LoadingSpinner({ 
  isDarkMode = false, 
  size = 'md', 
  message,
  type = 'default'
}: LoadingSpinnerProps) {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm': return 'w-4 h-4';
      case 'md': return 'w-6 h-6';
      case 'lg': return 'w-8 h-8';
      case 'xl': return 'w-12 h-12';
      default: return 'w-6 h-6';
    }
  };

  const getContainerSize = () => {
    switch (size) {
      case 'sm': return 'w-8 h-8';
      case 'md': return 'w-12 h-12';
      case 'lg': return 'w-16 h-16';
      case 'xl': return 'w-24 h-24';
      default: return 'w-12 h-12';
    }
  };

  const renderIcon = () => {
    switch (type) {
      case 'chat':
        return <Bot className={`${getSizeClasses()} animate-pulse`} />;
      case 'indexing':
        return <BookOpen className={`${getSizeClasses()} indexing-pulse`} />;
      default:
        return <Loader2 className={`${getSizeClasses()} animate-spin`} />;
    }
  };

  const getBackgroundClasses = () => {
    switch (type) {
      case 'chat':
        return isDarkMode 
          ? 'bg-gradient-to-br from-blue-600 to-purple-600' 
          : 'bg-gradient-to-br from-blue-500 to-purple-500';
      case 'indexing':
        return isDarkMode 
          ? 'bg-gradient-to-br from-green-600 to-blue-600' 
          : 'bg-gradient-to-br from-green-500 to-blue-500';
      default:
        return isDarkMode ? 'bg-gray-700' : 'bg-gray-200';
    }
  };

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Spinner Container */}
      <div className={`
        ${getContainerSize()} 
        rounded-xl 
        flex items-center justify-center 
        ${getBackgroundClasses()}
        ${type === 'indexing' ? 'indexing-glow shadow-2xl' : 'shadow-lg'}
        transition-all duration-300
      `}>
        <div className="text-white">
          {renderIcon()}
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className="text-center">
          <p className={`text-sm font-medium ${
            isDarkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>
            {message}
          </p>
          
          {/* Animated dots for some types */}
          {(type === 'chat' || type === 'indexing') && (
            <div className="flex items-center justify-center gap-1 mt-1">
              <div className={`w-1 h-1 rounded-full ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
              } animate-pulse`}></div>
              <div className={`w-1 h-1 rounded-full ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
              } animate-pulse`} style={{animationDelay: '0.2s'}}></div>
              <div className={`w-1 h-1 rounded-full ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
              } animate-pulse`} style={{animationDelay: '0.4s'}}></div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}