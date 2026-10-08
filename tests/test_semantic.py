import unittest
from nebius import validate_diagnosis, parse_reply

class EvidenceValidation(unittest.TestCase):
    trace = {"events": [{"id": "u1", "type":"user_transcript"}, {"id": "a1", "type":"assistant_text"}]}
    def test_contradiction_preserved_as_invalid_output(self):
        content = '{"verdict":"pass","findings":[{"reason":"Success","evidence":["a1"]}]}'
        result = parse_reply({"choices": [{"message": {"content": content}}]}, self.trace)
        self.assertEqual(result["status"], "invalid_model_output")
        self.assertEqual(result["untrusted_model_output"], content)
        self.assertNotIn("diagnosis", result)
    def test_supported_failure(self):
        data = {"verdict": "fail", "findings": [{"check":"task_intent", "reason": "Wrong date", "evidence": ["u1", "a1"]}]}
        self.assertEqual(validate_diagnosis(data, self.trace), data)
    def test_invented_event_rejected(self):
        with self.assertRaises(ValueError):
            validate_diagnosis({"verdict": "fail", "findings": [{"reason": "Wrong date", "evidence": ["invented"]}]}, self.trace)
    def test_ungrounded_failure_rejected(self):
        with self.assertRaises(ValueError):
            validate_diagnosis({"verdict": "fail", "findings": []}, self.trace)
    def test_conflicting_pass_rejected(self):
        with self.assertRaises(ValueError):
            validate_diagnosis({"verdict": "pass", "findings": [{"reason": "Error", "evidence": ["a1"]}]}, self.trace)
    def test_uncertain_accepted(self):
        self.assertEqual(validate_diagnosis({"verdict": "uncertain", "findings": []}, self.trace)["verdict"], "uncertain")

class MeasuredClaimValidation(unittest.TestCase):
    def test_tool_events_cannot_be_invented_interruption(self):
        trace={"id":"cancel","source":"synthetic_voice","expectations":{"interrupt_stop_budget_ms":250,"max_tool_calls":{"save_booking":0}},"events":[{"id":"u","time_ms":1000,"type":"user_transcript"},{"id":"t","time_ms":1600,"type":"tool_call","name":"save_booking"}]}
        with self.assertRaises(ValueError):
            validate_diagnosis({"verdict":"fail","findings":[{"check":"interruption_latency","reason":"Delay exceeded","evidence":["u","t"]}]},trace)
    def test_policy_compliant_tool_call_cannot_be_count_failure(self):
        trace={"id":"ok","source":"synthetic_event_fixture","expectations":{"interrupt_stop_budget_ms":250,"max_tool_calls":{"save_booking":1}},"events":[{"id":"t","time_ms":0,"type":"tool_call","name":"save_booking"}]}
        with self.assertRaises(ValueError):
            validate_diagnosis({"verdict":"fail","findings":[{"check":"tool_count","reason":"Too many calls","evidence":["t"]}]},trace)
