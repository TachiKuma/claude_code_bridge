# 协议字符串保护机制设计

**设计日期:** 2026-03-28
**Phase:** 02-架构设计
**需求:** ARCH-04
**状态:** 设计完成

---

## 1. 机制概述

### 目标
防止协议字符串被错误翻译，导致跨进程通信失败。

### 范围
- 所有翻译文件：`lib/i18n/**/*.json`
- 外部翻译文件：`~/.ccb/i18n/**/*.json`（可选检查）

### 方法
CI 自动检查 + 白名单对照（per D-12, D-13, D-14）

### 协议字符串定义
协议字符串是用于系统内部通信的标识符，包括：
- 环境变量名（如 `CCB_LANG`, `CCB_DONE`）
- 命令名称（如 `ask`, `cpend`, `ccb-mounted`）
- 完成标记（如 `ask.response`, `CCB_DONE`）
- 文件路径和扩展名（如 `.planning`, `.md`, `.json`）
- Git 引用（如 `HEAD`, `main`）
- JSON 键名（如 `phase`, `plan`, `type`）
- 配置键（如 `gsd_state_version`, `status`）

---

## 2. 白名单文件设计（per D-13）

### 位置
`.planning/protocol_whitelist.json`

### 格式
JSON 格式，按类别组织：

```json
{
  "version": "1.0",
  "description": "CCB 协议字符串白名单 - 这些字符串永不翻译",
  "last_updated": "2026-03-28",
  "total_count": 287,
  "categories": {
    "env_vars": ["CCB_LANG", "CCB_DONE", ...],
    "command_names": ["ask", "cask", "cpend", ...],
    "completion_markers": ["ask.response", "CCB_DONE", ...],
    "file_paths": [".planning", ".md", ".json", ...],
    "git_refs": ["HEAD", "main", "master"],
    "json_keys": ["phase", "plan", "type", ...],
    "config_keys": ["gsd_state_version", "status", ...]
  }
}
```

### 总数
287 个协议字符串（基于 Phase 1 分析结果）

### 维护
- 手动更新
- 新增协议字符串时同步添加到对应分类
- 更新 `total_count` 和 `last_updated` 字段

---

## 3. CI 检查脚本设计

### 脚本位置
`scripts/check_protocol_strings.py`

### 核心逻辑

```python
#!/usr/bin/env python3
"""检查翻译文件中是否包含协议字符串"""
import json
import sys
from pathlib import Path

def load_protocol_whitelist():
    """加载协议字符串白名单"""
    whitelist_path = Path(".planning/protocol_whitelist.json")
    with open(whitelist_path, encoding="utf-8") as f:
        data = json.load(f)

    # 提取所有协议字符串到集合
    protocol_strings = set()
    for category, strings in data["categories"].items():
        protocol_strings.update(strings)

    return protocol_strings

def check_translation_file(file_path, protocol_strings):
    """检查单个翻译文件"""
    errors = []

    try:
        with open(file_path, encoding="utf-8") as f:
            translations = json.load(f)
    except json.JSONDecodeError as e:
        return [f"JSON 解析失败: {e}"]

    # 检查每个翻译值
    for key, value in translations.items():
        if value in protocol_strings:
            errors.append({
                "key": key,
                "value": value,
                "reason": "协议字符串不应被翻译"
            })

    return errors

def main():
    """主函数"""
    # 1. 加载白名单
    protocol_strings = load_protocol_whitelist()
    print(f"✓ 加载了 {len(protocol_strings)} 个协议字符串")

    # 2. 扫描所有翻译文件
    translation_files = list(Path("lib/i18n").rglob("*.json"))
    print(f"✓ 找到 {len(translation_files)} 个翻译文件")

    # 3. 检查每个文件
    all_errors = {}
    for trans_file in translation_files:
        errors = check_translation_file(trans_file, protocol_strings)
        if errors:
            all_errors[str(trans_file)] = errors

    # 4. 报告结果
    if all_errors:
        print("\n❌ 协议字符串保护检查失败:\n")
        for file_path, errors in all_errors.items():
            print(f"  文件: {file_path}")
            for error in errors:
                if isinstance(error, dict):
                    print(f"    键 '{error['key']}' 的值 '{error['value']}' 是协议字符串")
                else:
                    print(f"    {error}")
        sys.exit(1)

    print("\n✓ 协议字符串保护检查通过")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 4. 检查范围

### 内置翻译
- 路径：`lib/i18n/**/*.json`
- 包括所有命名空间：`ccb/`, `common/`
- 递归扫描所有 JSON 文件

### 外部翻译（可选）
- 路径：`~/.ccb/i18n/**/*.json`
- 仅在 CI 环境中检查内置翻译
- 用户自定义翻译由用户负责

### 排除文件
- `.planning/protocol_whitelist.json` 本身
- 非翻译文件（如配置文件）

---

## 5. 错误检测逻辑

### 检查条件
翻译文件中的**值**（value）是否在白名单中

### 正常情况
翻译值是人类可读文本，不在白名单中

### 错误情况
翻译值是协议字符串（如 `"CCB_DONE"`），在白名单中

### 示例

**错误示例：**
```json
// lib/i18n/ccb/zh.json
{
  "ccb.env.lang": "CCB_LANG"  // ❌ 错误：CCB_LANG 是环境变量名
}
```

**正确示例：**
```json
// lib/i18n/ccb/zh.json
{
  "ccb.env.lang_desc": "语言设置环境变量"  // ✓ 正确：描述性文本
}
```

### 不检查的内容
- 翻译键名（key）— 键名可以包含协议相关词汇
- 注释和元数据
- 参数占位符（如 `{provider}`）

---

## 6. CI 集成方案（per D-14）

### 方案 A: GitHub Actions（推荐）

**配置文件：** `.github/workflows/i18n-check.yml`

```yaml
name: i18n Protocol Check

