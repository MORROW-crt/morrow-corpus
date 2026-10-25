"""Offline tests for Morrow's Moltbook agent. No live API access."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import morrow_moltbook as agent


class AgentSafetyTests(unittest.TestCase):
    def test_reject_unknown_host(self):
        with self.assertRaises(agent.BridgeError):
            agent.call("https://example.org/api", moltkey="fake-value")

    def test_never_send_moltbook_key_to_github_models(self):
        with self.assertRaises(agent.BridgeError):
            agent.call(agent.MODEL, moltkey="fake-value")

    def test_never_send_models_token_to_moltbook(self):
        with self.assertRaises(agent.BridgeError):
            agent.call(agent.BASE + "/agents/status", modeltoken="fake-value")

    def test_registration_forbidden_in_github_actions(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            with self.assertRaises(agent.BridgeError):
                agent.register("MorrowCRT")

    def test_claim_required_before_comment(self):
        with patch.object(agent, "call", return_value={"status": "pending_claim"}) as api:
            with self.assertRaises(agent.BridgeError):
                agent.post_comment("fake-key", "post_123456", "A careful, substantive comment on the original claim.")
            self.assertEqual(api.call_count, 1)
            self.assertEqual(api.call_args.args[0], agent.BASE + "/agents/status")

    def test_claim_required_before_new_post(self):
        with patch.object(agent, "call", return_value={"status": "pending_claim"}) as api:
            with self.assertRaises(agent.BridgeError):
                agent.publish_post("fake-key", "general", "A legitimate question", "This paragraph is long enough for a valid but refused test post.")
            self.assertEqual(api.call_count, 1)

    def test_search_is_read_only(self):
        with tempfile.TemporaryDirectory() as root:
            path = str(Path(root) / "review.json")
            with patch.object(agent, "claimed", return_value=True):
                with patch.object(agent, "call", return_value={"results": []}) as api:
                    with patch.dict(os.environ, {"GH_MODELS_TOKEN": ""}):
                        agent.scan("fake-key", path)
                    self.assertEqual(len(api.call_args_list), 3)
                    for c in api.call_args_list:
                        self.assertEqual(c.kwargs.get("method", "GET"), "GET")
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(data["published_count"], 0)
            self.assertEqual(data["candidates"], [])

    def test_comment_writes_only_when_claimed(self):
        with patch.object(agent, "call", side_effect=[
            {"status": "claimed"}, {"success": True}
        ]) as api:
            agent.post_comment("fake-key", "post_123456",
                "What specific evidence could distinguish the two causal explanations?")
            self.assertEqual(api.call_count, 2)
            self.assertEqual(api.call_args_list[1].kwargs["method"], "POST")
            self.assertEqual(api.call_args_list[1].kwargs["moltkey"], "fake-key")


if __name__ == "__main__":
    unittest.main()
