# Contract: Backend seams (probe → load → run)

Every new backend implements the three module-level, monkeypatchable seams the
existing backends define, and is registered in a dispatch table keyed by the
registry entry's `backend` discriminator. `ModelManager` and the routes are not
modified.

## Shared invariants (all families)

1. **probe(entry)** — cheap, passive, side-effect-free: import check /
   `shutil.which` / model-file stat + sha256 / one loopback GET with short
   timeout. Raises `MediaUnavailable` (an `ImportError` → server 501) carrying the
   reason-coded install hint. Runs BEFORE any eviction (existing invariant).
2. **load(entry)** — the heavy step; re-verifies model-file sha256
   (`verify_sha256`) before use (`model_files_mismatch` on failure). Never
   downloads (new backends).
3. **run(backend, entry, ...)** — one inference; subprocess calls only through
   `portable.run_subprocess(argv, timeout=...)` (no shell, no killpg,
   capture_output, explicit timeout → clean error).
4. All three are module-level so the offline suite stubs them; tests never invoke
   real binaries or sockets.

## Image — `_IMAGE_BACKENDS["sdcpp"]`

- probe: `sd` on PATH (`missing_binary`) + GGUF manifest present
  (`missing_model_files`) + sha256 ok (`model_files_mismatch`).
- load: returns the validated invocation context (binary path + model path) — no
  process is kept warm; residency cost is zero (like the video backends).
- run: `sd -p <prompt> --seed <seed> --steps <steps> -W <w> -H <h> -o <out_path>`
  (exact argv finalized against the pinned release in implementation; pinned in
  tests as the subprocess contract).

## STT — new `_STT_BACKENDS` table

- `"mlx"`: the three existing functions, moved into the table unchanged
  (byte-identical behavior; the `_seam_arity` shims keep old monkeypatched fakes
  working).
- `"whispercpp"`: probe = binary + model manifest (as image); run =
  `whisper-cli -m <model> -f <audio> ...` → transcript text parsed from output
  file/stdout; timeout minutes-scale.

## TTS — unchanged seams

`_probe_tts` / `_load_tts_backend` / `_run_tts_backend` untouched; they are
already portable (kokoro-onnx + soundfile).

## Embedding — dispatch in `embeddings.py`

- `"mlx"`: existing `_probe_embed` / `_load_embed` / `_run_embed`, byte-identical.
- `"llamacpp-gateway"`:
  - URL resolution: `AGENCY_STUDIO_EMBED_GATEWAY_URL` or the entry default;
    `portable.require_loopback(url)` hard-rejects any non-loopback host
    (127.0.0.1 / ::1 / localhost) before any socket is opened. Plain HTTP is
    permitted only because of this guarantee (spec FR-010).
  - probe: GET `<url>/health`, timeout ≤ 1 s → `gateway_down` with a start hint on
    failure.
  - run: POST `<url>/v1/embeddings` (JSON `{"input": [...]}`), parse
    `data[i].embedding` → plain Python float lists (same return contract as the
    MLX path); validate vector length == `entry.ndim`.

## `engines/portable.py` (new shared helpers)

| Helper | Contract |
|---|---|
| `find_binary(name) -> str \| None` | `shutil.which` wrapper (single stub point) |
| `require_loopback(url) -> str` | returns url; raises `ValueError` on non-loopback host or non-http(s) scheme |
| `get_json(url, timeout)` / `post_json(url, payload, timeout)` | stdlib urllib, no redirects off-loopback |
| `run_subprocess(argv, timeout) -> CompletedProcess` | no shell, text, captured output, `TimeoutExpired` → clean `MediaUnavailable`-adjacent error message |
| `verify_model_file(model_file) -> Path` | exists → sha256 check → path; reason-coded failures |
