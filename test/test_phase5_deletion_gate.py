"""13C：Phase 5 删除门禁脚手架的外部可观测行为测试。

只断言门禁对外可见的结论(证据齐备→pass、缺失→blocked、CLI 是否 fail-closed),
不测内部实现细节。门禁不删除任何业务代码,只根据证据清单给出可重跑的放行/阻塞判定。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REPO_ROOT / "scripts" / "phase5_deletion_gate.py"


def _load_gate():
    """从文件路径加载门禁模块,避免污染 sys.path。"""
    spec = importlib.util.spec_from_file_location("phase5_deletion_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    # dataclass 需要模块登记在 sys.modules 才能解析 __module__(Py3.12+)。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _materialize_all_evidence(gate, root: Path, *, validation_passed: bool) -> None:
    """在临时仓库根下造齐所有删除项声明的 characterization test 与 live validation 产物。"""
    for item in gate.DELETION_ITEMS:
        for rel in item.characterization_tests:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# characterization placeholder\n", encoding="utf-8")
        for rel in item.live_validation_artifacts:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"passed": validation_passed, "evidence": "live validation record"}),
                encoding="utf-8",
            )


def test_gate_declares_items_with_complete_checklist() -> None:
    """清单完整性:每个删除项都必须声明来源工单与非空 rollback 条件。"""
    gate = _load_gate()
    assert gate.DELETION_ITEMS, "至少要声明一个 Phase 5 删除项"
    for item in gate.DELETION_ITEMS:
        assert item.source_issue.strip()
        assert item.rollback_condition.strip(), f"{item.item_id} 缺少 rollback 条件"
        assert item.characterization_tests, f"{item.item_id} 缺少 characterization test"
        assert item.live_validation_artifacts, f"{item.item_id} 缺少 live validation 证据"


def test_gate_blocks_when_live_validation_absent() -> None:
    """真实仓库当前无 live validation 产物 → 门禁必须整体 blocked,且逐项因缺 validation 阻塞。

    characterization test 文件已存在,不应被误报为缺失,确保阻塞原因精确。
    """
    gate = _load_gate()
    report = gate.evaluate_deletion_gate(REPO_ROOT)
    assert report["overall_status"] == "blocked"
    assert report["items"]
    for item in report["items"]:
        assert item["missing_characterization"] == [], (
            f"{item['item_id']} 的 characterization test 应已存在: {item['missing_characterization']}"
        )
        assert item["status"] == "blocked"
        assert item["missing_validation"], f"{item['item_id']} 应因缺 live validation 而 blocked"
        assert item["rollback_condition"].strip()


def test_gate_passes_only_when_all_evidence_present(tmp_path: Path) -> None:
    """证据齐备(test 存在 + validation passed=true)→ 门禁放行,证明并非硬编码常 blocked。"""
    gate = _load_gate()
    _materialize_all_evidence(gate, tmp_path, validation_passed=True)
    report = gate.evaluate_deletion_gate(tmp_path)
    assert report["overall_status"] == "pass"
    for item in report["items"]:
        assert item["status"] == "pass"
        assert item["missing_characterization"] == []
        assert item["missing_validation"] == []


def test_gate_fails_closed_when_validation_present_but_not_passed(tmp_path: Path) -> None:
    """live validation 产物存在但 passed=false → 仍必须 blocked(fail-closed)。"""
    gate = _load_gate()
    _materialize_all_evidence(gate, tmp_path, validation_passed=False)
    report = gate.evaluate_deletion_gate(tmp_path)
    assert report["overall_status"] == "blocked"
    for item in report["items"]:
        assert item["status"] == "blocked"


def test_gate_rejects_bare_passed_flag_without_evidence(tmp_path: Path) -> None:
    """live validation 仅有裸 {"passed": true}、无 evidence 记录 → 视为未通过(fail-closed)。"""
    gate = _load_gate()
    for item in gate.DELETION_ITEMS:
        for rel in item.characterization_tests:
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# characterization placeholder\n", encoding="utf-8")
        for rel in item.live_validation_artifacts:
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"passed": True}), encoding="utf-8")
    report = gate.evaluate_deletion_gate(tmp_path)
    assert report["overall_status"] == "blocked"
    for item in report["items"]:
        assert item["status"] == "blocked"
        assert item["missing_validation"], "无 evidence 的裸 passed 应计入 missing_validation"


def test_cli_exits_nonzero_and_emits_report_when_blocked() -> None:
    """CLI 在门禁未通过时必须退出非零并输出结构化报告,供父工单据此保持 blocked。"""
    result = subprocess.run(
        [sys.executable, str(GATE_PATH), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["schema"] == "ccb.phase5.deletion_gate.v1"
    assert payload["overall_status"] == "blocked"
