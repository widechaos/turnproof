"""Evidence-backed checks for synthetic voice-agent event traces."""
import json
from collections import Counter
from pathlib import Path


def evaluate(trace):
    events = trace["events"]
    ids = [e["id"] for e in events]
    if len(ids) != len(set(ids)):
        raise ValueError("Event IDs must be unique")
    if any(e["time_ms"] < 0 for e in events):
        raise ValueError("Negative event timestamp")
    if any(a["time_ms"] > b["time_ms"] for a, b in zip(events, events[1:])):
        raise ValueError("Events must be ordered by timestamp")
    findings = []
    budget = trace["expectations"]["interrupt_stop_budget_ms"]
    tool_limit = trace["expectations"]["max_tool_calls"]
    active = None
    pending_interrupt = None
    for event in events:
        kind = event["type"]
        if kind == "assistant_audio_start":
            active = event
        elif kind == "user_interrupt" and active and pending_interrupt is None:
            pending_interrupt = event
        elif kind == "assistant_audio_stop":
            if pending_interrupt:
                delay = event["time_ms"] - pending_interrupt["time_ms"]
                if delay > budget:
                    findings.append({"code": "slow_interrupt_stop", "value_ms": delay,
                                     "evidence": [pending_interrupt["id"], event["id"]]})
            active = pending_interrupt = None
    if pending_interrupt:
        findings.append({"code": "missing_audio_stop", "evidence": [pending_interrupt["id"]]})
    calls = [e for e in events if e["type"] == "tool_call"]
    counts = Counter(e["name"] for e in calls)
    for name, count in counts.items():
        limit = tool_limit.get(name)
        if limit is not None and count > limit:
            findings.append({"code": "excess_tool_calls", "tool": name, "count": count,
                             "evidence": [e["id"] for e in calls if e["name"] == name]})
    for call in calls:
        expected = trace['expectations'].get('required_tool_arguments', {}).get(call['name'], {})
        for key, value in expected.items():
            if call.get('arguments', {}).get(key) != value:
                findings.append({'code': 'wrong_tool_argument', 'tool': call['name'],
                                 'argument': key, 'expected': value,
                                 'actual': call.get('arguments', {}).get(key),
                                 'evidence': [call['id']]})
    return {"trace_id": trace["id"], "source": trace["source"],
            "deterministic_pass": not findings, "findings": findings,
            "semantic_evaluation": "not_run", "audio_pipeline": "not_tested"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(json.loads(args.trace.read_text())), indent=2))
