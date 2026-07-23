from __future__ import annotations

from typing import Any

from agents.models import RuntimeMuxConfig, RuntimeStartConfig

from ..common import ConfigValidationError, StructuredConfigValidationError
from .expectations import expect_bool, expect_mapping

_RUNTIME_TOP_LEVEL_KEYS = {'mux', 'start'}
_RUNTIME_MUX_KEYS = {'backend'}
_RUNTIME_START_KEYS = {'no_attach'}
_MUX_BACKENDS = {'tmux', 'rmux', 'auto'}


def parse_runtime_mux(value: object) -> RuntimeMuxConfig:
    runtime = _parse_runtime_mapping(value)
    mux = expect_mapping(runtime.get('mux', {}), field_name='runtime.mux')
    unknown_mux = sorted(set(mux) - _RUNTIME_MUX_KEYS)
    if unknown_mux:
        raise ConfigValidationError(
            f'runtime.mux contains unknown fields: {", ".join(unknown_mux)}'
        )
    if 'backend' not in mux:
        return RuntimeMuxConfig()
    return RuntimeMuxConfig(backend=_parse_backend(mux['backend']), explicit_backend=True)


def parse_runtime_start(value: object) -> RuntimeStartConfig:
    runtime = _parse_runtime_mapping(value)
    start = expect_mapping(runtime.get('start', {}), field_name='runtime.start')
    unknown_start = sorted(set(start) - _RUNTIME_START_KEYS)
    if unknown_start:
        raise ConfigValidationError(
            f'runtime.start contains unknown fields: {", ".join(unknown_start)}'
        )
    if 'no_attach' not in start:
        return RuntimeStartConfig()
    return RuntimeStartConfig(
        no_attach=expect_bool(start['no_attach'], field_name='runtime.start.no_attach'),
        explicit_no_attach=True,
    )


def _parse_runtime_mapping(value: object) -> dict:
    if value is None:
        return {}
    runtime = expect_mapping(value, field_name='runtime')
    unknown_runtime = sorted(set(runtime) - _RUNTIME_TOP_LEVEL_KEYS)
    if unknown_runtime:
        raise ConfigValidationError(
            f'runtime contains unknown fields: {", ".join(unknown_runtime)}'
        )
    return dict(runtime)


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


def parse_v3_runtime_start(value: object) -> RuntimeStartConfig:
    try:
        return parse_runtime_start(value)
    except ConfigValidationError as exc:
        message = str(exc)
        path = 'runtime'
        if message.startswith('runtime.start.no_attach'):
            path = 'runtime.start.no_attach'
        elif message.startswith('runtime.start'):
            path = 'runtime.start'
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


__all__ = [
    'parse_runtime_mux',
    'parse_runtime_start',
    'parse_v3_runtime_mux',
    'parse_v3_runtime_start',
]
