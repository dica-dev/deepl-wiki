# DeepL Wiki Frontend

A Next.js frontend for the DeepL Wiki documentation system that provides real-time markdown monitoring and AI-powered chat interface.

## Features

- **Live Markdown Monitoring**: Automatically detects and syncs changes from your GitHub memo repository
- **AI-Powered Chat**: RAG-based chatbot using LlamaIndex for querying documentation
- **Wiki Browser**: Browse and search through your documentation files
- **Real-time Updates**: Live vector embedding updates when documentation changes

## Quick Start

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

4. **Choose your setup option**:
   - **Try Demo**: Click "Try Demo with Mock Data" for instant testing
   - **Real Setup**: Configure with your actual GitHub and Llama API credentials

## Configuration Options

### Option 1: Demo Mode (Recommended for Testing)
On first visit, click **"Try Demo with Mock Data"** to immediately explore the interface with sample documentation from 3 mock repositories.

### Option 2: Real Configuration
Enter your actual credentials in the setup screen:

- **GitHub Token**: Personal access token for GitHub API
  - Go to GitHub Settings → Developer settings → Personal access tokens
  - Generate token with `repo` scope
- **Llama API Key**: API key for Llama models
- **Repository Owner**: Your GitHub username
- **Repository Name**: Name of your memo repository

### Option 3: Environment Variables
Alternatively, set these in your `.env.local` file:
```bash
GITHUB_TOKEN=your_github_token
LLAMA_API_KEY=your_llama_api_key
REPO_OWNER=your_github_username
REPO_NAME=your_memo_repo_name
```

## Usage

### Initial Configuration

On first run, you'll be prompted to enter your configuration:
- **GitHub Token**: For accessing your memo repository
- **Llama API Key**: For AI processing and embeddings
- **Repository Details**: Owner and name of your memo repository

### Chat Interface

The chat interface allows you to:
- Ask questions about your documentation
- Get AI-generated responses based on your repo content
- Maintain conversation context

### Wiki Browser

The wiki browser provides:
- Folder-organized document tree
- Search functionality across all documents
- Document preview and reading
- Real-time updates when files change

## Architecture

- **Markdown Monitor**: Polls GitHub API for repository changes
- **RAG Engine**: Uses LlamaIndex for vector embeddings and retrieval
- **Real-time Updates**: WebSocket-like polling for live document sync
- **Component Architecture**: Modular React components for chat and wiki browsing

## Dependencies

- **Next.js 15**: React framework
- **LlamaIndex**: Vector embeddings and RAG
- **Octokit**: GitHub API client
- **Lucide React**: Icons
- **Tailwind CSS**: Styling

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Configuration Options

### Polling Interval
The markdown monitor polls every 30 seconds by default. You can adjust this in the `MarkdownMonitor` constructor.

### RAG Settings
Configure chunk size, overlap, and retrieval settings in the `RAGEngine` constructor.

### GitHub API
The system uses GitHub's REST API to monitor file changes and fetch content.
