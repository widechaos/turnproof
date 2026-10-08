"""Compare deterministic outcomes for matching test inputs and policies."""
import json
from collections import Counter
from pathlib import Path
from core import evaluate


def signature(trace):
    return {"source": trace["source"], "expectations": trace["expectations"],
            "user_events": [{k: v for k, v in e.items() if k != "id"}
                            for e in trace["events"] if e["type"].startswith("user_")]}


def measurements(trace):
    delays, active, pending = [], False, None
    for event in trace["events"]:
        if event["type"] == "assistant_audio_start":
            active = True
        elif event["type"] == "user_interrupt" and active and pending is None:
            pending = event
        elif event["type"] == "assistant_audio_stop":
            if pending:
                delays.append({"delay_ms": event["time_ms"] - pending["time_ms"],
                               "evidence": [pending["id"], event["id"]]})
            active, pending = False, None
    return {"interrupt_stops": delays,
            "tool_calls": dict(Counter(e["name"] for e in trace["events"]
                                       if e["type"] == "tool_call"))}


def compare(before, after):
    reports = [evaluate(before), evaluate(after)]
    if signature(before) != signature(after):
        raise ValueError("Comparison requires matching source, user inputs and expectations")
    return {"scope": "deterministic_event_comparison", "source": before["source"],
            "human_validation": "not_established", "semantic_evaluation": "not_run",
            "before": {**reports[0], **measurements(before)},
            "after": {**reports[1], **measurements(after)},
            "finding_count_change": len(reports[1]["findings"]) - len(reports[0]["findings"])}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(json.loads(args.before.read_text()),
                             json.loads(args.after.read_text())), indent=2))