on:
  pull_request:
    paths:
      - 'lib/i18n/**/*.json'
      - '.planning/protocol_whitelist.json'
  push:
    branches:
      - main

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Check protocol strings
        run: python scripts/check_protocol_strings.py
```

**触发条件：**
- PR 修改了翻译文件或白名单
- 推送到 main 分支

**优势：**
- 自动运行，无需手动触发
- PR 合并前强制检查
- 集成到 GitHub 状态检查

### 方案 B: pre-commit hook（本地检查）

**配置文件：** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: check-protocol-strings
        name: Check protocol strings in translations
        entry: python scripts/check_protocol_strings.py
        language: system
        files: ^lib/i18n/.*\.json$
        pass_filenames: false
```

**触发条件：**
- 提交包含翻译文件修改

**优势：**
- 本地快速反馈
- 减少 CI 失败次数
- 开发时即时发现问题

### 推荐方案
**同时使用两种方案：**
- pre-commit hook：本地开发时快速反馈
- GitHub Actions：PR 合并前强制检查（per D-14）

---

## 7. 阻止合并机制（per D-14）

### GitHub 分支保护规则

**配置步骤：**
1. 进入仓库 Settings → Branches
2. 添加分支保护规则（main 分支）
3. 启用 "Require status checks to pass before merging"
4. 选择 "i18n Protocol Check" 作为必需检查

**效果：**
- CI 检查失败时，PR 状态为 "failed"
- 无法合并 PR，直到检查通过
- 强制开发者修复错误后重新提交

### 本地 pre-commit 强制

**安装 pre-commit：**
```bash
pip install pre-commit
pre-commit install
```

**效果：**
- 提交前自动运行检查
- 检查失败时阻止提交
- 开发者必须修复后才能提交

---

## 8. 错误修复流程

### 当 CI 检查失败时

**步骤 1: 查看错误报告**
```
❌ 协议字符串保护检查失败:

  文件: lib/i18n/ccb/zh.json
    键 'ccb.command.ask' 的值 'ask' 是协议字符串
```

**步骤 2: 判断问题类型**

**情况 A: 误用翻译函数**
```python
# 错误做法
print(t("ccb.command.ask"))  # 翻译为 "ask"

# 正确做法
ASK_COMMAND = "ask"  # 使用常量
print(t("ccb.command.ask_desc", cmd=ASK_COMMAND))  # 翻译为 "使用 {cmd} 命令"
```

**情况 B: 翻译值错误**
```json
// 错误
{
  "ccb.env.lang": "CCB_LANG"
}

// 正确
{
  "ccb.env.lang_desc": "语言设置环境变量"
}
```

**步骤 3: 修复并重新提交**
```bash
# 修改翻译文件
vim lib/i18n/ccb/zh.json

# 本地测试
python scripts/check_protocol_strings.py

# 提交修复
git add lib/i18n/ccb/zh.json
git commit -m "fix: 移除协议字符串翻译"
git push
```

---

## 9. 白名单维护流程

### 新增协议字符串时

