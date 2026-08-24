#!/usr/bin/env python3
"""Phase 5 旧路径删除门禁(13C）。

本脚本是可重跑的删除门禁,不删除任何业务代码。它读取 Phase 5 剩余删除项清单,
逐项校验删除所需的证据是否齐备:

- characterization test:证明旧行为的等价测试文件必须已存在;
- live validation:无 WezTerm GUI 回退、有 mux 多项目 attach、mobile gateway 脱敏、
  Herdr 原生 agent_id 权威、archi hotspot 基线等实机/架构证据必须存在,且 JSON 顶层
  同时带 passed=true 与非空 evidence 记录(裸 {"passed": true} 空桩不放行)。

只要有任一删除项证据缺失或未通过,门禁即 fail-closed:整体判定为 blocked 且进程退出非零,
父工单(13/13A/13B/13C)据此保持 blocked,不允许进入 contract(删除)步骤。

用法::

    python scripts/phase5_deletion_gate.py        # 人类可读报告
    python scripts/phase5_deletion_gate.py --json # 结构化 JSON 报告

退出码:0 表示所有删除项证据齐备可放行;2 表示门禁未通过(blocked)。
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPORT_SCHEMA = "ccb.phase5.deletion_gate.v1"

# live validation 目录:实机/架构证据以 JSON 落盘,顶层字段 passed 必须为 true 才算通过。
LIVE_VALIDATION_DIR = "plans/architecture-optimization/live-validation"


@dataclass(frozen=True)
class DeletionItem:
    """一个 Phase 5 删除候选项及其删除前必须齐备的证据。"""

    item_id: str
    description: str
    source_issue: str
    blocking_issue: str
    characterization_tests: tuple[str, ...]
    live_validation_artifacts: tuple[str, ...]
    rollback_condition: str


# Phase 5 剩余删除项(来源:issues/13、13A、13B、13C 审计结论)。
# 当前均处于 blocked:live validation 与 Herdr 原生 agent_id 权威证据尚未产出。
DELETION_ITEMS: tuple[DeletionItem, ...] = (
    DeletionItem(
        item_id="delete-ccb-pane-agent-report-patch",
        description="删除 tmux_runtime 中 CCB 主动补 Herdr Agent 身份(report_pane_agent)的正常路径",
        source_issue="13B",
        blocking_issue="13A",
        characterization_tests=(
            "test/test_herdr_runtime_contracts.py",
            "test/test_v2_project_namespace_state.py",
        ),
        live_validation_artifacts=(
            f"{LIVE_VALIDATION_DIR}/agent-id-authority.json",
            f"{LIVE_VALIDATION_DIR}/archi-hotspot-baseline.json",
        ),
        rollback_condition=(
            "删除后若 reconnect/restore 出现 agent_id 漂移,或 runtime binding 丢失 "
            "pane/agent/provider/generation 归属,恢复 report_pane_agent 补丁并保持 blocked-by-13A。"
        ),
    ),
    DeletionItem(
        item_id="narrow-backend-capability-compat-gate",
        description=(
            "收窄 backend.py / runtime/capabilities.py / project_namespace_runtime/backend.py "
            "的兼容 capability gate,仅保留诊断/兼容 fallback"
        ),
        source_issue="13C",
        blocking_issue="13C",
        characterization_tests=(
            "test/test_herdr_backend_client.py",
            "test/test_ccbd_project_view.py",
            "test/test_mobile_gateway_service.py",
        ),
        live_validation_artifacts=(
            f"{LIVE_VALIDATION_DIR}/no-wezterm-gui-fallback.json",
            f"{LIVE_VALIDATION_DIR}/mux-multi-project-attach.json",
            f"{LIVE_VALIDATION_DIR}/mobile-gateway-redaction.json",
            f"{LIVE_VALIDATION_DIR}/archi-hotspot-baseline.json",
        ),
        rollback_condition=(
            "删除兼容 gate 后若明确选择 Herdr 后端在不可用时不再 fail-closed,或 project_view / "
            "mobile gateway 泄漏 prompt/reply/API key/OAuth token,恢复兼容 gate。"
        ),
    ),
)


def _validation_passed(artifact_path: Path) -> bool:
    """live validation 产物必须存在、passed 为 true、且带非空 evidence 记录才算通过。

    仅有裸 {"passed": true} 不足以放行,避免自证型空桩误通过;缺失或解析失败一律 fail-closed。
    """
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict) or payload.get("passed") is not True:
        return False
    return bool(payload.get("evidence"))


def _evaluate_item(item: DeletionItem, repo_root: Path) -> dict[str, Any]:
    """评估单个删除项:收集缺失的 characterization test 与未通过的 live validation。"""
    missing_characterization = [
        rel for rel in item.characterization_tests if not (repo_root / rel).is_file()
    ]
    missing_validation = [
        rel for rel in item.live_validation_artifacts if not _validation_passed(repo_root / rel)
    ]
    blocked = bool(missing_characterization or missing_validation)
    return {
        "item_id": item.item_id,
        "description": item.description,
        "source_issue": item.source_issue,
        "blocking_issue": item.blocking_issue,
        "status": "blocked" if blocked else "pass",
        "missing_characterization": missing_characterization,
        "missing_validation": missing_validation,
        "rollback_condition": item.rollback_condition,
    }


def evaluate_deletion_gate(repo_root: Path) -> dict[str, Any]:
    """评估全部删除项,返回结构化门禁报告。

    只要有任一删除项 blocked,整体 overall_status 即为 blocked(fail-closed）。
    """
    items = [_evaluate_item(item, repo_root) for item in DELETION_ITEMS]
    overall = "pass" if all(entry["status"] == "pass" for entry in items) else "blocked"
    return {
        "schema": REPORT_SCHEMA,
        "overall_status": overall,
        "items": items,
    }


def render_report(report: dict[str, Any]) -> str:
    """把门禁报告渲染成人类可读文本。"""
    lines = [
        "Phase 5 旧路径删除门禁(13C)",
        f"整体判定: {report['overall_status'].upper()}",
        "",
    ]
    for entry in report["items"]:
        lines.append(f"[{entry['status'].upper()}] {entry['item_id']}(来源 {entry['source_issue']})")
        lines.append(f"  说明: {entry['description']}")
        if entry["missing_characterization"]:
            lines.append(f"  缺 characterization test: {', '.join(entry['missing_characterization'])}")
        if entry["missing_validation"]:
            lines.append(f"  缺/未通过 live validation: {', '.join(entry['missing_validation'])}")
        lines.append(f"  rollback 条件: {entry['rollback_condition']}")
        lines.append("")
    if report["overall_status"] != "pass":
        lines.append("门禁未通过:父工单保持 blocked,不允许进入删除(contract)步骤。")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5 旧路径删除门禁(13C)")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出报告")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="仓库根目录(默认脚本所在仓库)",
    )
    args = parser.parse_args(argv)

    # Windows 控制台默认非 UTF-8 代码页会把简体中文报告显示成乱码,尽力切到 UTF-8。
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass

    report = evaluate_deletion_gate(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_report(report))
    return 0 if report["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
