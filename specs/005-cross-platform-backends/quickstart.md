# Quickstart: A mission with assets on a Linux/Windows machine

Goal of this walkthrough: reproduce the brick's "done when" — the same mission
with assets that runs on a Mac, running on a box without MLX.

## 1. Install the studio (any OS)

```bash
pip install -e . -e ./agencykit    # stdlib core — always works
pip install 'agency-studio[media]' # off-Mac this resolves the portable subset
                                   # (kokoro-onnx + soundfile); MLX packages are
                                   # darwin-only via environment markers
agency-studio                      # binds 127.0.0.1, opens the GUI
```

## 2. See the honest inventory

Open the capabilities panel. On a Linux/Windows machine you should see, for
example:

- image → `flux-schnell` UNAVAILABLE (`unsupported_runtime` — "requires
  Apple-Silicon macOS"), `stable-diffusion-cpp` UNAVAILABLE (`missing_binary`,
  hint: pinned release install step)
- stt → `whisper-cpp` UNAVAILABLE (`missing_binary` or `missing_model_files`)
- tts → `kokoro-v1.0` AVAILABLE (after step 1)
- embedding → `nomic-embed-gguf` UNAVAILABLE (`gateway_down` or unconfigured)

## 3. Enable the portable backends (guided by the hints)

Each UNAVAILABLE entry's hint is copy-paste concrete:

1. **Image**: install the pinned stable-diffusion.cpp release (`sd` on PATH),
   place the pinned GGUF checkpoint (sha256 in the hint) in the studio models dir.
2. **STT**: install the pinned whisper.cpp release (`whisper-cli` on PATH), place
   the pinned Whisper model file in the studio models dir.
3. **Embeddings**: start the pinned llama.cpp server with the pinned embedding
   GGUF on `http://127.0.0.1:8080` (hint shows the exact command). Non-loopback
   URLs are rejected.

Click Refresh — the entries flip to AVAILABLE / FREE. (A wrong-checksum model file
shows `model_files_mismatch`; a stopped gateway shows `gateway_down` with the start
command.)

## 4. Select without a terminal

In the panel, select `stable-diffusion-cpp` (image), `whisper-cpp` (stt),
`nomic-embed-gguf` (embedding). TTS needs no action. Selections persist across
restarts. (Power users: the `AGENCY_STUDIO_*` env vars still override.)

Note: with nothing selected, the platform-aware default already routes to the
first AVAILABLE entry — selection makes it explicit.

## 5. Run the mission with assets

Launch the same mission brief used on the Mac with assets enabled. Preflight
passes (all needed families available) and the mission completes with image and
speech assets produced by the portable backends.

Negative check: stop the llama.cpp gateway and launch a mission with documents
attached — the launch is refused with a 409 listing the `embedding` blocker and
its start hint; nothing runs partially.

Deferred live-run checklist (Wave 2 practice):

- [ ] Linux box: install `sd`, `whisper-cli`, and `llama.cpp`; place pinned model
  files; run the mission with assets.
- [ ] Windows box: repeat the same install and mission.
- [ ] Record real binary versions, model filenames, SHA-256 values, and wall-clock
  timings in this quickstart before declaring live acceptance complete.

## 6. Verify the offline suite (any OS, nothing installed)

```bash
python -m pytest            # green with zero optional backends, no network
```

CI runs this same suite on ubuntu / windows / macos runners on every PR
(`.github/workflows/offline-suite.yml`).
