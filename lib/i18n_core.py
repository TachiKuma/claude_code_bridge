"""
i18n_core - Namespace-based internationalization core module.

Provides I18nCore class with namespace isolation, fallback chain,
external translation override, and protocol string validation.

Design: .planning/phases/02-架构设计/designs/i18n_core_design.md
Structure: .planning/phases/02-架构设计/designs/translation_structure.md
"""

import json
import locale
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set


class I18nCore:
    """Namespace-based i18n core with fallback and external override support."""

    def __init__(self, namespace: str = "ccb") -> None:
        self.namespace = namespace
        self.translations: Dict[str, str] = {}
        self.fallback_translations: Dict[str, str] = {}
        self.current_lang: Optional[str] = None
        self.logger = logging.getLogger(f"i18n.{namespace}")

    def load_translations(self) -> None:
        """Load translations: builtin -> external override -> protocol validation."""
        lang = self._detect_language()
        self.current_lang = lang
        self.translations = {}
        self.fallback_translations = {}
        self.logger.info("Detected language: %s", lang)

        self.translations = self._load_language_translations(lang)
        if lang != "en":
            self.fallback_translations = self._load_language_translations("en")
        else:
            self.fallback_translations = self.translations

        # Runtime protocol string validation
        violations = self._validate_no_protocol_strings()
        if violations:
            self.logger.warning(
                "Protocol string violations detected: %d. "
                "Review translations and .planning/protocol_whitelist.json",
                len(violations),
            )

    def _load_language_translations(self, lang: str) -> Dict[str, str]:
        """Load builtin translations and merge allowed external overrides for one language."""
        translations: Dict[str, str] = {}

        builtin_path = Path(__file__).parent / "i18n" / self.namespace / f"{lang}.json"
        if builtin_path.exists():
            translations = self._load_json_file(builtin_path)
            if translations:
                self.logger.info("Loaded builtin translations: %s", builtin_path)
        else:
            self.logger.warning("Builtin translation file not found: %s", builtin_path)

        external_path = Path.home() / ".ccb" / "i18n" / self.namespace / f"{lang}.json"
        if external_path.exists():
            external = self._load_json_file(external_path)
            if external:
                translations = self._merge_external_translations(translations, external)
                self.logger.info("Loaded external translations: %s", external_path)
        else:
            self.logger.debug("No external translations at %s", external_path)

        return translations

    def _merge_external_translations(
        self, builtin: Dict[str, str], external: Dict[str, str]
    ) -> Dict[str, str]:
        """Merge external translations while rejecting protocol string values."""
        merged = dict(builtin)
        whitelist = self._load_whitelist()

        for key, value in external.items():
            if isinstance(value, str) and value in whitelist:
                self.logger.error(
                    "BLOCKED: Protocol key '%s' in external translation value '%s'",
                    key,
                    value,
                )
                continue
            merged[key] = value

        return merged

    def _detect_language(self) -> str:
        """Detect language: --lang (CCB_LANG) -> .ccb-config.json -> system locale -> default 'en'.

        Priority chain matches lib/i18n.py detect_language() and ccb entry point:
            --lang / CCB_LANG env -> .ccb-config.json Language -> locale -> 'en'
        """
        # 1. CCB_LANG env var (set by --lang CLI flag or user environment)
        ccb_lang = os.environ.get("CCB_LANG", "").strip().lower()
        if ccb_lang in ("zh", "cn", "chinese"):
            return "zh"
        if ccb_lang in ("en", "english"):
            return "en"
        if ccb_lang == "xx":
            return "xx"

        # 2. .ccb-config.json Language key (via ccb_config.get_language_setting)
        try:
            from ccb_config import get_language_setting
            config_lang = get_language_setting()
            if config_lang:
                if config_lang in ("zh", "cn", "chinese"):
                    return "zh"
                if config_lang in ("en", "english"):
                    return "en"
                if config_lang == "xx":
                    return "xx"
        except Exception:
            pass

        # 3. Auto-detect from system locale
        try:
            lang = (
                os.environ.get("LANG", "")
                or os.environ.get("LC_ALL", "")
                or os.environ.get("LC_MESSAGES", "")
            )
            if not lang:
                lang, _ = locale.getlocale()
                lang = lang or ""

            lang = lang.lower()
            if lang.startswith("zh") or "chinese" in lang:
                return "zh"
        except Exception:
            pass

        return "en"

    def t(self, key: str, **kwargs) -> str:
        """Translate key with optional format parameters.

        Fallback chain: current language -> English -> key name itself.
        """
        msg = self.translations.get(key)
        if msg is None:
            msg = self.fallback_translations.get(key)
        if msg is None:
            self.logger.warning("Translation key not found: %s", key)
            return key

        if kwargs:
            try:
                msg = msg.format(**kwargs)
            except (KeyError, ValueError) as e:
                self.logger.error("Failed to format translation '%s': %s", key, e)

        return msg

    def _load_json_file(self, path: Path) -> Dict[str, str]:
        """Load a JSON translation file. Returns empty dict on failure."""
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            self.logger.error("Failed to load translation file %s: %s", path, e)
            return {}

    def _validate_no_protocol_strings(self) -> List[str]:
        """Validate translation values don't contain protocol strings (runtime protection layer 2).

        Returns list of violation descriptions.
        """
        violations: List[str] = []
        whitelist = self._load_whitelist()
        if not whitelist:
            return violations

        for key, value in self.translations.items():
            if isinstance(value, str) and value in whitelist:
                violations.append(
                    f"Key '{key}' has protocol string value: '{value}'"
                )
                self.logger.warning(
                    "Protocol string violation: key='%s', value='%s'", key, value
                )

        return violations

    def _load_whitelist(self) -> Set[str]:
        """Load protocol whitelist from project root."""
        whitelist_path = Path(__file__).parent.parent / ".planning" / "protocol_whitelist.json"
        if not whitelist_path.exists():
            self.logger.debug("Protocol whitelist not found at %s", whitelist_path)
            return set()
        try:
            with open(whitelist_path, encoding="utf-8") as f:
                data = json.load(f)
            strings: Set[str] = set()
            for category, items in data.get("categories", {}).items():
                strings.update(items)
            return strings
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning("Failed to load protocol whitelist: %s", e)
            return set()
