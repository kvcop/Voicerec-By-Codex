# Voicerec-By-Codex

This repository hosts a monorepo for a local meeting transcription service. It contains a Python backend built with FastAPI and SQLAlchemy and a React frontend powered by Vite.

## Structure
- `backend/` – FastAPI application and tests
- `frontend/` – React application using Vite
- `docs/` – documentation and mermaid diagrams in `.md` files
- `install_deps.sh` – install Python and Node dependencies using `uv` and `npm`
- `AGENTS.md` – instructions for Codex agents
- `QUESTIONS.md` – ongoing Q&A with the repository owner

## Next Steps
1. Flesh out endpoints for uploading audio and returning transcripts.
2. Add authentication and database models.
3. Implement frontend UI with shadcn components.
4. Integrate local ML models for speech-to-text and speaker identification (mocked in tests).
5. Document database schema and overall process in `docs/`.
