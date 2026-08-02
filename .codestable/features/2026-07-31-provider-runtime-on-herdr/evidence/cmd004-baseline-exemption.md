---
doc_type: feature-evidence
feature: 2026-07-31-provider-runtime-on-herdr
command_id: CMD-004
kind: baseline-exemption
status: baseline-risk
updated_at: 2026-08-03
---

# CMD-004 baseline exemption

## 结论

S7 复跑 CMD-004 时，`test/test_v2_runtime_launch.py` 的 Codex named runtime bootstrap 路径仍因缺少 `input.fifo` / `output.fifo` 失败；该失败在 S4 记录为既有基线风险，不是 S7 evidence 变更引入。

本证据只允许下游把 CMD-004 解释为“存在已知基线红灯并已隔离归因”，不能解释为 CMD-004 全量通过。

## S7 复现

```text
$ python -m pytest -q "test/test_v2_runtime_launch.py" "test/test_runtime_launch_timings.py" "test/test_v2_runtime_launch_session_files.py" -k "runtime or launch or session or pane or mux or herdr or rmux" --basetemp "D:/tmp/pytest-provider-runtime-s7-cmd004" -p no:cacheprovider
timeout_after_seconds: 120
partial_result: failures present
```

```text
$ python -m pytest -q "test/test_v2_runtime_launch.py" "test/test_runtime_launch_timings.py" "test/test_v2_runtime_launch_session_files.py" -k "runtime or launch or session or pane or mux or herdr or rmux" --basetemp "D:/tmp/pytest-provider-runtime-s7-cmd004-detail" -p no:cacheprovider -x
exit_code: 1
first_failure: test_ensure_agent_runtime_launches_named_codex_session
error: RuntimeError: codex runtime bootstrap missing declared artifacts: input.fifo, output.fifo
```

## Prior baseline reference

`provider-runtime-on-herdr-implementation.md` 的 “已知基线风险” 在 S4 后已记录：

```text
CMD-004 全量 runtime launch bundle 当前仍受既有 Codex bridge bootstrap 基线问题影响，失败为 `codex runtime bootstrap missing declared artifacts: input.fifo, output.fifo`。该问题在 S2 前已存在，本轮 focused Herdr launch 测试不依赖该路径。
```

## Passing coverage around the exemption

- S7 catalog focused：`9 passed`
- CMD-005 provider session lifecycle：`15 passed`
- CMD-006 ask/pend/completion/cancel：`48 passed`
- CMD-007 provider-native completion/fallback：`26 passed, 23 deselected`
- CMD-008 runtime/restart Herdr surface：`18 passed`
- S7 scoped scope/content guard：passed
- CMD-010 Herdr agent state completed guard：passed

## QA residual risk

QA 必须保留该隔离假设：S7 没有证明 CMD-004 全量 runtime launch bundle 干净，只证明 S7 新增 evidence 和 Herdr provider runtime authority 相关 focused gates 未新增该失败。QA 若需要把 runtime launch regression 视作完全通过，必须先修复或重新基线 Codex bridge bootstrap artifacts。

## Verdict

baseline-risk
