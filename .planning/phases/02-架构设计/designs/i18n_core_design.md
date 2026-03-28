# i18n_core 模块架构设计

**设计日期:** 2026-03-28
**Phase:** 02-架构设计
**需求:** ARCH-01
**状态:** 设计完成

---

## 1. 模块概述

### 目标
为 CCB 提供可扩展的国际化框架，支持命名空间隔离、外部翻译定制和高性能查找。

### 范围
- **当前范围:** 仅 CCB（per D-18）
- **预留扩展:** common/ 命名空间供未来共享使用
- **冻结范围:** GSD 多语言功能冻结在当前状态

### 核心能力
1. **命名空间隔离** - 使用 ccb.* 前缀避免键冲突（per D-01）
2. **外部翻译覆盖** - 支持 ~/.ccb/i18n/ 用户自定义翻译（per D-04, D-17）
3. **高性能查找** - 启动时一次性加载，O(1) 字典查找（per D-05）
4. **优雅回退** - 键缺失时返回键名本身，便于调试（per D-02）

---

## 2. 命名空间设计（per D-01）

### 键格式规范
```
{namespace}.{category}.{specific}
```

### 命名空间列表
| 命名空间 | 用途 | 状态 |
|---------|------|------|
| `ccb.*` | CCB 特定消息 | 当前实现 |
| `common.*` | 共享消息（预留） | 预留扩展 |

### 键命名示例
```python
# CCB 特定消息
"ccb.error.no_terminal"           # 终端检测错误
"ccb.startup.backend_started"     # 启动成功消息
"ccb.command.sending_to"          # 命令执行提示
"ccb.connectivity.test_failed"    # 连接测试失败

# 共享消息（预留）
"common.error.file_not_found"     # 通用文件错误
"common.error.permission_denied"  # 通用权限错误
```

### 冲突避免机制
- 不同命名空间的键完全隔离
- 键名包含完整路径，无歧义
- 命名空间前缀在加载时验证

---

## 3. 核心类设计：I18nCore

### 类定义
```python
from typing import Dict, Optional
from pathlib import Path

class I18nCore:
    """共享 i18n 核心模块

    提供命名空间隔离的翻译查找，支持外部翻译覆盖。
    """

    def __init__(self, namespace: str = "ccb"):
        """初始化 i18n 核心

        Args:
            namespace: 命名空间前缀（ccb, common）
        """
        self.namespace = namespace
        self.translations: Dict[str, str] = {}
        self.current_lang: Optional[str] = None

    def load_translations(self) -> None:
        """启动时一次性加载所有翻译（per D-05）

        加载顺序：
        1. 内置翻译文件（lib/i18n/{namespace}/{lang}.json）
        2. 外部翻译文件（~/.ccb/i18n/{namespace}/{lang}.json）
        3. 外部翻译覆盖内置翻译（dict.update）
        """
        pass

    def _detect_language(self) -> str:
        """语言检测（per D-06）

        优先级：
        1. CCB_LANG 环境变量
        2. 系统 locale（LANG, LC_ALL）
        3. 默认英文

        Returns:
            语言代码（zh 或 en）
        """
        pass

    def t(self, key: str, **kwargs) -> str:
        """翻译函数（per D-03）

        Args:
            key: 翻译键（如 "ccb.error.no_terminal"）
            **kwargs: 格式化参数

        Returns:
            翻译后的消息，键缺失时返回键名本身（per D-02）
        """
        pass
```

---

## 4. 翻译键回退机制（per D-02）

### 查找顺序
```
1. 外部翻译文件（~/.ccb/i18n/{namespace}/{lang}.json）
   ↓ 未找到
2. 内置翻译文件（lib/i18n/{namespace}/{lang}.json）
   ↓ 未找到
3. 英文回退（如果当前语言非英文）
   ↓ 未找到
4. 返回键名本身（便于调试）
```

