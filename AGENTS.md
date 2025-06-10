# Instructions for Codex Agents

## Overview
This repository contains both backend and frontend code for a local meeting transcription service. All heavy ML models must be mocked in tests.

## Running Tests
- Backend tests: `pytest` inside `backend` directory.
- Frontend tests: `npm test` inside `frontend` directory (uses `vitest`).

Prior to running tests, run code linters and static analysis in the following order:
1. `ruff check backend --fix`
2. `ruff format backend`
3. `mypy backend`
4. `npm run lint` for the frontend.

We are adventurers and do not look for easy ways. Do **not** add ignore directives for `mypy` or `ruff`. If an error cannot be solved, add a question in `QUESTIONS.md`.

## Dependency Installation
The `install_deps.sh` script installs Python and Node dependencies on each environment start. It uses `uv` to create the virtual environment and install packages from `backend/pyproject.toml`.

## Documentation
The `docs/` folder must always contain current documentation. Update it whenever project behavior or structure changes. Include usage instructions, key features and diagrams. Recommended diagrams:
- Database schema diagram.
- Overall process flow of the service.
- File system structure if relevant.
Always keep diagrams up to date. Update `docs/` with any changes in database or process logic.

## Questions and Answers
`QUESTIONS.md` always exists. Read it before starting work. If the owner answered any previous questions, incorporate the information, mark them as resolved, and add new questions if needed.

The `pyproject.toml` sections for `ruff` and `mypy` must not be edited without explicit user instruction.

## Notes for Future Agents
- Do not commit `node_modules` or other large binaries.
- Heavy ML models should be mocked; see `backend/tests` for examples.
- Database uses PostgreSQL via SQLAlchemy. Connection string defined in `backend/app/db/session.py`.

## Code Style
Use Google-style docstrings in English. Functions with more than two arguments
must include an ``Args`` section. For complex return types or large functions,
add a ``Returns`` section. If a function explicitly raises an exception, include
a ``Raises`` section. API endpoints are exempt because their logic should reside
in service layers.
