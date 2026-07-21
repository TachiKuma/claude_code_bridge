---
doc_type: goal-functional-acceptance
goal: "windows-native-backend-capability-validation"
status: pass
reviewer_id: "019f84c3-8eae-7ff1-a4d0-73d92df33724"
final_iteration: "iterations/005.md"
---

# 功能验收

## Reviewer

可见 Task agent：

- 首轮验收：`019f84bf-0380-75a0-bdc6-fc03e8dfa7d4`（nickname: Erdos），verdict 为 fail，阻断项是流程状态与最终证据不一致。
- Focused 复验：`019f84c3-8eae-7ff1-a4d0-73d92df33724`（nickname: Kant），verdict 为 pass。

首轮验收认可技术证据，但要求补齐 goal 状态、iteration 和起点报告的一致性。iteration 004 已修复该流程问题，focused 复验通过。

Task agent 生命周期收尾：`019f84bf-0380-75a0-bdc6-fc03e8dfa7d4` 与 `019f84c3-8eae-7ff1-a4d0-73d92df33724` 均已通过 `close_agent` 关闭，关闭前状态分别保留首轮 fail 与 focused 复验 pass 结果。

## Scope

验收范围是 `windows-native-backend-capability-validation`：

- 验证当前本机 `psmux 3.3.3` capability gate。
- 按 owner 批准的选项 C 临时下载、校验并显式路径运行 `psmux 3.3.7` capability gate。
- 逐项分析 `psmux` required gaps 的修复情况、剩余缺口、workaround 接受条件和对 `ccb` Windows 运行需求的影响。
- 诊断 `rmux 0.9.0` 的安装布局、版本状态、`start-server` / `new-session` stdio capture 超时问题。
- 参考 `D:\Python\GitHub\claude_code_bridge-rmux-capability-gate` v8.0.16 rmux 实现，判断其经验是否能直接证明当前 `rmux 0.9.0` 胜任。
- 给出候选 Windows native backend 基座的证据化结论。

## Acceptance Checks

- `psmux 3.3.7` 下载到 goal evidence 目录，SHA256 与 Winget 元数据一致。
- `psmux 3.3.7` 使用解压目录中的显式 `psmux.exe` 运行 full capability probe。
- `psmux 3.3.7` gate 结果已记录：blocking gaps = 4，剩余 `attach_reattach`、`capture_format_fidelity_for_provider_completion`、`buffer_paste`、`ctrl_c_ctrl_d`。
- `psmux 3.3.7` 相比 `psmux 3.3.3` 的改善已记录：`set-window-option` 和 `user_options_title` 通过。
- `psmux` gap-specific evidence 已记录：paste + explicit submit 可用，`C-c` interrupt 可用，`C-d` 不等价 Windows EOF，attach/reattach 仍需真实前台终端验收。
- `rmux 0.9.0` 诊断已记录：默认 capture runner 下 `start-server` / `new-session` 会超时，`DEVNULL` 或继承 console stdio 可快速返回。
- `rmux 0.9.0` stdio-aware probe 已记录：即使绕过 daemon 启动 stdio 问题，full gate 仍有 8 个 gaps。
- v8.0.16 参考实现已被消费：其 `RmuxRunner capture_output=True`、foreground attach stdio issue、logical EOF 映射和 capability gate 分层都已进入结论。
- 最终结论没有把未通过能力伪装成通过：当前没有候选能无 workaround 直接胜任完整 `ccb` Windows native backend；推荐 `psmux 3.3.7` 作为后续首选候选，`rmux 0.9.0` 作为需重做 runner/lifecycle 后再评估的备选。
- Goal 产物状态已同步：`state.yaml.current_iteration = 5`，final iteration 与本验收报告双向引用。

## Functional Evidence

- `evidence/psmux-337-download/download-verification.json`：`sha256_matches = true`。
- `evidence/psmux-337-download/extracted-inventory.json`：显式路径版本为 `psmux 3.3.7`。
- `evidence/psmux-337/run-20260721T124326Z-6984/capability-report.json`：blocking gaps = 4。
- `evidence/psmux-337-gap-specific.json`：记录 window option、pane/user option、paste、interrupt/EOF 的专项复核。
- `evidence/psmux-337-attach-survival.json`：session survival 成立，但非交互 attach process 不保持前台 client，不能证明完整 UI attach/reattach。
- `evidence/rmux-090-stdio-shape-diagnostics.json`：`new-session` capture 模式超时，`DEVNULL` / inherit stdio 快速返回。
- `evidence/rmux-090-stdio-aware-probe/run-20260721T124903Z-15696/capability-report.json`：stdio-aware 后仍有 8 个 gaps。
- `backend-validation-conclusion.md`：候选排序、需求矩阵、workaround 条件和 verdict 已更新。
- Focused Task agent `019f84c3-8eae-7ff1-a4d0-73d92df33724` 复验 verdict：pass。
- `git diff --check`：通过。
- JSON 校验：`final-backend-candidate-summary.json`、`psmux-337-gap-specific.json`、`rmux-090-stdio-shape-diagnostics.json` 可解析。
- 进程检查：未发现本轮 `rmux` / `psmux` probe namespace 残留进程。

## Verdict

pass。

本 goal 的完成含义是：三条建议均已被证据化验证，并形成候选 backend 是否胜任 `ccb` Windows 运行需求的明确结论。结论不是 capability gate 通过，而是：

- `psmux 3.3.7` 是当前首选候选，但必须带明确 workaround / 后续验收进入设计。
- `rmux 0.9.0` 当前不推荐作为完整基座，除非先重做 stdio-aware lifecycle runner、foreground attach runner、logical EOF 映射，并重新通过完整 gate。
- 当前没有候选能在无 workaround 条件下直接胜任完整 `ccb` Windows native backend。

## Residual Risks

- 未做真实 Windows 前台交互终端 attach/reattach 人工或 UI 自动化验收。
- 未对真实 provider pane 做大文本输入、interrupt、EOF 和 completion workflow 验收。
- 未实现 named pipe、Job Object、provider process tree ownership 或完整 `ccbd` namespace lifecycle。
- 临时 `psmux 3.3.7` 仅在 goal evidence 目录执行，未改变全局安装状态。

## Delivery Record

- Final iteration：`iterations/005.md`。
- 首轮 Task agent 结果已消费；focused 复验结果已消费；两个 Task agent 均已关闭。
