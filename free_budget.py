"""Fail-closed, short-lived allowance for a manually verified free-credit batch.

This limits this application's requests, not the provider account or other clients.
Failed requests retain their reservation because the provider may have charged them.
"""
import fcntl
import json
import time
from pathlib import Path

ALLOWANCE = Path(__file__).parent / ".runtime/free-credit-session.json"
MAX_INPUT_BYTES = 4096
MAX_OUTPUT_TOKENS = 512
RESERVATION_USD = 0.001


def reserve_request(model, messages, output_tokens, allowance=ALLOWANCE, now=None):
    now = time.time() if now is None else now
    input_bytes = sum(len(m["content"].encode("utf-8")) for m in messages)
    if input_bytes > MAX_INPUT_BYTES or not 1 <= output_tokens <= MAX_OUTPUT_TOKENS:
        raise RuntimeError("Free batch input/output limit exceeded; no request sent")
    try:
        stream = allowance.open("r+")
    except FileNotFoundError:
        raise RuntimeError("Cloud disabled: no freshly verified free-credit allowance") from None
    with stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        state = json.load(stream)
        verified = state.get("verified_at", 0)
        if not 0 <= now - verified <= 600:
            raise RuntimeError("Free-credit verification expired; no request sent")
        if state.get("model") != model or state.get("free_credit_usd", 0) < 0.5:
            raise RuntimeError("Verified model/free-credit reserve missing; no request sent")
        # UI-confirmed upper prices; 1K extra input tokens allow message overhead.
        # Reserve more than twice the resulting maximum to cover tax and rounding.
        rates = (state.get("input_usd_per_million", -1),
                 state.get("output_usd_per_million", -1))
        if not (0 <= rates[0] <= 0.06 and 0 <= rates[1] <= 0.24):
            raise RuntimeError("Model pricing not verified within free-batch limits")
        calls = state.get("reserved_calls", 0)
        if not isinstance(calls, int) or not 0 <= calls < 2:
            raise RuntimeError("Free batch exhausted; no request sent")
        state["reserved_calls"] = calls + 1
        state["reserved_usd"] = (calls + 1) * RESERVATION_USD
        stream.seek(0)
        json.dump(state, stream)
        stream.truncate()
        stream.flush()
        return {"reserved_calls": calls + 1, "reserved_usd": state["reserved_usd"]}