### 回退示例
```python
# 场景 1: 键存在于当前语言
t("ccb.error.no_terminal")  # zh: "未检测到终端后端"

# 场景 2: 键不存在，回退到英文
t("ccb.new.feature")  # zh 缺失 → en: "New feature"

# 场景 3: 键完全不存在，返回键名
t("ccb.unknown.key")  # 返回 "ccb.unknown.key"（便于调试）
```

### 调试友好性
- 返回键名本身而非空字符串或异常
- 开发者可立即识别缺失的翻译键
- 不中断应用运行

---

## 5. 语言检测逻辑（per D-06）

### 检测优先级
```python
def _detect_language(self) -> str:
    # 1. CCB_LANG 环境变量（最高优先级）
    ccb_lang = os.environ.get("CCB_LANG", "auto").lower()
    if ccb_lang in ("zh", "cn", "chinese"):
        return "zh"
    if ccb_lang in ("en", "english"):
        return "en"

    # 2. 系统 locale
    import locale
    lang = os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
    if not lang:
        lang, _ = locale.getdefaultlocale()
        lang = lang or ""

    # 3. 默认英文
    return "zh" if lang.lower().startswith("zh") else "en"
```

### 支持的语言代码
| 环境变量值 | 解析结果 |
|-----------|---------|
| `zh`, `cn`, `chinese` | zh |
| `en`, `english` | en |
| `auto` | 根据系统 locale 自动检测 |

### Locale 格式处理
- 支持复杂格式：`zh_CN.UTF-8` → `zh`
- 使用 `locale.getdefaultlocale()` 解析
- 容错处理：解析失败时默认英文

---

## 6. 外部翻译目录支持（per D-04, D-17）

### 目录位置
```
~/.ccb/i18n/{namespace}/{lang}.json
```

### 加载优先级
外部翻译覆盖内置翻译（使用 `dict.update()`）：

```python
# 1. 加载内置翻译
builtin_path = Path(__file__).parent / "i18n" / self.namespace / f"{lang}.json"
if builtin_path.exists():
    with open(builtin_path, encoding="utf-8") as f:
        self.translations = json.load(f)

# 2. 加载外部翻译覆盖
external_path = Path.home() / ".ccb" / "i18n" / self.namespace / f"{lang}.json"
if external_path.exists():
    with open(external_path, encoding="utf-8") as f:
        external = json.load(f)
        self.translations.update(external)  # 覆盖内置翻译
```

### 错误处理
- **目录不存在:** 跳过，不中断启动
- **文件不存在:** 跳过，使用内置翻译
- **JSON 解析失败:** 记录警告，跳过该文件
- **权限错误:** 记录警告，跳过外部翻译

### 用户自定义示例
```json
// ~/.ccb/i18n/ccb/zh.json（用户自定义）
{
  "ccb.startup.backend_started": "后端已就绪"
}
```
仅需覆盖特定键，无需复制完整文件。

---

## 7. 性能优化（per D-05）

### 加载策略
- **启动时一次性加载** 所有翻译到内存（`self.translations: Dict[str, str]`）
- **查找时间:** O(1) 字典查找
- **无需按需加载**（当前翻译量小）

### 性能指标（基于 Phase 1 分析）
| 指标 | 值 | 说明 |
|------|-----|------|
| 内存占用 | ~5KB | 基于 56 条消息 ≈ 1.8KB，预估 CCB 翻译 ~3-5KB |
| 查找速度 | 0.85 μs | 10,000 次测试平均值 |
| 冷启动时间 | <5ms | 加载 JSON + 构建字典 |

### 无需优化的原因
- 翻译量小（<100 条消息）
- 内存占用可忽略（<10KB）
- 查找速度已达微秒级

---

## 8. API 兼容性（per D-03）

### 保持现有 API
```python
# 现有 lib/i18n.py 的 API
def t(key: str, **kwargs) -> str:
    """翻译函数"""
    pass
```

### 参数格式化
```python
# 使用 str.format(**kwargs)
t("ccb.startup.backend_started", provider="Claude", terminal="tmux", pane_id="1")
# 输出: "Claude 已启动 (tmux: 1)"
```

