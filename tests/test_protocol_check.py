"""Unit tests for protocol string check script and i18n_core runtime validation."""

import unittest
import json
import tempfile
import os
from pathlib import Path

from scripts.check_protocol_strings import (
    load_whitelist,
    check_translation_file,
    scan_translation_values,
)


class TestLoadWhitelist(unittest.TestCase):
    def test_load_real_whitelist(self):
        """Load actual whitelist file."""
        whitelist_path = Path(".planning/protocol_whitelist.json")
        whitelist = load_whitelist(whitelist_path)
        self.assertGreater(len(whitelist), 100)
        self.assertIn("CCB_LANG", whitelist)
        self.assertIn("ask", whitelist)
        self.assertIn("CCB_DONE", whitelist)


class TestCheckTranslationFile(unittest.TestCase):
    def test_clean_translation_passes(self):
        """Clean translation file passes check."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"ccb.error.normal": "This is a normal message"}, f)
            f.flush()
            errors = check_translation_file(Path(f.name), {"CCB_LANG", "ask"})
        os.unlink(f.name)
        self.assertEqual(len(errors), 0)

    def test_protocol_value_detected(self):
        """Protocol string value is detected."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"ccb.error.bad": "CCB_LANG", "ccb.error.good": "Normal message"}, f)
            f.flush()
            errors = check_translation_file(Path(f.name), {"CCB_LANG", "ask"})
        os.unlink(f.name)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["key"], "ccb.error.bad")
        self.assertEqual(errors[0]["value"], "CCB_LANG")

    def test_bad_fixture_detected(self):
        """Bad translation fixture is correctly detected."""
        whitelist = load_whitelist(Path(".planning/protocol_whitelist.json"))
        errors = check_translation_file(
            Path("tests/fixtures/bad_translations/zh_bad.json"),
            whitelist,
        )
        # Should detect 3 violations (CCB_LANG, ask, CCB_DONE)
        self.assertGreaterEqual(len(errors), 3)

    def test_parse_error_handled(self):
        """JSON parse error returns error entry."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("{invalid json")
            f.flush()
            errors = check_translation_file(Path(f.name), {"CCB_LANG"})
        os.unlink(f.name)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["type"], "parse_error")


class TestScanTranslationValues(unittest.TestCase):
    def test_scan_with_bad_fixture(self):
        """Scanning directory includes bad fixture."""
        whitelist = load_whitelist(Path(".planning/protocol_whitelist.json"))
        errors = scan_translation_values(
            Path("tests/fixtures/bad_translations"),
            whitelist,
        )
        self.assertGreater(len(errors), 0)

    def test_scan_clean_directory(self):
        """Scanning clean directory reports no errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            good_file = Path(tmpdir) / "en.json"
            good_file.write_text(
                json.dumps({"ccb.error.normal": "Normal message"}),
                encoding="utf-8",
            )
            errors = scan_translation_values(Path(tmpdir), {"CCB_LANG"})
            self.assertEqual(len(errors), 0)


class TestI18nCoreRuntimeValidation(unittest.TestCase):
    def test_validate_method_exists(self):
        """I18nCore has _validate_no_protocol_strings method."""
        from lib.i18n_core import I18nCore
        i = I18nCore("ccb")
        self.assertTrue(hasattr(i, "_validate_no_protocol_strings"))

    def test_validate_detects_violations(self):
        """Runtime validation detects protocol strings."""
        from lib.i18n_core import I18nCore
        i = I18nCore("ccb")
        i.translations = {"ccb.bad": "CCB_LANG", "ccb.good": "OK"}
        violations = i._validate_no_protocol_strings()
        self.assertEqual(len(violations), 1)

    def test_validate_clean_translations(self):
        """Runtime validation passes for clean translations."""
        from lib.i18n_core import I18nCore
        i = I18nCore("ccb")
        i.load_translations()
        violations = i._validate_no_protocol_strings()
        self.assertEqual(len(violations), 0)


class TestCheckScriptIntegration(unittest.TestCase):
    def test_script_runs_on_clean_translations(self):
        """Script passes on actual translation directory."""
        import subprocess
        result = subprocess.run(
            ["python", "scripts/check_protocol_strings.py", "--translations", "lib/i18n"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS", result.stdout)

    def test_script_fails_on_bad_translations(self):
        """Script fails on bad translation fixtures."""
        import subprocess
        result = subprocess.run(
            ["python", "scripts/check_protocol_strings.py",
             "--translations", "tests/fixtures/bad_translations"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
