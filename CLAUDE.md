# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Monorepo for a local meeting transcription service with:
- **Backend**: Python/FastAPI with PostgreSQL via SQLAlchemy
- **Frontend**: React/TypeScript with Vite and shadcn components
- **Infrastructure**: Mock GPU services for ASR, speaker identification, and summarization

## Critical Development Commands

### Backend (MUST run from `backend/` directory)
```bash
cd backend
uv sync                       # Required before any uv run commands
uv run ruff check --fix .     # Fix linting issues
uv run ruff format .          # Format code
uv run mypy .                 # Type checking (slow is normal)
uv run pytest                 # Run tests
uv run uvicorn app.main:app --reload  # Start dev server
```

### Frontend (run from `frontend/` directory)
```bash
cd frontend
npm run dev    # Development server
npm run lint   # ESLint
npm test       # Vitest tests
npm run build  # Production build
```

### Infrastructure
```bash
docker compose -f infra/docker-compose.gpu.yml up  # Mock GPU services
```

## Architecture & Code Organization

### Backend Structure
- `backend/app/api/` - FastAPI endpoints (keep thin, logic in services)
- `backend/app/core/` - Core utilities and configuration
- `backend/app/db/` - Database session and base models
- `backend/app/models/` - SQLAlchemy models
- `backend/app/database/repositories/` - Repository pattern implementations
- Service classes contain business logic, not endpoints
- gRPC clients use factory pattern for testability

### Frontend Structure
- Functional components with hooks only
- TypeScript prop types required
- Component folder structure with index.tsx
- CSS modules for styling

## Code Style Requirements

### Python
- Google-style docstrings
- Single quotes for strings
- Line length: 100 characters
- All functions need explicit type hints
- Functions with >2 args need `Args` docstring section
- NO mypy/ruff ignore directives (add issues to QUESTIONS.md instead)

### TypeScript/React
- Functional components only
- Explicit TypeScript types for all props
- ESLint configured, must pass before commit

## Task Completion Checklist
Before marking any task complete:
1. Run all linters/formatters in order (backend: ruff check → ruff format → mypy)
2. Run all tests (backend: pytest, frontend: npm test)
3. Update documentation in `docs/` if behavior changed
4. Verify no secrets/sensitive data in code

## Important Notes
- **AGENTS.md** contains detailed instructions for complex tasks
- **QUESTIONS.md** for unresolved issues or advanced research requests
- Database connection via `.env` file (see `.env.example`)
- GPU communication requires VPN/mTLS (see `docs/gpu_security.md`)
- Repository pattern mandatory for database operations
- Heavy ML models stay mocked in tests
- Secure storage migration deadline: end of 2025

## Environment Configuration
Create `.env` file in repository root with:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/app
GPU_GRPC_HOST=gpu.example.com
GPU_GRPC_PORT=50051
GPU_GRPC_USE_TLS=true
GPU_GRPC_TLS_CA=/path/to/ca.pem
GPU_GRPC_TLS_CERT=/path/to/client.pem
GPU_GRPC_TLS_KEY=/path/to/client.key
```