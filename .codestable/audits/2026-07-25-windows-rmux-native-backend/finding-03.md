---
doc_type: audit-finding
audit: 2026-07-25-windows-rmux-native-backend
finding_id: "performance-03"
nature: performance
severity: P2
confidence: high
suggested_action: cs-refactor
status: open
---

# Finding 03：terminal API 的全局 backend cache 实际无法命中

## 速答

`terminal_runtime.api.get_backend()` 维护 `_backend_cache`，但传给 `TerminalBackendSelection` 时只传了 cached backend 对象，没有传对应的 backend impl；命中条件要求 `cached_backend_impl == effective_backend`，因此跨次调用会重复构造 backend。

## 关键证据

- `lib/terminal_runtime/api.py:104` — 模块级 `_backend_cache` 预期缓存 `TerminalBackend`。
- `lib/terminal_runtime/api.py:128` — `get_backend()` 把 `_backend_cache` 传入 `_resolve_backend(...)`。
- `lib/terminal_runtime/api_selection.py:23` — `_resolve_backend()` 每次新建 `TerminalBackendSelection`。
- `lib/terminal_runtime/api_selection.py:36` — 只传 `cached_backend=cached_backend`，没有传 `cached_backend_impl`。
- `lib/terminal_runtime/backend_selection.py:39` — 缓存命中条件要求 `self.cached_backend_impl == effective_backend`。
- `lib/terminal_runtime/backend_selection.py:47` — `cached_backend_impl` 只在当前 `TerminalBackendSelection` 实例内设置；下一次 `_resolve_backend()` 新建实例后该字段恢复为 `None`。
- `lib/terminal_runtime/rmux_backend.py:116` — rmux backend 初始化会创建 capability gate。
- `lib/terminal_runtime/backend_resolver.py:216` — 默认 capability reader 会读 `.codestable/.../rmux-route-decision-summary.yaml`，重复初始化会带来重复 I/O。

## 影响

对 tmux 路径主要是多构造对象；对 Windows rmux 路径会重复执行 capability gate 初始化、环境解析和客户端封装，增加 `doctor`、启动和 runtime 路径的固定开销，也使 `_backend_cache` 的存在产生误导。

## 修复方向

要么把缓存状态提升到 `api.py` 同步保存 backend impl，要么删除跨调用 `_backend_cache` 并让调用方显式管理生命周期。当前代码应避免“有缓存变量但不能命中”的半状态。

## 建议动作

`cs-refactor`，因为主要是缓存生命周期和接口契约整理，行为修复可以通过现有 backend selection 测试补一条跨 `api.get_backend()` 命中用例。
