from __future__ import annotations

import socket

UNSUPPORTED_ACCELERATOR_TRANSPORT_REASON = "unsupported_platform:windows_no_af_unix"


def accelerator_transport_available() -> bool:
    return hasattr(socket, "AF_UNIX")


def accelerator_unsupported_reason() -> str:
    return "" if accelerator_transport_available() else UNSUPPORTED_ACCELERATOR_TRANSPORT_REASON


__all__ = [
    "UNSUPPORTED_ACCELERATOR_TRANSPORT_REASON",
    "accelerator_transport_available",
    "accelerator_unsupported_reason",
]
