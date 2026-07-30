---
doc_type: brainstorm
slug: windows-native-herdr-ccb
created: 2026-07-30
status: active
summary: 探索以 CCB v8.5.2 为基底、借助 Herdr 实现 Native Windows CCB 全功能的可行路径
tags: [windows, native-windows, herdr, ccb-v8.5.2, multiplexer, epic-candidate]
---

# Native Windows CCB via Herdr

> 创意空间 | 2026-07-30 | 下一步：cs-epic

## 出发点

owner 提出两个前置要求：

- 先暂停 `windows-rmux-ux-parity-hardening` 线，不继续沿 rmux/WezTerm UX parity hardening 推进。
- 以 CCB 最新版本 `v8.5.2` 为基底，研究是否可以利用 Herdr 在 Native Windows 平台实现 CCB 全功能。

本地事实需要单独标注：当前工作区 `package.json` 显示 `8.2.1`，但 git tag 已存在 `v8.5.2`，且 `v8.5.2:package.json` 为 `8.5.2`。因此后续若进入实现，应先从 `v8.5.2` tag 或等价 release 基线起步，不应把当前未同步工作区直接视为基底。

## 聊过的方向

### 方向 A：Herdr 作为 CCB 的 Native Windows mux backend

CCB 保持现有控制面、provider 隔离、ask/pend/watch、Mobile、Config UI、更新与诊断体系；Herdr 只承担 Native Windows 下的 session/pane/PTTY/布局/attach 运行时。

价值：最符合 KISS 和最小替换面，避免把 CCB 的 agent 协作控制面重写成 Herdr 插件体系。

代价：需要写一个稳定的 `MuxBackend`/`PaneRuntime` 适配层，把 CCB 当前 tmux/rmux 语义映射到 Herdr socket API。Herdr Windows beta 的不支持项必须显式降级，不能承诺为 fully supported。

### 方向 B：CCB 作为 Herdr 插件或插件集合

把 CCB 的 agent orchestration 投影到 Herdr 插件系统中，让 Herdr 成为用户可见主 shell，CCB 成为控制面/agent 插件。

价值：能复用 Herdr 的 agent detection、session restore 和 UI 机制，用户体验可能更 native。

代价：边界更重。CCB 现有能力不是单纯终端插件：它包含 provider 私有 home、completion 判定、daemon、Mobile relay、config/update/support tier、bounded recovery 等。直接插件化容易出现“双控制面”和“双状态源”。

### 方向 C：复制或嵌入 Herdr Windows terminal primitive

只借用 Herdr 的 ConPTY/Windows pane 低层实现，继续保留 CCB 自己的 mux 行为。

价值：理论上控制权最大。

代价：违反 DRY，后续要跟 Herdr upstream 行为漂移对齐；也会绕开 Herdr 已经提供的 socket API、session state 和 restore 机制。除非 socket API 无法满足 CCB 基础语义，否则不应作为首选。

## 当前倾向

倾向于选择方向 A：Herdr 作为 Native Windows mux backend，CCB 继续作为 control plane 和 provider runtime authority。

这不是“把 Herdr 接上就全功能完成”，而是一个多 feature epic：先验证 Herdr 是否能满足 CCB 的最小 backend contract，再逐步恢复 CCB 的全部 public workflow。第一阶段不应该承诺 stable Windows support，只能以 beta/experimental support tier 起步。

## 已敲定的点

- 已确认：暂停 `windows-rmux-ux-parity-hardening`，不继续在 rmux UX parity 线上投入。
- 已确认：目标基底是 CCB `v8.5.2`，不是当前工作区显示的 `8.2.1` 状态。
- 已确认：这是多 feature 规模，适合后续拆 `cs-epic`，不适合塞进单个 feature。
- 倾向：优先把 Herdr 作为 backend adapter，而不是把 CCB 重写成 Herdr 插件。
- 约束：Native Windows “全功能”应定义为 CCB public workflow parity；Herdr 当前不支持或 beta 的能力必须在 CCB support projection 中明确表达，不能伪装成 Linux/macOS fully supported。

## 遗留问题 & 下一步

- 需要锁定 Herdr 具体版本、安装方式和 socket API schema，避免依赖未稳定文档。
- 需要确认 Herdr socket API 是否覆盖 CCB 需要的 pane create/split/resize/focus/send/capture/kill/session restore/agent status 语义。
- 需要做 5-30 分钟 spike：用 Python 调 Herdr socket API 创建 session、启动一个 provider CLI pane、发送输入、捕获输出、重启后恢复 session。
- 若 spike 通过，进入 `cs-epic` 规划 Native Windows Herdr backend；若失败，记录具体缺口，再决定补 Herdr upstream、保留 rmux 线，或缩小 Native Windows 支持范围。
