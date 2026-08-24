# 领域文档

工程技能在探索代码库时如何消费本仓库的领域文档。

## 探索前先读

- 仓库根 `CONTEXT.md`，或
- 仓库根 `CONTEXT-MAP.md`（若存在）：它指向每个上下文各一份 `CONTEXT.md`。阅读与主题相关的每一份。
- `docs/adr/`：阅读即将工作区域相关的 ADR。多上下文仓库还需检查 `src/<context>/docs/adr/` 下的上下文级决策。

若上述文件不存在，**静默继续**。不要标记缺失，也不要主动建议立即创建。`/domain-modeling` 技能（经 `/grill-with-docs` 与 `/improve-codebase-architecture` 触达）会在术语或决策真正需要落定时惰性创建。

## 文件结构

单上下文仓库（大多数仓库）：

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-xxx.md
│   └── 0002-yyy.md
└── src/
```

多上下文仓库（根存在 `CONTEXT-MAP.md` 时）：

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← 系统级决策
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← 上下文级决策
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## 使用术语表的词汇

当输出命名领域概念（issue 标题、重构提案、假设、测试名）时，使用 `CONTEXT.md` 中定义的术语。不要漂移到术语表明确回避的同义词。

若所需概念尚未出现在术语表，这是一个信号：要么你在发明项目未使用的语言（重新考虑），要么存在真实缺口（记下来交给 `/domain-modeling`）。

## 标记 ADR 冲突

若输出与既有 ADR 冲突，显式指出而不是静默覆盖：

> _与 ADR-0007（xxx）冲突，但值得重新讨论，因为…_
