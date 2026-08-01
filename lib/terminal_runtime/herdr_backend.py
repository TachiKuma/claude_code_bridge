from __future__ import annotations

from typing import Literal

from terminal_runtime.backend_types import TerminalBackend
from terminal_runtime.herdr_backend_runtime.capabilities import HerdrCapabilityGate
from terminal_runtime.herdr_backend_runtime.client import HerdrSocketClient
from terminal_runtime.mux_backend_contract import (
    MuxCapabilitiesV2,
    MuxCommandErrorV2,
    MuxNamespaceRefV2,
    MuxOperationEvidenceV2,
    MuxPaneRefV2,
    make_namespace_ref,
    make_pane_ref,
)


class HerdrBackend(TerminalBackend):
    def __init__(
        self,
        *,
        client: HerdrSocketClient,
        capability_gate: HerdrCapabilityGate,
    ) -> None:
        self._client = client
        self._capability_gate = capability_gate
        self._panes: dict[str, MuxPaneRefV2] = {}
        self._pane_namespaces: dict[str, MuxNamespaceRefV2] = {}
        self._legacy_namespaces: dict[str, MuxNamespaceRefV2] = {}
        self._known_namespaces: dict[tuple[str, str], MuxNamespaceRefV2] = {}

    def capabilities(self) -> MuxCapabilitiesV2:
        return self._capability_gate.require_supported("capabilities")

    def prepare_server(self) -> None:
        self._capability_gate.require_supported("prepare_server")
        self._client.server_info()

    def ensure_server_policy(self) -> None:
        self.prepare_server()

    def create_session(
        self,
        *,
        project_id: str,
        cwd: str,
        title: str,
    ) -> MuxNamespaceRefV2:
        self._capability_gate.require_supported("create_session")
        self._client.server_info()
        return self._register_namespace(
            self._client.create_session(project_id=project_id, cwd=cwd, title=title)
        )

    def restore_session(self, *, restore_token: str) -> MuxNamespaceRefV2:
        self._capability_gate.require_supported("restore_session")
        self._client.server_info()
        return self._register_namespace(self._client.restore_session(restore_token=restore_token))

    def namespace_ref(self, session_name: str, namespace_id: str) -> MuxNamespaceRefV2:
        return self._register_namespace(
            make_namespace_ref(
                backend_impl="herdr",
                namespace_id=namespace_id,
                session_name=session_name,
                ipc_kind="herdr_socket",
                ipc_ref=self._client.socket_ref,
            )
        )

    def create_pane(
        self,
        namespace_or_cmd,
        cwd: str | None = None,
        direction: str = "right",
        percent: int = 50,
        parent_pane: str | None = None,
        *,
        command: list[str] | None = None,
        env: dict[str, str] | None = None,
        title: str = "",
    ):
        if isinstance(namespace_or_cmd, dict):
            namespace = self._namespace_ref_from_mapping(namespace_or_cmd, operation="create_pane")
            return self._create_v2_pane(
                namespace,
                command=list(command or []),
                cwd=cwd or "",
                env=env or {},
                title=title,
                direction=direction,
                percent=percent,
                parent_pane=str(parent_pane) if parent_pane is not None else None,
            )
        if parent_pane is not None:
            parent_key = str(parent_pane)
            try:
                namespace = self._pane_namespaces[parent_key]
            except KeyError as exc:
                raise MuxCommandErrorV2(
                    category="not-found",
                    backend_impl="herdr",
                    operation="create_pane",
                    detail=f"unknown Herdr pane {parent_key!r}",
                    evidence={"pane_id": parent_key},
                ) from exc
        else:
            namespace = self._ensure_legacy_namespace(cwd or "")
        legacy_command = (
            list(command)
            if command is not None
            else ([str(namespace_or_cmd)] if str(namespace_or_cmd).strip() else [])
        )
        pane = self._create_v2_pane(
            namespace,
            command=legacy_command,
            cwd=cwd or "",
            env=env or {},
            title=title or "legacy",
            direction=direction,
            percent=percent,
            parent_pane=str(parent_pane) if parent_pane is not None else None,
        )
        return pane["pane_id"]

    def split_pane(
        self,
        pane: MuxPaneRefV2,
        *,
        direction: Literal["left", "right", "up", "down"] = "right",
        percent: int = 50,
        command: list[str] | None = None,
        cwd: str = "",
        env: dict[str, str] | None = None,
        title: str = "",
    ) -> MuxPaneRefV2:
        pane_ref = self._pane_ref(pane, operation="split_pane")
        pane_id = pane_ref["pane_id"]
        namespace = self._pane_namespaces.get(pane_id) or self._known_namespace_for_session(
            pane_ref["session_name"],
            operation="split_pane",
            pane_id=pane_id,
        )
        if namespace is None:
            raise MuxCommandErrorV2(
                category="not-found",
                backend_impl="herdr",
                operation="split_pane",
                detail=f"unknown Herdr pane {pane_id!r}",
                evidence={"pane_id": pane_id},
            )
        return self._create_v2_pane(
            namespace,
            command=command or [],
            cwd=cwd,
            env=env or {},
            title=title,
            direction=direction,
            percent=percent,
            parent_pane=pane_id,
        )

    def _create_v2_pane(
        self,
        namespace: MuxNamespaceRefV2,
        *,
        command: list[str],
        cwd: str,
        env: dict[str, str],
        title: str,
        direction: str = "right",
        percent: int = 50,
        parent_pane: str | None = None,
    ) -> MuxPaneRefV2:
        namespace = self._register_namespace(namespace)
        self._capability_gate.require_supported("create_pane")
        self._client.server_info()
        pane = self._client.create_pane(
            namespace,
            command=command,
            cwd=cwd,
            env=env,
            title=title,
            direction=direction,
            percent=percent,
            parent_pane=parent_pane,
        )
        self._panes[pane["pane_id"]] = pane
        self._pane_namespaces[pane["pane_id"]] = namespace
        return pane

    def send_text(self, pane_id, text: str) -> MuxOperationEvidenceV2 | None:
        pane = self._pane_ref(pane_id, operation="send_text")
        self._capability_gate.require_supported("send_text")
        self._client.server_info()
        evidence = self._client.send_text(pane, text)
        return evidence if isinstance(pane_id, dict) else None

    def capture_pane(
        self,
        pane: MuxPaneRefV2,
        *,
        lines: int,
        ) -> tuple[str, MuxOperationEvidenceV2]:
        pane = self._pane_ref(pane, operation="capture_pane")
        self._capability_gate.require_supported("capture_pane")
        self._client.server_info()
        return self._client.capture_pane(pane, lines=lines)

    def kill_pane(self, pane_id) -> MuxOperationEvidenceV2 | None:
        pane = self._pane_ref(pane_id, operation="kill_pane")
        self._capability_gate.require_supported("kill_pane")
        self._client.server_info()
        evidence = self._client.kill_pane(pane)
        self._panes.pop(pane["pane_id"], None)
        self._pane_namespaces.pop(pane["pane_id"], None)
        return evidence if isinstance(pane_id, dict) else None

    def attach_namespace(
        self,
        namespace: MuxNamespaceRefV2,
        *,
        window_name: str | None = None,
    ) -> MuxOperationEvidenceV2:
        namespace_ref = self._namespace_ref_from_mapping(namespace, operation="attach_namespace")
        self._capability_gate.require_supported("attach_namespace")
        self._client.server_info()
        return self._client.attach_namespace(namespace_ref, window_name=window_name)

    def is_alive(self, pane_id) -> bool:
        try:
            pane = self._pane_ref(pane_id, operation="is_alive")
        except MuxCommandErrorV2 as exc:
            if exc.category == "not-found":
                return False
            raise
        cached = pane["pane_id"] in self._panes
        try:
            self._capability_gate.require_supported("capture_pane")
            self._client.server_info()
            self._client.capture_pane(pane, lines=1)
        except MuxCommandErrorV2 as exc:
            if exc.category == "not-found":
                self._panes.pop(pane["pane_id"], None)
                self._pane_namespaces.pop(pane["pane_id"], None)
                return False
            if exc.operation == "server_info" or exc.category in {"schema-mismatch", "unsupported"}:
                raise
            return cached
        return True

    def activate(self, pane_id: str) -> None:
        if pane_id not in self._panes:
            raise MuxCommandErrorV2(
                category="not-found",
                backend_impl="herdr",
                operation="activate",
                detail=f"unknown Herdr pane {pane_id!r}",
                evidence={"pane_id": pane_id},
            )
        raise MuxCommandErrorV2(
            category="unsupported",
            backend_impl="herdr",
            operation="activate",
            detail="Herdr pane activation is not supported by the current backend adapter",
            evidence={"pane_id": pane_id},
        )

    def _pane_ref(self, pane_or_id, *, operation: str) -> MuxPaneRefV2:
        if isinstance(pane_or_id, dict):
            pane_id = str(pane_or_id.get("pane_id") or "")
            session_name = str(pane_or_id.get("session_name") or "").strip()
            if (
                str(pane_or_id.get("backend_impl") or "") != "herdr"
                or not pane_id
                or not session_name
            ):
                raise MuxCommandErrorV2(
                    category="not-found",
                    backend_impl="herdr",
                    operation=operation,
                    detail=f"unknown Herdr pane {pane_id!r}",
                    evidence={"pane_id": pane_id},
                )
            cached = self._panes.get(pane_id)
            if cached is not None and cached.get("session_name") != session_name:
                raise MuxCommandErrorV2(
                    category="not-found",
                    backend_impl="herdr",
                    operation=operation,
                    detail=f"unknown Herdr pane {pane_id!r}",
                    evidence={"pane_id": pane_id},
                )
            if (
                cached is None
                and self._known_namespace_for_session(
                    session_name,
                    operation=operation,
                    pane_id=pane_id,
                )
                is None
            ):
                raise MuxCommandErrorV2(
                    category="not-found",
                    backend_impl="herdr",
                    operation=operation,
                    detail=f"unknown Herdr pane {pane_id!r}",
                    evidence={"pane_id": pane_id},
                )
            return make_pane_ref(
                backend_impl="herdr",
                pane_id=pane_id,
                session_name=session_name,
                window_name=pane_or_id.get("window_name"),  # type: ignore[arg-type]
                agent_slug=pane_or_id.get("agent_slug"),  # type: ignore[arg-type]
            )
        pane_id = str(pane_or_id)
        try:
            return self._panes[pane_id]
        except KeyError as exc:
            raise MuxCommandErrorV2(
                category="not-found",
                backend_impl="herdr",
                operation=operation,
                detail=f"unknown Herdr pane {pane_id!r}",
                evidence={"pane_id": pane_id},
            ) from exc

    def _namespace_ref_from_mapping(self, namespace: dict, *, operation: str) -> MuxNamespaceRefV2:
        session_name = str(namespace.get("session_name") or "").strip()
        ipc_ref = str(namespace.get("ipc_ref") or "").strip()
        if (
            namespace.get("backend_impl") != "herdr"
            or namespace.get("ipc_kind") != "herdr_socket"
            or not str(namespace.get("namespace_id") or "").strip()
            or not session_name
            or not self._namespace_ipc_ref_matches(ipc_ref, session_name)
        ):
            raise MuxCommandErrorV2(
                category="command-failed",
                backend_impl="herdr",
                operation=operation,
                detail="invalid Herdr namespace ref",
                evidence={"namespace_id": str(namespace.get("namespace_id") or "")},
            )
        return namespace  # type: ignore[return-value]

    def _register_namespace(self, namespace: MuxNamespaceRefV2) -> MuxNamespaceRefV2:
        self._known_namespaces[(namespace["session_name"], namespace["namespace_id"])] = namespace
        return namespace

    def _known_namespace_for_session(
        self,
        session_name: str,
        *,
        operation: str,
        pane_id: str,
    ) -> MuxNamespaceRefV2 | None:
        matches = [
            namespace
            for (known_session, _), namespace in self._known_namespaces.items()
            if known_session == session_name
        ]
        if len(matches) <= 1:
            return matches[0] if matches else None
        raise MuxCommandErrorV2(
            category="not-found",
            backend_impl="herdr",
            operation=operation,
            detail=f"ambiguous Herdr namespace for pane {pane_id!r}",
            evidence={"pane_id": pane_id, "session_name": session_name},
        )

    def _namespace_ipc_ref_matches(self, ipc_ref: str, session_name: str) -> bool:
        if ipc_ref == self._client.socket_ref:
            return True
        return self._client.allow_session_scoped_ipc_refs and ipc_ref == f"herdr://{session_name}"

    def _ensure_legacy_namespace(self, cwd: str) -> MuxNamespaceRefV2:
        key = (cwd or "").strip()
        namespace = self._legacy_namespaces.get(key)
        if namespace is None:
            namespace = self.create_session(
                project_id="ccb-herdr",
                cwd=cwd,
                title="ccb-herdr",
            )
            self._legacy_namespaces[key] = namespace
        return namespace


__all__ = ["HerdrBackend"]
