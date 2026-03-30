#!/usr/bin/env python3
"""i18n_core Demo - Demonstrate namespace translation, fallback, and external override."""

import os
import sys

sys.path.insert(0, ".")
from lib.i18n_core import I18nCore

print("=== i18n_core Demo ===")
print()

# 1. English
print("--- English (CCB_LANG=en) ---")
os.environ["CCB_LANG"] = "en"
i = I18nCore("ccb")
i.load_translations()
print(f"Language: {i.current_lang}")
print(f"  {i.t('ccb.terminal.no_terminal_backend')}")
print(f"  {i.t('ccb.startup.started_backend', provider='Claude', terminal='tmux', pane_id='3')}")
print()

# 2. Chinese
print("--- Chinese (CCB_LANG=zh) ---")
os.environ["CCB_LANG"] = "zh"
i2 = I18nCore("ccb")
i2.load_translations()
print(f"Language: {i2.current_lang}")
print(f"  {i2.t('ccb.terminal.no_terminal_backend')}")
print()

# 3. Pseudo-translation
print("--- Pseudo (CCB_LANG=xx) ---")
os.environ["CCB_LANG"] = "xx"
i3 = I18nCore("ccb")
i3.load_translations()
print(f"Language: {i3.current_lang}")
val = i3.t("ccb.terminal.no_terminal_backend")
print(f"  {val}")
print(f"  (Has markers: {chr(0xab) in val and chr(0xbb) in val})")
print()

# 4. Fallback
print("--- Fallback (missing key) ---")
os.environ["CCB_LANG"] = "en"
i4 = I18nCore("ccb")
i4.load_translations()
print(f"  Missing key: {i4.t('ccb.nonexistent.key')}")
print()

# 5. Backward compat
print("--- Backward compat (old key name) ---")
from lib.i18n import t as old_t
print(f"  t('no_terminal_backend') = {old_t('no_terminal_backend')}")
print(f"  t('sending_to', provider='Gemini') = {old_t('sending_to', provider='Gemini')}")
print()

print("=== Demo complete ===")
