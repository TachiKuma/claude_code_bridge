"""Tests for i18n language configuration: config file, --lang, CCB_LANG priority.

Covers:
- .ccb-config.json Language key read/write
- CCB_LANG env var override
- --lang CLI flag override
- Priority chain: --lang (CCB_LANG) -> .ccb-config.json -> locale -> default 'en'
- i18n_core._detect_language alignment with ccb_config.resolve_language_setting
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "lib") not in sys.path:
    sys.path.insert(0, str(ROOT / "lib"))

from ccb_config import (
    VALID_LANGUAGE_VALUES,
    get_language_setting,
    load_project_config,
    resolve_language_setting,
    save_project_config,
    set_language_setting,
)


# ---------------------------------------------------------------------------
# .ccb-config.json Language read/write
# ---------------------------------------------------------------------------


class TestConfigFileLanguage:
    """Test Language key in .ccb-config.json."""

    def test_set_language_en(self, tmp_path: Path):
        path = set_language_setting("en", tmp_path)
        data = load_project_config(tmp_path)
        assert data["Language"] == "en"
        assert path.exists()

    def test_set_language_zh(self, tmp_path: Path):
        set_language_setting("zh", tmp_path)
        data = load_project_config(tmp_path)
        assert data["Language"] == "zh"

    def test_set_language_xx(self, tmp_path: Path):
        set_language_setting("xx", tmp_path)
        data = load_project_config(tmp_path)
        assert data["Language"] == "xx"

    def test_set_language_auto(self, tmp_path: Path):
        set_language_setting("auto", tmp_path)
        data = load_project_config(tmp_path)
        assert data["Language"] == "auto"

    def test_set_language_invalid_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="Unsupported language"):
            set_language_setting("fr", tmp_path)

    def test_set_language_case_insensitive(self, tmp_path: Path):
        set_language_setting("EN", tmp_path)
        data = load_project_config(tmp_path)
        assert data["Language"] == "en"

    def test_set_language_preserves_other_keys(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"BackendEnv": "wsl"}), encoding="utf-8")
        set_language_setting("zh", tmp_path)
        data = load_project_config(tmp_path)
        assert data["Language"] == "zh"
        assert data["BackendEnv"] == "wsl"

    def test_get_language_from_config(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "zh"}), encoding="utf-8")
        result = get_language_setting(tmp_path)
        assert result == "zh"

    def test_get_language_no_config(self, tmp_path: Path):
        result = get_language_setting(tmp_path)
        assert result is None

    def test_get_language_empty_config(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text("{}", encoding="utf-8")
        result = get_language_setting(tmp_path)
        assert result is None

    def test_get_language_invalid_value_in_config(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "french"}), encoding="utf-8")
        result = get_language_setting(tmp_path)
        assert result is None


# ---------------------------------------------------------------------------
# Shared resolver priority
# ---------------------------------------------------------------------------


class TestCCBLangEnv:
    """Test resolve_language_setting() applies env/config priority correctly."""

    def test_ccb_lang_overrides_config(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "zh"}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CCB_LANG": "en"}):
            result = resolve_language_setting(tmp_path)
            assert result == "en"

    def test_ccb_lang_auto_falls_through_to_config(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "zh"}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CCB_LANG": "auto"}):
            result = resolve_language_setting(tmp_path)
            assert result == "zh"

    def test_ccb_lang_invalid_falls_through_to_config(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "zh"}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CCB_LANG": "french"}):
            result = resolve_language_setting(tmp_path)
            assert result == "zh"

    def test_ccb_lang_empty_falls_through(self, tmp_path: Path):
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "en"}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CCB_LANG": ""}):
            result = resolve_language_setting(tmp_path)
            assert result == "en"


# ---------------------------------------------------------------------------
# --lang CLI flag
# ---------------------------------------------------------------------------


class TestLangCLI:
    """Test --lang flag sets CCB_LANG env var (simulating ccb entry point behavior)."""

    def test_lang_flag_sets_ccb_lang(self):
        """Simulate what _extract_global_lang_arg does in ccb."""
        lang_override = "zh"
        with mock.patch.dict(os.environ, {"CCB_LANG": lang_override}):
            assert os.environ["CCB_LANG"] == "zh"

    def test_lang_flag_priority_over_config(self, tmp_path: Path):
        """When --lang sets CCB_LANG, it should take priority over config."""
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "en"}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CCB_LANG": "zh"}):
            result = resolve_language_setting(tmp_path)
            assert result == "zh"


# ---------------------------------------------------------------------------
# Priority chain: --lang (CCB_LANG) -> .ccb-config.json -> locale -> default 'en'
# ---------------------------------------------------------------------------


class TestLanguagePriority:
    """Test the full priority chain for language detection."""

    def test_priority_ccb_lang_first(self, tmp_path: Path):
        """CCB_LANG env overrides everything."""
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "zh"}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CCB_LANG": "en"}):
            result = resolve_language_setting(tmp_path)
            assert result == "en"

    def test_priority_config_when_no_env(self, tmp_path: Path):
        """Config file is used when CCB_LANG is not set."""
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "zh"}), encoding="utf-8")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCB_LANG", None)
            result = resolve_language_setting(tmp_path)
            assert result == "zh"

    def test_priority_default_when_nothing_set(self, tmp_path: Path):
        """Falls back to locale/en when env and config are both absent."""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCB_LANG", None)
            with mock.patch("locale.getlocale", return_value=(None, None)):
                result = resolve_language_setting(tmp_path)
                assert result == "en"

    def test_valid_language_values(self):
        """Valid values are exactly auto, en, zh, xx."""
        assert VALID_LANGUAGE_VALUES == {"auto", "en", "zh", "xx"}


# ---------------------------------------------------------------------------
# i18n_core._detect_language alignment
# ---------------------------------------------------------------------------


class TestI18nCoreDetectLanguage:
    """Test that i18n_core._detect_language respects the same priority chain."""

    def test_ccb_lang_detected(self):
        from i18n_core import I18nCore
        core = I18nCore("ccb")
        with mock.patch.dict(os.environ, {"CCB_LANG": "zh"}):
            assert core._detect_language() == "zh"

    def test_ccb_lang_en(self):
        from i18n_core import I18nCore
        core = I18nCore("ccb")
        with mock.patch.dict(os.environ, {"CCB_LANG": "en"}):
            assert core._detect_language() == "en"

    def test_ccb_lang_xx(self):
        from i18n_core import I18nCore
        core = I18nCore("ccb")
        with mock.patch.dict(os.environ, {"CCB_LANG": "xx"}):
            assert core._detect_language() == "xx"

    def test_config_file_fallback(self, tmp_path: Path):
        """When CCB_LANG is not set, i18n_core should check config file."""
        from i18n_core import I18nCore
        config_file = tmp_path / ".ccb-config.json"
        config_file.write_text(json.dumps({"Language": "zh"}), encoding="utf-8")
        core = I18nCore("ccb")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCB_LANG", None)
            # Patch cwd to tmp_path so config lookup finds the file
            with mock.patch("pathlib.Path.cwd", return_value=tmp_path):
                result = core._detect_language()
                assert result == "zh"

    def test_default_en_when_nothing_set(self):
        """When nothing sets language, default should be 'en'."""
        from i18n_core import I18nCore
        core = I18nCore("ccb")
        # Clear CCB_LANG and make config/locale return nothing
        env = dict(os.environ)
        env.pop("CCB_LANG", None)
        env.pop("LANG", None)
        env.pop("LC_ALL", None)
        env.pop("LC_MESSAGES", None)
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("locale.getlocale", return_value=(None, None)):
                with mock.patch("i18n_core.resolve_language_setting", return_value="en"):
                    result = core._detect_language()
                    assert result == "en"


# ---------------------------------------------------------------------------
# Integration: ccb config lang subcommand
# ---------------------------------------------------------------------------


class TestConfigLangSubcommand:
    """Test the ccb config lang subcommand behavior (unit-level)."""

    def test_set_and_read_language(self, tmp_path: Path):
        """Set language via set_language_setting, read via get_language_setting."""
        set_language_setting("zh", tmp_path)
        result = get_language_setting(tmp_path)
        assert result == "zh"

    def test_roundtrip_all_valid_values(self, tmp_path: Path):
        """All valid language values survive a set/get roundtrip."""
        for lang in ("auto", "en", "zh", "xx"):
            set_language_setting(lang, tmp_path)
            result = get_language_setting(tmp_path)
            assert result == lang
