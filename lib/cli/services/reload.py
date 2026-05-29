from __future__ import annotations

from cli.context import CliContext
from cli.models import ParsedReloadCommand

from .daemon import connect_current_mounted_daemon


def reload_config_dry_run(context: CliContext, command: ParsedReloadCommand) -> dict:
    if not command.dry_run:
        raise ValueError('reload currently requires --dry-run')
    handle = connect_current_mounted_daemon(context)
    assert handle.client is not None
    return handle.client.project_reload_config(dry_run=True)


__all__ = ['reload_config_dry_run']
