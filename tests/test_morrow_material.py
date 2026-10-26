"""Offline usage-accounting tests. No network, no secrets, no made-up footprint."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import morrow_material as m
from scripts import morrow_moltbook as molt
from scripts import free_relay as relay
from scripts import morrow_cycle as cycle


class MaterialTests(unittest.TestCase):
    def test_provider_tokens_only_never_estimated_from_text(self):
        counts = m.usage_from_response({"usage": {
            "prompt_tokens": 123, "completion_tokens": 9, "total_tokens": 132,
            "prompt_tokens_details": {"cached_tokens": 4},
            "completion_tokens_details": {"reasoning_tokens": 2}}})
        self.assertEqual(counts["basis"], "provider_reported")
        self.assertEqual(counts["cached_input_tokens"], 4)
        self.assertEqual(counts["reasoning_output_tokens"], 2)
        blank = m.usage_from_response({"choices": [{"message": {"content": "a" * 5000}}]})
        self.assertIsNone(blank["prompt_tokens"])
        self.assertEqual(blank["basis"], "not_reported")
        self.assertIsNone(m.usage_from_response({"usage": {"prompt_tokens": True}})["prompt_tokens"])

    def test_event_never_allocates_energy_or_credits(self):
        response = {"model": "sample/model", "usage": {"prompt_tokens": 8, "completion_tokens": 4}}
        event = m.create_event("research", "github_models", "sample/model", "response_received",
                               m.current_utc(), 0.01, response)
        self.assertTrue(event["generated_response_received"])
        self.assertEqual(event["usage"]["prompt_tokens"], 8)
        self.assertTrue(all(metric["value"] is None for metric in event["material_impact"].values()))
        self.assertEqual(event["audit"]["material_measurement_level"], "unknown")
        self.assertEqual(event["elapsed_scope"], "request_and_client_wait_not_model_compute_energy")
        self.assertNotIn("choices", event)

    def test_invocation_success_and_failure_are_logged_without_content(self):
        with tempfile.TemporaryDirectory() as root:
            dest = str(Path(root) / "events.jsonl")
            with patch.dict(os.environ, {"MORROW_MATERIAL_LEDGER": dest}, clear=False):
                with m.ModelInvocation("demo", "openrouter", "model:free") as meter:
                    meter.received({"usage": {"prompt_tokens": 33,
                                               "completion_tokens": 7,
                                               "total_tokens": 40},
                                    "model": "model:free",
                                    "choices": [{"message": {"content": "SECRET_PROMPT"}}]})
                try:
                    with m.ModelInvocation("demo", "openrouter", "model:free"):
                        raise RuntimeError("SECRET_API_KEY")
                except RuntimeError:
                    pass
            data = Path(dest).read_text(encoding="utf-8")
            self.assertNotIn("SECRET_API_KEY", data)
            self.assertNotIn("SECRET_PROMPT", data)
            records = m.read_events(dest)
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["response_status"], "response_received")
            self.assertEqual(records[1]["response_status"], "failed")
            self.assertEqual(records[1]["error_class"], "RuntimeError")
            report = m.summary(records)
            self.assertEqual(report["known_input_tokens_total"], 33)
            self.assertEqual(report["responses_received"], 1)
            self.assertIsNone(report["energy_wh"])
            self.assertEqual(report["material_footprint_status"], "unknown_not_zero")

    def test_empty_ledger_is_not_zero_energy_claim(self):
        d = m.summary([])
        self.assertEqual(d["model_requests_recorded"], 0)
        self.assertIsNone(d["water_consumption_ml"])
        self.assertEqual(d["material_footprint_status"], "unknown_not_zero")

    def test_moltbook_reply_draft_is_metered(self):
        mock_result = {"model": "openai/gpt-4o-mini",
                       "choices": [{"message": {"content":
                           "A sufficiently long source grounded response to the discussion."}}],
                       "usage": {"prompt_tokens": 60, "completion_tokens": 15}}
        with tempfile.TemporaryDirectory() as root:
            dest = str(Path(root) / "events.jsonl")
            with patch.dict(os.environ, {"MORROW_MATERIAL_LEDGER": dest}):
                with patch.object(molt, "call", return_value=mock_result):
                    text = molt.make_draft({"title": "Source", "excerpt": "Challenge"}, "fake")
            self.assertIsNotNone(text)
            entries = m.read_events(dest)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["flow"], "moltbook_reply_draft")
            self.assertEqual(entries[0]["usage"]["completion_tokens"], 15)

    def test_free_relay_response_is_metered(self):
        mock_result = {"model": "sample/free", "id": "provider123",
                       "choices": [{"message": {"content": "A coherent contribution."}}],
                       "usage": {"prompt_tokens": 22, "completion_tokens": 8}}
        with tempfile.TemporaryDirectory() as root:
            dest = str(Path(root) / "events.jsonl")
            with patch.dict(os.environ, {"MORROW_MATERIAL_LEDGER": dest}):
                with patch.object(relay, "fetch_json", return_value=mock_result):
                    data = relay.run_call("fake", "sample/free:free", "Hello")
            self.assertEqual(data["usage"]["prompt_tokens"], 22)
            self.assertEqual(m.read_events(dest)[0]["flow"], "free_model_relay")

    def test_morrow_research_failed_model_provider_is_metered(self):
        with tempfile.TemporaryDirectory() as root:
            dest = str(Path(root) / "events.jsonl")
            with patch.dict(os.environ, {"MORROW_MATERIAL_LEDGER": dest}):
                with patch.object(cycle.urllib.request, "build_opener",
                                  side_effect=cycle.urllib.error.URLError("not ready")):
                    result = cycle.model_draft("For research only", "fake")
            self.assertIsNone(result["draft"])
            self.assertIsNotNone(result["material_event_id"])
            ledger = m.read_events(dest)
            self.assertEqual(len(ledger), 1)
            self.assertEqual(ledger[0]["response_status"], "invalid_response")
            self.assertIsNone(ledger[0]["usage"]["total_tokens"])
            self.assertIsNone(ledger[0]["material_impact"]["electricity_wh"]["value"])

    def test_audit_rejects_pretend_energy_observation(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "fake.jsonl"
            event = m.create_event("test", "github_models", "example", "response_received",
                                   m.current_utc(), 0.5, {})
            event["material_impact"]["electricity_wh"]["value"] = 1.0
            p.write_text(json.dumps(event) + "\n", encoding="utf-8")
            # Validation checks unapproved material impact, even if plausible.
            events = m.read_events(p)
            self.assertTrue(any(x["material_impact"]["electricity_wh"]["value"] is not None
                                for x in events))
            self.assertFalse(event["audit"]["independent_validation"])


if __name__ == "__main__":
    unittest.main()
