'use client';

import React, { useState } from 'react';
import { X, Folder, AlertCircle } from 'lucide-react';

interface PathSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onPathSelect: () => void;
  isDarkMode: boolean;
}

export default function PathSelector({ isOpen, onClose, onPathSelect, isDarkMode }: PathSelectorProps) {
  const [isValidating, setIsValidating] = useState(false);
  const [validationMessage, setValidationMessage] = useState('');

  const validateAndSelectPath = async () => {
    setIsValidating(true);
    setValidationMessage('');

    try {
      // Call the path selection handler which will open the directory picker
      await onPathSelect();
      onClose();
    } catch (error) {
      setValidationMessage('Failed to select directory: ' + (error as Error).message);
    } finally {
      setIsValidating(false);
    }
  };



  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div 
        className={`absolute inset-0 transition-colors duration-200 ${
          isDarkMode ? 'bg-black/50' : 'bg-black/30'
        }`}
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className={`relative max-w-2xl w-full mx-4 rounded-xl shadow-2xl transition-colors duration-200 ${
        isDarkMode 
          ? 'bg-gray-800 border border-gray-600' 
          : 'bg-white border border-gray-200'
      }`}>
        {/* Header */}
        <div className={`p-6 border-b transition-colors duration-200 ${
          isDarkMode ? 'border-gray-600' : 'border-gray-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                isDarkMode ? 'bg-blue-900/30' : 'bg-blue-50'
              }`}>
                <Folder className={`w-5 h-5 ${
                  isDarkMode ? 'text-blue-400' : 'text-blue-600'
                }`} />
              </div>
              <div>
                <h2 className={`text-xl font-semibold transition-colors duration-200 ${
                  isDarkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  Select Documentation Path
                </h2>
                <p className={`text-sm transition-colors duration-200 ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  Choose a folder containing markdown files to browse
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Directory Picker Info */}
          <div className="space-y-3">
            <div className={`p-4 rounded-lg border transition-colors duration-200 ${
              isDarkMode 
                ? 'bg-blue-900/10 border-blue-700/30' 
                : 'bg-blue-50 border-blue-200'
            }`}>
              <div className="flex gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
                }`}>
                  <Folder className="w-3 h-3 text-white" />
                </div>
                <div className="space-y-1">
                  <p className={`text-sm font-medium transition-colors duration-200 ${
                    isDarkMode ? 'text-blue-300' : 'text-blue-700'
                  }`}>
                    Select Directory
                  </p>
                  <p className={`text-xs transition-colors duration-200 ${
                    isDarkMode ? 'text-blue-400' : 'text-blue-600'
                  }`}>
                    Click "Select Directory" below to open your browser's folder picker and choose a directory containing markdown files.
                  </p>
                </div>
              </div>
            </div>
            
            {validationMessage && (
              <div className={`p-3 rounded-lg border transition-colors duration-200 ${
                isDarkMode 
                  ? 'bg-red-900/20 border-red-700/50' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <p className="text-sm text-red-500 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  {validationMessage}
                </p>
              </div>
            )}
          </div>


          {/* Info */}
          <div className={`p-4 rounded-lg border transition-colors duration-200 ${
            isDarkMode 
              ? 'bg-blue-900/10 border-blue-700/30' 
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
              }`}>
                <span className="text-white text-xs font-bold">i</span>
              </div>
              <div className="space-y-1">
                <p className={`text-sm font-medium transition-colors duration-200 ${
                  isDarkMode ? 'text-blue-300' : 'text-blue-700'
                }`}>
                  How it works
                </p>
                <p className={`text-xs transition-colors duration-200 ${
                  isDarkMode ? 'text-blue-400' : 'text-blue-600'
                }`}>
                  The system will scan the selected directory for markdown (.md) files and display them in a tree structure. Subdirectories will be organized as folders.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={`p-6 border-t flex items-center justify-end gap-3 transition-colors duration-200 ${
          isDarkMode ? 'border-gray-600' : 'border-gray-200'
        }`}>
          <button
            onClick={onClose}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isDarkMode 
                ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            Cancel
          </button>
          <button
            onClick={validateAndSelectPath}
            disabled={isValidating}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-colors ${
              isValidating
                ? isDarkMode 
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : isDarkMode
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isValidating ? 'Opening Directory Picker...' : 'Select Directory'}
          </button>
        </div>
      </div>
    </div>
  );
}