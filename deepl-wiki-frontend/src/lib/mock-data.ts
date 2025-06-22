/**
 * Mock data for development and testing
 */

export interface MockDocument {
  path: string;
  content: string;
  lastModified: string;
  sha: string;
}

export const mockDocuments: MockDocument[] = [
  {
    path: "repo1/README.md",
    content: `# Authentication Service

## Overview
The authentication service handles user login, registration, and session management for our application.

## Features
- JWT token-based authentication
- OAuth integration (Google, GitHub)
- Role-based access control (RBAC)
- Session management with Redis
- Password hashing with bcrypt

## API Endpoints

### POST /auth/login
Authenticates a user with email and password.

**Request Body:**
\`\`\`json
{
  "email": "user@example.com",
  "password": "secretpassword"
}
\`\`\`

**Response:**
\`\`\`json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123",
    "email": "user@example.com",
    "role": "user"
  }
}
\`\`\`

### POST /auth/register
Creates a new user account.

## Security Considerations
- All passwords are hashed using bcrypt with salt rounds of 12
- JWT tokens expire after 24 hours
- Rate limiting applied to prevent brute force attacks
- CORS configured for production domains only`,
    lastModified: "2024-06-21T10:30:00Z",
    sha: "abc123def456"
  },
  {
    path: "repo1/API_REFERENCE.md",
    content: `# API Reference

## Base URL
\`https://api.example.com/v1\`

## Authentication
All API requests require authentication via JWT token in the Authorization header:
\`Authorization: Bearer <your-jwt-token>\`

## Endpoints

### Users API

#### GET /users
Retrieves a list of users (admin only).

**Query Parameters:**
- \`page\`: Page number (default: 1)
- \`limit\`: Items per page (default: 10)
- \`role\`: Filter by user role

#### GET /users/:id
Retrieves a specific user by ID.

#### PUT /users/:id
Updates a user's information.

### Posts API

#### GET /posts
Retrieves blog posts.

#### POST /posts
Creates a new blog post (authenticated users only).

#### DELETE /posts/:id
Deletes a blog post (author or admin only).

## Error Handling
The API returns consistent error responses:

\`\`\`json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": ["Email must be a valid email address"]
  }
}
\`\`\`

## Rate Limiting
- 100 requests per hour for authenticated users
- 20 requests per hour for unauthenticated users`,
    lastModified: "2024-06-21T09:15:00Z",
    sha: "def456ghi789"
  },
  {
    path: "repo2/DATABASE_SCHEMA.md",
    content: `# Database Schema

## Overview
Our application uses PostgreSQL as the primary database with the following schema design.

## Tables

### users
Stores user account information.

\`\`\`sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  role VARCHAR(50) DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\`\`\`

### posts
Stores blog post content.

\`\`\`sql
CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  content TEXT,
  author_id UUID REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'draft',
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\`\`\`

### sessions
Tracks user sessions for analytics.

\`\`\`sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  token_hash VARCHAR(255),
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\`\`\`

## Indexes
- \`users_email_idx\`: Index on email for fast lookups
- \`posts_author_idx\`: Index on author_id for user's posts
- \`sessions_token_idx\`: Index on token_hash for session validation

## Migrations
Database migrations are managed using Flyway and stored in \`/migrations\` directory.`,
    lastModified: "2024-06-21T11:45:00Z",
    sha: "ghi789jkl012"
  },
  {
    path: "repo2/DEPLOYMENT.md",
    content: `# Deployment Guide

## Production Environment

### Prerequisites
- Docker and Docker Compose
- PostgreSQL 14+
- Redis 6+
- Node.js 18+

### Environment Variables
Create a \`.env\` file with the following variables:

\`\`\`bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/myapp
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=24h

# External Services
STRIPE_SECRET_KEY=sk_live_...
SENDGRID_API_KEY=SG...

# App Configuration
NODE_ENV=production
PORT=3000
CORS_ORIGIN=https://yourdomain.com
\`\`\`

### Docker Deployment

1. Build the Docker image:
\`\`\`bash
docker build -t myapp:latest .
\`\`\`

2. Run with Docker Compose:
\`\`\`bash
docker-compose up -d
\`\`\`

### Kubernetes Deployment
We use Kubernetes for container orchestration:

\`\`\`yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-url
\`\`\`

### Health Checks
The application exposes health check endpoints:
- \`/health\`: Basic health check
- \`/health/db\`: Database connectivity check
- \`/health/redis\`: Redis connectivity check

## Monitoring
- Prometheus metrics at \`/metrics\`
- Structured logging with Winston
- Error tracking with Sentry`,
    lastModified: "2024-06-21T14:20:00Z",
    sha: "jkl012mno345"
  },
  {
    path: "repo3/FRONTEND_ARCHITECTURE.md",
    content: `# Frontend Architecture

## Overview
Our frontend is built with React 18 and TypeScript, following modern development practices.

## Tech Stack
- **React 18**: Component library with concurrent features
- **TypeScript**: Type safety and better developer experience
- **Vite**: Fast build tool and development server
- **React Query**: Server state management
- **Zustand**: Client state management
- **Tailwind CSS**: Utility-first styling
- **React Hook Form**: Form handling
- **React Router**: Client-side routing

## Project Structure

\`\`\`
src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI components (Button, Input, etc.)
│   ├── forms/          # Form components
│   └── layout/         # Layout components
├── pages/              # Route components
├── hooks/              # Custom React hooks
├── services/           # API services
├── stores/             # Zustand stores
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
└── styles/             # Global styles and Tailwind config
\`\`\`

## State Management

### Server State (React Query)
Used for data fetching, caching, and synchronization:

\`\`\`typescript
const { data: posts, isLoading } = useQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  staleTime: 5 * 60 * 1000, // 5 minutes
});
\`\`\`

### Client State (Zustand)
Used for UI state and user preferences:

\`\`\`typescript
interface AppStore {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
}

const useAppStore = create<AppStore>((set) => ({
  theme: 'light',
  sidebarOpen: false,
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
\`\`\`

## Component Patterns

### Composition Pattern
We favor composition over prop drilling:

\`\`\`typescript
<Card>
  <Card.Header>
    <Card.Title>User Profile</Card.Title>
  </Card.Header>
  <Card.Content>
    <UserForm user={user} />
  </Card.Content>
</Card>
\`\`\`

### Custom Hooks
Encapsulate component logic in reusable hooks:

\`\`\`typescript
function useAuth() {
  const { data: user } = useQuery(['auth/me'], fetchCurrentUser);
  
  const login = useMutation(loginUser);
  const logout = useMutation(logoutUser);
  
  return {
    user,
    isAuthenticated: !!user,
    login: login.mutate,
    logout: logout.mutate,
  };
}
\`\`\`

## Performance Optimization
- Code splitting with React.lazy
- Image optimization with next/image
- Bundle analysis with webpack-bundle-analyzer
- Lighthouse CI for performance monitoring`,
    lastModified: "2024-06-21T16:10:00Z",
    sha: "mno345pqr678"
  },
  {
    path: "repo3/TESTING_STRATEGY.md",
    content: `# Testing Strategy

## Overview
We follow a comprehensive testing approach with unit, integration, and end-to-end tests.

## Testing Pyramid

### Unit Tests (70%)
- **Jest**: JavaScript testing framework
- **React Testing Library**: React component testing
- **MSW**: API mocking

Example unit test:
\`\`\`typescript
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    screen.getByRole('button').click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
\`\`\`

### Integration Tests (20%)
- **Supertest**: API endpoint testing
- **Test containers**: Database testing with Docker

Example integration test:
\`\`\`typescript
describe('POST /api/users', () => {
  it('creates a new user', async () => {
    const userData = {
      email: 'test@example.com',
      password: 'password123'
    };

    const response = await request(app)
      .post('/api/users')
      .send(userData)
      .expect(201);

    expect(response.body.user.email).toBe(userData.email);
    expect(response.body.user.password).toBeUndefined();
  });
});
\`\`\`

### End-to-End Tests (10%)
- **Playwright**: Cross-browser testing
- **Docker Compose**: Full environment setup

Example E2E test:
\`\`\`typescript
test('user can register and login', async ({ page }) => {
  // Register
  await page.goto('/register');
  await page.fill('[data-testid=email]', 'test@example.com');
  await page.fill('[data-testid=password]', 'password123');
  await page.click('[data-testid=submit]');
  
  // Should redirect to dashboard
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Welcome');
});
\`\`\`

## Test Coverage
- Minimum 80% code coverage
- 100% coverage for critical paths (auth, payments)
- Coverage reports generated with Istanbul

## Continuous Integration
Tests run on every PR:
1. Lint and type checking
2. Unit and integration tests
3. Build verification
4. E2E tests on staging environment

## Test Data Management
- Factories for test data generation
- Database seeding for consistent test state
- Cleanup after each test suite`,
    lastModified: "2024-06-21T13:30:00Z",
    sha: "pqr678stu901"
  }
];

