from __future__ import annotations

from typing import Any

from agents.models import RuntimeMuxConfig

from ..common import ConfigValidationError, StructuredConfigValidationError
from .expectations import expect_mapping

_RUNTIME_TOP_LEVEL_KEYS = {'mux'}
_RUNTIME_MUX_KEYS = {'backend'}
_MUX_BACKENDS = {'tmux', 'rmux', 'auto'}


def parse_runtime_mux(value: object) -> RuntimeMuxConfig:
    if value is None:
        return RuntimeMuxConfig()
    runtime = expect_mapping(value, field_name='runtime')
    unknown_runtime = sorted(set(runtime) - _RUNTIME_TOP_LEVEL_KEYS)
    if unknown_runtime:
        raise ConfigValidationError(
            f'runtime contains unknown fields: {", ".join(unknown_runtime)}'
        )
    mux = expect_mapping(runtime.get('mux', {}), field_name='runtime.mux')
    unknown_mux = sorted(set(mux) - _RUNTIME_MUX_KEYS)
    if unknown_mux:
        raise ConfigValidationError(
            f'runtime.mux contains unknown fields: {", ".join(unknown_mux)}'
        )
    if 'backend' not in mux:
        return RuntimeMuxConfig()
    return RuntimeMuxConfig(backend=_parse_backend(mux['backend']), explicit_backend=True)


def parse_v3_runtime_mux(value: object) -> RuntimeMuxConfig:
    try:
        return parse_runtime_mux(value)
    except ConfigValidationError as exc:
        message = str(exc)
        path = 'runtime'
        if message.startswith('runtime.mux.backend'):
            path = 'runtime.mux.backend'
        elif message.startswith('runtime.mux'):
            path = 'runtime.mux'
        raise StructuredConfigValidationError(
            code='v3_runtime_invalid',
            path=path,
            message=message,
        ) from exc


def _parse_backend(value: Any) -> str:
    if not isinstance(value, str):
        raise ConfigValidationError('runtime.mux.backend must be tmux, rmux, or auto')
    backend = value.strip().lower()
    if backend not in _MUX_BACKENDS:
        raise ConfigValidationError('runtime.mux.backend must be tmux, rmux, or auto')
    return backend


__all__ = ['parse_runtime_mux', 'parse_v3_runtime_mux']
