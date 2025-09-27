#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR"/.. && pwd)
BACKEND_VENV="$REPO_ROOT/backend/.venv/bin/python"

"$SCRIPT_DIR/install_backend_deps.sh"

uv pip install --python "$BACKEND_VENV" "torch==2.5.1" "torchaudio==2.5.1"
