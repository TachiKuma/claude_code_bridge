# Phase 1: 代码库分析 - Research

**Researched:** 2026-03-28
**Domain:** 代码库静态分析与 i18n 文本分类
**Confidence:** HIGH

## Summary

Phase 1 的核心任务是识别 CCB（Python，98 文件，~27,443 行）和 GSD（JavaScript，18 文件，~11,651 行）中所有需要国际化的文本，并区分人类可读文本和协议字符串。这是可行性研究的基础，为后续架构设计提供数据支撑。

关键发现：
- CCB 已有基础 i18n 实现（`lib/i18n.py`），使用字典方案，支持中英文
- 协议字符串（如 `CCB_DONE`、`ask.response`）在 CCB 中出现 94+ 次，必须与人类文本严格隔离
- 需要使用 AST 静态分析确保完整覆盖，避免遗漏动态生成的字符串

**Primary recommendation:** 使用 Python `ast` 模块和 JavaScript `@babel/parser` 进行 AST 静态分析，按文件生成分类报告，为 Phase 2 架构设计提供准确的数据基础。

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ANALYSIS-01 | 扫描 CCB 代码库，识别所有硬编码文本位置 | Python AST 分析工具，遍历 98 个 .py 文件 |
| ANALYSIS-02 | 扫描 GSD 代码库，识别所有硬编码文本位置 | JavaScript AST 分析工具（@babel/parser），遍历 18 个 .js/.cjs 文件 |
| ANALYSIS-03 | 区分人类可读文本和协议字符串 | 基于命名模式的分类规则（全大写、特定前缀/后缀） |
| ANALYSIS-04 | 评估现有 CCB i18n.py 的可复用性和扩展性 | API 设计、性能、扩展性三维度分析 |

</phase_requirements>

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 使用 AST 静态分析（Python ast 模块）扫描代码库
- **D-02:** 分析语法树中的所有字符串节点，确保完整覆盖
- **D-03:** 扫描范围：CCB 的 98 个 Python 文件（~27,443 行）+ GSD 代码库（18 个 JS 文件，~11,651 行）
- **D-04:** 基于命名模式区分协议字符串和人类文本
- **D-05:** 协议字符串特征：全大写、特定前缀（CCB_、GSD_）、特定后缀（_DONE）
- **D-06:** 人类文本：其他所有字符串（用户界面、错误消息、日志等）
- **D-07:** 生成 Markdown 报告，按文件分组
- **D-08:** 每个条目包含：文件路径、行号、文本内容、分类（协议/人类）、上下文代码片段
- **D-09:** CCB i18n.py 可复用性评估包含三个维度：API 设计、性能、扩展性

### Claude's Discretion
- 具体的 AST 遍历算法实现
- Markdown 报告的具体排版样式
- 性能测试的具体方法

### Deferred Ideas (OUT OF SCOPE)
- 自动语言检测和用户切换功能 — 属于 Phase 2（架构设计）范畴
- 实际的翻译工作 — 超出可行性研究范围，属于完整实施阶段

</user_constraints>

## Standard Stack

### Core Technologies

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ast (stdlib) | Python 3.10+ | Python 代码 AST 解析 | 标准库，零依赖，完整的语法树访问 |
| @babel/parser | 7.24+ | JavaScript 代码 AST 解析 | 行业标准 JS 解析器，支持最新语法 |
| @babel/traverse | 7.24+ | AST 遍历与节点访问 | 与 @babel/parser 配套，简化遍历逻辑 |

### Supporting Tools

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | Python 3.10+ | 文件路径操作 | 跨平台路径处理 |
| json (stdlib) | Python 3.10+ | 数据序列化 | 中间结果存储 |
| re (stdlib) | Python 3.10+ | 正则表达式匹配 | 协议字符串模式识别 |

### Installation

```bash
# Python 部分（使用标准库，无需安装）
python3 --version  # 确认 3.10+

# JavaScript 部分（用于 GSD 分析）
npm install @babel/parser@^7.24.0 @babel/traverse@^7.24.0
```

