from __future__ import annotations

from typing import Any

from ..common import ConfigValidationError


def expect_mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigValidationError(f'{field_name} must be a table/object')
    return dict(value)


def expect_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ConfigValidationError(f'{field_name} must be a string')
    text = value.strip()
    if not text:
        raise ConfigValidationError(f'{field_name} cannot be empty')
    return text


def expect_bool(value: Any, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigValidationError(f'{field_name} must be a boolean')
    return value


def expect_string_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigValidationError(f'{field_name} must be a list of strings')
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ConfigValidationError(f'{field_name}[{index}] must be a string')
        text = item.strip()
        if not text:
            raise ConfigValidationError(f'{field_name}[{index}] cannot be empty')
        items.append(text)
    return tuple(items)


def expect_string_mapping(value: Any, *, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ConfigValidationError(f'{field_name} must be a table of strings')
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ConfigValidationError(f'{field_name} keys must be strings')
        if not isinstance(item, str):
            raise ConfigValidationError(f'{field_name}.{key} must be a string')
        result[str(key)] = item
    return result


def expect_jsonish_mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    raw = expect_mapping(value, field_name=field_name)
    return {
        str(key): _expect_jsonish(item, field_name=f'{field_name}.{key}')
        for key, item in raw.items()
        if _validate_jsonish_key(key, field_name=field_name)
    }


def _validate_jsonish_key(key: object, *, field_name: str) -> bool:
    if not isinstance(key, str) or not key.strip():
        raise ConfigValidationError(f'{field_name} keys must be non-empty strings')
    return True


def _expect_jsonish(value: Any, *, field_name: str) -> Any:
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    if isinstance(value, list):
        return [_expect_jsonish(item, field_name=f'{field_name}[]') for item in value]
    if isinstance(value, dict):
        return {
            str(key): _expect_jsonish(item, field_name=f'{field_name}.{key}')
            for key, item in value.items()
            if _validate_jsonish_key(key, field_name=field_name)
        }
    raise ConfigValidationError(f'{field_name} must be a TOML scalar, list, or table')


__all__ = [
    'expect_bool',
    'expect_jsonish_mapping',
    'expect_mapping',
    'expect_string',
    'expect_string_list',
    'expect_string_mapping',
]
