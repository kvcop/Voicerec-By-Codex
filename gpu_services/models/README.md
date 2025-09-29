# Diarization model artifacts

This directory stores the NVIDIA NeMo diarization resources that power the GPU diarization service.

The `gpu_services.diarization_resources` module assumes the following files are present by default:

| Filename | Purpose |
| --- | --- |
| `diar_inference.yaml` | Pipeline configuration copied from the NeMo diarization examples. |
| `vad_multilingual_marblenet.nemo` | Voice activity detection checkpoint. |
| `titanet_large.nemo` | Speaker embedding model. |
| `msdd_telephonic.nemo` | Optional Multiscale Diarization Decoder checkpoint for improved accuracy. |

Place the actual NeMo artifacts in this folder (or update the environment variables described below to point elsewhere). The repository deliberately keeps only documentation files under version control—real model weights are large and should be fetched manually, for example via the [NeMo model registry](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemo/models).

## Environment variables

The loader honours the following overrides:

- `DIARIZATION_MODEL_ROOT` – alternative directory with all diarization artifacts.
- `DIARIZATION_CONFIG_PATH` – path to the diarization YAML config.
- `DIARIZATION_VAD_MODEL_PATH` – path to the VAD checkpoint.
- `DIARIZATION_SPEAKER_MODEL_PATH` – path to the speaker embedding checkpoint.
- `DIARIZATION_MSDD_MODEL_PATH` – path to the MSDD checkpoint (set to an empty string to disable MSDD).
- `DIARIZATION_AUTO_DOWNLOAD` – set to `1` to allow automatic downloads when supported in the future.

Refer to the NeMo documentation for details on producing the `diar_inference.yaml` manifest and for downloading the matching checkpoints.
