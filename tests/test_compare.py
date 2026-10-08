import copy
import json
import unittest
from pathlib import Path
from compare import compare

class Comparison(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "fixtures"
        self.before = json.loads((root / "slow-interruption.json").read_text())
        self.after = json.loads((root / "normal-interruption.json").read_text())

    def test_matching_fixture_comparison_keeps_evidence(self):
        report = compare(self.before, self.after)
        self.assertEqual(report["before"]["interrupt_stops"][0]["delay_ms"], 700)
        self.assertEqual(report["after"]["interrupt_stops"][0]["delay_ms"], 150)
        self.assertEqual(report["after"]["interrupt_stops"][0]["evidence"], ["u1", "a2"])
        self.assertEqual(report["finding_count_change"], -2)
        self.assertEqual(report["human_validation"], "not_established")

    def test_changed_policy_or_input_cannot_claim_improvement(self):
        for changed in ("policy", "input", "source"):
            other = copy.deepcopy(self.after)
            if changed == "policy":
                other["expectations"]["interrupt_stop_budget_ms"] = 1000
            elif changed == "input":
                other["events"][1]["text"] = "Cancel"
            else:
                other["source"] = "authorized_human_recording"
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                compare(self.before, other)
