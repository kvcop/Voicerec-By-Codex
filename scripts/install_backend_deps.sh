#!/bin/bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
BACKEND_DIR="$REPO_ROOT/backend"

if [ -f "$BACKEND_DIR/pyproject.toml" ]; then
  (cd "$BACKEND_DIR" && \
    uv venv && \
    uv lock && \
    uv sync --frozen && \
    uv pip install -e .)
fi
