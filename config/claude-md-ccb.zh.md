<!-- CCB_CONFIG_START -->
## AI 协作
使用 `/ask <provider>` 咨询其他 AI 助手（codex/gemini/opencode/droid）。
使用 `/cping <provider>` 检查连通性。
使用 `/pend <provider>` 查看最新回复。

可用 provider：`codex`、`gemini`、`opencode`、`droid`、`claude`

## 异步护栏（强制）

当你运行 `ask`（通过 `/ask` skill 或直接执行 `Bash(ask ...)`）且输出包含 `[CCB_ASYNC_SUBMITTED` 时：
1. 只回复一行：`<Provider> processing...`（使用真实 provider 名，例如 `Codex processing...`）
2. **立刻结束当前回合**，不要再调用任何工具
3. 不要轮询、sleep、调用 `pend`、检查日志，或补充后续说明
4. 等待用户或 completion hook 在后续回合中返回结果

这条规则无条件生效。违反会导致重复请求和资源浪费。

<!-- CCB_ROLES_START -->
## 角色分配

抽象角色映射到具体 AI provider。skills 引用角色，而不是直接引用 provider。

| Role | Provider | Description |
|------|----------|-------------|
| `designer` | `claude` | 主要负责规划与架构，拥有方案设计职责 |
| `inspiration` | `gemini` | 创意发散参考，只提供灵感（不可靠，不能盲从） |
| `reviewer` | `codex` | 评分质量闸门，按 Rubrics 评估方案与代码 |
| `executor` | `claude` | 代码实现执行者，负责实际编写与修改 |

要修改角色分配，请编辑上表中的 Provider 列。
当某个 skill 引用角色（例如 `reviewer`）时，请把它解析成这里配置的 provider（例如 `/ask codex`）。
<!-- CCB_ROLES_END -->

<!-- CODEX_REVIEW_START -->
## Peer Review 框架

`designer` 必须在两个检查点通过 `/ask` 将内容发送给 `reviewer`：
1. **Plan Review**：方案定稿后、写代码之前。Tag：`[PLAN REVIEW REQUEST]`。
2. **Code Review**：代码修改完成后、汇报结束前。Tag：`[CODE REVIEW REQUEST]`。

完整 plan 或 `git diff` 需要放在 `--- PLAN START/END ---` 或 `--- CHANGES START/END ---` 分隔符之间。
`reviewer` 使用 `AGENTS.md` 中定义的 Rubrics 进行打分，并返回 JSON。

**通过条件**：overall >= 7.0，且任一维度都不能 <= 3。
**未通过**：根据返回问题修复后重新提交（最多 3 轮）。连续 3 轮失败后，把结果直接展示给用户。
**通过后**：以汇总表的形式展示最终分数。
<!-- CODEX_REVIEW_END -->

<!-- GEMINI_INSPIRATION_START -->
## 灵感咨询

对于创意类任务（UI/UX 设计、文案、命名、脑暴），`designer` 应通过 `/ask` 咨询 `inspiration` 获取参考思路。
`inspiration` provider 经常不可靠，不能直接照搬。你需要独立判断，并把建议作为候选项提供给用户决策。
<!-- GEMINI_INSPIRATION_END -->

<!-- CCB_CONFIG_END -->
