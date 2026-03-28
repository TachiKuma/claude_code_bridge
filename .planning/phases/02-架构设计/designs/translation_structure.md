# 翻译文件组织结构设计

**设计日期:** 2026-03-28
**Phase:** 02-架构设计
**需求:** ARCH-05
**状态:** 设计完成

---

## 1. 目录结构（per D-15, D-16）

### 内置翻译目录
```
lib/i18n/                      # 内置翻译根目录
├── ccb/                       # CCB 命名空间
│   ├── en.json               # 英文翻译
│   └── zh.json               # 中文翻译
└── common/                    # 共享命名空间（预留）
    ├── en.json
    └── zh.json
```

### 外部翻译目录（per D-17）
```
~/.ccb/i18n/                   # 外部翻译根目录
├── ccb/
│   ├── en.json               # 用户自定义英文翻译
│   └── zh.json               # 用户自定义中文翻译
└── common/
    ├── en.json
    └── zh.json
```

### 目录说明
- **lib/i18n/**: 内置翻译，随代码分发
- **~/.ccb/i18n/**: 用户自定义翻译，覆盖内置翻译
- **ccb/**: CCB 特定消息（当前实现）
- **common/**: 共享消息（预留扩展）

---

## 2. JSON 文件格式（per D-07）

### 文件结构
```json
{
  "namespace.category.specific": "翻译文本",
  "namespace.category.another": "带参数的翻译 {param}"
}
```

### 示例：lib/i18n/ccb/zh.json
```json
{
  "ccb.error.no_terminal": "未检测到终端后端 (WezTerm 或 tmux)",
  "ccb.startup.backend_started": "{provider} 已启动 ({terminal}: {pane_id})",
  "ccb.command.sending_to": "正在发送问题到 {provider}...",
  "ccb.connectivity.test_failed": "{provider} 连通性测试失败: {error}",
  "ccb.error.cannot_write_session": "无法写入 {filename}: {reason}"
}
```

### 示例：lib/i18n/ccb/en.json
```json
{
  "ccb.error.no_terminal": "No terminal backend detected (WezTerm or tmux)",
  "ccb.startup.backend_started": "{provider} started ({terminal}: {pane_id})",
  "ccb.command.sending_to": "Sending question to {provider}...",
  "ccb.connectivity.test_failed": "{provider} connectivity test failed: {error}",
  "ccb.error.cannot_write_session": "Cannot write {filename}: {reason}"
}
```

### 示例：lib/i18n/common/zh.json（预留）
```json
{
  "common.error.file_not_found": "文件未找到: {path}",
  "common.error.permission_denied": "权限被拒绝: {path}"
}
```

---

## 3. 文件命名约定

### 语言代码
- 使用 ISO 639-1 两字母代码
- 支持的语言：`en`（英文），`zh`（中文）

### 命名格式
```
{lang}.json
```

### 文件扩展名
- 统一使用 `.json`（per D-07）
- 便于手动编辑和版本控制

---

## 4. 加载优先级（per D-04, D-17）

### 查找顺序
对于键 `"ccb.error.no_terminal"`，查找顺序：

```
1. ~/.ccb/i18n/ccb/zh.json（用户自定义，最高优先级）
   ↓ 未找到
2. lib/i18n/ccb/zh.json（内置翻译）
   ↓ 未找到
3. lib/i18n/ccb/en.json（英文回退）
   ↓ 未找到
4. 返回键名 "ccb.error.no_terminal"（最终回退）
```

### 优先级规则
- **外部 > 内置**: 用户自定义翻译覆盖内置翻译
- **当前语言 > 英文**: 优先使用当前语言，缺失时回退到英文
- **键名回退**: 所有翻译都缺失时返回键名本身

---

## 5. 外部翻译覆盖机制

### 部分覆盖能力
用户仅需覆盖特定键，无需复制完整文件。

### 示例场景
**内置翻译（lib/i18n/ccb/zh.json）:**
```json
{
  "ccb.startup.backend_started": "{provider} 已启动 ({terminal}: {pane_id})",
  "ccb.command.sending_to": "正在发送问题到 {provider}..."
}
```

**用户自定义（~/.ccb/i18n/ccb/zh.json）:**
```json
{
  "ccb.startup.backend_started": "后端已就绪"
}
```

**最终结果:**
- `ccb.startup.backend_started` → "后端已就绪"（用户覆盖）
- `ccb.command.sending_to` → "正在发送问题到 {provider}..."（使用内置）

### 实现机制
```python
# 1. 加载内置翻译
self.translations = json.load(builtin_file)

# 2. 加载外部翻译并覆盖
external_translations = json.load(external_file)
self.translations.update(external_translations)  # 覆盖同名键
```

---

## 6. 从现有 lib/i18n.py 迁移

### 现有结构
```python
MESSAGES = {
    "en": {
        "no_terminal_backend": "No terminal backend detected",
        "starting_backend": "Starting {provider} backend"
    },
    "zh": {
        "no_terminal_backend": "未检测到终端后端",
        "starting_backend": "正在启动 {provider} 后端"
    }
}
```

### 新结构
```json
// lib/i18n/ccb/en.json
{
  "ccb.error.no_terminal_backend": "No terminal backend detected",
  "ccb.startup.starting_backend": "Starting {provider} backend"
}
```

### 迁移步骤
1. **提取字典**: 从 `MESSAGES["zh"]` 提取所有键值对
2. **添加前缀**: 为每个键添加 `"ccb."` 命名空间前缀
3. **分类组织**: 按 category 分组（error, startup, command 等）
4. **写入 JSON**: 保存到 `lib/i18n/ccb/zh.json`
5. **重复英文**: 对 `MESSAGES["en"]` 执行相同步骤

### 迁移脚本示例
```python
import json

# 提取现有翻译
old_messages = MESSAGES["zh"]

# 添加命名空间前缀
new_messages = {}
for key, value in old_messages.items():
    # 根据键名推断 category
    if "error" in key or "cannot" in key:
        category = "error"
    elif "start" in key or "backend" in key:
        category = "startup"
    else:
        category = "command"

    new_key = f"ccb.{category}.{key}"
    new_messages[new_key] = value

# 写入 JSON
with open("lib/i18n/ccb/zh.json", "w", encoding="utf-8") as f:
    json.dump(new_messages, f, ensure_ascii=False, indent=2)
```

---

## 7. 命名空间到目录的映射

### 映射规则
键的第一部分（点号前）对应目录名：

| 键前缀 | 目录路径 | 说明 |
|--------|---------|------|
| `ccb.*` | `lib/i18n/ccb/{lang}.json` | CCB 特定消息 |
| `common.*` | `lib/i18n/common/{lang}.json` | 共享消息 |

### 加载逻辑
```python
def _get_translation_path(namespace: str, lang: str) -> Path:
    """根据命名空间获取翻译文件路径"""
    return Path(__file__).parent / "i18n" / namespace / f"{lang}.json"

# 使用示例
ccb_path = _get_translation_path("ccb", "zh")
# 返回: lib/i18n/ccb/zh.json
```

---

## 8. 文件大小估算

### 基于 Phase 1 分析
- **现有消息数**: 56 条（英文 + 中文）
- **现有文件大小**: ~1.8KB

### 预估
| 文件 | 消息数 | 大小 |
|------|--------|------|
| lib/i18n/ccb/en.json | ~60 条 | ~3KB |
| lib/i18n/ccb/zh.json | ~60 条 | ~4KB |
| lib/i18n/common/en.json | ~10 条 | ~0.5KB |
| lib/i18n/common/zh.json | ~10 条 | ~0.7KB |
| **总计** | **~140 条** | **~8KB** |

### 外部翻译文件
- 通常 <1KB（仅覆盖少量键）
- 用户自定义场景：5-10 个键

---

## 9. 错误处理

### 文件不存在
```python
if not translation_file.exists():
    # 跳过，使用回退机制
    return
```

### JSON 解析失败
```python
try:
    translations = json.load(f)
except json.JSONDecodeError as e:
    # 记录警告，跳过该文件
    logger.warning(f"Failed to parse {file}: {e}")
    return
```

### 权限错误
```python
try:
    with open(external_file) as f:
        translations = json.load(f)
except OSError as e:
    # 记录警告，跳过外部翻译
    logger.warning(f"Cannot read {external_file}: {e}")
    return
```

### 不中断启动
所有错误都优雅降级，确保应用正常启动：
- 文件缺失 → 使用回退翻译
- 解析失败 → 跳过该文件
- 权限错误 → 使用内置翻译

---

## 10. 扩展性考虑

### 新增语言
添加新语言只需创建对应的 JSON 文件：
```
lib/i18n/ccb/ja.json  # 日语
lib/i18n/ccb/ko.json  # 韩语
```

### 新增命名空间
创建新目录（未来扩展）：
```
lib/i18n/gsd/         # GSD 命名空间（冻结）
lib/i18n/plugins/     # 插件命名空间（未来）
```

### 当前实现范围
- **ccb/**: 当前实现
- **common/**: 预留扩展
- **gsd/**: 冻结（per D-18, D-20）

---

## 11. 设计决策引用

本设计基于以下用户决策：

- **D-07:** JSON 格式存储翻译文件
- **D-15:** 三目录结构（ccb/, common/）
- **D-16:** 按语言分文件（en.json, zh.json）
- **D-17:** 外部翻译目录覆盖内置翻译
- **D-04:** 支持 ~/.ccb/i18n/ 自定义翻译

---

## 12. 实现指南

### Phase 4 实现清单
- [ ] 创建 `lib/i18n/ccb/` 目录
- [ ] 创建 `lib/i18n/common/` 目录
- [ ] 迁移现有翻译到 JSON 文件
- [ ] 实现加载优先级逻辑
- [ ] 添加错误处理
- [ ] 测试外部翻译覆盖

### 测试覆盖
- 内置翻译加载测试
- 外部翻译覆盖测试
- 文件缺失容错测试
- JSON 解析错误处理测试

---

**设计完成日期:** 2026-03-28
**下一步:** Phase 3 - 风险评估
