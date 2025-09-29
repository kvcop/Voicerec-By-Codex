#!/bin/bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
GPU_VENV="$REPO_ROOT/gpu_services/.venv"
PYTHON_BIN="$GPU_VENV/bin/python"
UV_BIN=$(command -v uv)

if [ ! -x "$PYTHON_BIN" ]; then
  echo "GPU virtualenv not found at $GPU_VENV. Run 'GPU_CUDA_VARIANT=cpu ./install_deps.sh --gpu' first." >&2
  exit 1
fi

if [ -z "$UV_BIN" ]; then
  echo "The 'uv' CLI is required to manage dependencies." >&2
  exit 1
fi

# Ensure grpcio is present in the GPU virtualenv (install_gpu_deps already installs it, but keep this idempotent).
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

AUDIO_DIR="$REPO_ROOT/data/raw"
SMOKE_AUDIO="$AUDIO_DIR/test_smoke.wav"
SOURCE_AUDIO="$REPO_ROOT/sample_dialogue.wav"
mkdir -p "$AUDIO_DIR"
if [ ! -f "$SMOKE_AUDIO" ]; then
  if [ ! -f "$SOURCE_AUDIO" ]; then
    echo "Sample audio file not found at $SOURCE_AUDIO" >&2
    exit 1
  fi
  cp "$SOURCE_AUDIO" "$SMOKE_AUDIO"
fi

export PYTHONPATH="$REPO_ROOT/backend:$REPO_ROOT"
export ASR_MODEL_SIZE=${ASR_MODEL_SIZE:-tiny}
export ASR_SERVICE_PORT=${ASR_SERVICE_PORT:-50051}
export TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE:-$REPO_ROOT/.cache/huggingface}

CACHE_DIR="$TRANSFORMERS_CACHE"
mkdir -p "$CACHE_DIR"

cleanup() {
  local status=$?
  if [ -n "${SERVER_PID:-}" ] && ps -p "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  return $status
}
trap cleanup EXIT

"$PYTHON_BIN" -m gpu_services.asr_service >"$REPO_ROOT/.asr_service.log" 2>&1 &
SERVER_PID=$!

# Wait for the gRPC port to accept connections.
"$PYTHON_BIN" - <<'PY'
import os
import socket
import time

port = int(os.environ.get('ASR_SERVICE_PORT', '50051'))
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
    raise SystemExit(f"ASR service did not start on port {port} within timeout")
PY

# Execute a gRPC request against the service and print the transcription.
"$PYTHON_BIN" - <<'PY'
import grpc
from app.clients import transcribe_pb2, transcribe_pb2_grpc

channel = grpc.insecure_channel('127.0.0.1:' + str(__import__('os').environ.get('ASR_SERVICE_PORT', '50051')))
stub = transcribe_pb2_grpc.TranscribeStub(channel)
response = stub.Run(transcribe_pb2.AudioRequest(path='data/raw/test_smoke.wav'))
print(response.text)
PY
