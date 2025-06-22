'use client';

import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

interface AdvancedTypingIndicatorProps {
  isDarkMode?: boolean;
  userName?: string;
}

export default function AdvancedTypingIndicator({ 
  isDarkMode = false,
  userName = "JAVI"
}: AdvancedTypingIndicatorProps) {
  return (
    <div className="flex items-start gap-3">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
        isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
      }`}>
        <Bot className={`w-3 h-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`} />
      </div>
      
      <div className={`rounded-lg px-4 py-3 max-w-xs relative overflow-hidden ${
        isDarkMode ? 'bg-gray-700 text-gray-100' : 'bg-gray-100 text-gray-900'
      }`}>
        {/* Animated background shimmer */}
        <div className={`absolute inset-0 opacity-20 ${
          isDarkMode ? 'bg-gradient-to-r from-blue-500 to-purple-500' : 'bg-gradient-to-r from-blue-400 to-purple-400'
        } shimmer-effect`}></div>
        
        <div className="relative z-10">
          {/* Header with AI name and sparkle */}
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs font-semibold ${
              isDarkMode ? 'text-blue-400' : 'text-blue-600'
            }`}>
              {userName}
            </span>
            <Sparkles className={`w-3 h-3 ${
              isDarkMode ? 'text-yellow-400' : 'text-yellow-500'
            } animate-pulse`} />
            <span className={`text-xs ${
              isDarkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              is thinking...
            </span>
          </div>
          
          {/* Advanced typing dots */}
          <div className="flex items-center gap-1">
            <div className="flex gap-1">
              <div className={`w-2 h-2 rounded-full typing-dots ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
              }`}></div>
              <div className={`w-2 h-2 rounded-full typing-dots ${
                isDarkMode ? 'bg-purple-400' : 'bg-purple-500'
              }`} style={{animationDelay: '0.2s'}}></div>
              <div className={`w-2 h-2 rounded-full typing-dots ${
                isDarkMode ? 'bg-pink-400' : 'bg-pink-500'
              }`} style={{animationDelay: '0.4s'}}></div>
            </div>
            
            {/* Animated text */}
            <div className={`ml-3 text-xs font-medium opacity-70 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-600'
            }`}>
              <span className="inline-block animate-pulse">Processing</span>
              <span className="inline-block animate-pulse" style={{animationDelay: '0.5s'}}>.</span>
              <span className="inline-block animate-pulse" style={{animationDelay: '1s'}}>.</span>
              <span className="inline-block animate-pulse" style={{animationDelay: '1.5s'}}>.</span>
            </div>
          </div>
        </div>
        
        {/* Subtle border glow */}
        <div className={`absolute inset-0 rounded-lg ${
          isDarkMode ? 'ring-1 ring-blue-500/20' : 'ring-1 ring-blue-400/20'
        } animate-pulse`}></div>
      </div>
    </div>
  );
}