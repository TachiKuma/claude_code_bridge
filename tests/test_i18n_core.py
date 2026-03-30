"""Unit tests for I18nCore class."""

import unittest
import os
import json
import tempfile
from pathlib import Path
from unittest import mock

from lib.i18n_core import I18nCore


class TestI18nCore(unittest.TestCase):
    def test_load_builtin_translations(self):
        """Builtin translation files load successfully."""
        i = I18nCore("ccb")
        i.load_translations()
        self.assertGreater(len(i.translations), 50)

    def test_namespace_key_lookup(self):
        """Namespaced keys can be looked up."""
        i = I18nCore("ccb")
        i.load_translations()
        result = i.t("ccb.terminal.no_terminal_backend")
        self.assertNotEqual(result, "ccb.terminal.no_terminal_backend")

    def test_missing_key_returns_key(self):
        """Missing key returns the key name itself."""
        i = I18nCore("ccb")
        i.load_translations()
        result = i.t("ccb.nonexistent.key")
        self.assertEqual(result, "ccb.nonexistent.key")

    def test_format_parameters(self):
        """Parameterized message formatting."""
        i = I18nCore("ccb")
        i.load_translations()
        result = i.t("ccb.startup.started_backend", provider="test", terminal="wezterm", pane_id="5")
        self.assertIn("test", result)

    def test_language_detection_env_var(self):
        """CCB_LANG environment variable controls language."""
        os.environ["CCB_LANG"] = "zh"
        i = I18nCore("ccb")
        i.load_translations()
        self.assertEqual(i.current_lang, "zh")
        del os.environ["CCB_LANG"]

    def test_partial_translation_fallback(self):
        """Missing key in current locale falls back to English."""
        i = I18nCore("ccb")
        i.translations = {"ccb.present": "ZH"}
        i.fallback_translations = {"ccb.partial.only_en": "English only"}
        result = i.t("ccb.partial.only_en")
        self.assertEqual(result, "English only")

    def test_missing_key_in_all_locales_returns_key(self):
        """Missing key in all locales returns the key name itself."""
        i = I18nCore("ccb")
        i.translations = {}
        i.fallback_translations = {}
        result = i.t("ccb.missing.everywhere")
        self.assertEqual(result, "ccb.missing.everywhere")

    def test_external_translation_override(self):
        """External translation file overrides builtin translations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext_dir = Path(tmpdir) / ".ccb" / "i18n" / "ccb"
            ext_dir.mkdir(parents=True)
            (ext_dir / "zh.json").write_text(
                json.dumps({"ccb.startup.started_backend": "CUSTOM OVERRIDE"}),
                encoding="utf-8",
            )
            # Monkey-patch Path.home to use temp dir
            original_home = Path.home
            try:
                import pathlib
                pathlib.Path.home = staticmethod(lambda: Path(tmpdir))
                os.environ["CCB_LANG"] = "zh"
                i = I18nCore("ccb")
                i.load_translations()
                result = i.t("ccb.startup.started_backend")
                self.assertEqual(result, "CUSTOM OVERRIDE")
            finally:
                pathlib.Path.home = original_home
                os.environ.pop("CCB_LANG", None)

    def test_protocol_key_rejected_from_external(self):
        """Protocol string values from external files are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext_dir = Path(tmpdir) / ".ccb" / "i18n" / "ccb"
            ext_dir.mkdir(parents=True)
            (ext_dir / "zh.json").write_text(
                json.dumps(
                    {
                        "ccb.startup.started_backend": "CCB_LANG",
                        "ccb.startup.warmup_failed": "SAFE OVERRIDE",
                    }
                ),
                encoding="utf-8",
            )
            original_home = Path.home
            try:
                import pathlib
                pathlib.Path.home = staticmethod(lambda: Path(tmpdir))
                os.environ["CCB_LANG"] = "zh"
                i = I18nCore("ccb")
                i.load_translations()
                self.assertNotEqual(i.t("ccb.startup.started_backend"), "CCB_LANG")
                self.assertEqual(i.t("ccb.startup.warmup_failed"), "SAFE OVERRIDE")
            finally:
                pathlib.Path.home = original_home
                os.environ.pop("CCB_LANG", None)

    def test_detect_language_uses_getlocale(self):
        """Language detection uses locale.getlocale when env vars are absent."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("locale.getlocale", return_value=("zh_CN", "UTF-8")):
                i = I18nCore("ccb")
                self.assertEqual(i._detect_language(), "zh")

    def test_pseudo_translation_has_markers(self):
        """Pseudo-translation file contains marker characters."""
        os.environ["CCB_LANG"] = "xx"
        i = I18nCore("ccb")
        i.load_translations()
        result = i.t("ccb.terminal.no_terminal_backend")
        # Check for marker characters: « (U+00AB) and » (U+00BB)
        self.assertIn("\u00ab", result)
        self.assertIn("\u00bb", result)
        del os.environ["CCB_LANG"]

    def test_load_json_file_not_found(self):
        """Missing JSON file returns empty dict."""
        i = I18nCore("ccb")
        result = i._load_json_file(Path("/nonexistent/path.json"))
        self.assertEqual(result, {})

    def test_validate_protocol_strings(self):
        """Protocol string validation detects violations."""
        i = I18nCore("ccb")
        i.translations = {"ccb.error.bad": "CCB_LANG", "ccb.error.good": "Normal text"}
        violations = i._validate_no_protocol_strings()
        self.assertEqual(len(violations), 1)
        self.assertIn("CCB_LANG", violations[0])

    def test_backward_compat_via_i18n(self):
        """Old key names work through backward compatibility layer."""
        from lib.i18n import t as old_t
        # Old key should return a non-key string
        result = old_t("no_terminal_backend")
        self.assertNotEqual(result, "no_terminal_backend")
        self.assertNotEqual(result, "ccb.terminal.no_terminal_backend")


if __name__ == "__main__":
    unittest.main()
