#!/bin/bash
set -e

# Python dependencies
if [ -f backend/pyproject.toml ]; then
    cd backend
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    uv sync
    cd -
fi

# Node dependencies
if [ -f frontend/package.json ]; then
    cd frontend && npm install && cd -
fi
