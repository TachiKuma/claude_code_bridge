"""Runtime helpers for namespace-based translations."""

from __future__ import annotations

from typing import Callable

try:
    from lib.i18n_core import I18nCore
except ModuleNotFoundError:
    from i18n_core import I18nCore


_CACHE: dict[tuple[str, str], I18nCore] = {}


def get_i18n(namespace: str = "ccb") -> I18nCore:
    """Return a cached I18nCore for the active language."""
    probe = I18nCore(namespace)
    lang = probe._detect_language()
    cache_key = (namespace, lang)

    if cache_key not in _CACHE:
        probe.load_translations()
        _CACHE[cache_key] = probe

    return _CACHE[cache_key]


def get_translator(namespace: str = "ccb") -> tuple[Callable[..., str], str]:
    """Return a translation callable and resolved language."""
    core = get_i18n(namespace)
    return core.t, core.current_lang or "en"


def t(key: str, namespace: str = "ccb", **kwargs) -> str:
    """Translate a key from the active namespace."""
    return get_i18n(namespace).t(key, **kwargs)