export class MockRAGEngine {
  private documents: MockDocument[] = [];
  private isIndexed = false;

  constructor() {
    // Simulate loading time
    setTimeout(() => {
      this.documents = mockDocuments;
      this.isIndexed = true;
      console.log('Mock RAG engine initialized with', this.documents.length, 'documents');
    }, 2000);
  }

  async indexDocuments(docs: Array<{ path: string; content: string }>) {
    console.log('Mock: Indexing', docs.length, 'documents...');
    this.documents = docs.map((doc, i) => ({
      ...doc,
      lastModified: new Date().toISOString(),
      sha: `mock-sha-${i}`
    }));
    this.isIndexed = true;
  }

  async query(question: string): Promise<string> {
    if (!this.isIndexed) {
      throw new Error('RAG engine not ready');
    }

    console.log('Mock query:', question);
    
    // Simple mock responses based on keywords
    const lowerQuestion = question.toLowerCase();
    
    if (lowerQuestion.includes('auth') || lowerQuestion.includes('login')) {
      return `Based on the authentication service documentation, our system uses JWT token-based authentication with the following features:

- JWT tokens for session management
- OAuth integration with Google and GitHub
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Rate limiting to prevent brute force attacks

The main login endpoint is POST /auth/login which accepts email and password, returning a JWT token and user information. All passwords are securely hashed using bcrypt with 12 salt rounds.`;
    }
    
    if (lowerQuestion.includes('database') || lowerQuestion.includes('schema')) {
      return `Our database schema uses PostgreSQL with the following main tables:

**users table**: Stores user account information with UUID primary keys, email, password hash, names, and roles.

**posts table**: Contains blog post content with references to authors and publication status.

**sessions table**: Tracks user sessions with token hashes and expiration times.

The schema includes optimized indexes for performance:
- users_email_idx for fast email lookups
- posts_author_idx for retrieving user posts
- sessions_token_idx for session validation

Database migrations are managed using Flyway.`;
    }
    
    if (lowerQuestion.includes('deploy') || lowerQuestion.includes('production')) {
      return `For deployment, we support both Docker and Kubernetes environments:

**Docker Deployment:**
- Uses Docker Compose for local/staging environments
- Requires PostgreSQL 14+ and Redis 6+
- Environment variables for database URLs, JWT secrets, and external service keys

**Kubernetes:**
- Production deployment with 3 replicas for high availability
- Secrets management for sensitive configuration
- Health check endpoints at /health, /health/db, and /health/redis

**Monitoring:**
- Prometheus metrics at /metrics endpoint
- Structured logging with Winston
- Error tracking with Sentry integration

The application requires Node.js 18+ and includes comprehensive health checks for all dependencies.`;
    }
    
    if (lowerQuestion.includes('frontend') || lowerQuestion.includes('react')) {
      return `Our frontend architecture is built with modern React patterns:

**Tech Stack:**
- React 18 with TypeScript for type safety
- Vite for fast development and building
- React Query for server state management
- Zustand for client state management
- Tailwind CSS for styling

**Architecture Patterns:**
- Composition pattern over prop drilling
- Custom hooks for reusable logic
- Component-based organization in src/components/

**Performance:**
- Code splitting with React.lazy
- Image optimization
- Bundle analysis and monitoring

The frontend follows a clear separation between server state (React Query) and client state (Zustand), with comprehensive TypeScript coverage.`;
    }
    
    if (lowerQuestion.includes('test') || lowerQuestion.includes('testing')) {
      return `Our testing strategy follows the testing pyramid approach:

**Unit Tests (70%):**
- Jest framework with React Testing Library
- MSW for API mocking
- Focus on component behavior and logic

**Integration Tests (20%):**
- Supertest for API endpoint testing
- Test containers with Docker for database testing
- Full request/response cycle validation

**End-to-End Tests (10%):**
- Playwright for cross-browser testing
- Docker Compose for full environment setup
- Critical user journey validation

**Coverage Requirements:**
- Minimum 80% overall code coverage
- 100% coverage for critical paths (authentication, payments)
- Automated coverage reporting with Istanbul

All tests run in CI/CD pipeline on every pull request.`;
    }
    
    // Default response
    return `I found relevant information in the documentation about "${question}". Based on the available docs, I can help you with:

- Authentication and security implementation
- Database schema and structure
- Deployment and infrastructure setup
- Frontend React architecture
- Testing strategies and coverage

Could you be more specific about what aspect you'd like to know more about?`;
  }

  async updateDocuments(docs: Array<{ path: string; content: string }>) {
    await this.indexDocuments(docs);
  }

  isReady(): boolean {
    return this.isIndexed;
  }

  getIndexedDocumentCount(): number {
    return this.documents.length;
  }
}