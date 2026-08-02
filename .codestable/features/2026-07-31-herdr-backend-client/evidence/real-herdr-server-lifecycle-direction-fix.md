---
doc_type: feature-evidence
feature: 2026-07-31-herdr-backend-client
kind: real-herdr-adapter-fix
status: passed
updated_at: 2026-08-02
---

# real Herdr server lifecycle / direction fix evidence

## 背景

owner 已确认采用 `ReopenBackendClient` 路线，重开已 accepted 的
`herdr-backend-client`，修复真实 Herdr 接触暴露的两个 blocker：

- Herdr socket/CLI 命令不会自动拉起 `herdr server`，adapter 需要拥有 server lifecycle
  启动 seam。
- ccbd 使用 `bottom` 表达垂直 split，Herdr CLI 只接受 `right|down`；adapter 不能把未知方向
  静默 fallback 到 `right`。

## 代码变更范围

- `lib/terminal_runtime/herdr_backend_runtime/cli.py`
  - server-backed command 遇到 Herdr `Os { code: 2, kind: NotFound }` 时启动
    `herdr --session <name> server`，然后重试原命令。
  - 已记录的 server process 若已退出，下一次 NotFound 会重新启动 server，不会因 session 已记录
    而重复失败。
  - `server_info` / `--version` / `api schema` 不触发 server 启动。
  - split direction 归一为 Herdr 支持的 `right|down`；`bottom` 映射到 `down`；
    `left/up/sideways` 这类不可表达方向 fail closed。
- `test/test_herdr_backend_client.py`
  - 覆盖 server auto-start + retry。
  - 覆盖 `server_info` 不启动 server。
  - 覆盖 `bottom -> down` 与不可表达方向 fail closed。

未修改 provider runtime、ccbd durable state、recovery、doctor/support、package/release。

## Fresh Verification

- `python -m py_compile "lib/terminal_runtime/herdr_backend_runtime/cli.py" "test/test_herdr_backend_client.py"` -> exit 0
- `python -m pytest -q "test/test_herdr_backend_client.py" -k "server or split_direction or bottom or unrepresentable or cli_request_adapter"` -> 38 passed, 105 deselected
- review-fix rerun: `python -m pytest -q "test/test_herdr_backend_client.py" -k "server or split_direction or bottom or unrepresentable or cli_request_adapter"` -> 39 passed, 105 deselected
- `python -m pytest -q "test/test_herdr_backend_client.py" "test/test_terminal_runtime_backend_selection.py"` -> 158 passed
- `python -m pytest -q "test/test_mux_backend_contract.py" -k "V2 or herdr"` -> 8 passed, 12 deselected
- `python -m pytest -q "test/test_mux_backend_contract.py" "test/test_terminal_runtime_backend_selection.py"` -> 35 passed
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml" --yaml-only` -> 1 passed
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` -> 1 passed

## Real Herdr Smoke

Environment:

- executable: `C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe`
- version: `0.7.5-preview.2026-07-29-44b3adb12552`
- api schema: `Herdr API`

Action:

- instantiate `HerdrCliRequestAdapter` with a temporary session.
- call `server_info`.
- call `create_session`; adapter auto-started `herdr server` when needed.
- call `create_pane` with `direction="bottom"`; adapter mapped it to Herdr `down`.
- call `kill_pane`.
- cleanup: `herdr --session <temp> server stop`.

Result:

```text
{'version': '0.7.5-preview.2026-07-29-44b3adb12552', 'api_schema': 'Herdr API', 'namespace_id': 'w1', 'pane_id': 'w1:p2', 'kill_status': 'ok'}
```

## Verdict

passed. The two reattributed CMD-013 blockers are fixed within the backend-client adapter boundary and verified by unit/focused regression plus real Herdr smoke.

## Review Closure Notes

独立 reviewer `019fbf9d-af8d-7ae3-b1f9-24ff45881bd0` 指出：

- `_start_server()` 不能只依赖 session set；需要检查 `Popen.poll()`，否则 server 退出后不会重启。
- unsupported direction 应在任何 Herdr command 之前 fail closed。

Closure:

- `_start_server()` 现在检查已保存 process，只有 `poll() is None` 才复用；已退出或缺失时清除旧记录并重新 `Popen`。
- `_split_direction()` 校验提前到 `_create_pane()` 的第一段，先于 parent pane 查询和 server-backed command。
- 新增测试覆盖 exited process 重新启动，以及 unsupported direction 不执行任何 Herdr command。
