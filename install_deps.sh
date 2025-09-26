#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./install_deps.sh [--backend] [--frontend]

Without arguments installs both backend and frontend dependencies. Use flags to
limit the installation scope.
USAGE
}

BACKEND=false
FRONTEND=false

if [ $# -eq 0 ]; then
  BACKEND=true
  FRONTEND=true
else
  for arg in "$@"; do
    case "$arg" in
      --backend)
        BACKEND=true
        ;;
      --frontend)
        FRONTEND=true
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $arg" >&2
        usage >&2
        exit 1
        ;;
    esac
  done
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [ "$BACKEND" = true ]; then
  "$SCRIPT_DIR"/scripts/install_backend_deps.sh
fi

if [ "$FRONTEND" = true ]; then
  "$SCRIPT_DIR"/scripts/install_frontend_deps.sh
fi
