"""Tests for Windows encoding fallback chain in lib/compat.py (D-09).

Covers UTF-8, GBK, Windows-1252, Shift-JIS encoding fallback behavior,
BOM detection, environment override, and surrogate-free guarantee.
"""

import locale
import os
import sys
from unittest import mock

import pytest

from lib.compat import decode_stdin_bytes


pytestmark = [pytest.mark.windows, pytest.mark.compat]


# ---------------------------------------------------------------------------
# Test 1: Plain UTF-8
# ---------------------------------------------------------------------------
class TestUTF8Strict:
    def test_decode_utf8_strict(self):
        """Plain UTF-8 bytes 'hello world' decoded successfully."""
        result = decode_stdin_bytes("hello world".encode("utf-8"))
        assert result == "hello world"

    def test_decode_utf8_chinese(self):
        """UTF-8 bytes for Chinese characters decoded successfully."""
        data = "中文测试".encode("utf-8")
        result = decode_stdin_bytes(data)
        assert "中文" in result


# ---------------------------------------------------------------------------
# Test 2: BOM detection
# ---------------------------------------------------------------------------
class TestBOMDetection:
    def test_decode_utf8_bom(self):
        """Bytes with UTF-8 BOM prefix decoded successfully."""
        data = b"\xef\xbb\xbf" + "hello".encode("utf-8")
        result = decode_stdin_bytes(data)
        assert result == "hello"

    def test_decode_utf16le_bom(self):
        """Bytes with UTF-16 LE BOM prefix decoded successfully."""
        data = b"\xff\xfe" + "hello".encode("utf-16-le")
        result = decode_stdin_bytes(data)
        assert result == "hello"

    def test_decode_utf16be_bom(self):
        """Bytes with UTF-16 BE BOM prefix decoded successfully."""
        data = b"\xfe\xff" + "hello".encode("utf-16-be")
        result = decode_stdin_bytes(data)
        assert result == "hello"


# ---------------------------------------------------------------------------
# Test 3: Encoding fallback (GBK, Windows-1252, Shift-JIS)
# ---------------------------------------------------------------------------
class TestEncodingFallback:
    def test_decode_gbk_fallback(self):
        """GBK-encoded Chinese text decoded when locale returns 'gbk'."""
        data = "中文测试".encode("gbk")
        with mock.patch("locale.getpreferredencoding", return_value="gbk"):
            with mock.patch("sys.platform", "win32"):
                result = decode_stdin_bytes(data)
        assert "中文" in result

    def test_decode_windows_1252_fallback(self):
        """Windows-1252-encoded em dash decoded when locale returns 'cp1252'."""
        text = "\u2014em dash\u2014"
        data = text.encode("windows-1252")
        with mock.patch("locale.getpreferredencoding", return_value="cp1252"):
            with mock.patch("sys.platform", "win32"):
                result = decode_stdin_bytes(data)
        assert "em dash" in result

    def test_decode_shift_jis_no_crash(self):
        """Shift-JIS bytes do not crash, returns str (may have replacement chars)."""
        data = "テスト".encode("shift_jis")
        with mock.patch("locale.getpreferredencoding", return_value="utf-8"):
            with mock.patch("sys.platform", "win32"):
                result = decode_stdin_bytes(data)
        assert isinstance(result, str)  # key: must not crash

    def test_decode_mbcs_windows_data_loss(self):
        """On win32, mbcs fallback with mismatched encoding returns str (may lose data)."""
        # Encode with shift_jis, but locale/mbcs won't match, so it falls through
        # to utf-8 with replace
        data = "テスト".encode("shift_jis")
        with mock.patch("locale.getpreferredencoding", return_value="utf-8"):
            with mock.patch("sys.platform", "win32"):
                result = decode_stdin_bytes(data)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Test 4: Edge cases
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_decode_empty_bytes(self):
        """Empty bytes return empty string."""
        result = decode_stdin_bytes(b"")
        assert result == ""

    def test_decode_env_override(self):
        """CCB_STDIN_ENCODING='utf-8' forces UTF-8 even when locale is different.

        GBK bytes forced through UTF-8 strict will fail, then use errors='replace'.
        Result must be str (may have replacement chars).
        """
        data = "中文测试".encode("gbk")
        with mock.patch.dict(os.environ, {"CCB_STDIN_ENCODING": "utf-8"}):
            with mock.patch("locale.getpreferredencoding", return_value="gbk"):
                result = decode_stdin_bytes(data)
        assert isinstance(result, str)

    def test_decode_env_override_invalid_encoding(self):
        """CCB_STDIN_ENCODING='nonexistent-encoding' uses errors='replace' fallback."""
        data = "hello".encode("utf-8")
        with mock.patch.dict(os.environ, {"CCB_STDIN_ENCODING": "nonexistent-encoding"}):
            result = decode_stdin_bytes(data)
        assert isinstance(result, str)

    def test_decode_mixed_surrogate_free(self):
        """Result from decode_stdin_bytes never contains lone surrogates (U+D800-U+DFFF)."""
        # Create bytes that would be ambiguous under different encodings
        data = b"\x80\x81\xfe\xff\x00\x01\x02\x03"
        result = decode_stdin_bytes(data)
        assert all(
            ord(c) < 0xD800 or ord(c) > 0xDFFF
            for c in result
        ), f"Result contains lone surrogates: {[hex(ord(c)) for c in result if 0xD800 <= ord(c) <= 0xDFFF]}"
