'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, RefreshCw, FolderPlus, AlertCircle, CheckCircle } from 'lucide-react';
import { BackendRAGEngine } from '@/lib/backend-rag-engine';
import { ApiRepository } from '@/lib/api-client';

interface RepositoryManagerProps {
  ragEngine: BackendRAGEngine;
  isDarkMode?: boolean;
  onRepositoryChange?: () => void;
}

export default function RepositoryManager({ 
  ragEngine, 
  isDarkMode = false,
  onRepositoryChange 
}: RepositoryManagerProps) {
  const [repositories, setRepositories] = useState<ApiRepository[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newRepo, setNewRepo] = useState({
    path: '',
    name: '',
    description: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadRepositories();
  }, [ragEngine]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadRepositories = async () => {
    try {
      setIsLoading(true);
      const repos = ragEngine.getRepositories();
      setRepositories(repos);
    } catch (err) {
      console.error('Failed to load repositories:', err);
      setError('Failed to load repositories');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddRepository = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRepo.path.trim() || !newRepo.name.trim()) {
      setError('Path and name are required');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      await ragEngine.addRepository(
        newRepo.path.trim(),
        newRepo.name.trim(),
        newRepo.description.trim()
      );
      
      setNewRepo({ path: '', name: '', description: '' });
      setShowAddForm(false);
      setSuccess('Repository added successfully!');
      setTimeout(() => setSuccess(null), 3000);
      
      await loadRepositories();
      onRepositoryChange?.();
    } catch (err) {
      console.error('Failed to add repository:', err);
      setError(err instanceof Error ? err.message : 'Failed to add repository');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveRepository = async (repositoryId: number, repositoryName: string) => {
    if (!confirm(`Are you sure you want to remove "${repositoryName}"?`)) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      await ragEngine.removeRepository(repositoryId);
      setSuccess('Repository removed successfully!');
      setTimeout(() => setSuccess(null), 3000);
      
      await loadRepositories();
      onRepositoryChange?.();
    } catch (err) {
      console.error('Failed to remove repository:', err);
      setError(err instanceof Error ? err.message : 'Failed to remove repository');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshRepositories = async () => {
    await loadRepositories();
  };

  return (
    <div className={`space-y-4 p-4 rounded-xl border ${
      isDarkMode 
        ? 'bg-gray-800/50 border-gray-600/50' 
        : 'bg-white/50 border-gray-200/50'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderPlus className={`w-5 h-5 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Repository Management
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefreshRepositories}
            disabled={isLoading}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode 
                ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            } disabled:opacity-50`}
            title="Refresh repositories"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
              isDarkMode 
                ? 'bg-blue-600 text-white hover:bg-blue-700' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            <Plus className="w-4 h-4" />
            Add Repository
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className={`flex items-center gap-2 p-3 rounded-lg ${
          isDarkMode ? 'bg-green-900/20 text-green-400' : 'bg-green-50 text-green-600'
        }`}>
          <CheckCircle className="w-4 h-4" />
          {success}
        </div>
      )}

      {error && (
        <div className={`flex items-center gap-2 p-3 rounded-lg ${
          isDarkMode ? 'bg-red-900/20 text-red-400' : 'bg-red-50 text-red-600'
        }`}>
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Add Repository Form */}
      {showAddForm && (
        <form onSubmit={handleAddRepository} className="space-y-4">
          <div>
            <label className={`block text-sm font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Repository Path *
            </label>
            <input
              type="text"
              value={newRepo.path}
              onChange={(e) => setNewRepo({ ...newRepo, path: e.target.value })}
              placeholder="/path/to/your/repository"
              className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors ${
                isDarkMode 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              } focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500`}
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Repository Name *
            </label>
            <input
              type="text"
              value={newRepo.name}
              onChange={(e) => setNewRepo({ ...newRepo, name: e.target.value })}
              placeholder="My Awesome Project"
              className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors ${
                isDarkMode 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              } focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500`}
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Description
            </label>
            <textarea
              value={newRepo.description}
              onChange={(e) => setNewRepo({ ...newRepo, description: e.target.value })}
              placeholder="A brief description of what this repository contains"
              rows={3}
              className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors resize-none ${
                isDarkMode 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              } focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500`}
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isLoading}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'bg-green-600 text-white hover:bg-green-700' 
                  : 'bg-green-500 text-white hover:bg-green-600'
              } disabled:opacity-50`}
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Add Repository
            </button>
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Repository List */}
      <div className="space-y-2">
        {repositories.length === 0 ? (
          <div className={`text-center py-8 ${
            isDarkMode ? 'text-gray-400' : 'text-gray-600'
          }`}>
            <FolderPlus className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No repositories added yet.</p>
            <p className="text-sm">Add a repository to get started!</p>
          </div>
        ) : (
          repositories.map((repo) => (
            <div
              key={repo.id}
              className={`flex items-center justify-between p-3 rounded-lg border ${
                isDarkMode 
                  ? 'bg-gray-700/50 border-gray-600/50 hover:bg-gray-700' 
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
              } transition-colors`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className={`font-medium truncate ${
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    {repo.name}
                  </h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    repo.status === 'active'
                      ? isDarkMode ? 'bg-green-900/30 text-green-400' : 'bg-green-100 text-green-600'
                      : isDarkMode ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {repo.status}
                  </span>
                </div>
                <p className={`text-sm truncate ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  {repo.path}
                </p>
                {repo.description && (
                  <p className={`text-xs truncate ${
                    isDarkMode ? 'text-gray-500' : 'text-gray-500'
                  }`}>
                    {repo.description}
                  </p>
                )}
                {repo.indexed_at && (
                  <p className={`text-xs ${
                    isDarkMode ? 'text-gray-500' : 'text-gray-500'
                  }`}>
                    Indexed: {new Date(repo.indexed_at).toLocaleString()}
                  </p>
                )}
              </div>
              <button
                onClick={() => handleRemoveRepository(repo.id, repo.name)}
                disabled={isLoading}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode 
                    ? 'text-red-400 hover:text-red-300 hover:bg-red-900/20' 
                    : 'text-red-600 hover:text-red-700 hover:bg-red-50'
                } disabled:opacity-50`}
                title="Remove repository"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}