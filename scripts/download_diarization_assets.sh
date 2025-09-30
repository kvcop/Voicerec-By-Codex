#!/bin/bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
MODELS_DIR="$REPO_ROOT/gpu_services/models"
CHECKSUM_FILE="$MODELS_DIR/checksums.sha256"

VAD_URL="https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/resolve/main/frame_vad_multilingual_marblenet_v2.0.nemo"
SPEAKER_URL="https://huggingface.co/nvidia/speakerverification_en_titanet_large/resolve/main/speakerverification_en_titanet_large.nemo"
MSDD_URL="https://api.ngc.nvidia.com/v2/models/nvidia/nemo/diar_msdd_telephonic/versions/1.0.1/files/diar_msdd_telephonic.nemo"

VAD_FILE="vad_multilingual_marblenet.nemo"
SPEAKER_FILE="titanet_large.nemo"
MSDD_FILE="msdd_telephonic.nemo"

mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

command -v curl >/dev/null 2>&1 || {
  echo "curl is required to download diarization artifacts." >&2
  exit 1
}
command -v sha256sum >/dev/null 2>&1 || {
  echo "sha256sum is required to verify diarization artifacts." >&2
  exit 1
}

download() {
  local url="$1"
  local output="$2"
  local label="$3"

  echo "Downloading ${label}..."
  curl -L --fail --retry 3 --retry-delay 3 -o "$output" "$url"
}

write_checksums() {
  cat >"$CHECKSUM_FILE" <<'SHA'
84bda37e925ac6fd740c2ced55642cb79f94f81348e1fa0db992ca50d4b09706  vad_multilingual_marblenet.nemo
e838520693f269e7984f55bc8eb3c2d60ccf246bf4b896d4be9bcabe3e4b0fe3  titanet_large.nemo
SHA
}

verify_checksums() {
  if [ ! -f "$CHECKSUM_FILE" ]; then
    write_checksums
  fi
  echo "Verifying checksums..."
  sha256sum --status -c "$CHECKSUM_FILE" && return 0
  echo "Checksum mismatch detected. Re-downloading affected files." >&2
  return 1
}

ensure_file() {
  local file="$1"
  local url="$2"
  local label="$3"
  local skip_reason="$4"

  if [ -f "$file" ]; then
    echo "Found existing ${label}. Skipping download."
    return 0
  fi

  if [ -n "$skip_reason" ]; then
    echo "Skipping ${label}: $skip_reason"
    return 0
  fi

  download "$url" "$file" "$label"
}

SKIP_MSDD_REASON=""
if [ "${SKIP_MSDD:-0}" != "0" ]; then
  SKIP_MSDD_REASON="SKIP_MSDD flag is set"
elif [ -n "${DIARIZATION_SKIP_MSDD:-}" ]; then
  SKIP_MSDD_REASON="DIARIZATION_SKIP_MSDD flag is set"
fi

ensure_file "$VAD_FILE" "$VAD_URL" "VAD model" ""
ensure_file "$SPEAKER_FILE" "$SPEAKER_URL" "speaker embedding model" ""
ensure_file "$MSDD_FILE" "$MSDD_URL" "MSDD model" "$SKIP_MSDD_REASON"

if ! verify_checksums; then
  # Re-download known files and verify again
  download "$VAD_URL" "$VAD_FILE" "VAD model"
  download "$SPEAKER_URL" "$SPEAKER_FILE" "speaker embedding model"
  write_checksums
  sha256sum -c "$CHECKSUM_FILE"
fi

echo "All requested diarization artifacts are ready under $MODELS_DIR."

if [ -n "$SKIP_MSDD_REASON" ]; then
  echo "MSDD model was skipped (${SKIP_MSDD_REASON}). Set SKIP_MSDD=0 to attempt download via NVIDIA NGC."
fi