**Version verification:**
```bash
# Python ast 是标准库，版本跟随 Python
python3 -c "import ast; print(ast.__doc__[:50])"

# Babel 版本验证
npm view @babel/parser version  # 当前最新: 7.24.5 (2024-04)
npm view @babel/traverse version  # 当前最新: 7.24.5 (2024-04)
```

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ast (Python) | libcst | libcst 保留格式信息，但对于文本提取任务，ast 已足够且零依赖 |
| @babel/parser | esprima | esprima 更轻量，但 Babel 生态更完善，支持最新 JS 语法 |
| 手动正则提取 | AST 分析 | 正则快速但易遗漏（字符串拼接、模板字符串、动态生成），AST 保证完整性 |

## Architecture Patterns

### Recommended Project Structure

```
.planning/phases/01-代码库分析/
├── analysis-tools/          # 分析脚本
│   ├── scan_ccb.py         # CCB Python 代码扫描器
│   ├── scan_gsd.js         # GSD JavaScript 代码扫描器
│   └── classify.py         # 协议/人类文本分类器
├── results/                 # 扫描结果
│   ├── ccb_strings.json    # CCB 提取的所有字符串
│   ├── gsd_strings.json    # GSD 提取的所有字符串
│   └── classified.json     # 分类后的结果
└── 01-ANALYSIS-REPORT.md   # 最终分析报告
```

### Pattern 1: AST 遍历提取字符串

**What:** 使用 Visitor 模式遍历 AST，提取所有字符串字面量节点

**When to use:** 需要完整、准确地识别代码中的所有硬编码文本

**Example (Python):**
```python
import ast

class StringExtractor(ast.NodeVisitor):
    def __init__(self):
        self.strings = []

    def visit_Str(self, node):  # Python 3.7-
        self.strings.append({
            'value': node.s,
            'line': node.lineno,
            'col': node.col_offset
        })

    def visit_Constant(self, node):  # Python 3.8+
        if isinstance(node.value, str):
            self.strings.append({
                'value': node.value,
                'line': node.lineno,
                'col': node.col_offset
            })
        self.generic_visit(node)

# 使用
with open('file.py', 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read(), filename='file.py')
extractor = StringExtractor()
extractor.visit(tree)
```

**Example (JavaScript):**
```javascript
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const fs = require('fs');

const code = fs.readFileSync('file.js', 'utf-8');
const ast = parser.parse(code, { sourceType: 'module' });

const strings = [];
traverse(ast, {
  StringLiteral(path) {
    strings.push({
      value: path.node.value,
      line: path.node.loc.start.line,
      col: path.node.loc.start.column
    });
  },
  TemplateLiteral(path) {
    // 处理模板字符串
    path.node.quasis.forEach(quasi => {
      if (quasi.value.raw) {
        strings.push({
          value: quasi.value.raw,
          line: quasi.loc.start.line,
          col: quasi.loc.start.column,
          type: 'template'
        });
      }
    });
  }
});
```

### Pattern 2: 协议字符串识别规则

**What:** 基于命名模式自动分类协议字符串和人类文本

**When to use:** 需要区分机器协议标记和用户可见文本

**Example:**
```python
import re

def classify_string(text: str, context: dict) -> str:
    """
    分类字符串为 'protocol' 或 'human'

    Args:
        text: 字符串内容
        context: 上下文信息（变量名、函数名等）

    Returns:
        'protocol' 或 'human'
    """
    # 协议字符串特征
    protocol_patterns = [
        r'^[A-Z_]+$',              # 全大写：CCB_DONE, ASK_RESPONSE
        r'^CCB_[A-Z_]+$',          # CCB 前缀
        r'^GSD_[A-Z_]+$',          # GSD 前缀
        r'_DONE$',                 # 完成标记后缀
        r'^ask\.[a-z_]+$',         # RPC 协议：ask.response
        r'^\.[a-z_]+$',            # 文件扩展名：.json, .md
    ]

    for pattern in protocol_patterns:
        if re.match(pattern, text):
            return 'protocol'

    # 环境变量名（通常是协议）
    if context.get('is_env_var'):
        return 'protocol'

    # JSON 键名（需要进一步判断）
    if context.get('is_json_key'):
        # 如果键名是全大写或包含下划线，可能是协议
        if text.isupper() or '_' in text:
            return 'protocol'

    # 默认为人类文本
    return 'human'
```

### Pattern 3: 上下文感知提取

**What:** 提取字符串时同时记录上下文信息（变量名、函数调用、赋值目标）

**When to use:** 需要更准确地判断字符串用途

