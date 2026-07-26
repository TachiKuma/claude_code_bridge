# Attention

本文件是 CodeStable 技能启动必读的项目注意事项入口。所有 CodeStable 子技能开始工作前必须读取它。

## 报告语言

CodeStable 所有落盘产出的正文用**中文**：plan / design、plan review / design-review、code review、QA、验收、issue（report / analysis / fix-note）、refactor、roadmap、goal、沉淀（compound）等所有人读报告都用中文表达。机器状态（YAML / JSON / `state.yaml` / frontmatter 字段）保持机读格式不翻译。如需改默认语言，改这一节。

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
