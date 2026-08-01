from __future__ import annotations
import sys
sys.stdout.buffer.write(
    "CCB_RMUX_TRAILING   \n"
    "\x1b]0;ccb-rmux-title\x07CCB_RMUX_OSC_AFTER\n"
    "CCB_RMUX_WRAP_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"
    "CCB_RMUX_WIDE_宽字符\n"
    "CCB_RMUX_LASTN\n"
    .encode("utf-8")
)