**Example:**
```python
class ContextAwareExtractor(ast.NodeVisitor):
    def visit_Assign(self, node):
        # 检测环境变量赋值：os.environ['CCB_LANG']
        if isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    if self._is_environ_access(target):
                        # 这是环境变量名，标记为协议
                        pass
        self.generic_visit(node)

    def _is_environ_access(self, node):
        return (isinstance(node.value, ast.Attribute) and
                node.value.attr == 'environ')
```

### Anti-Patterns to Avoid

- **手动正则提取字符串:** 会遗漏字符串拼接、f-string、模板字符串等复杂情况
- **忽略注释中的文本:** 注释也可能需要翻译（文档字符串、用户帮助）
- **假设所有大写字符串都是协议:** 某些人类文本也可能全大写（如 "ERROR", "WARNING"）
- **不记录上下文:** 仅凭字符串内容无法准确分类，需要结合使用场景

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| AST 解析 | 自定义正则表达式解析器 | ast (Python), @babel/parser (JS) | 语言语法复杂，正则无法处理嵌套、转义、多行字符串 |
| 文件遍历 | 手动递归目录 | pathlib.rglob(), glob.glob() | 标准库已优化，处理符号链接、权限等边界情况 |
| 字符编码检测 | 自己实现编码猜测 | chardet 库或假设 UTF-8 | 编码检测复杂，标准库 open() 默认 UTF-8 已足够 |
| Markdown 生成 | 字符串拼接 | 模板引擎或简单格式化 | 手动拼接易出错，难以维护 |

**Key insight:** 代码分析是已解决的问题，使用成熟的 AST 工具而非重新发明轮子。重点应放在分类逻辑和报告生成上。

## Common Pitfalls

### Pitfall 1: 遗漏动态生成的字符串
**What goes wrong:** AST 只能捕获字面量，无法识别运行时拼接的字符串
**Why it happens:** 字符串通过 + 拼接、f-string 变量、模板字符串
**How to avoid:** 扫描时标记拼接操作，人工审查拼接模式
**Warning signs:** 扫描结果中出现不完整句子片段

### Pitfall 2: 协议字符串误分类
**What goes wrong:** 将协议标记误判为人类文本，或反之
**Why it happens:** 分类规则过于简单，缺乏上下文信息
**How to avoid:** 结合上下文分析，建立协议字符串白名单
**Warning signs:** 环境变量名出现在"人类文本"列表中

### Pitfall 3: 忽略文档字符串和注释
**What goes wrong:** 只扫描字符串字面量，忽略文档和注释
**Why it happens:** 认为注释"不需要翻译"
**How to avoid:** 明确决策哪些注释需要翻译，提取文档字符串
**Warning signs:** --help 输出未翻译

### Pitfall 4: 文件编码问题
**What goes wrong:** 扫描工具因编码错误崩溃或产生乱码
**Why it happens:** 假设所有文件都是 UTF-8
**How to avoid:** 使用 errors='ignore' 或 errors='replace'
**Warning signs:** 提取的字符串包含 � 替换字符

### Pitfall 5: CCB i18n.py 评估不全面
**What goes wrong:** 仅评估 API 设计，忽略性能和扩展性
**Why it happens:** 现有实现"看起来能用"
**How to avoid:** 三维度评估（API、性能、扩展性），基准测试
**Warning signs:** 评估报告没有性能数据


## Code Examples

### Example 1: Python 字符串扫描器
```python
import ast
import json
from pathlib import Path

class StringExtractor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.strings = []
        
    def visit_Constant(self, node):
        if isinstance(node.value, str) and node.value.strip():
            self.strings.append({
                'file': self.filepath,
                'line': node.lineno,
                'value': node.value
            })
        self.generic_visit(node)

def scan_directory(root):
    results = []
    for py_file in Path(root).rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            extractor = StringExtractor(str(py_file))
            extractor.visit(tree)
            results.extend(extractor.strings)
        except Exception as e:
            print(f"Error: {py_file}: {e}")
    return results
```

### Example 2: 协议字符串分类器
```python
import re

PROTOCOL_PATTERNS = [
    r'^[A-Z_]{3,}$',
    r'^CCB_[A-Z_]+$',
    r'^GSD_[A-Z_]+$',
    r'_DONE$',
    r'^ask\.[a-z_]+$',
]

def classify_string(text):
    if not text.strip() or len(text) == 1:
        return 'ignore'
    for pattern in PROTOCOL_PATTERNS:
        if re.match(pattern, text):
            return 'protocol'
    return 'human'
```

