#!/bin/bash
set -e

#
# 1. Python dependencies
#
if [ -f backend/pyproject.toml ]; then
    cd backend && \
    uv venv && \
    uv sync && \
    uv pip install -e . && \
    source .venv/bin/activate && \
    cd -
fi

#
# 2. Node dependencies
#
if [ -f frontend/package.json ]; then
    cd frontend && npm install && cd -
fi
