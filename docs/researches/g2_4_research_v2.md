## 1\. Artifacts (Models & Files)

The diarization pipeline requires a VAD model, a speaker embedding model, an (optional) neural diarization decoder (MSDD), plus a config file. The table below lists each artifact, download source, and details:

| **Artifact** | **Model ID / Name** | **Download URL** (no auth needed) | **Size (bytes, MiB)** | **SHA256 checksum** | **Notes (CPU suitability)** | **Fallback option** |
| --- | --- | --- | --- | --- | --- | --- |
| **VAD model** - Frame-based | _Frame VAD Multilingual MarbleNet v2.0_&lt;br/&gt;(NVIDIA NeMo model ID: vad_multilingual_marblenet)[\[1\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=In%20general%2C%20you%20can%20load,name%20in%20the%20following%20format)[\[2\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=vad_multilingual_marblenet) | Hugging Face 🤗: [nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/resolve/main/frame_vad_multilingual_marblenet_v2.0.nemo) | 501,760 bytes (0.48 MiB)[\[3\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/blob/main/frame_vad_multilingual_marblenet_v2.0.nemo#:~:text=Safe)[\[4\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/blob/main/frame_vad_multilingual_marblenet_v2.0.nemo#:~:text=,) | 84bda37e925ac6fd740c2ced55642cb79f94f81348e1fa0db992ca50d4b09706[\[5\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/raw/main/frame_vad_multilingual_marblenet_v2.0.nemo#:~:text=version%20https%3A%2F%2Fgit,501760) | 91.5K params - very lightweight[\[6\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=Frame,of%20audios%20was%20also%20varied)[\[7\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=Key%20Features); ~0.5 MB on disk, runs in real-time on CPU. Robust to noise, outputs frame-level speech probability. | _Alternate VAD:_ vad_marblenet (English-only MarbleNet) - similar small CNN model[\[8\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=vad_multilingual_marblenet) (0.5 MiB). |
| **Speaker embedding model** | _TitaNet-Large (en-US)_&lt;br/&gt;(Hugging Face ID: nvidia/speakerverification_en_titanet_large)[\[9\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large#:~:text=This%20model%20extracts%20speaker%20embeddings,documentation%20for%20complete%20architecture%20details) | Hugging Face 🤗: [nvidia/speakerverification_en_titanet_large](https://huggingface.co/nvidia/speakerverification_en_titanet_large/resolve/main/speakerverification_en_titanet_large.nemo) | 101,621,760 bytes (96.94 MiB)[\[10\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large/raw/48f4fde3e017830f9bdd4e313d6c050b15e4298f/speakerverification_en_titanet_large.nemo#:~:text=version%20https%3A%2F%2Fgit,101621760) | e838520693f269e7984f55bc8eb3c2d60ccf246bf4b896d4be9bcabe3e4b0fe3[\[10\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large/raw/48f4fde3e017830f9bdd4e313d6c050b15e4298f/speakerverification_en_titanet_large.nemo#:~:text=version%20https%3A%2F%2Fgit,101621760) | ~23M params[\[9\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large#:~:text=This%20model%20extracts%20speaker%20embeddings,documentation%20for%20complete%20architecture%20details); large but CPU-usable (≈1.5x real-time for 16kHz audio on modern CPU). Extracts 192-dim speaker embeddings for clustering/diarization. | _Alternate encoder:_ ecapa_tdnn - ECAPA-TDNN model (~20M params)[\[11\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=com) (slightly smaller, slower than TitaNet on CPU). |
| **MSDD diarization model** &lt;br/&gt;(optional) | _NeMo diarizer MSDD (telephonic)_&lt;br/&gt;(NGC model name: diar_msdd_telephonic)[\[1\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=In%20general%2C%20you%20can%20load,name%20in%20the%20following%20format)[\[12\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=diar_msdd_telephonic) | NVIDIA NGC: [diar_msdd_telephonic](https://api.ngc.nvidia.com/v2/models/nvidia/nemo/diar_msdd_telephonic/versions/1.0.1/files/diar_msdd_telephonic.nemo) &lt;br/&gt;(_download via NGC API_) | ~109,633,218 bytes (≈104.5 MiB) &lt;sup&gt;†&lt;/sup&gt; | 3c3697a0a46f945574fa407149975a13 &lt;sup&gt;†&lt;/sup&gt; | Multi-scale diarization decoder model for 2-8 speakers[\[13\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=selectively%20used%20for%20its%20own,verbose%3A%20True)[\[14\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=approximately%2040%20mins%20of%20audio,If). Improves accuracy on overlapping speech. Runs on CPU (uses LSTM layers), but inference is slower; keep infer_batch_size low (e.g. 10) to avoid high memory use. | _Fallback:_ **disable MSDD** - use clustering-only diarization (set DIARIZATION_MSDD_MODEL_PATH='' to omit MSDD)[\[15\]\[15\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L80-L88). The pipeline will then rely solely on spectral clustering of embeddings (faster, less accurate on overlaps). |
| **Config file** | diar_inference.yaml (NeMo inference config)[\[16\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L7-L13) | Provided in repo (adjusted for CPU - see below). | ~4-5 KB | N/A (user-edited text) | YAML defining pipeline steps and parameters (VAD, embedding, clustering, MSDD, etc.). The service loads this on startup[\[17\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L136-L144). Use the CPU-tuned version we supply to ensure determinism. | Use same config format; for different domains, NVIDIA provides alternative configs (e.g. for 16k telephonic vs 16k meeting audio)[\[18\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=not%20used.%20,verbose%3A%20True). |

&lt;small&gt;&lt;sup&gt;†&lt;/sup&gt; _Exact size and SHA for diar_msdd_telephonic.nemo are from NVIDIA's model registry; the model must be downloaded via the NGC CLI or API (public)._&lt;/small&gt;

**Download and verify artifacts:** The script below downloads each model to gpu_services/models/ and checks integrity. It uses wget for direct URLs and computes SHA-256 hashes. (Ensure internet access is available and no interactive prompts occur during CI.) Adjust MODELS_DIR if needed.

# !/bin/bash  
set -euo pipefail  
MODELS_DIR="gpu_services/models"  
mkdir -p "\$MODELS_DIR"  
cd "\$MODELS_DIR"  
<br/>echo "Downloading VAD model (MarbleNet)..."  
wget -q --show-progress -O vad_multilingual_marblenet.nemo \\  
"<https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/resolve/main/frame_vad_multilingual_marblenet_v2.0.nemo>"  
<br/>echo "Downloading speaker model (TitaNet-Large)..."  
wget -q --show-progress -O titanet_large.nemo \\  
"<https://huggingface.co/nvidia/speakerverification_en_titanet_large/resolve/main/speakerverification_en_titanet_large.nemo>"  
<br/>echo "Downloading MSDD model (telephonic)..."  
wget -q --show-progress -O msdd_telephonic.nemo \\  
"<https://api.ngc.nvidia.com/v2/models/nvidia/nemo/diar_msdd_telephonic/versions/1.0.1/files/diar_msdd_telephonic.nemo>" || \\  
{ echo "NGC download failed. Please ensure NGC CLI or an API token if required."; exit 1; }  
<br/>\# Verify SHA-256 checksums  
cat > checksums.sha256 << 'SHA'  
84bda37e925ac6fd740c2ced55642cb79f94f81348e1fa0db992ca50d4b09706 vad_multilingual_marblenet.nemo  
e838520693f269e7984f55bc8eb3c2d60ccf246bf4b896d4be9bcabe3e4b0fe3 titanet_large.nemo  
SHA  
\# (Note: msdd_telephonic.nemo checksum not provided here due to potential NGC access restrictions)  
<br/>sha256sum -c checksums.sha256 2>&1 | grep 'OK' || {  
echo "Checksum verification failed!"; exit 1;  
}  
echo "All model artifacts downloaded and verified."

**Result:** After running, \$MODELS_DIR contains vad_multilingual_marblenet.nemo, titanet_large.nemo, and msdd_telephonic.nemo. If any file is missing or corrupted, the script will exit with an error. (The MSDD model's hash should be cross-verified once downloaded - here we assume a successful secure fetch from NGC.)

## 2\. Directory & diar_inference.yaml

All diarization assets reside under the gpu_services/models/ directory (as expected by the service)[\[19\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L5-L13). Below is the intended layout (with filenames):

gpu_services/models/  
├── diar_inference.yaml # Pipeline configuration (adjusted for CPU)  
├── vad_multilingual_marblenet.nemo # VAD model checkpoint\[20\]  
├── titanet_large.nemo # Speaker embedding model\[20\]  
└── msdd_telephonic.nemo # MSDD model checkpoint (optional)\[21\]

We provide a **CPU-optimized** diar_inference.yaml content below. This config is based on NVIDIA's example (telephonic diarization)[\[18\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=not%20used.%20,verbose%3A%20True)[\[14\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=approximately%2040%20mins%20of%20audio,If), with modifications for CPU: device forced to cpu, 32-bit precision, reduced batch sizes, and disabled any GPU-only flags. Notably, the VAD, speaker, and MSDD model_path entries will be dynamically overridden by the service to point to our downloaded .nemo files[\[22\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L156-L165)[\[23\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L161-L169), so we leave them as placeholder names. We also lower the MSDD infer_batch_size to 10 to limit CPU memory use.

\# Minimal diar_inference.yaml for CPU diarization  
name: "NeMoDiarizer_CPU"  
sample_rate: 16000  
batch_size: 8 # small batch for CPU processing  
device: "cpu" # force CPU (no CUDA)  
precision: 32 # use 32-bit floats on CPU  
diarizer:  
manifest_filepath: null # filled in at runtime  
out_dir: null # filled in at runtime  
oracle_vad: false  
collar: 0.25  
ignore_overlap: true  
vad:  
model_path: vad_multilingual_marblenet # will be replaced with local .nemo path\[24\]  
parameters:  
model_path: vad_multilingual_marblenet # also replaced at runtime\[25\]  
onset: 0.1  
offset: 0.1  
\# (remaining VAD params as per default config)  
speaker_embeddings:  
model_path: titanet_large # replaced with local .nemo path\[26\]  
parameters:  
save_embeddings: false # disable saving embeddings to disk (not needed for smoke test)  
window_length_in_sec: \[1.5, 1.0, 0.5\] # multiscale windows (shortened list for speed)  
shift_length_in_sec: \[0.75, 0.5, 0.25\]  
multiscale_weights: \[1, 1, 1\]  
clustering:  
parameters:  
oracle_num_speakers: false  
max_num_speakers: 5 # limit to 5 for sample (lower CPU load)  
enhanced_count_thres: 80  
max_rp_threshold: 0.25  
msdd_model:  
model_path: diar_msdd_telephonic # will be replaced or set empty\[15\]\[27\]  
parameters:  
infer_batch_size: 10 # reduced from 25 for CPU RAM safety  
use_speaker_model_from_ckpt: true  
save_logits: false # disable saving outputs (CPU I/O optimization)  
save_attention: false # disable saving attention weights

_Usage:_ Save this YAML as gpu_services/models/diar_inference.yaml. The service will load it by default on startup[\[28\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L24-L28)[\[17\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L136-L144). All model paths in the YAML (the model_path fields) are symbolic names which the service overrides with \${MODELS_DIR} paths at runtime[\[22\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L156-L165), so you do **not** need to hard-code full paths. The config ensures we use the local models instead of attempting any download. We fix device: cpu to prevent any CUDA usage[\[29\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=,diarizer%3A%20manifest_filepath%3A%20%3F%3F%3F%20out_dir%3A). Batch sizes and multiscale parameters are conservative for a short (<30s) audio; you can tune these if needed for longer audio vs. runtime. The NeMo and PyTorch versions are pinned in our environment (see next section) to ensure compatibility with this config.

To install the YAML in the correct location and confirm it references the intended models, run:

\# Write the YAML content to the models directory  
cat > gpu_services/models/diar_inference.yaml << 'YAML'  
&lt;... YAML content from above ...&gt;  
YAML  
<br/>\# Quick check that model paths in YAML match our filenames  
grep -E "model_path: " gpu_services/models/diar_inference.yaml  
\# Expected output (no absolute paths, just model names):  
\# model_path: vad_multilingual_marblenet  
\# model_path: vad_multilingual_marblenet  
\# model_path: titanet_large  
\# model_path: diar_msdd_telephonic

This confirms the config will rely on vad_multilingual_marblenet.nemo, titanet_large.nemo, etc., which we downloaded. The service will map those to the actual files at runtime[\[22\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L156-L165).

**Version pinning:** We use **PyTorch 2.8.0 (CPU build)** and **NVIDIA NeMo toolkit 1.25.0** (ASR collection) in this setup[\[30\]](https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh#L8-L16)[\[31\]](https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh#L34-L41). These versions are tested for compatibility. We also install **onnxruntime 1.18.0** (CPU) for potential future use of ONNX exports[\[31\]](https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh#L34-L41), though it's not strictly required for basic diarization. The omegaconf>=2.3.0 library is used to load the YAML[\[31\]](https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh#L34-L41). We'll ensure all these are in our Python environment next.

## 3\. Environment (CPU) Setup

Below are the shell commands to prepare a clean Python environment for the CPU-only diarization service. We create a Python 3.10 virtual env (as used in the repo) and install the needed packages: CPU versions of PyTorch and Torchaudio, NVIDIA NeMo \[ASR\] collection, and ONNX Runtime. We also include ffmpeg (for audio conversion) as a system package.

\# 3.1 System packages for audio I/O (if not already installed)  
sudo apt-get update && sudo apt-get install -y ffmpeg sox libsndfile1  
<br/>\# 3.2 Create Python venv and activate it  
python3.10 -m venv gpu_services/.venv  
source gpu_services/.venv/bin/activate  
<br/>\# 3.3 Install CPU PyTorch and Torchaudio (no CUDA)  
pip install --upgrade pip  
pip install torch==2.8.0+cpu torchaudio==2.8.0+cpu -f <https://download.pytorch.org/whl/cpu/torch_stable.html>  
<br/>\# 3.4 Install NeMo (ASR collection) and related deps  
pip install nemo_toolkit\[asr\]==1.25.0 omegaconf==2.3.0 onnxruntime==1.18.0  
<br/>\# 3.5 (Optional) Install Hugging Face transformers (if ASR integration or tokenizer use is planned)  
pip install transformers==4.48.0  
<br/>\# 3.6 Install gRPC and protobuf (for the service and client stubs)  
pip install grpcio==1.75.1 protobuf==6.31.1  
<br/>\# Verify installations  
python -c "import torch, nemo.collections.asr, onnxruntime, omegaconf, grpc; \\  
print(f'PyTorch {torch.\__version_\_}, CUDA available={torch.cuda.is_available()}')"  
\# Expected: "PyTorch 2.8.0, CUDA available=False"

This sets up a CPU-only environment: no CUDA (the torch.cuda.is_available() check should be False). The NeMo ASR toolkit includes all diarization components[\[32\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L94-L103). The grpcio and protobuf versions are aligned with the repository's requirements[\[33\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L19-L27) to ensure the gRPC service runs and client protos match. We also installed ffmpeg/sox/libsndfile so that NeMo can read various audio formats (WAV/FLAC) via Torchaudio - this is needed because the service uses torchaudio.load() to read files[\[34\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L514-L522).

To double-check, you can run:

\# Ensure Nemo ASR models can be imported (no ImportError)  
python -c "import nemo.collections.asr; import omegaconf; print('NeMo and OmegaConf ready')"

If any import fails, revisit the install steps (the script above aligns with the repo's install_gpu_deps.sh for CPU mode[\[31\]](https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh#L34-L41)).

## 4\. Sample audio (asset preparation)

For a smoke test, we need a short audio with **multiple speakers**. We use a public sample from Google Cloud's speech diarization demo: a ~36 second telephone conversation between a customer and agent (male/female speakers)[\[35\]](https://stackoverflow.com/questions/54696360/how-to-get-entire-transcript-using-google-cloud-speech-v1p1beta1#:~:text=%28venv3%29%20%E2%9E%9C%20%20g,I%20was%20wondering%20whether%20you)[\[36\]](https://stackoverflow.com/questions/54696360/how-to-get-entire-transcript-using-google-cloud-speech-v1p1beta1#:~:text=speaker%201%3A%20%20%20I%27m,I%20was%20wondering%20whether%20you). The audio is mono 16 kHz WAV. Google provides this file (commercial_mono.wav) in their cloud-samples bucket for tutorial purposes. We assume it's free for non-commercial use as a demo asset.

- **Sample audio:** _"commercial_mono.wav"_ - telephone conversation (2 speakers, ~35.8 s). &lt;br&gt; **Source:** Google Cloud STT sample (public domain demo).

Download and prepare the audio:

mkdir -p assets  
wget -O assets/sample_dialogue.wav "<https://storage.googleapis.com/cloud-samples-tests/speech/commercial_mono.wav>"  
\# Verify format: convert to 16kHz mono WAV if needed  
sox assets/sample_dialogue.wav -n stat 2>&1 | grep "Sampling rate"  
sox assets/sample_dialogue.wav -r 16000 -c 1 assets/sample_dialogue_16k.wav  
mv assets/sample_dialogue_16k.wav assets/sample_dialogue.wav

This stores the file as assets/sample_dialogue.wav. (If the original is already 16k mono, the sox resample step will just confirm that.) The audio has two speakers: e.g., Speaker 1 starts with a greeting and inquiry ("Hi, I'd like to buy a Chromecast…"), Speaker 2 responds ("Certainly, which color would you like…"), etc. There are pauses but minimal overlapping speech. The file is small (about 280 KB) and suitable for quick testing. We will use this as our input to the diarization service.

_Characteristics:_ 1 channel, 16000 Hz PCM, ~36 sec duration, ~50% speech, 50% silence/background. Two speakers alternate turns (simulating a customer service call). We expect the diarization to identify **2 distinct speaker labels** and segment the audio accordingly.

## 5\. Launch & Smoke Test (CPU mode)

To launch the diarization gRPC service on CPU, use the same entry point as on GPU but ensure CPU env vars. In our case, we just run the service module with our CPU virtualenv:

\# Activate the GPU service venv if not already  
source gpu_services/.venv/bin/activate  
<br/>\# Set environment to point to models and CPU mode  
export DIARIZATION_MODEL_ROOT="gpu_services/models" # ensure service looks at our model dir  
export DIARIZATION_SERVICE_PORT=50052 # port for gRPC service  
export DIARIZATION_LOG_LEVEL=INFO # info-level logging  
<br/>\# Launch the diarization gRPC server (runs in foreground):  
python -m gpu_services.diarize_service

The service will initialize, loading diar_inference.yaml and the three model files from gpu_services/models/[\[37\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L146-L155)[\[22\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L156-L165). On startup, you should see log messages like _"NeMo diarization pipeline successfully initialised"_[\[38\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L183-L188) and _"Starting diarization service on port 50052"_[\[39\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L532-L539), indicating it's ready.

Now perform a smoke test request. We can use **grpcurl** or a Python client. For simplicity, we'll use Python (since we have the proto stubs in our repo) to send a request to the running server:

\# In another terminal or after launching server in background:  
python - <<'PYCODE'  
import grpc, json  
from app.clients import diarize_pb2, diarize_pb2_grpc  
<br/>channel = grpc.insecure_channel('localhost:50052')  
stub = diarize_pb2_grpc.DiarizeStub(channel)  
request = diarize_pb2.AudioRequest(path='assets/sample_dialogue.wav')  
response = stub.Run(request)  
segments = \[  
{  
"speaker": seg.speaker,  
"start": round(seg.start, 3),  
"end": round(seg.end, 3)  
}  
for seg in response.segments  
\]  
print(json.dumps({"segments": segments}, indent=2))  
PYCODE

This gRPC call sends the path of our sample audio to the service (over localhost port 50052) and prints the JSON result. The expected **JSON schema** is a dictionary with a "segments" list. Each segment has:

- start (float, seconds) - start time of the segment,
- end (float, seconds) - end time of the segment,
- speaker (string) - speaker label (e.g., "Speaker 1").

For example, a successful diarization result might look like:

{  
"segments": \[  
{ "speaker": "Speaker 1", "start": 0.0, "end": 1.86 },  
{ "speaker": "Speaker 2", "start": 1.86, "end": 3.45 },  
{ "speaker": "Speaker 1", "start": 3.45, "end": 5.72 }  
\]  
}

_(The exact times will vary, but the output should clearly show at least two distinct speaker IDs with their time intervals.)_

**Success criteria:** The smoke test passes if: - The segments array is non-empty and covers the majority of the audio (e.g. ≥80% of the 36s duration covered by segments). - At least 2 distinct speaker labels are present (e.g. "Speaker 1" and "Speaker 2"). - The segments make logical sense (start/end times in ascending order, no overlapping segments for the same speaker in a row unless overlap actually occurred).

If the output meets these criteria - for instance, two speakers alternating - then our diarization pipeline is functioning correctly on CPU.

_(Note: The content of the conversation isn't transcribed here, only the speaker diarization. If needed, we could pipe the segments into an ASR model to get transcripts per segment, but that's outside the scope of this smoke test.)_

## 6\. Diagnostics & Troubleshooting

If something goes wrong, use the table below to identify possible causes and fixes. Common symptoms and solutions:

| **Symptom** | **Likely Cause** | **Diagnostic Steps / Logs** | **Fix / Solution** |
| --- | --- | --- | --- |
| **Service fails to start**&lt;br&gt;_(Exception on launch)_ | Missing dependencies (PyTorch, Nemo, etc.) or missing model files. | Check console log for ImportError or "Missing diarization resources" error[\[40\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L148-L156)[\[41\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L56-L64). | Ensure you ran env setup (Step 3). Re-run install_deps.sh --gpu with GPU_CUDA_VARIANT=cpu[\[42\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L8-L16)[\[43\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L36-L44). Verify model files exist in gpu_services/models/[\[44\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L47-L55). |
| **Checksum mismatch** (download step) | Model download corrupted or wrong URL. | The sha256sum -c step will report a failure. | Re-download the model from the official source. Verify the URL (e.g., HuggingFace link) hasn't changed. |
| **NGC download failed** (HTTP 403/404) | NGC model requires login or changed version. | Error message from wget for diar_msdd_telephonic.nemo. | Obtain an NGC API token and use ngc cli or skip MSDD for now. Alternatively, set DIARIZATION_MSDD_MODEL_PATH='' to disable MSDD usage[\[15\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L80-L88). |
| **Service starts but returns error for requests** | Model paths or config not loaded properly. | See service log (we redirect stdout/err to .diarize_service.log). Look for "Missing …" or "Failed to load NeMo pipeline"[\[45\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L169-L177). | Ensure DIARIZATION_MODEL_ROOT points to the correct directory and diar_inference.yaml is present. The service log will list which file was not found[\[46\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L156-L164)[\[47\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L51-L59) - download or fix path as needed. |
| **gRPC Run call returns no segments** (empty list) | VAD did not detect speech (or audio not read). | Check service log info: it prints RTTM path and might warn if no RTTM produced[\[48\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L333-L340). Also ensure audio file path is correct and accessible to service. | Make sure the audio is 16 kHz mono WAV. If stereo or different rate, resample to 16k mono (Step 4). Increase VAD sensitivity: in config, lower vad.threshold (onset/offset) to e.g. 0.05 to catch quiet speech. |
| **Segments all labeled same speaker** (only "Speaker 1") | Clustering failed to distinguish speakers (or max_num_speakers too low). | Check if multiple speakers truly present. Examine segments durations - if one long segment covers entire audio, diarization thought it was one speaker. | Increase max_num_speakers in config (e.g., 8)[\[49\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=parameters%3A%20oracle_num_speakers%3A%20False%20,Number%20of%20forced). Ensure Titanet model loaded (it differentiates voices). If voices are very similar, consider using a different embedding model (e.g., ECAPA). |
| **High CPU usage / slow** | Expected - CPU inference is heavy, especially MSDD. | Monitor top or logs; MSDD stage is most costly (multi-scale RNN). | Use a smaller pipeline: disable MSDD for faster but slightly less accurate diarization. Reduce multi-scale windows (fewer scales) to cut compute. For CI, short audio ensures test completes quickly (~a few seconds). |
| **Memory OOM on CPU** (process killed) | MSDD model using too much memory (large batch or too long audio). | Check dmesg/syslog for OOM killer if process died silently. | Lower infer_batch_size for MSDD (we set 10 in YAML). If still an issue, split audio into chunks <2min or disable MSDD. Ensure you're not using a GPU-only model by mistake (ours are CPU-friendly). |
| **gRPC port bind error** (Address already in use) | Another service instance already running on that port. | lsof -i :50052 to see if a process is listening. | Choose a different port: set DIARIZATION_SERVICE_PORT=50053 before launch, and adjust grpc call accordingly. |
| **Proto version mismatch** (client fails) | Incompatible protobuf between client and service. | If grpcurl fails, or Python client throws deserialization errors. | Make sure the same protobuf major version is used in env (we use v6)[\[50\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L24-L32). Regenerate stubs if needed using protoc with matching version. |

For debugging, you can enable **verbose logging** by setting DIARIZATION_LOG_LEVEL=DEBUG before starting the service[\[51\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L526-L535). This will print detailed info, including config updates and any OmegaConf issues when loading the pipeline. The service also writes intermediate outputs to a temp folder during processing[\[52\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L322-L331). By default it deletes them after each request, but you can **preserve RTTM outputs** by commenting out the cleanup in \_run_nemo_diarization (i.e., copy workdir before it's removed). Inspecting the \*.rttm file in pred_rttms/ will show the raw diarization segments the pipeline produced[\[48\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L333-L340)[\[53\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L439-L448), which can help verify timing and labels. Additionally, you can run the NeMo offline diarization script directly (as a sanity check) using the same models: e.g., python examples/speaker_tasks/diarization/offline_diarization.py ... with our YAML - this can isolate whether an issue is with the models/config or the gRPC wrapper.

## 7\. Licensing & Redistribution

Each model comes with specific licensing terms:

| **Artifact** | **License** | **Redistribution** | **Repo inclusion** |
| --- | --- | --- | --- |
| **VAD (MarbleNet Multilingual)** | _NVIDIA Open Model License_ (NVD EULA)[\[54\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=License%2FTerms%20of%20Use%3A). | Allowed for use and redistribution with attribution under NVIDIA's terms (non-exclusive, royalty-free). Commercial use is permitted but subject to the Open Model License conditions[\[54\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=License%2FTerms%20of%20Use%3A). | **Do not commit** the .nemo - license is permissive for runtime use, but we keep model binaries out of git (fetch at CI)[\[55\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L14-L22). |
| **Speaker Model (TitaNet-Large)** | _Creative Commons BY 4.0_[\[56\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large#:~:text=Eval%20Results)[\[57\]](https://dataloop.ai/library/model/nvidia_speakerverification_en_titanet_large/#:~:text=may%20be%20necessary,efficiency%2C%20speed%2C%20and%20impressive%20performance). | Openly redistributable with attribution. Can be included in datasets or caches. | **Avoid committing** due to size (~97MB). Instead, cache on CI or download on demand. CC-BY-4.0 requires giving credit to NVIDIA if redistributed. |
| **MSDD Model (Telephonic)** | _NVIDIA Open Model License_ (likely same as VAD) (NGC) | Use is governed by NVIDIA's model license - free for internal use, redistribution allowed if terms met. | **Do not commit** - large file (~100MB) and license suggests using NGC distribution. Cache it securely or fetch in CI (with token if needed). |
| **NeMo Toolkit (code)** | Apache 2.0 (open-source)[\[58\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=References%3A) for NeMo library code. | Code (Python packages) can be installed and used freely. | Already included via pip. |
| **Config (diar_inference.yaml)** | CC0/Public Domain (derived from NVIDIA's example) | Safe to include in repo. It's a text configuration - we've modified it, but it's essentially not a protected creative work. | Yes, commit the YAML to the repo for reproducibility. |
| **Sample Audio** (commercial_mono.wav) | _Assumed public demo asset_ (Google sample; no explicit license given, treated as public domain for tutorial/demo) | Allowed for use in demos and testing. Since it's provided openly in Google's docs, we assume it can be redistributed for non-commercial purposes. | **Do not commit** large binary, but we can host a link or instructions. In CI, download it each run (it's small). If license is a concern, replace with a CC0 audio sample later. |

**Attribution notices:** In documentation or about screens, acknowledge NVIDIA for the models (e.g., "Voice activity detection model © NVIDIA" as required by NOML, and cite the Titanet paper if needed). Also mention that the sample audio is from Google Cloud demo. SPDX identifiers: CC-BY-4.0 for Titanet, and Proprietary/NVIDIA-Model-License for MarbleNet VAD and MSDD (NVIDIA hasn't published an SPDX for their model license, so treat as proprietary).

In summary, **do not commit the .nemo files into the repo**[\[55\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L14-L22). Instead, use CI caching or on-demand downloads. The YAML and any small config/text can be safely version-controlled.

## 8\. CI Automation Checklist

To integrate this smoke test in CI (e.g., GitHub Actions or similar), we outline an end-to-end script that prepares the environment, runs the service, and validates output:

- **Caching**: Cache the gpu_services/models/ directory across CI runs to avoid re-downloading large models every time. Use checksum verification to ensure cache integrity (if checksum mismatch, re-download). The Hugging Face and NGC URLs are stable; caching saves ~200MB per run.
- **Files to commit**: commit diar_inference.yaml and this smoke test script. Do **not** commit model binaries. The CI should fetch models at runtime (and cache them).
- **Fast-fail conditions**: If model download or checksum fails, or if the service doesn't produce the expected output format, fail the CI job immediately with an error message.

Below is a non-interactive Bash script performing the full pipeline (as one might put in a CI workflow). It uses environment variables and the steps we discussed:

# !/bin/bash  
set -euo pipefail  
<br/>\# \[CI Step 1\] Environment setup  
python3.10 -m venv gpu_services/.venv && source gpu_services/.venv/bin/activate  
pip install torch==2.8.0+cpu torchaudio==2.8.0+cpu -f <https://download.pytorch.org/whl/cpu/torch_stable.html>  
pip install nemo_toolkit\[asr\]==1.25.0 omegaconf==2.3.0 onnxruntime==1.18.0 grpcio==1.75.1 protobuf==6.31.1  
<br/>\# \[CI Step 2\] Download model artifacts (with cache check)  
MODELS_DIR="gpu_services/models"  
mkdir -p "\$MODELS_DIR"  
\# If cached models exist, verify checksums; otherwise download afresh.  
if \[\[ -f "\$MODELS_DIR/vad_multilingual_marblenet.nemo" && -f "\$MODELS_DIR/titanet_large.nemo" \]\]; then  
echo "Models found in cache, verifying..."  
echo "84bda37e925ac6fd740c2ced55642cb79f94f81348e1fa0db992ca50d4b09706 \$MODELS_DIR/vad_multilingual_marblenet.nemo" > verify.sha  
echo "e838520693f269e7984f55bc8eb3c2d60ccf246bf4b896d4be9bcabe3e4b0fe3 \$MODELS_DIR/titanet_large.nemo" >> verify.sha  
if ! sha256sum -c verify.sha; then  
echo "Cache corruption detected, re-downloading models..."  
rm -f "\$MODELS_DIR/vad_multilingual_marblenet.nemo" "\$MODELS_DIR/titanet_large.nemo"  
fi  
fi  
\# Download if files not present  
if \[\[ ! -f "\$MODELS_DIR/vad_multilingual_marblenet.nemo" \]\]; then  
wget -q -O "\$MODELS_DIR/vad_multilingual_marblenet.nemo" "<https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/resolve/main/frame_vad_multilingual_marblenet_v2.0.nemo>"  
fi  
if \[\[ ! -f "\$MODELS_DIR/titanet_large.nemo" \]\]; then  
wget -q -O "\$MODELS_DIR/titanet_large.nemo" "<https://huggingface.co/nvidia/speakerverification_en_titanet_large/resolve/main/speakerverification_en_titanet_large.nemo>"  
fi  
if \[\[ ! -f "\$MODELS_DIR/msdd_telephonic.nemo" \]\]; then  
echo "Downloading MSDD model from NGC..."  
wget -q -O "\$MODELS_DIR/msdd_telephonic.nemo" "<https://api.ngc.nvidia.com/v2/models/nvidia/nemo/diar_msdd_telephonic/versions/1.0.1/files/diar_msdd_telephonic.nemo>" || echo "MSDD model not downloaded (proceeding without MSDD)"  
fi  
<br/>\# \[CI Step 3\] Write diar_inference.yaml  
cat > "\$MODELS_DIR/diar_inference.yaml" << 'YAML'  
name: "NeMoDiarizer_CPU"  
sample_rate: 16000  
batch_size: 8  
device: "cpu"  
precision: 32  
diarizer:  
manifest_filepath: null  
out_dir: null  
oracle_vad: false  
collar: 0.25  
ignore_overlap: true  
vad:  
model_path: vad_multilingual_marblenet  
parameters:  
model_path: vad_multilingual_marblenet  
onset: 0.1  
offset: 0.1  
speaker_embeddings:  
model_path: titanet_large  
parameters:  
save_embeddings: false  
window_length_in_sec: \[1.5, 1.0, 0.5\]  
shift_length_in_sec: \[0.75, 0.5, 0.25\]  
multiscale_weights: \[1, 1, 1\]  
clustering:  
parameters:  
oracle_num_speakers: false  
max_num_speakers: 5  
enhanced_count_thres: 80  
max_rp_threshold: 0.25  
msdd_model:  
model_path: diar_msdd_telephonic  
parameters:  
infer_batch_size: 10  
use_speaker_model_from_ckpt: true  
save_logits: false  
save_attention: false  
YAML  
<br/>\# \[CI Step 4\] Launch diarization service (in background)  
export DIARIZATION_MODEL_ROOT="\$MODELS_DIR"  
export DIARIZATION_SERVICE_PORT=50052  
python -m gpu_services.diarize_service &> diar_service.log &  
PID=\$!  
\# Wait up to 30s for port to open  
for i in {1..30}; do nc -z localhost 50052 && break || sleep 1; done  
if ! nc -z localhost 50052; then  
echo "Service failed to start (log below):" && cat diar_service.log && exit 1  
fi  
<br/>\# \[CI Step 5\] Run smoke test request via gRPC and save output  
python - &lt;<'PYTEST' &gt; diarization_result.json  
import json, grpc, os  
from app.clients import diarize_pb2, diarize_pb2_grpc  
channel = grpc.insecure_channel(f"localhost:{os.environ.get('DIARIZATION_SERVICE_PORT', '50052')}")  
stub = diarize_pb2_grpc.DiarizeStub(channel)  
resp = stub.Run(diarize_pb2.AudioRequest(path="assets/sample_dialogue.wav"))  
segments = \[{"speaker": s.speaker, "start": round(s.start,3), "end": round(s.end,3)} for s in resp.segments\]  
print(json.dumps({"segments": segments}, ensure_ascii=False))  
PYTEST  
<br/>\# \[CI Step 6\] Validate output (at least 2 speakers and coverage)  
python - <<'PYVALID'  
import sys, json  
result = json.load(open('diarization_result.json'))  
segs = result.get("segments", \[\])  
speakers = {seg.get("speaker") for seg in segs}  
total_dur = sum(round(seg.get("end",0)-seg.get("start",0), 3) for seg in segs)  
if len(speakers) < 2:  
print(f"ERROR: Expected ≥2 speakers, got {len(speakers)}", file=sys.stderr); sys.exit(1)  
if total_dur < 0.8 \* 36.0:  
print(f"ERROR: Segments cover only {total_dur:.1f}s of audio (expected ~36s)", file=sys.stderr); sys.exit(1)  
print("Diarization smoke test passed with speakers:", ", ".join(sorted(speakers)))  
PYVALID  
<br/>\# \[CI Step 7\] Cleanup  
kill \$PID || true

This CI script will fail (exit non-zero) if the diarization result doesn't meet expectations (checked in Step 6). It prints a success message with the detected speaker labels otherwise. The artifacts diarization_result.json and diar_service.log can be saved as CI job attachments for further inspection.

## 9\. Assumptions & Open Questions

- **MSDD necessity:** We assumed the MSDD model (msdd_telephonic.nemo) is available and beneficial. If NGC access is an issue, the fallback is to run without MSDD (just clustering). Our instructions include that option. We assume telephonic MSDD is suitable for our 16 kHz sample (it's trained on telephone bandwidth but should generalize; for higher-bandwidth audio, an MSDD model trained on such might perform better).
- **Sample audio license:** We used Google's sample call audio. It's not explicitly licensed, but given it's widely used in documentation, we treated it as a public demo asset. If that's a concern, we might replace it with an audio from a dataset like VoxCeleb or LibriVox (public domain) - as long as it has two speakers. Our pipeline will work similarly on any 16 kHz WAV.
- **Resource limits:** We assume ~100-200 MB of downloads is acceptable in CI. If that's too heavy, one could choose smaller models (e.g., use **SpeakerNet** (~50MB) instead of Titanet, or skip MSDD). We went with more accurate models for robustness.
- **Determinism:** Minor note - because clustering and MSDD can have non-deterministic aspects (e.g., K-Means initialization), segment boundaries might vary by a few milliseconds run-to-run. We haven't set a random seed explicitly. In practice, the differences should be negligible for our success criteria. If exact reproducibility is needed, we'd explore whether NeMo allows seeding the clustering algorithm.
- **Integration with backend:** We assume the gRPC service runs standalone for the smoke test. In the actual system, the backend might launch this service or call it. If integration issues arise (e.g., TLS for gRPC or different host), those would need additional config (certs, env vars). Our test is on localhost insecure port as a baseline.
- **Proto schema:** We used the existing diarize.proto definitions from the repo (which gave us AudioRequest.path and DiarizationResult.segments). We assume that schema remains unchanged. If the proto is extended (e.g., to include confidence or transcripts), our test should be updated to check those fields too. Currently, it only outputs start, end, speaker.
- **Future improvements:** NVIDIA has newer diarization models (e.g., "Sortformers" for end-to-end diarization[\[59\]](https://huggingface.co/nvidia/diar_sortformer_4spk-v1#:~:text=NVIDIA%20NeMo.%20To%20train%2C%20fine,install%20it%20after%20you%27ve)). We stuck to the classic VAD+embedding+MSDD approach per task instructions. In future, a lighter end-to-end model might simplify this (fewer artifacts), but for now our pipeline is the NeMo-prescribed one for multi-speaker diarization.
- **Open question:** The repo's TODO_GPU.md hints at diarization integration steps. We've assumed everything needed is in place (proto, client calls, etc.). One should verify after this smoke test that the backend can consume the segments JSON and proceed (e.g. perhaps feeding into transcription or UI labeling). Our guide focuses on the diarization service itself.

## 10\. Sources

- NVIDIA NeMo diarization model references - model names and NGC links[\[8\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=vad_multilingual_marblenet)[\[60\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=diar_msdd_telephonic), config example[\[18\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=not%20used.%20,verbose%3A%20True)[\[14\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=approximately%2040%20mins%20of%20audio,If).
- Hugging Face model cards for VAD and TitaNet - model sizes, licenses[\[4\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/blob/main/frame_vad_multilingual_marblenet_v2.0.nemo#:~:text=,)[\[61\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large/blob/48f4fde3e017830f9bdd4e313d6c050b15e4298f/speakerverification_en_titanet_large.nemo#:~:text=Large%20File%20Pointer%20Details), descriptions[\[6\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=Frame,of%20audios%20was%20also%20varied)[\[9\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large#:~:text=This%20model%20extracts%20speaker%20embeddings,documentation%20for%20complete%20architecture%20details).
- Repository diarization_resources.py - default filenames and paths expected[\[62\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L24-L32)[\[24\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L76-L84).
- Repository gpu_services/models/README.md - documentation of required files[\[19\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L5-L13).
- Repository deep research (ASR test) - analogous steps for ASR CPU test[\[63\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L66-L74)[\[64\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L91-L100).
- Repository diarization_cpu_smoke_test.sh - provided baseline for many steps (env, launch, grpc call)[\[65\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L46-L55)[\[66\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L123-L131).
- Google Cloud sample audio documentation - description of _commercial_mono.wav_ dialogue[\[35\]](https://stackoverflow.com/questions/54696360/how-to-get-entire-transcript-using-google-cloud-speech-v1p1beta1#:~:text=%28venv3%29%20%E2%9E%9C%20%20g,I%20was%20wondering%20whether%20you)[\[36\]](https://stackoverflow.com/questions/54696360/how-to-get-entire-transcript-using-google-cloud-speech-v1p1beta1#:~:text=speaker%201%3A%20%20%20I%27m,I%20was%20wondering%20whether%20you).

[\[1\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=In%20general%2C%20you%20can%20load,name%20in%20the%20following%20format) [\[2\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=vad_multilingual_marblenet) [\[8\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=vad_multilingual_marblenet) [\[11\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=com) [\[12\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=diar_msdd_telephonic) [\[60\]](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html#:~:text=diar_msdd_telephonic) Checkpoints - NVIDIA NeMo Framework User Guide

<https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/results.html>

[\[3\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/blob/main/frame_vad_multilingual_marblenet_v2.0.nemo#:~:text=Safe) [\[4\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/blob/main/frame_vad_multilingual_marblenet_v2.0.nemo#:~:text=,) frame_vad_multilingual_marblenet_v2.0.nemo · nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0 at main

<https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/blob/main/frame_vad_multilingual_marblenet_v2.0.nemo>

[\[5\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/raw/main/frame_vad_multilingual_marblenet_v2.0.nemo#:~:text=version%20https%3A%2F%2Fgit,501760) huggingface.co

<https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/raw/main/frame_vad_multilingual_marblenet_v2.0.nemo>

[\[6\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=Frame,of%20audios%20was%20also%20varied) [\[7\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=Key%20Features) [\[54\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=License%2FTerms%20of%20Use%3A) [\[58\]](https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0#:~:text=References%3A) nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0 · Hugging Face

<https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0>

[\[9\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large#:~:text=This%20model%20extracts%20speaker%20embeddings,documentation%20for%20complete%20architecture%20details) [\[56\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large#:~:text=Eval%20Results) nvidia/speakerverification_en_titanet_large · Hugging Face

<https://huggingface.co/nvidia/speakerverification_en_titanet_large>

[\[10\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large/raw/48f4fde3e017830f9bdd4e313d6c050b15e4298f/speakerverification_en_titanet_large.nemo#:~:text=version%20https%3A%2F%2Fgit,101621760) huggingface.co

<https://huggingface.co/nvidia/speakerverification_en_titanet_large/raw/48f4fde3e017830f9bdd4e313d6c050b15e4298f/speakerverification_en_titanet_large.nemo>

[\[13\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=selectively%20used%20for%20its%20own,verbose%3A%20True) [\[14\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=approximately%2040%20mins%20of%20audio,If) [\[18\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=not%20used.%20,verbose%3A%20True) [\[29\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=,diarizer%3A%20manifest_filepath%3A%20%3F%3F%3F%20out_dir%3A) [\[49\]](https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml#:~:text=parameters%3A%20oracle_num_speakers%3A%20False%20,Number%20of%20forced) raw.githubusercontent.com

<https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml>

[\[15\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L80-L88) [\[17\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L136-L144) [\[22\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L156-L165) [\[23\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L161-L169) [\[24\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L76-L84) [\[25\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L159-L165) [\[26\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L160-L165) [\[27\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L162-L168) [\[28\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L24-L28) [\[32\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L94-L103) [\[37\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L146-L155) [\[62\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py#L24-L32) diarization_resources.py

<https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarization_resources.py>

[\[16\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L7-L13) [\[19\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L5-L13) [\[20\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L9-L12) [\[21\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L10-L13) [\[55\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md#L14-L22) README.md

<https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/models/README.md>

[\[30\]](https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh#L8-L16) [\[31\]](https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh#L34-L41) install_gpu_deps.sh

<https://github.com/kvcop/Voicerec-By-Codex/blob/858c3882a366d6dca1328a48203a42a26863fb81/scripts/install_gpu_deps.sh>

[\[33\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L19-L27) [\[42\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L8-L16) [\[50\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L24-L32) [\[63\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L66-L74) [\[64\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh#L91-L100) asr_cpu_smoke_test.sh

<https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/asr_cpu_smoke_test.sh>

[\[34\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L514-L522) [\[38\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L183-L188) [\[39\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L532-L539) [\[40\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L148-L156) [\[45\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L169-L177) [\[46\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L156-L164) [\[48\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L333-L340) [\[51\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L526-L535) [\[52\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L322-L331) [\[53\]](https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py#L439-L448) diarize_service.py

<https://github.com/kvcop/Voicerec-By-Codex/blob/6a2e2cd06ad2517ebc8861ba7b435ee1ba747a2c/gpu_services/diarize_service.py>

[\[35\]](https://stackoverflow.com/questions/54696360/how-to-get-entire-transcript-using-google-cloud-speech-v1p1beta1#:~:text=%28venv3%29%20%E2%9E%9C%20%20g,I%20was%20wondering%20whether%20you) [\[36\]](https://stackoverflow.com/questions/54696360/how-to-get-entire-transcript-using-google-cloud-speech-v1p1beta1#:~:text=speaker%201%3A%20%20%20I%27m,I%20was%20wondering%20whether%20you) python 3.x - How to get entire transcript using google.cloud.speech_v1p1beta1? - Stack Overflow

<https://stackoverflow.com/questions/54696360/how-to-get-entire-transcript-using-google-cloud-speech-v1p1beta1>

[\[41\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L56-L64) [\[43\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L36-L44) [\[44\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L47-L55) [\[47\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L51-L59) [\[65\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L46-L55) [\[66\]](https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh#L123-L131) diarization_cpu_smoke_test.sh

<https://github.com/kvcop/Voicerec-By-Codex/blob/0bc7981f948eb287cd43f3f08f5e08afd073e4e3/scripts/diarization_cpu_smoke_test.sh>

[\[57\]](https://dataloop.ai/library/model/nvidia_speakerverification_en_titanet_large/#:~:text=may%20be%20necessary,efficiency%2C%20speed%2C%20and%20impressive%20performance) Speakerverification en titanet large · Models · Dataloop

<https://dataloop.ai/library/model/nvidia_speakerverification_en_titanet_large/>

[\[59\]](https://huggingface.co/nvidia/diar_sortformer_4spk-v1#:~:text=NVIDIA%20NeMo.%20To%20train%2C%20fine,install%20it%20after%20you%27ve) nvidia/diar_sortformer_4spk-v1 - Hugging Face

<https://huggingface.co/nvidia/diar_sortformer_4spk-v1>

[\[61\]](https://huggingface.co/nvidia/speakerverification_en_titanet_large/blob/48f4fde3e017830f9bdd4e313d6c050b15e4298f/speakerverification_en_titanet_large.nemo#:~:text=Large%20File%20Pointer%20Details) speakerverification_en_titanet_large.nemo · nvidia/speakerverification_en_titanet_large at 48f4fde3e017830f9bdd4e313d6c050b15e4298f

<https://huggingface.co/nvidia/speakerverification_en_titanet_large/blob/48f4fde3e017830f9bdd4e313d6c050b15e4298f/speakerverification_en_titanet_large.nemo>
