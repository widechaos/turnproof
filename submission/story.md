## Inspiration

Voice agents can sound convincing while taking the wrong action. A cancellation that still creates a booking is easy to miss if a test only scores the transcript. I built TurnProof to connect failures to the exact user, playback and tool events that caused them.

## What it does

TurnProof is an evidence-first regression lab. Its browser workspace checks event traces, highlights cited evidence, compares matching controls, imports JSON traces and exports reports. It includes original synthetic audio, measured file-based reference-agent replays, and recorded NVIDIA model evaluations.

Deterministic code checks interruption stop budgets, repeated actions and required tool arguments. NVIDIA Nemotron separately reviews semantic intent: did the action contradict what the user asked? A passing mechanical report is never presented as proof of complete task success.

## How I built it

The core uses Python's standard library. A matching JavaScript engine supports local browser checks without uploading imported traces. whisper.cpp transcribes original Kokoro-generated WAV files; an offline reference booking agent executes real test tool callbacks and produces Kokoro replies. The four recorded cases include date correction and cancellation, each with a control and an intentionally injected fault.

For cloud evaluation, I called `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` through the Nebius Token Factory public chat-completions endpoint. The model receives user/action evidence and a semantic goal. Output validation checks JSON, verdict consistency and event references. Recorded results, including rejected attempts, are available in the public repository. The public UI shows historical cloud runs; it does not claim to make live requests.

## Challenges and what I learned

Early model responses invented interruption findings in file-based audio runs that had no streaming interruption measurement. I rejected those responses, retained the evidence, and narrowed the model's input and responsibility to semantic intent. Mechanical timing and action constraints remain deterministic. The later intent-only runs correctly cited the cancellation and wrong-date contradictions.

This taught me that adding more prompt instructions was less useful than separating measurable checks from judgment and enforcing the evidence contract.

## Accomplishments

The four measured audio replays produced the expected two passing controls and two detected injected faults. NVIDIA inference correctly identified both faulty action contradictions in the later intent-only runs. The interactive demo, test collection, MIT source, license notices and reproduction instructions are public. I also verified parity between the browser and Python findings on the supplied traces.

## Limitations and next steps

All supplied recordings are synthetic. The booking agent is a small offline reference target. Batch processing times include ASR and speech generation; they are not streaming barge-in latency. There were no human participants, and this small collection is not an accuracy benchmark. A local pass covers configured rules only.

My next step is a streaming adapter with measured playback-stop events and a broader annotated collection from authorized real-world integrations.

## Platform feedback

Nebius's public endpoint allowed NVIDIA evaluation without deploying a GPU instance, and per-request token usage made small experiments inspectable. The compact NVIDIA model supported concise intent diagnoses, but schema-valid output still required evidence validation. I would value an account-level hard free-credit spending cap and clearer provider-native structured-output examples for compact models. My client uses expiring, manually verified, two-request allowances; that is an application guard, not a provider-wide billing guarantee.
