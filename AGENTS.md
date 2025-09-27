# Instructions for Codex Agents

## Overview
This repository contains both backend and frontend code for a local meeting transcription service. All heavy ML models remain mocked in tests.

## Running Tests
- Backend tests: run from inside the `backend` directory using `uv run pytest`.
- Frontend tests: `npm test` inside `frontend` directory (uses `vitest`).
- Always run `uv sync` in the `backend` directory before executing any `uv run` commands or tests. All `uv run` commands must be executed from the `backend` folder and not from the repository root.

Prior to running tests, run code linters and static analysis from the `backend` directory in the following order using `uv run` (do this whenever you modify backend code):
1. `uv run ruff check --fix .`
2. `uv run ruff format .`
3. `uv run mypy .` *(execution may take a long time and that is expected)*

Whenever you modify frontend code, run `npm run lint` from the `frontend` directory and include the command in your execution l
og.

These linting and type-checking commands are mandatory for every backend code change.

We are adventurers and do not look for easy ways. Do **not** add ignore directives for `mypy` or `ruff`. If an error cannot be solved, add a question in `QUESTIONS.md`.

## Dependency Installation
The `install_deps.sh` script installs Python and Node dependencies on each environment start. It uses `uv` to create the virtual environment and install packages from `backend/pyproject.toml`.

## Documentation
The `docs/` folder must always contain current documentation. Update it whenever project behavior or structure changes. Include usage instructions, key features and diagrams. Recommended diagrams:
- Database schema diagram.
- Overall process flow of the service.
- File system structure if relevant.
Always keep diagrams up to date. Update `docs/` with any changes in database or process logic.
After every code change, check whether the documentation requires updates and keep it synchronized with the implementation.

## Questions and Answers
`QUESTIONS.md` always exists. Read it before starting work. If the owner answered any previous questions, incorporate the information, mark them as resolved, and add new questions if needed. For the completed work you should remove paragraphs or whole questions with their answers in the `QUESTIONS.md`.

### Maintaining `QUESTIONS.md`

- Whenever you remove an answered question, verify that the underlying task is fully implemented. If it is not, keep the question.
- If the answer contains knowledge useful for future work, move it into `docs/` (for example, the research summary in `docs/ai-context/speech_stack_research.md`).
- Document every relocated answer by referencing the new documentation in both `README.md` and this `AGENTS.md` file so the context remains discoverable.
- Leave in `QUESTIONS.md` only the items that still require input from the owner.

`LATEST_RESEARCH.md` should exist. It contains latest information about the project with the date specified and version. You should use it whenever possible.

The `pyproject.toml` sections for `ruff` and `mypy` must not be edited without explicit user instruction.

## Requesting Advanced Research
If you need additional analysis that exceeds the scope of the repository documentation,
you may ask the owner to run more capable models: **"o3"**, **"o3 pro"** or **"deep research"**.
Responses from "o3" arrive in roughly 1–3 minutes, "o3 pro" in about 10–20 minutes,
and "deep research" in around 20 minutes. Submit your question in English if you
want the answer in English and clearly state which model you are requesting.
Include your question in `QUESTIONS.md` with an empty placeholder where the owner
can insert the results. Agents without write access may ask the owner directly to
run the research on their behalf.

Only the repository owner should paste the research outcomes into
`QUESTIONS.md`. Provide an empty placeholder below your question where the owner
can insert the results, for example:

```
### Research: <topic>
<your question>
<!-- OWNER: paste research answer here -->
```

Whenever research has been requested or previously completed, mention it in your
response or pull request so the owner can link any new context to the correct
discussion thread.

## Notes for Future Agents
- Do not commit `node_modules` or other large binaries.
- Do not add `package-lock.json` or `uv.lock` back into version control; both files are generated automatically and must remain ignored to avoid merge conflicts.
- Heavy ML models should be mocked; see `backend/tests` for examples.
- Database uses PostgreSQL via SQLAlchemy. Connection string defined in `backend/app/db/session.py`.
- Apply the repository pattern. Repository classes should reside in `backend/app/database/repositories/`.
- Instantiate gRPC clients through a factory so tests can swap in mocks easily.
- When creating new tasks, aim for atomic pieces of work that do not overlap so
  multiple agents can operate in parallel.
- If such isolation is impossible, explicitly list in the user response which
  tasks may overlap or depend on one another and note that they must run
  sequentially.

## Code Style

### Backend
Use Google-style docstrings in English. Functions with more than two arguments
must include an ``Args`` section. For complex return types or large functions,
add a ``Returns`` section. If a function explicitly raises an exception, include
a ``Raises`` section. API endpoints are exempt because their logic should reside
in service layers.

- All functions must have explicit argument and return types.
- Keep controllers (endpoints) thin; place the logic inside service classes.
- Organize asynchronous functions and database access via repositories.


### Frontend
- Write all React components as functional components using hooks.
- Specify explicit TypeScript prop types for every component.
- Follow the structure "component – folder – index.tsx" and use CSS modules
  for styles.
  