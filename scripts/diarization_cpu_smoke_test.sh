#!/bin/bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
GPU_VENV="$REPO_ROOT/gpu_services/.venv"
PYTHON_BIN="$GPU_VENV/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "GPU virtualenv not found at $GPU_VENV. Run 'GPU_CUDA_VARIANT=cpu ./install_deps.sh --gpu' first." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "The 'uv' CLI is required to manage dependencies." >&2
  exit 1
fi
UV_BIN=$(command -v uv)

# Ensure grpcio and protobuf are present in the GPU virtualenv.
if ! "$PYTHON_BIN" -c "import grpc" >/dev/null 2>&1; then
  "$UV_BIN" pip install --python "$PYTHON_BIN" "grpcio>=1.75.1"
fi

if ! "$PYTHON_BIN" -c "import google.protobuf" >/dev/null 2>&1; then
  "$UV_BIN" pip install --python "$PYTHON_BIN" "protobuf>=6.31.1"
elif ! "$PYTHON_BIN" - <<'PY'
import google.protobuf

major = int(google.protobuf.__version__.split('.')[0])
raise SystemExit(0 if major >= 6 else 1)
PY
then
  "$UV_BIN" pip install --python "$PYTHON_BIN" "protobuf>=6.31.1"
fi

# Verify NeMo diarization dependencies are available before starting the service.
if ! "$PYTHON_BIN" -c "import nemo.collections.asr" >/dev/null 2>&1; then
  echo "Missing NeMo diarization dependencies. Re-run 'GPU_CUDA_VARIANT=cpu ./install_deps.sh --gpu'." >&2
  exit 1
fi

if ! "$PYTHON_BIN" -c "import omegaconf" >/dev/null 2>&1; then
  echo "OmegaConf is required for diarization. Re-run 'GPU_CUDA_VARIANT=cpu ./install_deps.sh --gpu'." >&2
  exit 1
fi

# Check that diarization model artifacts are present.
MISSING_ARTIFACTS=$("$PYTHON_BIN" - <<'PY'
from gpu_services.diarization_resources import discover_nemo_artifacts

artifacts = discover_nemo_artifacts()
missing = [str(path) for path in artifacts.iter_required_paths() if not path.is_file()]
print('\n'.join(missing), end='')
PY
)

if [ -n "$MISSING_ARTIFACTS" ]; then
  echo "Missing diarization artifacts:" >&2
  echo "$MISSING_ARTIFACTS" >&2
  echo "Download the NeMo checkpoints listed above into the gpu_services/models/ directory." >&2
  exit 1
fi

AUDIO_DIR="$REPO_ROOT/data/raw"
DEFAULT_SMOKE_AUDIO="$AUDIO_DIR/diarization_smoke.wav"
SMOKE_AUDIO=${DIARIZATION_SMOKE_AUDIO:-$DEFAULT_SMOKE_AUDIO}
SOURCE_AUDIO="$REPO_ROOT/sample_dialogue.wav"

mkdir -p "$(dirname "$SMOKE_AUDIO")"

if [ ! -f "$SMOKE_AUDIO" ]; then
  if [ -f "$SOURCE_AUDIO" ]; then
    cp "$SOURCE_AUDIO" "$SMOKE_AUDIO"
  else
    echo "Smoke test audio not found at $SMOKE_AUDIO and sample_dialogue.wav is missing." >&2
    echo "Provide a short multi-speaker WAV file via DIARIZATION_SMOKE_AUDIO before running the test." >&2
    exit 1
  fi
fi

SMOKE_AUDIO=$("$PYTHON_BIN" -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$SMOKE_AUDIO")

export PYTHONPATH="$REPO_ROOT/backend:$REPO_ROOT"
export DIARIZATION_SERVICE_PORT=${DIARIZATION_SERVICE_PORT:-50052}
export DIARIZATION_LOG_LEVEL=${DIARIZATION_LOG_LEVEL:-INFO}
export DIARIZATION_SMOKE_TARGET="$SMOKE_AUDIO"

cleanup() {
  local status=$?
  if [ -n "${SERVER_PID:-}" ] && ps -p "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  return $status
}
trap cleanup EXIT

"$PYTHON_BIN" -m gpu_services.diarize_service >"$REPO_ROOT/.diarize_service.log" 2>&1 &
SERVER_PID=$!

# Wait for the gRPC port to accept connections.
"$PYTHON_BIN" - <<'PY'
import os
import socket
import time

port = int(os.environ.get('DIARIZATION_SERVICE_PORT', '50052'))
address = ('127.0.0.1', port)
for _ in range(60):
    sock = socket.socket()
    try:
        sock.settimeout(1.0)
        sock.connect(address)
    except OSError:
        time.sleep(1)
    else:
        sock.close()
        break
else:
    raise SystemExit(f"Diarization service did not start on port {port} within timeout")
PY

# Execute a gRPC request against the service and print the diarization segments.
"$PYTHON_BIN" - <<'PY'
import json
import os

import grpc

from app.clients import diarize_pb2, diarize_pb2_grpc

port = os.environ.get('DIARIZATION_SERVICE_PORT', '50052')
channel = grpc.insecure_channel(f'127.0.0.1:{port}')
stub = diarize_pb2_grpc.DiarizeStub(channel)
response = stub.Run(diarize_pb2.AudioRequest(path=os.environ['DIARIZATION_SMOKE_TARGET']))

segments = [
    {
        'speaker': segment.speaker,
        'start': round(segment.start, 3),
        'end': round(segment.end, 3),
    }
    for segment in response.segments
]

print(json.dumps({'segments': segments}, indent=2, ensure_ascii=False))
PY
