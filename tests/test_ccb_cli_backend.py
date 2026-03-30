import unittest
from unittest.mock import MagicMock, patch

from lib.ccb_cli_backend import (
    CCBCLIBackend,
    EXIT_ERROR,
    EXIT_NO_REPLY,
    EXIT_OK,
    SUPPORTED_PROVIDERS,
)
from lib.task_models import TaskHandle


class TestCCBCLIBackend(unittest.TestCase):
    def setUp(self):
        self.backend = CCBCLIBackend()

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_submit_returns_handle(self, mock_run, mock_lock):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = self.backend.submit("codex", "Test prompt")
        self.assertIsInstance(handle, TaskHandle)
        self.assertEqual(handle.provider, "codex")
        self.assertGreater(handle.timestamp, 0)

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_submit_with_context(self, mock_run, mock_lock):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = self.backend.submit("codex", "Test", context={"key": "value"})
        self.assertEqual(handle.provider, "codex")

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_poll_completed(self, mock_run, mock_lock):
        mock_run.return_value = MagicMock(
            returncode=EXIT_OK, stdout="Hello world", stderr=""
        )
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = TaskHandle(provider="codex", timestamp=1000.0)
        result = self.backend.poll(handle)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output, "Hello world")

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_poll_pending(self, mock_run, mock_lock):
        mock_run.return_value = MagicMock(
            returncode=EXIT_NO_REPLY, stdout="", stderr=""
        )
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = TaskHandle(provider="codex", timestamp=1000.0)
        result = self.backend.poll(handle)
        self.assertEqual(result.status, "pending")
        self.assertIsNone(result.output)

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_poll_error(self, mock_run, mock_lock):
        mock_run.return_value = MagicMock(
            returncode=EXIT_ERROR, stdout="", stderr="Connection refused"
        )
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = TaskHandle(provider="codex", timestamp=1000.0)
        result = self.backend.poll(handle)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error, "Connection refused")

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_poll_timeout(self, mock_run, mock_lock):
        mock_lock.return_value.__enter__ = MagicMock(
            side_effect=TimeoutError("lock timeout")
        )
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = TaskHandle(provider="codex", timestamp=1000.0)
        result = self.backend.poll(handle)
        self.assertEqual(result.status, "error")
        self.assertIn("Timeout", result.error)

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_poll_command_not_found(self, mock_run, mock_lock):
        mock_run.side_effect = FileNotFoundError("not found")
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = TaskHandle(provider="codex", timestamp=1000.0)
        result = self.backend.poll(handle)
        self.assertEqual(result.status, "error")
        self.assertIn("Command not found", result.error)

    @patch("lib.ccb_cli_backend.ProviderLock")
    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_poll_exit_code_mapping(self, mock_run, mock_lock):
        """Verify correct exit code mapping: 0->completed, 2->pending, 1->error"""
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)
        handle = TaskHandle(provider="codex", timestamp=1000.0)

        # EXIT_OK -> completed
        mock_run.return_value = MagicMock(
            returncode=0, stdout="response", stderr=""
        )
        self.assertEqual(self.backend.poll(handle).status, "completed")

        # EXIT_NO_REPLY -> pending
        mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="")
        self.assertEqual(self.backend.poll(handle).status, "pending")

        # EXIT_ERROR -> error
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="oops"
        )
        self.assertEqual(self.backend.poll(handle).status, "error")

        # Unknown exit code -> error
        mock_run.return_value = MagicMock(returncode=99, stdout="", stderr="")
        self.assertEqual(self.backend.poll(handle).status, "error")

    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_ping_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.backend.ping("codex"))

    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_ping_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(self.backend.ping("codex"))

    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_ping_timeout(self, mock_run):
        mock_run.side_effect = FileNotFoundError("not found")
        self.assertFalse(self.backend.ping("codex"))

    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_list_providers(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"mounted": ["codex", "droid"]}'
        )
        providers = self.backend.list_providers()
        self.assertEqual(providers, ["codex", "droid"])

    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_list_providers_empty(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        providers = self.backend.list_providers()
        self.assertEqual(providers, [])

    @patch("lib.ccb_cli_backend.subprocess.run")
    def test_list_providers_invalid_json(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="not json")
        providers = self.backend.list_providers()
        self.assertEqual(providers, [])

    def test_supported_providers(self):
        self.assertIn("codex", SUPPORTED_PROVIDERS)
        self.assertIn("droid", SUPPORTED_PROVIDERS)
        self.assertIn("gemini", SUPPORTED_PROVIDERS)
        self.assertIn("claude", SUPPORTED_PROVIDERS)
