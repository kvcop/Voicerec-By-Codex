# GPU TLS Certificate Distribution

Mutual TLS between the backend and GPU services will rely on standard certificate files (a CA certificate, and a client certificate with its private key) provided to the backend. These files should be stored in a secure location on the backend server (or passed in as Kubernetes/Docker secrets) and referenced by the environment variables GPU_GRPC_TLS_CA, GPU_GRPC_TLS_CERT, and GPU_GRPC_TLS_KEY[\[1\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/.env.example#L4-L10). For example, one might place the files in a protected directory (e.g. /etc/voicerec/certs/ca.pem, /etc/voicerec/certs/client.pem, /etc/voicerec/certs/client.key) and set the .env accordingly. The repository's config expects these paths in order to enable mTLS[\[1\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/.env.example#L4-L10).

Currently, the exact distribution of these certificate files is pending input from the repository owner[\[2\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO.md#L26-L34). In practice, obtaining them involves generating or receiving a client certificate signed by the GPU service's CA. The **CA certificate** (public) should come from the GPU node or cluster (to trust the GPU service's server cert), and a **client keypair** should be generated for the backend and signed by that CA. The repository owner or infrastructure team should provide these files through a secure channel. Once available, they must be placed at the designated paths and possibly mounted into containers if using Docker Compose. (For instance, the documentation suggests mounting a certs/ folder into the GPU service containers for TLS[\[3\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L8-L11).) In summary, the CA cert and client cert/key will reside on the backend filesystem (or secret store), at paths configured via GPU_GRPC_TLS_CA, GPU_GRPC_TLS_CERT, and GPU_GRPC_TLS_KEY. This ensures the backend's gRPC client uses the CA to verify the GPU server and presents the client certificate for authentication. (If a VPN is used instead of mTLS, these files are not needed[\[4\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/gpu_security.md#L5-L13)[\[5\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/gpu_security.md#L14-L22).)

**Note:** Because the precise file locations and distribution mechanism have not been explicitly documented yet[\[2\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO.md#L26-L34), the repository owner should update the docs (e.g. docs/gpu_security.md) with those details. In the interim, you can assume the certificates will be provided out-of-band and should be stored in a secure path, with the .env updated accordingly for the backend to pick them up.

## ASR Service Manual Testing Plan (G1_5 Verification)

To fully test the ASR gRPC service (Whisper-based speech recognition) without GPU, follow these steps. This will use a smaller Whisper model that fits in a CPU environment, run the ASR service on CPU, send it an audio file, and verify the transcription (including the replacement of "рум" with **RUMA** in the text).

**1\. Prepare the environment - install ASR service dependencies.** The ASR service requires PyTorch, Torchaudio, Hugging Face Transformers, and the OpenAI Whisper package. If you haven't installed these (they are intentionally omitted from the default install due to size), run the provided script with CPU settings. For example, from the repository root:

GPU_CUDA_VARIANT=cpu ./install_deps.sh --gpu

This will create the gpu_services/.venv virtual environment and install the necessary packages (using the CPU-only build of PyTorch)[\[6\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/researches/2025-09-27-v1-gpu-audio-processing.md#L30-L38). Ensure you activate that virtual environment (e.g. source gpu_services/.venv/bin/activate) so that running the service will use the installed packages.

**2\. Download a compact Whisper model for CPU use.** By default, the service is configured to use Whisper Large-v2, which is too heavy for CPU. We will use a smaller model. For example, **Whisper Small** (HF model ID: openai/whisper-small) is a multilingual model ~244M parameters that can run on a CPU[\[7\]](https://huggingface.co/openai/whisper-small#:~:text=Size%20Parameters%20English,1550%20M%20x%20%2050). Set the environment variable ASR_MODEL_SIZE=small in your .env (or export it in the shell) to force the service to load this model instead of large[\[8\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L23-L29)[\[9\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L25-L29). To avoid any internet download delays or offline issues, pre-download the model files from Hugging Face. Run the following commands to fetch the model weights and tokenizer files directly from the Hugging Face Hub:

\# Download Whisper Small model weights and config from Hugging Face  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/pytorch_model.bin>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/config.json>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/tokenizer.json>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/tokenizer_config.json>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/special_tokens_map.json>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/normalizer.json>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/preprocessor_config.json>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/merges.txt>  
wget -q --show-progress <https://huggingface.co/openai/whisper-small/resolve/main/vocab.json>

Each wget command above pulls a specific file (the model weights ~967MB and supporting files) from the Whisper Small repository. After downloading, place these files in the directory where Hugging Face will find them. By default, running from_pretrained("openai/whisper-small") will check the Hugging Face cache. You can create a folder (for example, ~/.cache/huggingface/transformers/openai/whisper-small) and move the files there, or set the TRANSFORMERS_CACHE environment variable to point to the download location. This ensures the ASR service will load the model from disk instead of trying to fetch it online. (If the environment has internet access, this manual download step is optional - the service would download the model on first run - but doing it now avoids a long pause or any connectivity issues.)

**3\. Obtain a test audio file.** For a meaningful test, you'll need a short WAV audio clip (just a few seconds of speech). Ideally, this clip **should include the word "RUMA"** (or a scenario where Whisper might misrecognize "RUMA" as "рум") to verify the post-processing correction[\[10\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/researches/2025-09-27-v1-gpu-audio-processing.md#L17-L25)[\[11\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L232-L240). If such a sample is not readily available in the repository, the repository owner should create one - for example, by reading a line from the product's documentation or glossary that contains "RUMA". (This will ensure we have a known ground-truth transcript for verification.) Currently, the repository provides a sample WAV recording (a conversation) in the project root, but it does **not** contain the keyword "RUMA". Consider this a TODO: to fully test the RUMA replacement, a new audio sample with that term should be prepared.

For now, use whatever sample is available (e.g. sample.wav). Copy or move the WAV file into the directory used for raw audio (by default data/raw/). The backend and GPU services share this location for audio files[\[12\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L27-L31). For example, if your audio file is sample.wav, do:

mkdir -p data/raw  
cp sample.wav data/raw/test.wav

Here we renamed it to **test.wav** for clarity. The filename can be anything, but you will use this name in the request. Ensure that the ASR service will have access to this path. By default, RAW_AUDIO_DIR is data/raw[\[13\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/README.md#L40-L48)[\[14\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/README.md#L46-L49), so placing the file in data/raw/ means the service can find it via request.path = "data/raw/test.wav".

**4\. Launch the ASR gRPC service on CPU.** In one terminal, start the ASR service. Make sure the virtual environment is activated (if used) and the ASR_MODEL_SIZE env var is set to the small model. Then run:

export ASR_MODEL_SIZE=small # ensure we're using the small model  
export ASR_SERVICE_PORT=50051 # (optional) port, 50051 is default  
python -m gpu_services.asr_service

This will initialize the ASR gRPC server. You should see log output indicating that it's loading the Whisper model 'small' on CPU (since no CUDA is available)[\[15\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L72-L80)[\[16\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L81-L88). For example, the log may state _"Loading Whisper model 'openai/whisper-small' on device 'cpu'…"_. The server will listen on port 50051 by default[\[17\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L246-L254) (you can change ASR_SERVICE_PORT if needed). It uses an insecure gRPC channel (no TLS) for simplicity. Leave this terminal running; the service is now awaiting requests.

**5\. Send a gRPC request with the audio file via grpcurl.** In a second terminal, we will call the Run method of the gRPC service with our audio file path. We can use **grpcurl** (a command-line gRPC client) for this. Since the server does not have reflection enabled, we'll supply the proto definition for the request. The proto file transcribe.proto defines the service name services.transcribe.Transcribe and the request/response messages[\[18\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/backend/app/clients/transcribe_pb2.py#L22-L30). Assuming protos/transcribe.proto is available, run:

grpcurl -plaintext -proto protos/transcribe.proto \\  
\-d '{ "path": "data/raw/test.wav" }' \\  
localhost:50051 services.transcribe.Transcribe/Run

Let's break this down:

- \-plaintext tells grpcurl to use an insecure connection (our service isn't using TLS on its gRPC port).
- \-proto protos/transcribe.proto provides the service definition. (Make sure the path is correct for your setup.)
- The -d flag sends the JSON for our AudioRequest. We provide the exact path to the WAV file as the path field. Here, "data/raw/test.wav" is used, which the service should find (since it's running with working directory at project root and uses data/raw by default).
- localhost:50051 is the address and port of the running ASR service.
- services.transcribe.Transcribe/Run is the fully-qualified RPC method (package services.transcribe, service Transcribe, method Run).

If everything is configured properly, this command will contact the ASR service and perform the transcription. The service will load the WAV, preprocess it (resample to 16 kHz mono if needed)[\[19\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L220-L229), run Whisper inference, and apply post-processing.

**6\. Observe the output and verify the transcription.** The grpcurl call should print the response in JSON. It will look like:

{  
"text": "transcribed text of your audio..."  
}

The exact text depends on your audio. If you used the provided sample without the keyword, you should still see a plausible transcription of that speech. The main thing is that you get a non-error response containing a "text" field.

- **RUMA post-processing:** If your test audio contained the word "RUMA" (or if Whisper misheard something as "рум"), check that the output text has "RUMA" correctly capitalized. The ASR service applies a regex replacement for the exact word "рум" (case-insensitive) to "RUMA"[\[11\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L232-L240). For example, if the spoken phrase was "Platform RUMA is active" but Whisper originally transcribed "Platform рум is active," the final output should replace that with "Platform RUMA is active." This confirms the post-processing step is working. In our test scenario, since we might not have a clip with "RUMA" yet, this specific verification might be deferred - consider adding a **TODO** to test this once an appropriate audio sample is available (e.g. have the project owner record a snippet from the admin guide that includes _RUMA_ for a ground-truth test).
- **General accuracy:** Even with a smaller model on CPU, the transcription should be intelligible. Verify that the text corresponds to the speech in the audio. If it's a Russian sample, you should see Cyrillic transcription (Whisper small is multilingual). Minor errors are expected with a smaller model, but it should capture the gist. The key is that we got a response and not an error.
- **Diagnostics:** If the grpcurl command returns an error, check the details:
- **File not found**: The service will return a gRPC NOT_FOUND error if it cannot locate the file at the given path[\[20\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L109-L117). Ensure the path is correct and accessible (the service log will also show "Audio file not found" in that case).
- **Empty or invalid audio**: If the file was empty or not a valid WAV, the service might abort with INVALID_ARGUMENT (e.g., "no samples" or format errors)[\[21\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L126-L134). In such cases, use a known-good WAV file (16-bit PCM WAV is expected).
- **Model loading issues**: If the service failed to load the model (e.g., if the files weren't in the right place and it tried to download but couldn't), it might have thrown an exception on startup. Check the first terminal's logs. You should see a log about model loading and another when inference completes, e.g. _"Finished Whisper inference for data/raw/test.wav in X.XX seconds"_[\[22\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L148-L156). If the service crashed before responding, resolve any model path issues (ensure step 2 was done and ASR_MODEL_SIZE is set to the downloaded model).
- **Logs:** The ASR service logs are your friend. It prints info-level messages for each request and debugging messages for the normalized text[\[23\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L76-L84)[\[24\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L154-L159). After the grpcurl request, check the service console: it should log the received path and the final transcription after normalization. For example, _"Transcription after normalisation: ..."_[\[25\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L152-L159). Seeing **RUMA** in that log (if applicable) confirms the replacement happened even before sending the response.

By following the above plan, you perform a manual end-to-end test of the ASR gRPC service on a CPU-only setup. We installed the needed packages, used a smaller Whisper model (as configured by ASR_MODEL_SIZE for CPU testing[\[26\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/researches/2025-09-27-v1-gpu-audio-processing.md#L32-L38)), invoked the service with a test audio, and checked the output. The expected result is that the service returns a JSON with a transcribed "text". If the word "RUMA" is spoken in the audio, the result should contain "RUMA" in the text (thanks to post-processing)[\[11\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L232-L240). Otherwise, you simply verify that the transcription makes sense. Any deviations or errors would indicate a problem to fix (e.g., audio file not accessible, model not loaded, etc.).

**Reminder:** Once the repository owner provides a proper audio sample with **"RUMA"** and its expected transcript (perhaps by reading a known script from the admin guide), that should be used to conclusively verify the post-processing. Until then, treat the verification of the RUMA-replacement as partially tested (the logic is in place, as seen in code[\[11\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/gpu_services/asr_service.py#L232-L240), but a real audio trigger is pending). Mark this as a follow-up item in your testing checklist.

[\[1\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/.env.example#L4-L10) .env.example

<https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/.env.example>

[\[2\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO.md#L26-L34) TODO.md

<https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO.md>

[\[3\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L8-L11) [\[8\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L23-L29) [\[9\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L25-L29) [\[12\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md#L27-L31) TODO_GPU.md

<https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/TODO_GPU.md>

[\[4\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/gpu_security.md#L5-L13) [\[5\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/gpu_security.md#L14-L22) gpu_security.md

<https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/gpu_security.md>

[\[6\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/researches/2025-09-27-v1-gpu-audio-processing.md#L30-L38) [\[10\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/researches/2025-09-27-v1-gpu-audio-processing.md#L17-L25) [\[26\]](https://github.com/kvcop/Voicerec-By-Codex/blob/15d26488b77c6fa5318e55c3e9a6ec75f41c806f/docs/researches/2025-09-27-v1-gpu-audio-processing.md#L32-L38) 2025-09-27-v1-gpu-audio-processing.md

<https://github.com/kvcop/Vo
