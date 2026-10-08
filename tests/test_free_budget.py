import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from free_budget import reserve_request
from nebius import diagnose


class FreeBudget(unittest.TestCase):
    model = "nvidia/test-model"
    messages = [{"content": "Synthetic trace"}]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "allowance.json"
        self.state = {"verified_at": 1000, "model": self.model,
                      "free_credit_usd": 1, "input_usd_per_million": 0.06,
                      "output_usd_per_million": 0.24, "reserved_calls": 0}

    def write(self):
        self.path.write_text(json.dumps(self.state))

    def reserve(self):
        return reserve_request(self.model, self.messages, 512, self.path, 1001)

    def test_missing_allowance_blocks(self):
        with self.assertRaises(RuntimeError):
            self.reserve()

    def test_batch_stops_after_two_reservations(self):
        self.write()
        self.reserve()
        self.reserve()
        with self.assertRaises(RuntimeError):
            self.reserve()
        self.assertEqual(json.loads(self.path.read_text())["reserved_usd"], 0.002)

    def test_expired_verification_blocks(self):
        self.state["verified_at"] = 300
        self.write()
        with self.assertRaises(RuntimeError):
            self.reserve()

    def test_low_credit_wrong_model_and_high_price_block(self):
        for field, value in [("free_credit_usd", 0.1), ("model", "other"),
                             ("output_usd_per_million", 10)]:
            with self.subTest(field=field):
                original = self.state[field]
                self.state[field] = value
                self.write()
                with self.assertRaises(RuntimeError):
                    self.reserve()
                self.state[field] = original

    def test_oversized_input_does_not_reserve(self):
        self.write()
        with self.assertRaises(RuntimeError):
            reserve_request(self.model, [{"content": "大" * 2000}], 512, self.path, 1001)
        self.assertEqual(json.loads(self.path.read_text())["reserved_calls"], 0)

    def test_disabled_guard_prevents_network(self):
        with patch.dict("os.environ", {"NEBIUS_API_KEY": "test-only", "NEBIUS_MODEL": self.model}), \
             patch("nebius.reserve_request", side_effect=RuntimeError("Cloud disabled")), \
             patch("nebius.urllib.request.build_opener") as network:
            with self.assertRaises(RuntimeError):
                diagnose({"source": "synthetic", "expectations": {}, "events": []})
            network.assert_not_called()
