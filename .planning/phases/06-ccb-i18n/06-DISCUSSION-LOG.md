# Phase 6: CCB i18n 实施 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 06-ccb-i18n
**Areas discussed:** Skill 模板范围, Install 脚本补漏, CLI help 文本 i18n, Config 模板策略

---

## Skill 模板范围

| Option | Description | Selected |
|--------|-------------|----------|
| 仅元数据 + 用法说明 | 只翻译 short-description 和 description 字段，AI 指令保持英文 | |
| 全量翻译 | 翻译 SKILL.md 的全部内容，包括 AI 指令 | ✓ |
| CLI 层翻译显示名 | 保持 SKILL.md 英文不变，CLI 层显示时翻译 | |

**User's choice:** 全量翻译
**Notes:** 用户要求 12 个 SKILL.md 模板全部翻译。实现方式建议提供双语版本文件。

---

## Install 脚本补漏

| Option | Description | Selected |
|--------|-------------|----------|
| 全量迁移 + 统一前缀 | 所有硬编码字符串提取到 Get-Msg，Write-Warning 改为 Write-Host | ✓ |
| 仅高频消息 | 只迁移高频用户消息 | |
| 保持现状 | 接受 PowerShell 系统前缀的混合输出 | |

**User's choice:** 全量迁移 + 统一前缀
**Notes:** 用户提供的 install.ps1 输出显示 "警告:" 前缀来自 PowerShell Write-Warning 系统行为。需要将 Write-Warning 改为 Write-Host "[WARNING] ..." 以统一控制。install.sh 同步处理。

---

## CLI help 文本 i18n

| Option | Description | Selected |
|--------|-------------|----------|
| 全量 t() 包裹 | 所有 argparse description/help= 替换为 t() 调用 | ✓ |
| 延迟替换 | --help 输出时替换文本，不修改 argparse 定义 | |

**User's choice:** 全量 t() 包裹
**Notes:** 需要处理 parser 构建时机问题——当前 argparse 在语言检测前构建。可通过延迟构建或 t() 函数延迟求值解决。

---

## Config 模板策略

| Option | Description | Selected |
|--------|-------------|----------|
| 混合翻译 | 用户可见说明翻译，代码块/JSON schema/命令示例保持英文 | ✓ |
| 双版本文件 | 提供完整中英两份文件，安装时选择 | |
| 不翻译 | 纯英文，因为注入的是给 AI 看的指令 | |

**User's choice:** 混合翻译
**Notes:** Config 模板中的说明文本和注释需要翻译，但代码块和技术命令保持英文确保可复制性。

---

## Claude's Discretion

翻译 key 命名空间细分、Skill 双语文件命名约定、argparse t() 实现方式、盘占脚本实现等由实现决定。

## Deferred Ideas

无新 deferred ideas。
