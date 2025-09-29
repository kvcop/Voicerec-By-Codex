#!/bin/bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
GPU_DIR="$REPO_ROOT/gpu_services"
VENV_DIR="$GPU_DIR/.venv"

GPU_PYTHON_VERSION=${GPU_PYTHON_VERSION:-3.10}
GPU_TORCH_VERSION=${GPU_TORCH_VERSION:-2.8.0}
GPU_TORCHAUDIO_VERSION=${GPU_TORCHAUDIO_VERSION:-2.8.0}
GPU_CUDA_VARIANT=${GPU_CUDA_VARIANT:-cu121}

if ! command -v uv >/dev/null 2>&1; then
  echo "The 'uv' CLI is required to install GPU dependencies." >&2
  exit 1
fi

mkdir -p "$GPU_DIR"

uv venv --python "$GPU_PYTHON_VERSION" "$VENV_DIR"
PYTHON_BIN="$VENV_DIR/bin/python"

if [ "$GPU_CUDA_VARIANT" = "cpu" ]; then
  uv pip install --python "$PYTHON_BIN" \
    "torch==${GPU_TORCH_VERSION}" \
    "torchaudio==${GPU_TORCHAUDIO_VERSION}"
else
  uv pip install --python "$PYTHON_BIN" \
    --index-url "https://download.pytorch.org/whl/${GPU_CUDA_VARIANT}" \
    --extra-index-url "https://pypi.org/simple" \
    "torch==${GPU_TORCH_VERSION}+${GPU_CUDA_VARIANT}" \
    "torchaudio==${GPU_TORCHAUDIO_VERSION}+${GPU_CUDA_VARIANT}"
fi

uv pip install --python "$PYTHON_BIN" \
  "transformers>=4.48.0" \
  "openai-whisper>=20240918" \
  "nemo_toolkit[asr]>=1.25.0" \
  "omegaconf>=2.3.0" \
  "onnxruntime>=1.18.0" \
  "soundfile>=0.12.1"

echo "GPU ASR dependencies installed in $VENV_DIR"
echo "To activate the environment run: source $VENV_DIR/bin/activate"
echo "Whisper weights (large-v2) will be downloaded automatically on first use."
echo "NeMo diarization dependencies installed. Download the diarization checkpoints"
echo "into gpu_services/models/ (see README in that directory)."