### 错误处理
```python
# 格式化失败时返回未格式化消息（不抛出异常）
try:
    msg = msg.format(**kwargs)
except (KeyError, ValueError):
    pass  # 返回原始消息
```

---

## 9. 与现有 lib/i18n.py 的关系

### 迁移路径
1. **Phase 4:** 实现 i18n_core 模块
2. **Phase 5:** lib/i18n.py 调用 i18n_core（保持向后兼容）
3. **未来:** 逐步移除 lib/i18n.py，直接使用 i18n_core

### API 兼容性保证
```python
# 现有代码无需修改
from lib.i18n import t
t("no_terminal_backend")  # 仍然工作

# 新代码使用命名空间
from lib.i18n_core import I18nCore
i18n = I18nCore("ccb")
i18n.t("ccb.error.no_terminal")  # 新 API
```

### 差异对比
| 特性 | lib/i18n.py | i18n_core |
|------|-------------|-----------|
| 命名空间 | ✗ | ✓ ccb.*, common.* |
| 外部文件 | ✗ | ✓ ~/.ccb/i18n/ |
| 回退机制 | ✓ | ✓ 增强（返回键名） |
| API 签名 | t(key, **kwargs) | t(key, **kwargs) |

---

## 10. 类型注解

### 完整类型定义
```python
from typing import Dict, Optional
from pathlib import Path
import json
import os

class I18nCore:
    """共享 i18n 核心模块"""

    namespace: str
    translations: Dict[str, str]
    current_lang: Optional[str]

    def __init__(self, namespace: str = "ccb") -> None:
        self.namespace = namespace
        self.translations = {}
        self.current_lang = None

    def load_translations(self) -> None:
        """加载翻译文件"""
        lang = self._detect_language()
        self.current_lang = lang

        # 加载内置翻译
        builtin_path = Path(__file__).parent / "i18n" / self.namespace / f"{lang}.json"
        if builtin_path.exists():
            with open(builtin_path, encoding="utf-8") as f:
                self.translations = json.load(f)

        # 加载外部翻译覆盖
        external_path = Path.home() / ".ccb" / "i18n" / self.namespace / f"{lang}.json"
        if external_path.exists():
            try:
                with open(external_path, encoding="utf-8") as f:
                    external = json.load(f)
                    self.translations.update(external)
            except (OSError, json.JSONDecodeError) as e:
                # 记录警告但不中断
                pass

    def _detect_language(self) -> str:
        """检测语言"""
        ccb_lang = os.environ.get("CCB_LANG", "auto").lower()
        if ccb_lang in ("zh", "cn", "chinese"):
            return "zh"
        if ccb_lang in ("en", "english"):
            return "en"

        import locale
        lang = os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
        if not lang:
            try:
                lang, _ = locale.getdefaultlocale()
                lang = lang or ""
            except Exception:
                return "en"

        return "zh" if lang.lower().startswith("zh") else "en"

    def t(self, key: str, **kwargs) -> str:
        """翻译函数"""
        msg = self.translations.get(key, key)
        if kwargs:
            try:
                msg = msg.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return msg
```

---

## 11. 设计决策引用

本设计基于以下用户决策：

- **D-01:** 命名空间前缀（ccb.*）
- **D-02:** 键缺失时返回键名本身
- **D-03:** 保持 t(key, **kwargs) API
- **D-04:** 外部翻译目录支持
- **D-05:** 启动时一次性加载
- **D-06:** 语言检测优先级
- **D-07:** JSON 格式存储

---

## 12. 实现指南

### Phase 4 实现清单
- [ ] 创建 `lib/i18n_core.py` 文件
- [ ] 实现 `I18nCore` 类
- [ ] 创建 `lib/i18n/ccb/` 目录
- [ ] 迁移现有翻译到 JSON 文件
- [ ] 添加单元测试
- [ ] 更新 `lib/i18n.py` 调用 i18n_core

### 测试覆盖
- 命名空间隔离测试
- 回退机制测试
- 外部翻译覆盖测试
- 语言检测测试
- 性能基准测试

---

**设计完成日期:** 2026-03-28
**下一步:** 创建翻译文件组织结构设计文档
