# TurnProof

**Catch the turn that broke—with event evidence.**

[Try the interactive demo](https://widechaos.github.io/turnproof/) · [Recorded test collection](assets/recorded)

TurnProof is an evidence-first regression lab for voice agents, built for the Nebius × NVIDIA Global AI Hackathon. It separates measurable rules from semantic judgment: deterministic code checks interruption stops, action counts and required tool arguments; NVIDIA Nemotron on Nebius checks whether an action contradicts the user's intent.

## Try it

The public demo runs checks in your browser. Choose a fault or normal control, click **Run local checks**, follow a finding to its events, compare outcomes, import a JSON trace, or export your report. Inspect the four audio replays and listen to the original synthetic inputs and reference-agent replies. NVIDIA results are recorded cloud calls, explicitly labeled as history. The interface never sends your imported trace to a server or makes an inference request.

```sh
python3 server.py
# Open http://127.0.0.1:4187/
python3 core.py fixtures/slow-interruption.json
python3 compare.py fixtures/slow-interruption.json fixtures/normal-interruption.json
python3 -m unittest discover -s tests
node tests/check_browser_parity.mjs
```

Python 3.10+; core/server use only the standard library. Node is needed only for the browser parity check. The checked-in `docs/` is a self-contained static build, including recorded evidence and synthetic audio.

## What actually runs

1. **Trace checks:** excessive/missing interruption stops, excess tool calls and incorrect configured tool arguments, each tied to event IDs.
2. **Audio replay:** original WAV → local whisper.cpp transcription → offline reference booking agent → real test tool actions → Kokoro-generated reply. Fault injection produces wrong-date and ignored-cancellation cases; the controls execute the expected actions.
3. **Semantic review:** `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` on the Nebius Token Factory public endpoint reviews only user intent and agent actions. Schema, event references and verdict consistency are validated. An invalid model response is rejected, never shown as a successful evaluation.

The four recorded audio cases contain two passing controls and two detected injected faults. Two later intent-only cloud runs correctly identified the cancellation and wrong-date contradictions. Earlier model attempts invented unmeasured interruption findings; those rejected outputs are retained in `assets/recorded/` to make the limitation inspectable. This small collection is not an accuracy benchmark.

## Reproduce audio replay

Install [FFmpeg](https://ffmpeg.org/) and [whisper.cpp](https://github.com/ggml-org/whisper.cpp), including `whisper-cli` on PATH. Download its English base model separately. Install the optional speech dependencies in a virtual environment:

```sh
python3 -m venv .runtime/venv
.runtime/venv/bin/pip install kokoro-onnx soundfile
.runtime/venv/bin/python run_audio_suite.py \
  --whisper-model /path/to/ggml-base.en.bin \
  --tts-model /path/to/kokoro-v1.0.onnx \
  --voices /path/to/voices-v1.0.bin
python3 build_demo.py
```

Obtain the Kokoro ONNX files from the [official runtime instructions](https://github.com/thewh1teagle/kokoro-onnx). Model weights are not bundled. `assets/audio/` contains my original synthetic clips. Generated speech remains labeled synthetic; no real-person voice is claimed.

## Optional live NVIDIA evaluation

Cloud calls default to disabled. Supply your own `NEBIUS_API_KEY` through the process environment and an account-verified `NEBIUS_MODEL` beginning `nvidia/`. Do not put secrets in a trace, shell history or repository. `keychain.py` is an optional local macOS credential adapter; judges do not need it.

After checking your provider's current free credit and model prices, explicitly authorize a bounded batch:

```sh
python3 authorize_free_batch.py --credit 1 --input-price 0.06 --output-price 0.24 \
  --model nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B --verified-now
python3 nebius.py assets/recorded/cancel-ignore_cancel.json
```

This is a manual attestation, not a billing API lookup. The allowance expires after ten minutes, requires at least $0.50 free credit, limits the batch to two calls, caps input/output and reserves $0.001 per attempt, including failures. There are no retries or automatic renewals. This guard is local to this client; it cannot prevent charges caused by other clients or provider billing. Use only verified free credit if avoiding paid usage.

## Evidence and limits

- Synthetic event fixtures illustrate 700 ms versus 150 ms stops; these are not measured production improvements.
- Audio replays measure **file-based batch processing**, including ASR and TTS. They do not measure streaming barge-in, real-time speech latency or human usability.
- The reference booking agent is intentionally small and deterministic. It is a test target, not a production assistant.
- A local pass covers configured rules only. Event citations make model output inspectable, but do not prove every semantic judgment correct.
- Source labels are declarations. TurnProof does not authenticate recordings or human participation.
- Public demo imports remain in the browser; reports may still contain sensitive data you import. Review them before sharing.

## License

MIT for this project's code and original synthetic assets. External models and runtimes retain their own licenses; see [third-party notices](THIRD_PARTY.md).
