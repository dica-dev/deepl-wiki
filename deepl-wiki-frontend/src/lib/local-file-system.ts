// Local File System Service for Browser Environment

export interface LocalMarkdownFile {
  name: string;
  path: string;
  relativePath: string;
  content?: string;
  size: number;
  lastModified: number;
}

export interface LocalDirectory {
  name: string;
  path: string;
  files: LocalMarkdownFile[];
  subdirectories: LocalDirectory[];
}

export interface LocalFileTree {
  rootPath: string;
  totalFiles: number;
  structure: LocalDirectory;
}

// File System Access API types (for TypeScript)
declare global {
  interface Window {
    showDirectoryPicker?: () => Promise<FileSystemDirectoryHandle>;
  }
}

interface FileSystemHandle {
  readonly kind: 'file' | 'directory';
  readonly name: string;
}

interface FileSystemFileHandle extends FileSystemHandle {
  readonly kind: 'file';
  getFile(): Promise<File>;
}

interface FileSystemDirectoryHandle extends FileSystemHandle {
  readonly kind: 'directory';
  entries(): AsyncIterableIterator<[string, FileSystemHandle]>;
  values(): AsyncIterableIterator<FileSystemHandle>;
  keys(): AsyncIterableIterator<string>;
}

// Check if File System Access API is supported
const isFileSystemAccessSupported = () => {
  return typeof window !== 'undefined' && 'showDirectoryPicker' in window;
};

// Build directory tree from FileSystemDirectoryHandle
const buildDirectoryTree = async (
  dirHandle: FileSystemDirectoryHandle,
  basePath: string = '',
  maxDepth: number = 10,
  currentDepth: number = 0
): Promise<{ directory: LocalDirectory; totalFiles: number }> => {
  if (currentDepth > maxDepth) {
    return {
      directory: {
        name: dirHandle.name,
        path: basePath + dirHandle.name,
        files: [],
        subdirectories: []
      },
      totalFiles: 0
    };
  }

  const files: LocalMarkdownFile[] = [];
  const subdirectories: LocalDirectory[] = [];
  let totalFiles = 0;

  try {
    for await (const [name, handle] of dirHandle.entries()) {
      // Skip hidden files and common ignore patterns
      if (name.startsWith('.') || 
          ['node_modules', '__pycache__', 'venv', '.git', 'dist', 'build'].includes(name)) {
        continue;
      }

      if (handle.kind === 'file' && name.toLowerCase().endsWith('.md')) {
        const fileHandle = handle as FileSystemFileHandle;
        const file = await fileHandle.getFile();
        files.push({
          name: name,
          path: basePath + dirHandle.name + '/' + name,
          relativePath: basePath ? basePath.replace(/^\//, '') + dirHandle.name + '/' + name : name,
          size: file.size,
          lastModified: file.lastModified
        });
        totalFiles++;
      } else if (handle.kind === 'directory') {
        const { directory: subDir, totalFiles: subFiles } = await buildDirectoryTree(
          handle as FileSystemDirectoryHandle,
          basePath + dirHandle.name + '/',
          maxDepth,
          currentDepth + 1
        );
        if (subFiles > 0) {
          subdirectories.push(subDir);
          totalFiles += subFiles;
        }
      }
    }
  } catch (error) {
    console.warn('Error reading directory:', error);
  }

  return {
    directory: {
      name: dirHandle.name,
      path: basePath + dirHandle.name,
      files: files.sort((a, b) => a.name.localeCompare(b.name)),
      subdirectories: subdirectories.sort((a, b) => a.name.localeCompare(b.name))
    },
    totalFiles
  };
};

// Read file content from FileSystemFileHandle
const readFileContent = async (fileHandle: FileSystemFileHandle): Promise<string> => {
  try {
    const file = await fileHandle.getFile();
    return await file.text();
  } catch (error) {
    console.error('Error reading file:', error);
    throw new Error('Failed to read file content');
  }
};

export class LocalFileSystemService implements FileSystemService {
  private directoryHandle: FileSystemDirectoryHandle | null = null;
  private fileTree: LocalFileTree | null = null;
  private fileHandles: Map<string, FileSystemFileHandle> = new Map();

  // Check if the service is supported in this browser
  static isSupported(): boolean {
    return isFileSystemAccessSupported();
  }

  // Select and scan a directory
  async selectDirectory(): Promise<LocalFileTree> {
    if (!isFileSystemAccessSupported()) {
      throw new Error('File System Access API is not supported in this browser');
    }

    try {
      // Show directory picker
      if (!window.showDirectoryPicker) {
        throw new Error('Directory picker not available');
      }
      
      this.directoryHandle = await window.showDirectoryPicker();

      if (!this.directoryHandle) {
        throw new Error('No directory selected');
      }

      // Build file tree
      const { directory, totalFiles } = await buildDirectoryTree(this.directoryHandle);
      
      this.fileTree = {
        rootPath: this.directoryHandle.name,
        totalFiles,
        structure: directory
      };

      // Store file handles for later content reading
      await this.indexFileHandles(this.directoryHandle, '');

      return this.fileTree;
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        throw new Error('Directory selection was cancelled');
      }
      console.error('Error selecting directory:', error);
      throw new Error('Failed to select directory');
    }
  }

  // Index file handles for content reading
  private async indexFileHandles(dirHandle: FileSystemDirectoryHandle, basePath: string): Promise<void> {
    try {
      for await (const [name, handle] of dirHandle.entries()) {
        if (name.startsWith('.') || 
            ['node_modules', '__pycache__', 'venv', '.git', 'dist', 'build'].includes(name)) {
          continue;
        }

        const fullPath = basePath + (basePath ? '/' : '') + name;

        if (handle.kind === 'file' && name.toLowerCase().endsWith('.md')) {
          this.fileHandles.set(fullPath, handle as FileSystemFileHandle);
        } else if (handle.kind === 'directory') {
          await this.indexFileHandles(handle as FileSystemDirectoryHandle, fullPath);
        }
      }
    } catch (error) {
      console.warn('Error indexing file handles:', error);
    }
  }

  // Read content of a specific file
  async readFileContent(relativePath: string): Promise<string> {
    const fileHandle = this.fileHandles.get(relativePath);
    if (!fileHandle) {
      throw new Error(`File not found: ${relativePath}`);
    }

    return await readFileContent(fileHandle);
  }

  // Get the current file tree
  getFileTree(): LocalFileTree | null {
    return this.fileTree;
  }

  // Get all markdown files as a flat list
  getAllMarkdownFiles(): LocalMarkdownFile[] {
    if (!this.fileTree) return [];

    const collectFiles = (dir: LocalDirectory): LocalMarkdownFile[] => {
      let files = [...dir.files];
      for (const subDir of dir.subdirectories) {
        files = files.concat(collectFiles(subDir));
      }
      return files;
    };

    return collectFiles(this.fileTree.structure);
  }

  // Search for files by name or path
  searchFiles(query: string): LocalMarkdownFile[] {
    const allFiles = this.getAllMarkdownFiles();
    const searchTerm = query.toLowerCase();
    
    return allFiles.filter(file => 
      file.name.toLowerCase().includes(searchTerm) ||
      file.relativePath.toLowerCase().includes(searchTerm)
    );
  }

  // Clear the current selection
  clear(): void {
    this.directoryHandle = null;
    this.fileTree = null;
    this.fileHandles.clear();
  }
}

