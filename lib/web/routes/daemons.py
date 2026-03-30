"""
Daemon management API routes.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from i18n_runtime import t
from web.auth import require_auth

router = APIRouter()


class DaemonStatus(BaseModel):
    """Daemon status response."""
    name: str
    running: bool
    pid: Optional[int] = None
    uptime: Optional[float] = None


class DaemonAction(BaseModel):
    """Daemon action response."""
    success: bool
    message: str


def _detail(key: str, **kwargs) -> HTTPException:
    """Build a translated HTTP exception detail."""
    return HTTPException(status_code=404, detail=t(key, **kwargs))


def get_askd_status() -> DaemonStatus:
    """Get askd daemon status."""
    try:
        from askd_rpc import read_state
        state = read_state()
        if state:
            # Check if process is alive
            try:
                os.kill(state.get("pid", 0), 0)
                return DaemonStatus(
                    name="askd",
                    running=True,
                    pid=state.get("pid"),
                )
            except (OSError, ProcessLookupError):
                pass
    except Exception:
        pass
    return DaemonStatus(name="askd", running=False)


def get_maild_status() -> DaemonStatus:
    """Get maild daemon status."""
    try:
        from mail.daemon import get_daemon_status
        status = get_daemon_status()
        if status.get("running"):
            return DaemonStatus(
                name="maild",
                running=True,
                pid=status.get("pid"),
                uptime=status.get("uptime"),
            )
    except Exception:
        pass
    return DaemonStatus(name="maild", running=False)


@router.get("")
async def list_daemons(user: dict = Depends(require_auth)) -> list[DaemonStatus]:
    """List all daemon statuses."""
    return [
        get_askd_status(),
        get_maild_status(),
    ]


@router.get("/{name}")
async def get_daemon(name: str, user: dict = Depends(require_auth)) -> DaemonStatus:
    """Get specific daemon status."""
    if name == "askd":
        return get_askd_status()
    if name == "maild":
        return get_maild_status()
    raise _detail("ccb.web.daemons.error_unknown_daemon", name=name)


@router.post("/{name}/start")
async def start_daemon_route(name: str, user: dict = Depends(require_auth)) -> DaemonAction:
    """Start a daemon."""
    if name == "askd":
        try:
            from askd_client import maybe_start_daemon
            maybe_start_daemon()
            return DaemonAction(success=True, message=t("ccb.web.daemons.askd_started"))
        except Exception as e:
            return DaemonAction(success=False, message=str(e))

    if name == "maild":
        try:
            from mail.daemon import start_daemon, is_daemon_running
            if is_daemon_running():
                return DaemonAction(success=True, message=t("ccb.web.daemons.maild_already_running"))
            start_daemon(foreground=False)
            return DaemonAction(success=True, message=t("ccb.web.daemons.maild_started"))
        except Exception as e:
            return DaemonAction(success=False, message=str(e))

    raise _detail("ccb.web.daemons.error_unknown_daemon", name=name)


@router.post("/{name}/stop")
async def stop_daemon_route(name: str, user: dict = Depends(require_auth)) -> DaemonAction:
    """Stop a daemon."""
    if name == "askd":
        try:
            from askd_rpc import shutdown_daemon
            shutdown_daemon()
            return DaemonAction(success=True, message=t("ccb.web.daemons.askd_stopped"))
        except Exception as e:
            return DaemonAction(success=False, message=str(e))

    if name == "maild":
        try:
            from mail.daemon import stop_daemon
            if stop_daemon():
                return DaemonAction(success=True, message=t("ccb.web.daemons.maild_stopped"))
            return DaemonAction(success=False, message=t("ccb.web.daemons.maild_not_running"))
        except Exception as e:
            return DaemonAction(success=False, message=str(e))

    raise _detail("ccb.web.daemons.error_unknown_daemon", name=name)
