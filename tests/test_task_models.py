import json
import time
import unittest

from lib.task_models import TaskHandle, TaskResult


class TestTaskHandle(unittest.TestCase):
    def test_create_handle(self):
        h = TaskHandle(provider="codex", timestamp=1000.0)
        self.assertEqual(h.provider, "codex")
        self.assertEqual(h.timestamp, 1000.0)

    def test_to_dict(self):
        h = TaskHandle(provider="droid", timestamp=2000.0)
        d = h.to_dict()
        self.assertEqual(d["provider"], "droid")
        self.assertEqual(d["timestamp"], 2000.0)

    def test_to_json(self):
        h = TaskHandle(provider="gemini", timestamp=3000.0)
        j = h.to_json()
        data = json.loads(j)
        self.assertEqual(data["provider"], "gemini")
        self.assertEqual(data["timestamp"], 3000.0)

    def test_to_json_valid_json(self):
        h = TaskHandle(provider="claude", timestamp=4000.0)
        j = h.to_json()
        # Verify it's valid JSON
        parsed = json.loads(j)
        self.assertIsInstance(parsed, dict)


class TestTaskResult(unittest.TestCase):
    def test_completed_result(self):
        r = TaskResult(provider="codex", status="completed", output="OK")
        self.assertTrue(r.is_done)
        self.assertTrue(r.is_success)
        self.assertEqual(r.output, "OK")

    def test_pending_result(self):
        r = TaskResult(provider="codex", status="pending")
        self.assertFalse(r.is_done)
        self.assertFalse(r.is_success)
        self.assertIsNone(r.output)
        self.assertIsNone(r.error)

    def test_error_result(self):
        r = TaskResult(provider="codex", status="error", error="Failed")
        self.assertTrue(r.is_done)
        self.assertFalse(r.is_success)
        self.assertEqual(r.error, "Failed")

    def test_to_dict(self):
        r = TaskResult(provider="claude", status="completed", output="Hello")
        d = r.to_dict()
        self.assertEqual(d["provider"], "claude")
        self.assertEqual(d["status"], "completed")
        self.assertEqual(d["output"], "Hello")

    def test_to_json_roundtrip(self):
        r = TaskResult(provider="claude", status="completed", output="Hello")
        j = r.to_json()
        data = json.loads(j)
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["output"], "Hello")

    def test_error_with_provider(self):
        r = TaskResult(provider="droid", status="error", error="Connection refused")
        self.assertEqual(r.provider, "droid")
        self.assertEqual(r.status, "error")
        self.assertEqual(r.error, "Connection refused")
