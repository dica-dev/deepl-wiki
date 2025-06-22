'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, Zap } from 'lucide-react';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  onSendMessage: (message: string) => Promise<string>;
  isLoading?: boolean;
  placeholder?: string;
}

export default function ChatInterface({ 
  onSendMessage, 
  isLoading = false,
  placeholder = "Ask me anything about your documentation..."
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your documentation assistant. I can help answer questions about your project documentation. What would you like to know?',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    setInput('');
    setIsProcessing(true);

    try {
      const response = await onSendMessage(input.trim());
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
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

  return (
    <div className="flex flex-col h-full bg-bg-secondary/50 backdrop-blur-xl rounded-3xl overflow-hidden relative">
      {/* Animated Header */}
      <div className="relative p-6 border-b border-border-primary/50">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-llama-purple to-llama-accent rounded-xl flex items-center justify-center animate-pulse-glow">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="absolute -top-1 -right-1">
              <Sparkles className="w-4 h-4 text-llama-accent animate-pulse" />
            </div>
          </div>
          <div>
            <h2 className="text-xl font-black text-text-primary">AI Documentation Assistant</h2>
            <p className="text-sm text-text-secondary font-medium">
              Powered by <span className="text-llama-purple">Llama</span> with RAG
            </p>
          </div>
          {isLoading && (
            <div className="ml-auto flex items-center gap-3 glass-effect px-4 py-2 rounded-full border border-border-primary">
              <Loader2 className="w-4 h-4 animate-spin text-llama-accent" />
              <span className="text-sm text-text-secondary font-medium">Indexing...</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 relative">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="w-full h-full bg-gradient-to-br from-llama-purple/20 via-transparent to-llama-accent/20"></div>
        </div>

        {messages.map((message, index) => (
          <div
            key={message.id}
            className={`flex items-start gap-4 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            } animate-in slide-in-from-bottom duration-500`}
            style={{ animationDelay: `${index * 100}ms` }}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 relative">
                <div className="w-10 h-10 bg-gradient-to-br from-llama-purple to-llama-blue rounded-xl flex items-center justify-center shadow-lg">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-llama-green rounded-full border-2 border-bg-secondary flex items-center justify-center">
                  <Zap className="w-2 h-2 text-white" />
                </div>
              </div>
            )}
            
            <div
              className={`group max-w-[75%] relative ${
                message.role === 'user'
                  ? 'bg-gradient-to-br from-llama-purple to-llama-accent text-white rounded-2xl rounded-br-md'
                  : 'glass-effect border border-border-primary text-text-primary rounded-2xl rounded-bl-md'
              } px-6 py-4 shadow-lg hover:shadow-xl transition-all duration-300`}
            >
              <div className="whitespace-pre-wrap break-words leading-relaxed font-medium">
                {message.content}
              </div>
              <div
                className={`text-xs mt-2 flex items-center gap-1 ${
                  message.role === 'user' 
                    ? 'text-white/70' 
                    : 'text-text-tertiary'
                }`}
              >
                <div className="w-1 h-1 rounded-full bg-current opacity-50"></div>
                {formatTimestamp(message.timestamp)}
              </div>
              
              {/* Message glow effect */}
              {message.role === 'assistant' && (
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-llama-purple/10 to-llama-blue/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10"></div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 relative">
                <div className="w-10 h-10 bg-gradient-to-br from-llama-accent to-llama-accent-light rounded-xl flex items-center justify-center shadow-lg">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-llama-purple rounded-full border-2 border-bg-secondary"></div>
              </div>
            )}
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex items-start gap-4 animate-in slide-in-from-bottom duration-300">
            <div className="flex-shrink-0 relative">
              <div className="w-10 h-10 bg-gradient-to-br from-llama-purple to-llama-blue rounded-xl flex items-center justify-center shadow-lg animate-pulse-glow">
                <Bot className="w-5 h-5 text-white" />
              </div>
            </div>
            <div className="glass-effect border border-border-primary px-6 py-4 rounded-2xl rounded-bl-md">
              <div className="flex items-center gap-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-llama-purple rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-llama-accent rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-2 h-2 bg-llama-blue rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                </div>
                <span className="text-text-secondary font-medium">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Enhanced Input */}
      <div className="p-6 border-t border-border-primary/50 bg-bg-secondary/30 backdrop-blur-xl">
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative group">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
              disabled={isProcessing || isLoading}
              className="w-full pl-6 pr-16 py-4 bg-bg-tertiary border border-border-primary rounded-2xl text-text-primary placeholder-text-tertiary focus:outline-none focus:border-llama-purple focus:glow-purple transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            />
            <button
              type="submit"
              disabled={!input.trim() || isProcessing || isLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-gradient-to-r from-llama-purple to-llama-accent text-white rounded-xl hover:glow-purple transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center group"
            >
              {isProcessing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5 group-hover:scale-110 transition-transform" />
              )}
            </button>
          </div>
          
          {/* Input hint */}
          <div className="mt-3 flex items-center justify-between text-xs text-text-tertiary">
            <span>Press Enter to send, Shift+Enter for new line</span>
            <div className="flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-llama-green animate-pulse"></div>
              <span>RAG enabled</span>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}