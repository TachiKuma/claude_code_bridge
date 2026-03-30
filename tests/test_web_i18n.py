"""Web i18n smoke tests."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "lib"
for candidate in (ROOT, LIB):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

try:
    from fastapi.testclient import TestClient
    from mail.config import MailConfigV3
    from web.app import create_app
    from web.auth import require_auth
    FASTAPI_AVAILABLE = True
except ModuleNotFoundError:
    FASTAPI_AVAILABLE = False


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed in this environment")
class TestWebI18n(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_lang = os.environ.get("CCB_LANG")

    def tearDown(self) -> None:
        if self.previous_lang is None:
            os.environ.pop("CCB_LANG", None)
        else:
            os.environ["CCB_LANG"] = self.previous_lang

    def _make_client(self) -> TestClient:
        app = create_app()
        app.dependency_overrides[require_auth] = lambda: {"authenticated": True}
        return TestClient(app)

    def test_dashboard_and_mail_pages_use_pseudo_locale(self) -> None:
        os.environ["CCB_LANG"] = "xx"
        client = self._make_client()

        dashboard = client.get("/")
        mail_page = client.get("/mail")

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(mail_page.status_code, 200)
        self.assertIn("«", dashboard.text)
        self.assertIn("«", mail_page.text)

    def test_unknown_daemon_detail_uses_chinese_translation(self) -> None:
        os.environ["CCB_LANG"] = "zh"
        client = self._make_client()

        response = client.get("/api/daemons/unknown")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "未知守护进程: unknown")

    def test_send_test_email_message_uses_pseudo_locale(self) -> None:
        os.environ["CCB_LANG"] = "xx"
        client = self._make_client()
        config = MailConfigV3()
        config.service_account.email = "sender@example.com"
        config.target_email = "target@example.com"

        with (
            mock.patch("mail.config.load_config", return_value=config),
            mock.patch("mail.sender.SmtpSender.send_test_email", return_value=(True, "id-1")),
        ):
            response = client.post("/api/mail/send-test")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("«", payload["message"])
        self.assertIn("target@example.com", payload["message"])


if __name__ == "__main__":
    unittest.main()