### Example 3: i18n.py 性能基准
```python
import time
from i18n import t, MESSAGES

def benchmark_lookup(iterations=10000):
    keys = list(MESSAGES['en'].keys())
    start = time.perf_counter()
    for _ in range(iterations):
        for key in keys:
            _ = t(key)
    elapsed = time.perf_counter() - start
    total = iterations * len(keys)
    print(f"Lookups/sec: {total/elapsed:.0f}")
```


## Environment Availability

Phase 1 仅依赖标准库和 Node.js 生态，无外部服务依赖。

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | CCB 扫描脚本 | ✓ | 3.10+ | — |
| Node.js 18+ | GSD 扫描脚本 | ✓ | 18+ | — |
| npm | Babel 安装 | ✓ | 9+ | — |

**Missing dependencies:** 无

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | pytest.ini（Wave 0 创建） |
| Quick run command | `pytest tests/test_scanner.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANALYSIS-01 | CCB 扫描器提取所有字符串 | unit | `pytest tests/test_ccb_scanner.py -x` | ❌ Wave 0 |
| ANALYSIS-02 | GSD 扫描器提取所有字符串 | unit | `node tests/test_gsd_scanner.js` | ❌ Wave 0 |
| ANALYSIS-03 | 分类器正确区分协议/人类文本 | unit | `pytest tests/test_classifier.py -x` | ❌ Wave 0 |
| ANALYSIS-04 | i18n.py 性能基准达标 | integration | `python tests/benchmark_i18n.py` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `tests/test_ccb_scanner.py` — 覆盖 ANALYSIS-01
- [ ] `tests/test_gsd_scanner.js` — 覆盖 ANALYSIS-02
- [ ] `tests/test_classifier.py` — 覆盖 ANALYSIS-03
- [ ] `tests/benchmark_i18n.py` — 覆盖 ANALYSIS-04
- [ ] `pytest.ini` — pytest 配置


## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手动 grep 查找字符串 | AST 静态分析 | 2020+ | 完整性保证，捕获所有字面量 |
| 硬编码字典翻译 | gettext + Babel | 2015+ | 工具链支持，标准化流程 |
| 单一 i18n 库 | 命名空间隔离 | 2022+ | 避免多库冲突 |

**Deprecated/outdated:**
- 手动正则提取 — 无法处理复杂语法
- 直接修改源码添加翻译 — 现代工具链使用消息目录

## Open Questions

1. **GSD 中是否有动态生成的用户消息？**
   - What we know: GSD 使用模板系统生成提示词
   - What's unclear: 模板中的占位符是否需要特殊处理
   - Recommendation: 扫描后人工审查模板文件

2. **CCB 中的日志消息是否需要翻译？**
   - What we know: 当前日志全部英文
   - What's unclear: 用户是否需要看到翻译后的日志
   - Recommendation: 区分用户可见日志和开发者调试日志

3. **协议字符串的完整列表是否需要文档化？**
   - What we know: 当前无集中文档
   - What's unclear: 是否需要维护"不可翻译列表"
   - Recommendation: 在 Phase 2 创建协议字符串注册表


## Sources

### Primary (HIGH confidence)
- Python ast module documentation — https://docs.python.org/3/library/ast.html
- Babel Parser documentation — https://babeljs.io/docs/babel-parser
- CCB 现有代码库 lib/i18n.py — 实际实现分析

### Secondary (MEDIUM confidence)
- Real Python: Python AST Guide — https://realpython.com/python-ast-guide/
- Babel Handbook — https://github.com/jamiebuilds/babel-handbook

### Tertiary (LOW confidence)
- 项目研究文档 .planning/research/PITFALLS.md — 协议字符串风险

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 使用标准库和成熟工具
- Architecture: HIGH — AST 分析是已验证的方法
- Pitfalls: HIGH — 基于项目研究和行业最佳实践

**Research date:** 2026-03-28
**Valid until:** 2026-06-28（90 天，技术栈稳定）

---

*Research complete for Phase 1: 代码库分析*
*Ready for planning*
