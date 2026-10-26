"""Offline Morrow I programme tests: no external calls, no publication."""
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import morrow_cycle as m


class ProgrammeTests(TestCase):
    def test_method_and_audit_are_complete_and_not_self_certifying(self):
        self.assertEqual(len(m.MOVEMENTS), 7)
        self.assertEqual(len(m.AUDIT_GATES), 8)
        self.assertIn("Conjuration ↶ Sankofa", m.MOVEMENTS)
        self.assertTrue(all(x["status"] == "NOT_ASSESSED"
                            for x in m.audit_template().values()))

    def test_no_key_can_leak_to_news_or_wrong_host(self):
        with self.assertRaises(m.TransportError):
            m.api_get("https://news.google.com/rss/search?q=x", "moltbook_fake")
        with self.assertRaises(m.TransportError):
            m.api_get("https://evil.example/data", "moltbook_fake")

    def test_search_filters_unverified_results(self):
        self.assertEqual(m.moltbook_rows({"results": {"invalid": True}}), [])
        self.assertEqual(m.moltbook_rows({"results": [{"id": "abc123456"}]}),
                         [{"id": "abc123456"}])

    def test_cleaned_payload_has_no_unsupported_gate_passes(self):
        row = {"kind": "news_rss_lead", "url": "https://news.google.com/test",
               "title": "Climate risk", "excerpt": "A proposed intervention"}
        with patch.object(m, "model_draft", return_value={
                "draft": None, "model": None, "usage": None,
                "error": "No model"}):
            result = m.record("situational-conjuration", row, 1, "")
        self.assertFalse(result["independent_review"])
        self.assertEqual(result["publications_created"], 0)
        self.assertIsNone(result["computational_outcome"]["energy_kwh"])
        self.assertEqual(result["computational_outcome"]["decision"], "defer")
        self.assertTrue(all(v["status"] == "NOT_ASSESSED"
                            for v in result["eight_gate_audit"].values()))

    def test_daily_dry_run_requires_no_keys_and_cannot_post(self):
        source = {"kind": "news_rss_lead", "url": "https://news.google.com/test",
                  "title": "Climate adaptation in the Caribbean",
                  "excerpt": "A new study of risk and resource allocation"}
        with tempfile.TemporaryDirectory() as temp:
            outfile = str(Path(temp) / "morrow.json")
            with patch.dict(os.environ, {"MOLTBOOK_API_KEY": "", "GH_MODELS_TOKEN": ""}):
                with patch.object(m, "discover_news", return_value=[source]):
                    with patch.object(m, "model_draft",
                                      return_value={"draft": None, "model": None,
                                                    "usage": None, "error": "dry-run"}) as invoke:
                        data = m.produce("daily", outfile, dry_run=True)
            self.assertEqual(len(data["records"]), 1)
            self.assertEqual(data["outreach_sent"], 0)
            self.assertEqual(data["publications_created"], 0)
            self.assertEqual(data["records"][0]["authorization"], "internal_draft_only")
            self.assertTrue(Path(outfile).exists())
            self.assertEqual(invoke.call_count, 1)

    def test_conceptual_conjuration_does_not_need_news_or_public_discourse(self):
        with tempfile.TemporaryDirectory() as temp:
            output = str(Path(temp) / "conceptual.json")
            with patch.object(m, "discover_news") as news, patch.object(
                    m, "discover_moltbook") as molt:
                data = m.produce("conceptual-conjuration", output, dry_run=True)
            news.assert_not_called()
            molt.assert_not_called()
            self.assertEqual(data["records"][0]["track"], "conceptual-conjuration")

    def test_first_witness_is_not_first_essay(self):
        commissions = json.loads((m.ROOT / "agent" / "commissions.json").read_text())
        self.assertEqual(commissions["publication_order"]["first_substantial_essay"],
                         "Every Answer Has a History")
        self.assertEqual(commissions["publication_order"]["witness_status"], "draft_only")
        self.assertFalse(commissions["publication_order"]["automated_publication"])

    def test_rank_deduplicates_and_is_bounded(self):
        rows = [{"url": "https://news.google.com/" + str(i // 2),
                 "title": "Climate agent infrastructure", "excerpt": ""} for i in range(60)]
        self.assertLessEqual(len(m.rank_leads(rows)), m.MAX_CANDIDATES)
        urls = [row["url"] for row in m.rank_leads(rows)]
        self.assertEqual(len(urls), len(set(urls)))


if __name__ == "__main__":
    main()
