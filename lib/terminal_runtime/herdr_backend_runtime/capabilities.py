from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from terminal_runtime.mux_backend_contract import (
    MuxCapabilitiesV2,
    MuxCommandErrorV2,
    capability_statuses_supported,
    make_capabilities,
)

_REQUIRED_CAPABILITIES = {
    "session_attach",
    "pane_spawn",
    "send_input",
    "read_output",
    "kill_pane",
}
_SUPPORTED_STATUS = {"supported", "partial", "unsupported", "workaround"}
_CONTINUE_RECOMMENDATIONS = {"continue"}
_PASS_VERDICTS = {"pass"}
_STOP_RECOMMENDATIONS = {"stop", "needs-upstream-issue"}
_BLOCKING_VERDICTS = {"blocked", "failed"}


@dataclass(frozen=True)
class HerdrCapabilityGate:
    capabilities: MuxCapabilitiesV2 | None
    failure_reason: str | None = None
    diagnostic: str | None = None
    capability_report_ref: str | None = None

    @classmethod
    def from_spike_evidence(
        cls,
        spike_evidence: Mapping[str, object] | None,
        *,
        capability_report_ref: str | None,
    ) -> "HerdrCapabilityGate":
        if not spike_evidence:
            return cls(
                capabilities=None,
                failure_reason="herdr-capability-missing",
                diagnostic="Herdr capability evidence is unavailable",
                capability_report_ref=capability_report_ref,
            )

        adapter_recommendation = str(spike_evidence.get("adapter_recommendation") or "").strip()
        verdict = str(spike_evidence.get("verdict") or "").strip()
        failure_class = str(spike_evidence.get("failure_class") or "").strip()
        if adapter_recommendation in _STOP_RECOMMENDATIONS:
            return cls._blocked(
                capability_report_ref,
                f"Herdr spike adapter recommendation is {adapter_recommendation}",
            )
        if adapter_recommendation not in _CONTINUE_RECOMMENDATIONS:
            return cls._blocked(
                capability_report_ref,
                "Herdr spike adapter recommendation is missing or unknown",
            )
        if verdict in _BLOCKING_VERDICTS:
            return cls._blocked(capability_report_ref, f"Herdr spike verdict is {verdict}")
        if verdict not in _PASS_VERDICTS:
            return cls._blocked(capability_report_ref, "Herdr spike verdict is missing or unknown")
        if failure_class and failure_class != "none":
            return cls._blocked(
                capability_report_ref,
                f"Herdr spike failure_class is {failure_class}",
            )

        projection = spike_evidence.get("capability_projection")
        if not isinstance(projection, Mapping):
            return cls._blocked(capability_report_ref, "Herdr capability projection is missing")

        command_status = _status_mapping(projection.get("command_status"))
        semantic_status = _status_mapping(projection.get("semantic_status"))
        windows_beta_gaps = _string_list(projection.get("windows_beta_gaps"))
        blocking_gaps = _string_list(projection.get("blocking_gaps"))
        if command_status is None or semantic_status is None or windows_beta_gaps is None or blocking_gaps is None:
            return cls._blocked(
                capability_report_ref,
                "Herdr capability projection contains unknown status values or malformed gap fields",
            )
        capabilities = make_capabilities(
            backend_impl="herdr",
            command_status=command_status,
            semantic_status=semantic_status,
            windows_beta_gaps=windows_beta_gaps,
            blocking_gaps=blocking_gaps,
            source_ref=capability_report_ref,
        )
        capabilities["adapter_recommendation"] = adapter_recommendation  # type: ignore[typeddict-unknown-key]
        capabilities["verdict"] = verdict  # type: ignore[typeddict-unknown-key]
        capabilities["failure_class"] = failure_class or "none"  # type: ignore[typeddict-unknown-key]
        if not capability_statuses_supported(capabilities):
            return cls._blocked(
                capability_report_ref,
                "Herdr capability projection is partial, unsupported, or has blocking gaps",
            )
        return cls(
            capabilities=capabilities,
            failure_reason=None,
            diagnostic=None,
            capability_report_ref=capability_report_ref,
        )

    @classmethod
    def _blocked(
        cls,
        capability_report_ref: str | None,
        diagnostic: str,
    ) -> "HerdrCapabilityGate":
        return cls(
            capabilities=None,
            failure_reason="unsupported-capability",
            diagnostic=diagnostic,
            capability_report_ref=capability_report_ref,
        )

    def require_supported(self, operation: str) -> MuxCapabilitiesV2:
        if self.capabilities is not None:
            return self.capabilities
        raise MuxCommandErrorV2(
            category="unsupported",
            backend_impl="herdr",
            operation=operation,
            detail=self.diagnostic or "Herdr capability gate is blocked",
            evidence={
                "failure_reason": self.failure_reason or "unsupported-capability",
                "capability_report_ref": self.capability_report_ref,
            },
        )


def _status_mapping(raw: object) -> dict[str, str] | None:
    if not isinstance(raw, Mapping):
        return None
    result: dict[str, str] = {}
    for key, value in raw.items():
        key_str = str(key)
        status = str(value or "").strip()
        if status not in _SUPPORTED_STATUS:
            return None
        if key_str in _REQUIRED_CAPABILITIES:
            result[key_str] = status
    if not _REQUIRED_CAPABILITIES.issubset(result):
        return None
    return result


def _string_list(raw: object) -> list[str] | None:
    if not isinstance(raw, list):
        return None
    result: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            return None
        item = item.strip()
        if item:
            result.append(item)
    return result


def herdr_capability_report_supported(capabilities: Mapping[str, object]) -> bool:
    adapter_recommendation = str(capabilities.get("adapter_recommendation") or "").strip()
    verdict = str(capabilities.get("verdict") or "").strip()
    failure_class = str(capabilities.get("failure_class") or "").strip()
    return (
        adapter_recommendation in _CONTINUE_RECOMMENDATIONS
        and verdict in _PASS_VERDICTS
        and failure_class in {"", "none"}
        and capability_statuses_supported(capabilities)
    )


__all__ = ["HerdrCapabilityGate", "herdr_capability_report_supported"]
