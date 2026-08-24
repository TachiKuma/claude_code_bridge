# 工单跟踪：本地 Markdown

本仓库的 issue 与 spec 以 Markdown 文件存放在 `.scratch/` 下。

## 约定

- 每个功能一个目录：`.scratch/<feature-slug>/`
- spec 为 `.scratch/<feature-slug>/spec.md`
- 实现工单是每个 ticket 一个文件，位于 `.scratch/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 开始编号，不使用单一合并 tickets 文件
- triage 状态记录在 issue 文件顶部附近的 `Status:` 行（角色字符串见 `triage-labels.md`）
- 评论与对话历史以 `## Comments` 标题追加到文件底部

## 当技能说「发布到 issue tracker」时

在 `.scratch/<feature-slug>/` 下创建新文件（目录不存在时一并创建）。

## 当技能说「获取相关 ticket」时

读取引用路径对应的文件。用户通常会直接给出路径或 issue 编号。

## 路径查找操作（供 `/wayfinder` 使用）

**Map** 是一个文件，每个 ticket 对应一个子文件。

- **Map**：`.scratch/<effort>/map.md`（Notes / Decisions-so-far / Fog 正文）
- **子 ticket**：`.scratch/<effort>/issues/NN-<slug>.md`，从 `01` 编号，问题写在正文；`Type:` 行记录 ticket 类型（`research`/`prototype`/`grilling`/`task`）；`Status:` 行记录 `claimed`/`resolved`
- **阻塞**：顶部附近的 `Blocked by: NN, NN` 行；当它列出的每个文件都是 `resolved` 时 ticket 解除阻塞
- **前沿扫描**：扫描 `.scratch/<effort>/issues/`，找开放、未阻塞、未认领的文件；编号最小者优先
- **认领**：开始工作前先把 `Status: claimed` 并保存
- **解决**：在 `## Answer` 标题下追加答案，置 `Status: resolved`，再把上下文指针（gist + 链接）追加到 map.md 的 Decisions-so-far