// Common interface for file system services
export interface FileSystemService {
  selectDirectory(): Promise<LocalFileTree>;
  readFileContent(relativePath: string): Promise<string>;
  getAllMarkdownFiles(): LocalMarkdownFile[];
  searchFiles(query: string): LocalMarkdownFile[];
  clear(): void;
}

// Fallback service for browsers that don't support File System Access API
export class FallbackFileSystemService implements FileSystemService {
  private files: LocalMarkdownFile[] = [];
  private fileContents: Map<string, string> = new Map();

  static isSupported(): boolean {
    return true; // Always supported as fallback
  }

  // Manual directory selection (fallback to file selection)
  async selectDirectory(): Promise<LocalFileTree> {
    return this.selectFiles();
  }

  // Manual file selection (multiple files)
  async selectFiles(): Promise<LocalFileTree> {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = true;
      input.accept = '.md,.markdown';
      input.webkitdirectory = true; // Allow directory selection

      input.onchange = async (event) => {
        const files = (event.target as HTMLInputElement).files;
        if (!files || files.length === 0) {
          reject(new Error('No files selected'));
          return;
        }

        try {
          this.files = [];
          this.fileContents.clear();

          // Process selected files
          for (const file of Array.from(files)) {
            if (file.name.toLowerCase().endsWith('.md')) {
              const content = await file.text();
              const relativePath = file.webkitRelativePath || file.name;
              
              const markdownFile: LocalMarkdownFile = {
                name: file.name,
                path: file.webkitRelativePath || file.name,
                relativePath: relativePath,
                size: file.size,
                lastModified: file.lastModified
              };

              this.files.push(markdownFile);
              this.fileContents.set(relativePath, content);
            }
          }

          // Build simple tree structure
          const rootPath = this.files.length > 0 
            ? this.files[0].relativePath.split('/')[0] 
            : 'Selected Files';

          const fileTree: LocalFileTree = {
            rootPath,
            totalFiles: this.files.length,
            structure: {
              name: rootPath,
              path: rootPath,
              files: this.files,
              subdirectories: []
            }
          };

          resolve(fileTree);
        } catch (error) {
          reject(error);
        }
      };

      input.oncancel = () => {
        reject(new Error('File selection was cancelled'));
      };

      input.click();
    });
  }

  async readFileContent(relativePath: string): Promise<string> {
    const content = this.fileContents.get(relativePath);
    if (!content) {
      throw new Error(`File content not found: ${relativePath}`);
    }
    return content;
  }

  getAllMarkdownFiles(): LocalMarkdownFile[] {
    return this.files;
  }

  searchFiles(query: string): LocalMarkdownFile[] {
    const searchTerm = query.toLowerCase();
    return this.files.filter(file => 
      file.name.toLowerCase().includes(searchTerm) ||
      file.relativePath.toLowerCase().includes(searchTerm)
    );
  }

  clear(): void {
    this.files = [];
    this.fileContents.clear();
  }
}

// Factory function to get the appropriate service
export function createFileSystemService(): FileSystemService {
  if (LocalFileSystemService.isSupported()) {
    return new LocalFileSystemService();
  } else {
    return new FallbackFileSystemService();
  }
}