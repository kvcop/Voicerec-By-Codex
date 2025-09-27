# Project Structure - Voicerec By Codex

This document provides the complete technology stack and file tree structure for the Voicerec meeting transcription service. **AI agents MUST read this file to understand the project organization before making any changes.**

## Technology Stack

### Backend Technologies
- **Python 3.13+** with **uv** - Fast Python package installer and resolver
- **FastAPI 0.115.12+** - Modern async web framework with automatic API documentation
- **SQLAlchemy 2.0.41+** with **asyncpg** - Async ORM with PostgreSQL driver
- **Pydantic Settings 2.0+** - Configuration management with type validation and .env support
- **Uvicorn 0.34.3+** - Lightning-fast ASGI server for production

### Integration Services & APIs
- **gRPC** - High-performance RPC framework for GPU node communication
- **PostgreSQL** - Primary database with async support via asyncpg
- **GPU Services** (mocked in development):
  - ASR (Automatic Speech Recognition) service
  - Speaker identification service
  - Summarization service
- **mTLS/VPN** - Secure communication with GPU nodes

### Real-time Communication
- **Server-Sent Events (SSE)** - Real-time transcript streaming
- **httpx 0.28.1+** - Async HTTP client for external service communication
- **python-multipart 0.0.7+** - Multipart form data handling for audio uploads

### Development & Quality Tools
- **Ruff 0.11.13** - Extremely fast Python linter and formatter (replaces Black, isort, and more)
- **mypy 1.16.0+** - Static type checker with strict configuration
- **pytest 8.4.0+** with **pytest-asyncio** - Testing framework with async support
- **Pre-commit hooks** - Automated code quality checks

### Frontend Technologies
- **TypeScript 5.0+** - Type-safe JavaScript development
- **React 18.2+** - Component-based UI framework
- **Vite 5.0+** - Next-generation frontend build tool
- **Tailwind CSS** with **shadcn/ui** - Utility-first CSS with component library
- **Vitest 3.2.3+** - Fast unit testing framework
- **ESLint 9.0+** - JavaScript/TypeScript linting
- **React Testing Library** - Component testing utilities

### Infrastructure & Deployment
- **Docker Compose** - Local development environment for GPU service mocks
- **Environment-based configuration** - Separate configs for dev/staging/prod
- **GitHub Actions** - CI/CD pipeline (planned)

### Future Technologies
- **Secure Storage System** - Encrypted storage for audio and transcripts (deadline: end of 2025)
- **Advanced ML Models** - Production GPU-backed transcription and analysis
- **Kubernetes** - Container orchestration for production deployment

## Complete Project Structure

