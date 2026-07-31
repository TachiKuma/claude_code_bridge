---
doc_type: requirement
slug: native-windows-ccb-via-herdr
pitch: 让 Windows x64 用户不用 WSL，也能完整使用 CCB 的公开工作流
status: draft
last_reviewed: 2026-07-31
implemented_by: []
tags: [windows, herdr, native-windows, providers, support]
---

# 在 Windows x64 上完整使用 CCB

## 用户故事

- 作为 Windows x64 用户，我希望直接在原生 Windows 环境里使用 CCB，而不是为了 tmux 兼容性切到 WSL。
- 作为同时使用多个 AI provider 的开发者，我希望 Codex、Claude、Gemini、Opencode 等公开 provider 都能在 Windows 上完成 ask、pend、completion 和 cancel，而不是每个 provider 支持状态不一致。
- 作为需要远程查看或诊断运行状态的人，我希望 Mobile terminal、Config UI、doctor、ping、mounted 和项目视图都能清楚显示 Windows 后端是否可用，而不是只看到“启动失败”。
- 作为准备把 Windows 路线交给更多用户的人，我希望 CCB 只在真实证据足够时宣称 supported，而不是把 beta、partial 或 blocked 状态包装成正式支持。

## 为什么需要

Windows 用户现在很难获得和 Unix/WSL 用户同等级的 CCB 体验。问题不只是能不能打开一个终端窗口，而是 provider 能不能可靠运行、状态能不能被 CCB 判断、异常能不能恢复、用户界面能不能看懂失败原因、安装和诊断能不能给出一致结论。没有这条能力，Windows 原生路线就只能停留在实验或手工排障阶段，无法成为可信的 supported 入口。

## 怎么解决

CCB 在检测到 Native Windows x64 环境时，把终端承载能力路由到用户自备的 Herdr，并负责检测 Herdr、校验环境、提示缺失项和阻塞原因。所有公开 provider 都必须在 Herdr pane 下完成核心工作流；foreground attach、Mobile terminal、Config UI、doctor、ping、mounted、项目视图、安装 dry-run 和支持等级展示都必须消费同一套证据。只有专用 Windows x64 机器上的完整证据证明核心工作流、用户可见面和发布面 dry-run 都通过时，才允许把这条路线标为 Windows x64 CCB supported。

## 边界

- 只面向 Native Windows x64；不承诺 32-bit Windows、arm64 Windows、WOW64、WSL 或 Linux/macOS 默认路线变化。
- Herdr 由用户自备；CCB 负责检测、诊断和提示，不负责自动下载或安装 Herdr。
- Windows 环境下默认目标是直接走 Herdr；如果 Herdr 缺失、版本不匹配或能力不完整，必须清楚阻塞，而不是静默伪装成功。
- 所有公开 provider 都是支持门槛；不能只用一个 provider 成功来代表整体 supported。
- Mobile terminal 和 Config UI 是 supported 的硬要求；它们 degraded 时不能宣称完整支持。
- Herdr 自动恢复如果不能关闭或不能证明只观察不接管，就阻塞 supported。
- 开工基线必须严格来自 CCB `v8.5.2` 源头并在新分支上推进；当前工作区状态不能直接当实现基线。
- 本能力只要求代码层支持 Windows npm install dry-run；真实 npm 发布、tag、push、release、promotion 仍需要独立授权。
