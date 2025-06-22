/**
 * Markdown monitoring service for tracking changes in the memo repository
 */

import { Octokit } from '@octokit/rest';
import { EventEmitter } from 'events';

export interface MarkdownFile {
  path: string;
  content: string;
  sha: string;
  lastModified: string;
}

export interface RepoConfig {
  owner: string;
  repo: string;
  branch?: string;
  path?: string;
}

export class MarkdownMonitor extends EventEmitter {
  private octokit: Octokit;
  private config: RepoConfig;
  private pollInterval: number;
  private isRunning: boolean = false;
  private lastCommitSha: string | null = null;
  private intervalId: NodeJS.Timeout | null = null;

  constructor(config: RepoConfig, githubToken: string, pollInterval: number = 30000) {
    super();
    this.config = { branch: 'main', path: '', ...config };
    this.pollInterval = pollInterval;
    this.octokit = new Octokit({ auth: githubToken });
  }

  async start() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    console.log(`Starting markdown monitor for ${this.config.owner}/${this.config.repo}`);
    
    // Initial load
    await this.checkForUpdates();
    
    // Set up polling
    this.intervalId = setInterval(async () => {
      await this.checkForUpdates();
    }, this.pollInterval);
  }

  stop() {
    if (!this.isRunning) return;
    
    this.isRunning = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    console.log('Markdown monitor stopped');
  }

  private async checkForUpdates() {
    try {
      // Get latest commit on the branch
      const { data: commit } = await this.octokit.rest.repos.getCommit({
        owner: this.config.owner,
        repo: this.config.repo,
        ref: this.config.branch!,
      });

      const currentCommitSha = commit.sha;
      
      // If this is the first check or commit has changed
      if (!this.lastCommitSha || this.lastCommitSha !== currentCommitSha) {
        console.log(`New commit detected: ${currentCommitSha}`);
        this.lastCommitSha = currentCommitSha;
        
        // Fetch all markdown files
        const markdownFiles = await this.fetchMarkdownFiles();
        this.emit('filesUpdated', markdownFiles);
      }
    } catch (error) {
      console.error('Error checking for updates:', error);
      this.emit('error', error);
    }
  }

  private async fetchMarkdownFiles(): Promise<MarkdownFile[]> {
    const files: MarkdownFile[] = [];
    
    try {
      const { data: contents } = await this.octokit.rest.repos.getContent({
        owner: this.config.owner,
        repo: this.config.repo,
        path: this.config.path!,
        ref: this.config.branch,
      });

      // Handle both single file and directory responses
      const items = Array.isArray(contents) ? contents : [contents];
      
      for (const item of items) {
        if (item.type === 'file' && item.name.endsWith('.md')) {
          const fileContent = await this.fetchFileContent(item.path);
          if (fileContent) {
            files.push(fileContent);
          }
        } else if (item.type === 'dir') {
          // Recursively fetch markdown files from subdirectories
          const subFiles = await this.fetchMarkdownFilesFromPath(item.path);
          files.push(...subFiles);
        }
      }
    } catch (error) {
      console.error('Error fetching markdown files:', error);
    }

    return files;
  }

  private async fetchMarkdownFilesFromPath(path: string): Promise<MarkdownFile[]> {
    const files: MarkdownFile[] = [];
    
    try {
      const { data: contents } = await this.octokit.rest.repos.getContent({
        owner: this.config.owner,
        repo: this.config.repo,
        path: path,
        ref: this.config.branch,
      });

      const items = Array.isArray(contents) ? contents : [contents];
      
      for (const item of items) {
        if (item.type === 'file' && item.name.endsWith('.md')) {
          const fileContent = await this.fetchFileContent(item.path);
          if (fileContent) {
            files.push(fileContent);
          }
        } else if (item.type === 'dir') {
          const subFiles = await this.fetchMarkdownFilesFromPath(item.path);
          files.push(...subFiles);
        }
      }
    } catch (error) {
      console.error(`Error fetching files from path ${path}:`, error);
    }

    return files;
  }

  private async fetchFileContent(filePath: string): Promise<MarkdownFile | null> {
    try {
      const { data: file } = await this.octokit.rest.repos.getContent({
        owner: this.config.owner,
        repo: this.config.repo,
        path: filePath,
        ref: this.config.branch,
      });

      if ('content' in file && file.content) {
        const content = Buffer.from(file.content, 'base64').toString('utf-8');
        
        return {
          path: filePath,
          content,
          sha: file.sha,
          lastModified: new Date().toISOString(),
        };
      }
    } catch (error) {
      console.error(`Error fetching file ${filePath}:`, error);
    }

    return null;
  }

  async getMarkdownFiles(): Promise<MarkdownFile[]> {
    return this.fetchMarkdownFiles();
  }
}