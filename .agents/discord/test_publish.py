"""Exercise delivery safety without sending any Discord messages."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import publish


class WebhookSettingsTests(unittest.TestCase):
    def setUp(self):
        self.url = "https://discord.com/api/webhooks/123/test-token"
        self.environment = patch.dict(publish.os.environ, {publish.WEBHOOK_SETTING: ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_stored_credential_is_used_without_checkout_settings(self):
        with patch.object(publish.credential_store, "read_webhook", return_value=self.url):
            self.assertEqual(publish.webhook_url(), self.url)

    def test_repository_env_does_not_supply_a_webhook(self):
        state = Path(__file__).resolve().parent / "state"
        state.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=state) as directory:
            (Path(directory) / ".env").write_text(
                publish.WEBHOOK_SETTING + "=" + self.url, encoding="utf-8"
            )
            with contextlib.chdir(directory):
                with patch.object(publish.credential_store, "read_webhook", return_value=None):
                    self.assertIsNone(publish.webhook_url())

    def test_environment_override_skips_credential_store(self):
        with patch.dict(publish.os.environ, {publish.WEBHOOK_SETTING: self.url}):
            with patch.object(publish.credential_store, "read_webhook") as stored:
                self.assertEqual(publish.webhook_url(), self.url)
                stored.assert_not_called()

    def test_invalid_stored_url_is_rejected(self):
        with patch.object(publish.credential_store, "read_webhook", return_value="https://example.invalid/webhook"):
            with self.assertRaises(publish.DeliveryError):
                publish.webhook_url()


class PublisherTests(unittest.TestCase):
    def setUp(self):
        state = Path(__file__).resolve().parent / "state"
        state.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=state)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Campaign test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "core.hooksPath", ".disabled-hooks")
        self.image = self.root / "Adventures/2026-10-03/scene.png"
        self.image.parent.mkdir(parents=True)
        self.image.write_bytes(b"committed image bytes")
        outbox = self.root / publish.OUTBOX
        outbox.mkdir(parents=True)
        self.entry = {"id": "test-scene", "content": "A leaky tent.",
                      "images": ["Adventures/2026-10-03/scene.png"]}
        self.entry_path = outbox / "test-scene.json"
        self.entry_path.write_text(json.dumps(self.entry), encoding="utf-8")
        self.git("add", "Adventures", publish.OUTBOX)
        self.git("commit", "-qm", "test fixture")
        self.url = "https://discord.com/api/webhooks/123/test-token"
        self.metadata = {"id": "123", "type": 1, "guild_id": publish.GUILD_ID,
                         "channel_id": publish.PARENT_CHANNEL_ID}
        self.message = {"id": "456", "webhook_id": "123", "channel_id": publish.THREAD_ID,
                        "content": self.entry["content"],
                        "attachments": [{"filename": "scene.png", "size": len(self.image.read_bytes())}]}

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args],
                                       stderr=subprocess.DEVNULL)

    def run_publish(self):
        with contextlib.redirect_stdout(io.StringIO()):
            publish.publish(self.root, self.url)

    def test_upload_uses_committed_image_and_routes_to_thread_once(self):
        self.image.write_bytes(b"uncommitted replacement")
        with patch.object(publish, "request_json", side_effect=[self.metadata, self.message, self.message]) as api:
            self.run_publish()
            calls = api.call_args_list
            self.assertIn("wait=true&thread_id=" + publish.THREAD_ID, calls[1].args[0])
            self.assertEqual(calls[1].args[1], "POST")
            self.assertIn(b"committed image bytes", calls[1].args[2])
            self.assertNotIn(b"uncommitted replacement", calls[1].args[2])
            self.assertIn(b'"allowed_mentions": {"parse": []}', calls[1].args[2])
            self.assertEqual(calls[2].args[0], self.url + "/messages/456?thread_id=" + publish.THREAD_ID)
        with patch.object(publish, "request_json") as api:
            self.run_publish()
            api.assert_not_called()

    def test_wrong_parent_channel_prevents_send(self):
        wrong = dict(self.metadata, channel_id=publish.THREAD_ID)
        with patch.object(publish, "request_json", return_value=wrong) as api:
            with self.assertRaises(publish.DeliveryError):
                self.run_publish()
            self.assertEqual(api.call_count, 1)

    def test_lost_send_response_cannot_create_a_duplicate(self):
        with patch.object(publish, "request_json", side_effect=[self.metadata, publish.RequestError("No confirmation")]):
            with self.assertRaises(publish.RequestError):
                self.run_publish()
        with patch.object(publish, "request_json", return_value=self.metadata) as api:
            with self.assertRaisesRegex(publish.DeliveryError, "uncertain send"):
                self.run_publish()
            self.assertEqual(api.call_count, 1)

    def test_failed_readback_recovers_without_posting_again(self):
        with patch.object(publish, "request_json", side_effect=[self.metadata, self.message, publish.RequestError("No readback")]):
            with self.assertRaises(publish.RequestError):
                self.run_publish()
        with patch.object(publish, "request_json", side_effect=[self.metadata, self.message]) as api:
            self.run_publish()
            self.assertEqual(api.call_count, 2)
            self.assertTrue(all(len(call.args) == 1 for call in api.call_args_list))

    def test_wrong_thread_message_is_not_confirmed(self):
        wrong = dict(self.message, channel_id=publish.PARENT_CHANNEL_ID)
        with patch.object(publish, "request_json", side_effect=[self.metadata, wrong]):
            with self.assertRaises(publish.DeliveryError):
                self.run_publish()
        receipt = publish.receipts_for(self.root)["test-scene"]
        self.assertEqual(receipt["status"], "sent")

    def test_archived_desktop_receipt_prevents_replay_in_fresh_checkout(self):
        message_url = f"https://discord.com/channels/{publish.GUILD_ID}/{publish.THREAD_ID}/456"
        with contextlib.redirect_stdout(io.StringIO()):
            publish.record_ui(self.root, "test-scene", message_url)
        self.git("add", publish.DELIVERED)
        self.git("commit", "-qm", "save delivery")
        (self.root / ".agents/discord/state/receipts.json").unlink()
        self.assertEqual(publish.pending_posts(self.root), [])

    def test_invalid_image_path_cannot_read_private_files(self):
        self.entry["images"] = ["Adventures/../../.env"]
        self.entry_path.write_text(json.dumps(self.entry), encoding="utf-8")
        self.git("add", publish.OUTBOX)
        self.git("commit", "-qm", "invalid path")
        with self.assertRaisesRegex(publish.DeliveryError, "only attach images"):
            publish.committed_posts(self.root)

    def test_desktop_receipt_rejects_other_destination(self):
        with self.assertRaises(publish.DeliveryError):
            publish.record_ui(self.root, "test-scene", "https://discord.com/channels/1/2/456")
        self.assertEqual(publish.receipts_for(self.root), {})


if __name__ == "__main__":
    unittest.main()
