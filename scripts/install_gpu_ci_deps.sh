#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./scripts/install_gpu_ci_deps.sh [--ci]

Installs the backend virtual environment and seeds it with CPU-only
PyTorch wheels so GPU CI checks can run without CUDA downloads.

Options:
  --ci    Optimise dependency installation for CI runners by forcing
          CPU wheels (no NVIDIA libraries are fetched).
USAGE
}

CI_MODE=false
while (($# > 0)); do
  case "$1" in
    --ci)
      CI_MODE=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR"/.. && pwd)
BACKEND_VENV="$REPO_ROOT/backend/.venv/bin/python"

"$SCRIPT_DIR/install_backend_deps.sh"

uv_args=()
if [ "$CI_MODE" = true ]; then
  uv_args+=(--torch-backend cpu)
fi

uv pip install "${uv_args[@]}" --python "$BACKEND_VENV" "torch==2.8.0" "torchaudio==2.8.0"
