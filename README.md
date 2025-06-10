# Voicerec-By-Codex

This repository hosts a monorepo for a local meeting transcription service. It contains a Python backend built with FastAPI and SQLAlchemy and a React frontend powered by Vite.
**Note:** A secure storage milestone is scheduled for completion by the end of 2025.

## Structure
- `backend/` – FastAPI application and tests
- `frontend/` – React application using Vite
- `docs/` – documentation and mermaid diagrams in `.md` files
- `install_deps.sh` – install Python and Node dependencies using `uv` and `npm`
- `AGENTS.md` – instructions for Codex agents
- `QUESTIONS.md` – ongoing Q&A with the repository owner

## Configuration
The backend reads settings from a `.env` file using **pydantic-settings**. Create
that file in the repository root and set the `DATABASE_URL` variable to configure
the PostgreSQL connection.

## Next Steps
1. Flesh out endpoints for uploading audio and returning transcripts.
2. Add authentication and database models.
3. Implement frontend UI with shadcn components.
4. Integrate local ML models for speech-to-text and speaker identification (mocked in tests).
5. Document database schema and overall process in `docs/`.

## Testing

The project contains tests for both backend and frontend parts. Run them after installing dependencies:

```bash
./install_deps.sh
```

### Backend

Execute the following commands from the `backend` directory:

```bash
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
uv run pytest
```

### Frontend

Navigate to the `frontend` directory and run:

```bash
npm run lint
npm test
```

Frontend tests use **vitest** and the configuration resides in `frontend/vitest.config.ts`.

## Future Milestones
- Secure storage for transcripts with encryption at rest is scheduled for completion by the end of 2025.

