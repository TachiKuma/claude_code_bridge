# Attention

本文件是 CodeStable 技能启动必读的项目注意事项入口。所有 CodeStable 子技能开始工作前必须读取它。

## 报告语言

CodeStable 所有落盘产出的正文用**中文**：plan / design、plan review / design-review、code review、QA、验收、issue（report / analysis / fix-note）、refactor、roadmap、goal、沉淀（compound）等所有人读报告都用中文表达。机器状态（YAML / JSON / `state.yaml` / frontmatter 字段）保持机读格式不翻译。如需改默认语言，改这一节。

关键节点的交流提交也使用中文：需求确认、路线拆解、设计结论、实施检查点、验证结果、风险/阻塞和收尾报告都要优先用中文表达，方便项目内协作。这里的“提交”指面向人读的阶段性汇报或工作流产物；`git commit` 可在用户明确授权时自动执行，但默认不自动提交；`git push` 仍禁止。提交摘要和描述尽量中文，可适当夹带英文术语。

## 代码索引优先

查看或修改代码前，先用 CodeGraph 查找相关符号、调用关系、影响面或文件结构；当 CodeGraph 精度不足、索引未覆盖目标或需要核对字面内容时，再直接读取源码文件。读取普通文档、配置和 CodeStable 工作流资产时可按需直接打开文件。

CodeGraph 项目规则已将 `.codestable/**/*.md` 纳入 include。当前本机 CodeGraph 0.7.9 尚未提供 Markdown grammar，索引结果因此只能覆盖其中的代码文件；在工具升级支持 Markdown 文件节点前，不得把该规则误报为已完成全文/符号索引。

## 项目碎片知识

<!-- cs-note managed: 用 cs-note 维护，新条目按下面分节追加 -->

### 编译与构建

### 运行与本地起服务

### 测试

### 命令与脚本陷阱

- 跑 `.codestable` 下 cs 工具脚本（如 `codestable-workflow-next.py`）前先 `export PYTHONDONTWRITEBYTECODE=1`；否则脚本第 16 行 `os.execvpe` 自我重执行在本机 Python 3.14 + Windows 触发 access violation（段错误 exit 139）。

### 路径与目录约定

### 环境变量与凭证

### 其他

- Herdr dispatch 结构化原语后续迭代必须先核对现有边界：`dispatch` 在本项目同时可能指 CCB job dispatcher、legacy topology dispatch、Herdr agent activation。`ccb herdr dispatch` 只能作为 Herdr terminal agent activation primitive 设计，不得拥有 job / queue / completion / cancel 权威，不得复活 topology communication DSL；当前代码状态标记见 `.codestable/epics/windows-native-herdr-ccb.md` 的 ITEM-8 和 `.codestable/lessons/2026-08-10-herdr-dispatch-interactive-terminal.md`。
