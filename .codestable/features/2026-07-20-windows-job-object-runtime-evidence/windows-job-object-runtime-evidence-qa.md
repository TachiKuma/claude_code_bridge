---
doc_type: feature-qa
feature: windows-job-object-runtime-evidence
status: passed
updated_at: "2026-07-22"
---

# windows-job-object-runtime-evidence QA

## Scope

QA 覆盖 process_ref contract、runtime store / provider facts / helper manifest roundtrip、health pane/process evidence 顺序、Windows kill / cleanup ownership gating、project view diagnostics、YAML 产物与 guard。

## Commands

```text
python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-checklist.yaml" --yaml-only
python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"
python -m pytest -q "test/test_v2_provider_health_store.py" "test/test_ccbd_health_monitor_rebind.py" "test/test_ccbd_health_assessment_provider_pane.py"
python -m pytest -q "test/test_provider_helper_cleanup.py" "test/test_cli_kill_runtime_processes.py" "test/test_v2_kill_service.py" "test/test_ccbd_stop_flow_runtime.py"
python -m pytest -q "test/test_ccbd_project_view.py" "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_registry.py" -k "process_ref or runtime_authority or job or pane_state"
rg -n -e "os\\.kill\\(pid, 0\\)" -e "if os_name == 'nt':" -e "return True" -e "taskkill" -e "/T" -e "process_ref" -e "job_id" -e "owner_pid" "lib/ccbd/system.py" "lib/runtime_pid_cleanup" "lib/provider_runtime" "lib/ccbd/services/provider_runtime_facts.py"
git diff --check
```

## Evidence

- checklist YAML：passed。
- roadmap items YAML：passed。
- runtime facts / health diagnostics / pane vs process evidence：`9 passed`。
- helper cleanup / kill cleanup / destructive ownership gating：`48 passed`。
- project view / runtime refresh / registry selector：`17 passed, 75 deselected`。
- focused process_ref/store/helper/kill tests：`28 passed`。
- CMD-006 guard：返回预期 matches，无无条件 Windows pid cleanup 门。
- diff whitespace check：clean。

## Notes

`test/test_ccbd_project_view.py` 的 fixed DoD selector 命中 recent jobs helper 用例；Windows 下 `.py` helper 不能依赖 shebang 直接执行，因此 `rust_helpers` 增加 `.py` helper 通过当前 Python 解释器启动的兼容路径。