```
Voicerec-By-Codex/
├── README.md                           # Project overview, setup instructions, and roadmap
├── CLAUDE.md                           # Master AI context with development commands
├── AGENTS.md                           # Detailed instructions for AI agents
├── QUESTIONS.md                        # Q&A between agents and repository owner
├── .gitignore                          # Git ignore patterns
├── .env.example                        # Environment variable template
├── install_deps.sh                     # Dependency installation script
├── install_postgres.sh                 # PostgreSQL setup script
├── package-lock.json                   # Node.js dependency lock (frontend)
├── .claude/                            # Claude-specific configuration
│   └── CLAUDE.md                       # User's global instructions
├── .github/                            # GitHub configuration
│   └── workflows/                      # CI/CD workflows (future)
├── .serena/                            # Serena MCP server memories
│   └── memories/                       # Project knowledge base
│       ├── project_overview.md         # High-level project description
│       ├── suggested_commands.md       # Development command reference
│       ├── code_style_and_conventions.md # Coding standards
│       └── task_completion_checklist.md  # Quality assurance checklist
├── backend/                            # FastAPI backend application
│   ├── pyproject.toml                  # Python project configuration
│   ├── uv.lock                         # Python dependency lock
│   ├── app/                            # Application source code
│   │   ├── __init__.py                 # Package initialization
│   │   ├── main.py                     # FastAPI application entry point
│   │   ├── grpc_client.py              # gRPC client factory and implementations
│   │   ├── api/                        # API endpoints layer
│   │   │   ├── __init__.py             # API package initialization
│   │   │   └── meeting.py              # Meeting/transcript endpoints
│   │   ├── core/                       # Core configuration and utilities
│   │   │   ├── __init__.py             # Core package initialization
│   │   │   └── settings.py             # Pydantic settings (DB, GPU config)
│   │   ├── db/                         # Database layer
│   │   │   ├── __init__.py             # DB package initialization
│   │   │   └── session.py              # AsyncSession factory
│   │   └── models/                     # SQLAlchemy models
│   │       └── __init__.py             # Models package initialization
│   └── tests/                          # Test suite
│       ├── __init__.py                 # Test package initialization
│       ├── test_main.py                # Application tests
│       ├── test_meeting.py             # Meeting API tests
│       └── test_grpc_client.py         # gRPC client tests
├── frontend/                           # React frontend application
│   ├── package.json                    # Node.js project configuration
│   ├── package-lock.json               # Node.js dependency lock
│   ├── tsconfig.json                   # TypeScript configuration
│   ├── vite.config.ts                  # Vite build configuration
│   ├── vitest.config.ts                # Vitest test configuration
│   ├── eslint.config.js                # ESLint configuration
│   ├── .eslintrc.cjs                   # ESLint rules (legacy format)
│   ├── index.html                      # Application HTML entry point
│   └── src/                            # Source code
│       ├── main.tsx                    # React application entry point
│       ├── App.test.tsx                # Application component tests
│       ├── components/                 # React components
│       │   ├── App/                    # Main application component
│       │   │   ├── index.tsx           # App component implementation
│       │   │   └── styles.module.css   # App component styles
│       │   └── Dialog/                 # Dialog component
│       │       ├── index.tsx           # Dialog component implementation
│       │       └── styles.module.css   # Dialog component styles
│       └── locales/                    # Internationalization
│           ├── en.json                 # English translations
│           └── ru.json                 # Russian translations
├── docs/                               # Project documentation
│   ├── README.md                       # Documentation overview
│   ├── database_diagram.md             # Database schema documentation
│   ├── filesystem_structure.md         # File organization patterns
│   ├── gpu_security.md                 # GPU node security configuration
│   ├── process_overview.md             # System process flow
│   ├── secure_storage_todo.md          # Secure storage implementation plan
│   ├── ai-context/                     # AI-optimized documentation
│   │   ├── project-structure.md        # This file - project organization
│   │   ├── docs-overview.md            # Documentation architecture
│   │   ├── system-integration.md       # Cross-component patterns (to be created)
│   │   ├── deployment-infrastructure.md # Infrastructure docs (to be created)
│   │   └── handoff.md                  # Task continuity (to be created)
│   ├── specs/                          # Technical specifications
│   │   └── [spec files]                # Feature and API specifications
│   └── open-issues/                    # Known issues and TODOs
│       └── [issue files]               # Issue tracking documents
├── protos/                             # Protocol buffer definitions
│   └── [proto files]                   # gRPC service definitions
├── infra/                              # Infrastructure configuration
│   ├── docker-compose.ci.yml           # PostgreSQL service for CI pipelines
│   ├── docker-compose.dev.yml          # PostgreSQL service for local development
│   └── docker-compose.gpu.yml          # Mock GPU services configuration
├── data/                               # Data storage (temporary)
│   └── raw/                            # Raw audio storage (migrate by 2025)
└── logs/                               # Application logs
    └── [log files]                     # Runtime logs and debugging
```

## Key Architectural Decisions

### Repository Pattern
- All database modules live under `backend/app/db/` (session management, base metadata, and repository classes as they are introduced)
- Separation of business logic from data access layer
- Easier testing through dependency injection

### Service Layer Architecture
- Thin controllers (API endpoints) with logic in service classes
- Services handle business rules and orchestration
- Clear separation of concerns

### gRPC Client Factory Pattern
- Factory pattern for creating gRPC clients
- Easy mocking for tests
- Centralized configuration management

### Component-Based Frontend
- Functional components with TypeScript
- CSS modules for styling isolation
- Folder-based component organization

### Configuration Management
- Environment-based configuration via .env files
- Pydantic for type-safe settings
- Separate configs for different environments

## Development Workflow

### Backend Development
1. All commands run from `backend/` directory
2. Run `uv sync` before any development
3. Use `uv run` prefix for all Python commands
4. Strict linting with ruff and mypy (no ignore directives)

### Frontend Development
1. All commands run from `frontend/` directory
2. Component-folder structure with index.tsx
3. TypeScript with explicit prop types
4. Vitest for testing with jsdom environment

### Quality Assurance
1. Pre-commit hooks for automatic checks
2. Required linting before commits
3. Test coverage requirements
4. Documentation updates with code changes

---

*This document is the authoritative source for project structure and technology decisions. Update it whenever the architecture evolves.*