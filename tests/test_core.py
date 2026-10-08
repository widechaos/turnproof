import json
import unittest
from pathlib import Path
from core import evaluate

ROOT = Path(__file__).resolve().parent.parent

class TraceChecks(unittest.TestCase):
    def fixture(self, name):
        return json.loads((ROOT / "fixtures" / name).read_text())

    def test_failed_trace_has_grounded_findings(self):
        trace = self.fixture("slow-interruption.json")
        report = evaluate(trace)
        self.assertFalse(report["deterministic_pass"])
        self.assertEqual({f["code"] for f in report["findings"]},
                         {"slow_interrupt_stop", "excess_tool_calls"})
        ids = {e["id"] for e in trace["events"]}
        for finding in report["findings"]:
            self.assertTrue(set(finding["evidence"]).issubset(ids))
        self.assertEqual(report["semantic_evaluation"], "not_run")

    def test_normal_control(self):
        self.assertTrue(evaluate(self.fixture("normal-interruption.json"))["deterministic_pass"])

    def test_missing_stop_fails(self):
        trace = self.fixture("normal-interruption.json")
        trace["events"] = trace["events"][:2]
        self.assertEqual(evaluate(trace)["findings"][0]["code"], "missing_audio_stop")

    def test_malformed_timestamp_rejected(self):
        trace = self.fixture("normal-interruption.json")
        trace["events"][1]["time_ms"] = -1
        with self.assertRaises(ValueError):
            evaluate(trace)