**步骤 1: 在代码中使用常量**
```python
# 定义协议常量
CCB_NEW_PROTOCOL = "CCB_NEW_FEATURE"

# 不要通过 t() 翻译
# ❌ 错误: t("ccb.protocol.new_feature")  # 返回 "CCB_NEW_FEATURE"

# ✓ 正确: 直接使用常量
os.environ[CCB_NEW_PROTOCOL] = "value"
```

**步骤 2: 添加到白名单**
```json
// .planning/protocol_whitelist.json
{
  "categories": {
    "env_vars": [
      "CCB_LANG",
      "CCB_NEW_FEATURE"  // 新增
    ]
  },
  "total_count": 288,  // 更新总数
  "last_updated": "2026-03-28"  // 更新日期
}
```

**步骤 3: 提交白名单更新**
```bash
git add .planning/protocol_whitelist.json
git commit -m "chore: 添加新协议字符串到白名单"
```

### 定期审查

**频率：** 每个 Phase 结束时

**检查项：**
- 白名单是否完整（是否有遗漏的协议字符串）
- 是否有废弃的协议字符串可以移除
- 分类是否合理

---

## 10. 性能考虑

### 检查时间
- 预估：<1 秒
- 扫描约 10 个 JSON 文件
- 白名单加载：<10ms
- 每个文件检查：<100ms

### 内存占用
- 白名单：<10KB（287 个字符串）
- 翻译文件：~8KB（所有文件）
- 总内存：<1MB

### CI 影响
- 可忽略（相比其他 CI 步骤）
- 不影响构建速度
- 可并行运行

---

## 11. 局限性和风险

### 局限性

**1. 仅检查翻译文件的值**
- 不检查键名（key）
- 不检查代码中的 t() 调用

**2. 不检查代码中的误用**
```python
# 这种误用无法检测
result = t("some.key")
if result == "CCB_DONE":  # 协议字符串硬编码在代码中
    pass
```

**3. 依赖白名单完整性**
- 遗漏的协议字符串不会被检测
- 需要手动维护白名单

### 风险

**风险 1: 白名单不完整**
- **影响：** 新增协议字符串可能被错误翻译
- **缓解：** 定期审查白名单，代码审查时注意

**风险 2: 假阴性（漏报）**
- **影响：** 协议字符串在代码中硬编码，未被检测
- **缓解：** 代码审查，明确文档说明哪些是协议字符串

**风险 3: 假阳性（误报）**
- **影响：** 正常翻译值恰好与协议字符串相同
- **缓解：** 协议字符串使用特殊前缀（如 CCB_），降低冲突概率

---

## 12. 未来增强

### 增强 1: 静态代码分析
检测 t() 调用是否包装了协议字符串：

```python
# 检测这种模式
t("ccb.command.name")  # 如果返回值是协议字符串，报警
```

### 增强 2: 自动白名单生成
从代码中自动提取协议字符串：

```python
# 扫描代码中的常量定义
CCB_LANG = "CCB_LANG"  # 自动添加到白名单
```

### 增强 3: 翻译键命名约定
使用特定前缀标识协议相关的键：

```json
{
  "protocol.ccb.lang": "CCB_LANG",  // 明确标识为协议
  "ccb.error.message": "错误消息"   // 普通翻译
}
```

### 增强 4: 运行时检查
在应用启动时验证翻译值：

```python
def validate_translations():
    for key, value in translations.items():
        if value in PROTOCOL_STRINGS:
            raise ValueError(f"Translation {key} contains protocol string")
```

---

## 13. 设计决策引用

本设计基于以下用户决策：

- **D-12:** CI 自动检查翻译文件，确保协议字符串未被翻译
- **D-13:** 维护白名单文件列出所有协议字符串，CI 检查对照
- **D-14:** CI 检查失败时阻止合并，强制修复后才能继续

---

## 14. 实现清单

### Phase 4 实现任务

- [ ] 创建 `scripts/check_protocol_strings.py` 脚本
- [ ] 创建 `.github/workflows/i18n-check.yml` 配置
- [ ] 创建 `.pre-commit-config.yaml` 配置
- [ ] 配置 GitHub 分支保护规则
- [ ] 编写测试用例
- [ ] 更新开发文档

### 测试覆盖

- [ ] 正常翻译文件通过检查
- [ ] 包含协议字符串的翻译文件被检测
- [ ] JSON 解析错误处理
- [ ] 文件不存在容错
- [ ] 白名单加载测试

---

**设计完成日期:** 2026-03-28
**下一步:** Phase 3 - 风险评估

