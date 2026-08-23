from __future__ import annotations

from dataclasses import dataclass

from .contracts import HerdrRuntimeManifest


@dataclass(frozen=True)
class HerdrRuntimeEnsureResult:
    ok: bool
    manifest: HerdrRuntimeManifest
    socket_ref: str | None = None
    session_name: str | None = None
    reason: str | None = None
    warnings: tuple[str, ...] = ()

    def to_record(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "project_id": self.manifest.project_id,
            "session_name": self.session_name or self.manifest.session_name,
            "generation": self.manifest.generation,
            "socket_ref": self.socket_ref,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


def ensure_runtime(
    manifest: HerdrRuntimeManifest,
    restore_token: str | None = None,
    *,
    herdr_exe: str | None = None,
    herdr_session: str | None = None,
    bootstrap_fn=None,
) -> HerdrRuntimeEnsureResult:
    if bootstrap_fn is None:
        from platforms.windows.herdr.bootstrap import ensure_herdr_bootstrap_env

        bootstrap_fn = ensure_herdr_bootstrap_env
    session_name = str(herdr_session or manifest.session_name).strip() or manifest.session_name
    result = bootstrap_fn(
        herdr_exe=herdr_exe,
        herdr_session=herdr_session,
        auto_start_server=True,
        start_session=session_name,
    )
    if result.get("ok") is not True:
        return HerdrRuntimeEnsureResult(
            ok=False,
            manifest=manifest,
            session_name=session_name,
            reason=str(result.get("reason") or "herdr runtime ensure failed"),
            warnings=_warnings(result),
        )
    return HerdrRuntimeEnsureResult(
        ok=True,
        manifest=manifest,
        socket_ref=str(result.get("socket_ref") or "").strip() or None,
        session_name=str(result.get("herdr_session") or session_name).strip() or session_name,
        warnings=_warnings(result),
    )


def _warnings(result: object) -> tuple[str, ...]:
    if not isinstance(result, dict):
        return ()
    warnings = result.get("warnings")
    if not isinstance(warnings, list):
        return ()
    return tuple(str(item) for item in warnings if str(item).strip())


__all__ = ["HerdrRuntimeEnsureResult", "ensure_runtime"]
