# validation summary

Recorded: 2026-07-27

## Commands

```text
> $env:PYTHONDONTWRITEBYTECODE='1'; python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"
Validated 1 file(s): 1 passed, 0 failed.

> $env:PYTHONDONTWRITEBYTECODE='1'; python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py" --file ".codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml" --yaml-only
Validated 1 file(s): 1 passed, 0 failed.

> $env:PYTHONPATH='lib'; python -m pytest -q -rs test/test_v2_tmux_ui.py
13 passed, 2 skipped

> cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet
63 passed

> python -c "import json, pathlib; p=pathlib.Path('.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/windows-rmux-ux-parity-evidence.json'); d=json.loads(p.read_text(encoding='utf-8')); req={'schema_version','host_kind','terminal_host','backend_impl','control_plane','parity_dimension','evidence_status','failure_class','artifacts','residual_risks'}; assert req <= d.keys(); assert d['schema_version']==1; assert d['host_kind']=='native_windows'; assert d['terminal_host']=='wezterm'; assert d['backend_impl']=='rmux'; assert d['control_plane']=='ccbd'; assert d['parity_dimension']=='foreground_interaction'; assert d['evidence_status']=='blocked'; assert d['failure_class']=='unsupported_capability'; assert isinstance(d['artifacts'], dict) and d['artifacts']; base=p.parents[1]; assert all(isinstance(v,str) and v.strip() and ((pathlib.Path(v) if pathlib.Path(v).is_absolute() else base/pathlib.Path(v)).exists()) for v in d['artifacts'].values()); assert isinstance(d['residual_risks'], list) and d['residual_risks']; route=d.get('details',{}).get('sidebar_settings_routing',{}); assert route.get('selected_route')=='unsupported_capability'; assert route.get('runtime_behavior_changed') is False; assert route.get('broad_fallback_added') is False; assert route.get('failure_detail')"
passed
```

UX JSON validator 精确断言：

```text
evidence_status == blocked
failure_class == unsupported_capability
details.sidebar_settings_routing.selected_route == unsupported_capability
details.sidebar_settings_routing.runtime_behavior_changed == false
details.sidebar_settings_routing.broad_fallback_added == false
```

## Scoped cleanliness

命令：

```text
rg -n "send-keys -t = c|send-keys -t %0 c|broad.*fallback|sidebar.*left-click|token=[A-Za-z0-9]|console\.log|console\.error|print\(|fmt\.Print|TODO|FIXME|XXX" \
  ".codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing" \
  "lib/cli/services/tmux_ui_runtime/service.py" \
  "test/test_v2_tmux_ui.py" \
  "tools/ccb-agent-sidebar/src"
```

结果解释：

- `test/test_v2_tmux_ui.py` 命中的是既有禁止 broad fallback 的断言。
- `tools/ccb-agent-sidebar/src/tui.rs`、`tools/ccb-agent-sidebar/src/mouse_probe.rs` 命中的是既有测试 fixture 与脱敏断言，不是新增真实 token。
- 当前 feature design/brainstorm/evidence 命中的是“拒绝 broad fallback”和 direct `c` 诊断说明，均为本 feature 的核心证据语义。
- 未发现本 feature 新增默认 debug 输出、真实 token、临时 TODO/FIXME/XXX 或运行时 broad fallback。

## Final route

```json
{
  "selected_route": "unsupported_capability",
  "runtime_behavior_changed": false,
  "broad_fallback_added": false
}
```

## TDD exception

本 feature 终态为 capability evidence + blocked projection，不改变 runtime 行为。自动化验证覆盖现有禁止 broad fallback 的回归测试、Rust sidebar helper tests、YAML/JSON schema；真实前台 settings click 仍按 UX JSON 投影为 `blocked/unsupported_capability`。
