"""Mail/TUI i18n coverage tests."""

from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from email.message import Message
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "lib"
for candidate in (ROOT, LIB):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from mail.config import MailConfigV3
from mail.sender import SmtpSender
from mail_tui import wizard


class DummyConnection:
    """Capture outbound SMTP messages without sending them."""

    def __init__(self) -> None:
        self.messages: list[Message] = []

    def send_message(self, message: Message) -> None:
        self.messages.append(message)


class TestMailI18n(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_lang = os.environ.get("CCB_LANG")

    def tearDown(self) -> None:
        if self.previous_lang is None:
            os.environ.pop("CCB_LANG", None)
        else:
            os.environ["CCB_LANG"] = self.previous_lang

    def _make_config(self) -> MailConfigV3:
        config = MailConfigV3()
        config.service_account.email = "sender@example.com"
        config.service_account.smtp.host = "smtp.example.com"
        config.service_account.smtp.port = 587
        return config

    def test_send_test_email_uses_pseudo_locale(self) -> None:
        os.environ["CCB_LANG"] = "xx"
        sender = SmtpSender(self._make_config())

        with mock.patch.object(SmtpSender, "send_reply", return_value=(True, "ok")) as send_reply:
            success, result = sender.send_test_email("target@example.com")

        self.assertTrue(success)
        self.assertEqual(result, "ok")
        kwargs = send_reply.call_args.kwargs
        self.assertEqual(kwargs["to_addr"], "target@example.com")
        self.assertIn("«", kwargs["subject"])
        self.assertIn("«", kwargs["body"])

    def test_connect_failure_uses_pseudo_locale_error(self) -> None:
        os.environ["CCB_LANG"] = "xx"
        sender = SmtpSender(self._make_config())

        with mock.patch("mail.sender.get_password", return_value=None):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                success = sender.connect()

        self.assertFalse(success)
        output = buffer.getvalue()
        self.assertIn("«", output)
        self.assertIn("sender@example.com", output)

    def test_send_output_uses_pseudo_locale_body(self) -> None:
        os.environ["CCB_LANG"] = "xx"
        config = self._make_config()
        config.notification.max_email_length = 12

        sender = SmtpSender(config)
        connection = DummyConnection()
        sender._connection = connection

        success, _ = sender.send_output(
            to_addr="target@example.com",
            provider="claude",
            output="0123456789abcdefghijklmnopqrstuvwxyz",
            work_dir="E:/demo/project",
        )

        self.assertTrue(success)
        self.assertEqual(len(connection.messages), 1)
        message = connection.messages[0]
        payload = message.get_payload()[0].get_payload(decode=True).decode("utf-8")
        self.assertIn("«", message["Subject"])
        self.assertIn("«", payload)

    def test_simple_wizard_prints_chinese_copy(self) -> None:
        os.environ["CCB_LANG"] = "zh"
        config = MailConfigV3()

        mock_poller = mock.Mock()
        mock_poller.test_connection.return_value = (True, "imap ok")
        mock_sender = mock.Mock()
        mock_sender.test_connection.return_value = (True, "smtp ok")

        with (
            mock.patch("mail_tui.wizard.load_config", return_value=config),
            mock.patch("mail_tui.wizard.has_password", return_value=False),
            mock.patch("mail_tui.wizard.store_password"),
            mock.patch("mail_tui.wizard.save_config"),
            mock.patch("mail_tui.wizard.ImapPoller", return_value=mock_poller),
            mock.patch("mail_tui.wizard.SmtpSender", return_value=mock_sender),
            mock.patch("builtins.input", side_effect=["1", "user@gmail.com", "1", "1", "", "", "n"]),
            mock.patch("getpass.getpass", return_value="secret"),
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = wizard.run_simple_wizard()

        self.assertTrue(result)
        output = buffer.getvalue()
        self.assertIn("CCB 邮件配置向导", output)
        self.assertIn("选择你的邮件服务商", output)

    def test_simple_wizard_provider_list_uses_pseudo_locale(self) -> None:
        os.environ["CCB_LANG"] = "xx"
        config = MailConfigV3()

        mock_poller = mock.Mock()
        mock_poller.test_connection.return_value = (True, "imap ok")
        mock_sender = mock.Mock()
        mock_sender.test_connection.return_value = (True, "smtp ok")

        with (
            mock.patch("mail_tui.wizard.load_config", return_value=config),
            mock.patch("mail_tui.wizard.has_password", return_value=False),
            mock.patch("mail_tui.wizard.store_password"),
            mock.patch("mail_tui.wizard.save_config"),
            mock.patch("mail_tui.wizard.ImapPoller", return_value=mock_poller),
            mock.patch("mail_tui.wizard.SmtpSender", return_value=mock_sender),
            mock.patch("builtins.input", side_effect=["1", "user@gmail.com", "1", "1", "", "", "n"]),
            mock.patch("getpass.getpass", return_value="secret"),
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = wizard.run_simple_wizard()

        self.assertTrue(result)
        output = buffer.getvalue()
        self.assertIn("[«Claudexx»]", output)
        self.assertIn("[«Droidxx»]", output)


if __name__ == "__main__":
    unittest.main()
