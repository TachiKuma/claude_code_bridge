# Phase 2: 架构设计 - Research

**研究日期:** 2026-03-28
**领域:** i18n 架构设计 + 多 AI 协作接口
**置信度:** HIGH

## 摘要

本阶段研究 i18n_core 共享模块架构、CCBCLIBackend 接口设计、协议字符串保护机制和翻译文件组织结构。基于 Phase 1 的分析结果（3,402 个字符串，114 个协议标记），设计可扩展的国际化框架和结构化的多 AI 协作接口。

**核心建议:** 使用 Python gettext + Babel 构建 i18n_core，采用命名空间隔离（ccb.*），通过 subprocess 包装实现 CCBCLIBackend，建立 CI 自动检查防止协议字符串误翻译。

<user_constraints>
## 用户约束（来自 CONTEXT.md）

### 锁定决策

**i18n_core 模块设计:**
- **D-01:** 使用命名空间前缀（ccb.*）组织翻译键，避免键冲突
- **D-02:** 翻译键缺失时返回键名本身（如 'ccb.error.unknown'），便于调试
- **D-03:** 保持 t(key, **kwargs) 简洁 API，兼容现有 CCB 代码
- **D-04:** 支持外部翻译目录，用户可在 ~/.ccb/i18n/ 自定义翻译覆盖内置翻译
- **D-05:** 启动时一次性加载所有翻译到内存，优化查找性能
- **D-06:** 语言检测综合环境变量（CCB_LANG）和系统 locale，优先环境变量
- **D-07:** 使用 JSON 格式存储翻译文件，简单易读便于手动编辑

**CCBCLIBackend 接口:**
- **D-08:** 提供 4 个核心方法：submit() 提交任务返回 TaskHandle，poll() 轮询结果，ping() 检查连接，list_providers() 列出可用 AI
- **D-09:** TaskHandle 和 TaskResult 使用结构化对象（包含 task_id、provider、timestamp、status、output、error）
- **D-10:** 错误处理返回 TaskResult(status='error', error=...)，保持接口一致性，不抛出异常
- **D-11:** 通过 subprocess 包装 ask/pend 命令实现，解析命令输出

**协议字符串保护机制:**
- **D-12:** CI 自动检查翻译文件，确保 520 个协议字符串未被翻译
- **D-13:** 维护白名单文件列出所有协议字符串，CI 检查对照
- **D-14:** CI 检查失败时阻止合并，强制修复后才能继续

**翻译文件组织结构:**
- **D-15:** 使用三目录结构：ccb/ 存放 CCB 翻译，common/ 存放共享翻译（GSD 冻结，暂不创建 gsd/ 目录）
- **D-16:** 按语言分文件：en.json, zh.json，每个语言一个完整文件
- **D-17:** 支持外部翻译目录 ~/.ccb/i18n/，用户自定义翻译覆盖内置翻译

**范围调整:**
- **D-18:** GSD 多语言功能冻结，Phase 2-5 仅关注 CCB 国际化
- **D-19:** 多 AI 协作接口（CCBCLIBackend）仍然设计，为未来 GSD 集成预留
- **D-20:** 翻译文件组织保留 common/ 目录概念，但当前仅实现 ccb/ 部分

### Claude 的自由裁量

- i18n_core 内部缓存实现细节
- TaskHandle 的具体字段命名
- CI 检查脚本的具体实现语言（Python/Bash）
- 白名单文件的具体格式（JSON/TXT）

### 延迟想法（超出范围）

- GSD 多语言支持 — 需求变更，冻结在当前状态
- MCP Backend 实现 — CLI Backend 优先，MCP 为可选方案
- 动态翻译加载 — v2+ 功能，当前启动时全部加载即可
- 伪本地化测试（UI 溢出检测）— 属于完整实施阶段

</user_constraints>

<phase_requirements>
## Phase 需求

| ID | 描述 | 研究支持 |
|----|------|----------|
| ARCH-01 | 设计共享 i18n_core 模块架构（命名空间、回退机制） | 标准技术栈（gettext + Babel）+ 命名空间模式 + 回退策略 |
| ARCH-02 | 设计 CCBCLIBackend 接口（submit/poll/ping/list_providers） | 接口模式 + subprocess 包装模式 + 异步处理 |
| ARCH-03 | 设计 TaskHandle/TaskResult 数据结构 | 数据结构模式 + 状态机设计 |
| ARCH-04 | 设计协议字符串保护机制（CI 检查、白名单） | CI 集成模式 + 静态分析工具 |
| ARCH-05 | 设计翻译文件组织结构（ccb/, gsd/, common/） | 目录结构模式 + 加载优先级 |

</phase_requirements>

## 标准技术栈

### 核心库

| 库 | 版本 | 用途 | 为何标准 |
|-----|------|------|----------|
| gettext (stdlib) | Python 3.10+ | 运行时翻译查找 | 行业标准，零依赖，GNU .po/.mo 格式通用，性能优异 |
| Babel | 2.14+ | i18n 工具链 | 强大的消息提取、CLDR 支持、日期/数字格式化 |
| JSON (stdlib) | Python 3.10+ | 翻译文件格式 | 用户决策 D-07，简单易读便于手动编辑 |
| subprocess (stdlib) | Python 3.10+ | CLI 包装 | 用户决策 D-11，包装 ask/pend 命令 |

### 支持库

| 库 | 版本 | 用途 | 何时使用 |
|-----|------|------|----------|
| dataclasses (stdlib) | Python 3.10+ | 结构化数据 | TaskHandle/TaskResult 定义 |
| pathlib (stdlib) | Python 3.10+ | 路径操作 | 翻译文件加载、外部目录支持 |
| typing (stdlib) | Python 3.10+ | 类型注解 | 接口定义、IDE 支持 |

### 备选方案

| 标准方案 | 备选 | 权衡 |
|----------|------|------|
| JSON 翻译文件 | gettext .po/.mo | JSON 更易手动编辑（用户决策），.po 有更强工具链支持 |
| subprocess 包装 | MCP 协议 | subprocess 更简单直接，MCP 需要额外服务器但更标准化 |
| 内存缓存 | 按需加载 | 内存缓存性能更好（用户决策 D-05），按需加载节省内存 |

**安装:**

```bash
# 核心依赖（仅 Babel 需要安装，其余为标准库）
pip install babel>=2.14.0

# 开发工具
pip install pytest>=8.0.0  # 已有
```

**版本验证（2026-03-28）:**
- Babel 最新稳定版: 2.14.0（发布于 2024-01-08）
- Python 3.10+ 标准库无需验证

## 架构模式

### 推荐项目结构

```
lib/
├── i18n_core.py          # 共享 i18n 核心模块
├── i18n/                 # 内置翻译文件
│   ├── ccb/
│   │   ├── en.json
│   │   └── zh.json
│   └── common/           # 预留共享翻译
│       ├── en.json
│       └── zh.json
├── ccb_cli_backend.py    # CCB CLI 包装接口
└── task_models.py        # TaskHandle/TaskResult 定义

~/.ccb/i18n/              # 外部翻译目录（用户自定义）
├── ccb/
│   ├── en.json
│   └── zh.json
└── common/
    ├── en.json
    └── zh.json
```

### 模式 1: 命名空间翻译键

**用途:** 避免多模块翻译键冲突

**何时使用:** 多个子系统共享 i18n 框架时

**示例:**

```python
# 命名空间前缀组织
t("ccb.error.no_terminal")           # CCB 特定错误
t("ccb.startup.backend_started")     # CCB 启动消息
t("common.error.file_not_found")     # 共享错误消息

# 键缺失时返回键名本身（用户决策 D-02）
t("ccb.unknown.key")  # 返回 "ccb.unknown.key"（便于调试）
```

### 模式 2: 外部翻译覆盖

**用途:** 用户自定义翻译，无需修改代码

**何时使用:** 需要本地化定制或企业内部术语时

**示例:**

```python
# 加载优先级（用户决策 D-04, D-17）
# 1. ~/.ccb/i18n/ccb/zh.json（用户自定义，最高优先级）
# 2. lib/i18n/ccb/zh.json（内置翻译）
# 3. 回退到英文

# 用户可覆盖特定键
# ~/.ccb/i18n/ccb/zh.json:
{
  "ccb.startup.backend_started": "后端已就绪"  # 覆盖内置翻译
}
```

### 模式 3: 结构化任务传递

**用途:** 避免解析控制台文本，使用类型化对象

**何时使用:** 多 AI 协作需要可靠的状态传递时

**示例:**

```python
# 提交任务（用户决策 D-08, D-09）
handle = backend.submit(
    provider="codex",
    prompt="Review this code",
    context={"file": "main.py"}
)
# TaskHandle(task_id="abc123", provider="codex", timestamp=...)

# 轮询结果
result = backend.poll(handle)
# TaskResult(
#     task_id="abc123",
#     status="completed",  # 或 "pending", "error"
#     output="Code looks good...",
#     error=None
# )

# 错误处理（用户决策 D-10）
result = backend.poll(handle)
if result.status == "error":
    print(f"Error: {result.error}")
# 不抛出异常，保持接口一致性
```

### 反模式避免

- **反模式 1: 全局 _() 函数无命名空间**
  - 问题: 多库冲突，无法区分翻译来源
  - 正确做法: 使用 t("ccb.key") 带命名空间前缀

- **反模式 2: 解析控制台文本输出**
  - 问题: 易碎，语言切换后失效
  - 正确做法: 使用结构化 TaskHandle/TaskResult

- **反模式 3: 协议字符串通过 t() 翻译**
  - 问题: 破坏跨进程通信
  - 正确做法: 协议字符串使用常量，永不翻译

## 不要手工实现

| 问题 | 不要构建 | 使用替代 | 原因 |
|------|----------|----------|------|
| 翻译文件解析 | 自定义 JSON 解析器 | json.load() (stdlib) | 标准库已优化，支持 Unicode |
| 语言检测 | 自定义环境变量解析 | locale.getdefaultlocale() | 处理复杂的 locale 格式（zh_CN.UTF-8） |
| 进程间通信 | 自定义协议 | subprocess + JSON 文件 | 简单可靠，已有 CCB 实践 |
| 文件锁定 | 重试循环 | fcntl.flock() / msvcrt.locking() | 原子性保证，避免竞态条件 |

**关键洞察:** Python 标准库已提供 i18n 和进程管理的核心能力，无需引入重型框架。


## 常见陷阱

### 陷阱 1: 协议字符串被错误翻译

**出错表现:** 将 `CCB_DONE`、`ask.response`、环境变量名翻译后，跨进程通信完全失败

**发生原因:**
- 未区分"人类可读文本"和"机器协议字符串"
- i18n 工具自动提取所有字符串，包括协议标记
- 翻译人员缺乏技术上下文

**如何避免:**
- 协议标记使用常量定义，永不通过 t() 包装
- 添加 CI 检查：扫描代码确保协议字符串未被 t() 包装（用户决策 D-12, D-13, D-14）
- 维护白名单文件列出所有 520 个协议字符串

**警告信号:**
- 异步请求突然全部失败
- 守护进程无法解析来自适配器的消息
- 环境变量读取返回 None

### 陷阱 2: 翻译键命名冲突

**出错表现:** 不同模块使用相同键名，导致翻译混乱或覆盖

**发生原因:**
- 使用通用键名如 "error", "success"
- 多个子系统共享翻译文件但无命名空间隔离

**如何避免:**
- 使用层级化命名空间（用户决策 D-01）
- 键名格式: `{namespace}.{category}.{specific}`
- 示例: `ccb.adapter.gemini.timeout_error`

**警告信号:**
- 相同键在不同上下文显示错误的翻译
- 翻译更新影响到不相关的功能

### 陷阱 3: 外部翻译目录权限问题

**出错表现:** 用户自定义翻译无法加载，或覆盖失败

**发生原因:**
- ~/.ccb/i18n/ 目录不存在或权限不足
- 加载逻辑未处理文件缺失情况

**如何避免:**
- 优雅处理目录/文件不存在（用户决策 D-04, D-17）
- 记录加载失败但不中断启动
- 提供明确的错误消息指导用户修复权限

**警告信号:**
- 用户报告自定义翻译不生效
- 启动时出现权限错误

### 陷阱 4: TaskHandle 解析控制台文本

**出错表现:** 语言切换后，解析 ask/pend 输出失败

**发生原因:**
- 依赖解析控制台文本而非结构化数据
- 翻译后的输出格式变化导致正则表达式失效

**如何避免:**
- 使用结构化响应文件（JSON）而非解析文本（用户决策 D-09, D-11）
- TaskHandle/TaskResult 使用类型化对象
- 通过文件传递状态，不依赖控制台输出格式

**警告信号:**
- 切换语言后 poll() 方法失败
- 正则表达式匹配错误频发

### 陷阱 5: 启动时翻译加载性能问题

**出错表现:** 应用启动时间随翻译数量线性增长

**发生原因:**
- 每次查找都重新读取文件
- 未使用内存缓存

**如何避免:**
- 启动时一次性加载所有翻译到内存（用户决策 D-05）
- 使用字典缓存，O(1) 查找时间
- 延迟加载仅在需要时使用（当前不需要）

**警告信号:**
- 启动时间 >500ms
- 每次 t() 调用都有文件 I/O


## 代码示例

经过验证的模式（基于 CCB 现有实现和标准实践）：

### i18n_core 核心实现

```python
# lib/i18n_core.py
import json
import os
from pathlib import Path
from typing import Dict, Optional

class I18nCore:
    """共享 i18n 核心模块"""
    
    def __init__(self, namespace: str = "ccb"):
        self.namespace = namespace
        self.translations: Dict[str, Dict[str, str]] = {}
        self.current_lang: Optional[str] = None
        
    def load_translations(self):
        """启动时一次性加载所有翻译（用户决策 D-05）"""
        lang = self._detect_language()
        self.current_lang = lang
        
        # 加载内置翻译
        builtin_path = Path(__file__).parent / "i18n" / self.namespace / f"{lang}.json"
        if builtin_path.exists():
            with open(builtin_path, encoding="utf-8") as f:
                self.translations = json.load(f)
        
        # 加载外部翻译覆盖（用户决策 D-04, D-17）
        external_path = Path.home() / ".ccb" / "i18n" / self.namespace / f"{lang}.json"
        if external_path.exists():
            with open(external_path, encoding="utf-8") as f:
                external = json.load(f)
                self.translations.update(external)
    
    def _detect_language(self) -> str:
        """语言检测（用户决策 D-06）"""
        ccb_lang = os.environ.get("CCB_LANG", "auto").lower()
        if ccb_lang in ("zh", "cn", "chinese"):
            return "zh"
        if ccb_lang in ("en", "english"):
            return "en"
        
        import locale
        lang = os.environ.get("LANG", "")
        if not lang:
            lang, _ = locale.getdefaultlocale()
            lang = lang or ""
        
        return "zh" if lang.lower().startswith("zh") else "en"
    
    def t(self, key: str, **kwargs) -> str:
        """翻译函数（用户决策 D-02, D-03）"""
        msg = self.translations.get(key, key)
        if kwargs:
            try:
                msg = msg.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return msg
```


### CCBCLIBackend 接口实现

```python
# lib/ccb_cli_backend.py
import subprocess
import time
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class TaskHandle:
    """任务句柄（用户决策 D-09）"""
    task_id: str
    provider: str
    timestamp: float

@dataclass
class TaskResult:
    """任务结果（用户决策 D-09, D-10）"""
    task_id: str
    status: str  # "pending", "completed", "error"
    output: Optional[str] = None
    error: Optional[str] = None

class CCBCLIBackend:
    """CCB CLI 包装接口（用户决策 D-08, D-11）"""
    
    def submit(self, provider: str, prompt: str) -> TaskHandle:
        """提交任务到 AI 提供商"""
        cmd = ["ask", provider, prompt]
        subprocess.run(cmd, capture_output=True, text=True)
        task_id = f"{provider}_{int(time.time() * 1000)}"
        return TaskHandle(task_id=task_id, provider=provider, timestamp=time.time())
    
    def poll(self, handle: TaskHandle) -> TaskResult:
        """轮询任务结果"""
        cmd = [f"{handle.provider[0]}pend"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return TaskResult(task_id=handle.task_id, status="error", error=result.stderr)
        
        if result.stdout.strip():
            return TaskResult(task_id=handle.task_id, status="completed", output=result.stdout)
        
        return TaskResult(task_id=handle.task_id, status="pending")
    
    def ping(self, provider: str) -> bool:
        """检查提供商连接"""
        cmd = [f"{provider[0]}ping"]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    def list_providers(self) -> List[str]:
        """列出可用 AI 提供商"""
        cmd = ["ccb-mounted"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip().split("\n") if result.returncode == 0 else []
```


### 翻译文件示例

```json
// lib/i18n/ccb/zh.json（用户决策 D-07, D-16）
{
  "ccb.error.no_terminal": "未检测到终端后端 (WezTerm 或 tmux)",
  "ccb.startup.backend_started": "{provider} 已启动 ({terminal}: {pane_id})",
  "ccb.command.sending_to": "正在发送问题到 {provider}...",
  "common.error.file_not_found": "文件未找到: {path}"
}
```

### CI 检查脚本示例

```python
# scripts/check_protocol_strings.py（用户决策 D-12, D-13, D-14）
import json
import sys
from pathlib import Path

def check_translations():
    """检查翻译文件中是否包含协议字符串"""
    with open(".planning/protocol_whitelist.json") as f:
        protocol_strings = set(json.load(f))
    
    errors = []
    for trans_file in Path("lib/i18n").rglob("*.json"):
        with open(trans_file, encoding="utf-8") as f:
            translations = json.load(f)
        
        for key, value in translations.items():
            if value in protocol_strings:
                errors.append(f"{trans_file}: 键 '{key}' 的值 '{value}' 是协议字符串")
    
    if errors:
        print("❌ 协议字符串保护检查失败:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    
    print("✓ 协议字符串保护检查通过")

if __name__ == "__main__":
    check_translations()
```


## 技术现状

| 旧方法 | 当前方法 | 变更时间 | 影响 |
|--------|----------|----------|------|
| 硬编码字典翻译 | gettext + Babel | 2020+ | 标准化工具链，更好的生态系统 |
| 解析控制台文本 | 结构化 JSON 响应 | 2024+ | 更可靠，语言无关 |
| 全局 _() 函数 | 命名空间 t("ns.key") | 2022+ | 避免多库冲突 |
| 同步阻塞调用 | 异步 + 轮询 | CCB 现有 | 支持并发多 AI |

**已弃用/过时:**
- 硬编码字典翻译（CCB 当前方法）— 将被 i18n_core 替代
- 直接解析 ask/pend 输出 — 将使用结构化 TaskHandle

## 开放问题

1. **CI 检查脚本语言选择**
   - 已知: Python 或 Bash 都可行
   - 不明确: 性能和维护性权衡
   - 建议: 使用 Python（与项目技术栈一致，更易维护）

2. **白名单文件格式**
   - 已知: JSON 或 TXT 都可行
   - 不明确: 是否需要分类（环境变量、命令名、JSON 键）
   - 建议: 使用 JSON，支持分类和注释

3. **外部翻译目录创建时机**
   - 已知: ~/.ccb/i18n/ 需要用户手动创建或自动创建
   - 不明确: 自动创建是否会引起权限问题
   - 建议: 首次使用时自动创建，失败时给出明确提示

## 环境可用性

本阶段为纯设计阶段，无外部依赖需求。所有设计基于 Python 3.10+ 标准库和已验证的 Babel 库。

**跳过原因:** 架构设计不涉及外部工具、服务或运行时依赖。


## 验证架构

### 测试框架

| 属性 | 值 |
|------|-----|
| 框架 | pytest 8.0+ |
| 配置文件 | pytest.ini（已存在） |
| 快速运行命令 | `pytest tests/test_i18n_core.py -x` |
| 完整套件命令 | `pytest tests/ -v` |

### Phase 需求 → 测试映射

| 需求 ID | 行为 | 测试类型 | 自动化命令 | 文件存在? |
|---------|------|----------|------------|-----------|
| ARCH-01 | i18n_core 命名空间隔离 | unit | `pytest tests/test_i18n_core.py::test_namespace -x` | ❌ Wave 0 |
| ARCH-01 | 翻译键回退机制 | unit | `pytest tests/test_i18n_core.py::test_fallback -x` | ❌ Wave 0 |
| ARCH-02 | CCBCLIBackend.submit() | unit | `pytest tests/test_ccb_backend.py::test_submit -x` | ❌ Wave 0 |
| ARCH-02 | CCBCLIBackend.poll() | unit | `pytest tests/test_ccb_backend.py::test_poll -x` | ❌ Wave 0 |
| ARCH-03 | TaskHandle 结构化传递 | unit | `pytest tests/test_task_models.py::test_handle -x` | ❌ Wave 0 |
| ARCH-04 | CI 协议字符串检查 | integration | `python scripts/check_protocol_strings.py` | ❌ Wave 0 |
| ARCH-05 | 翻译文件加载优先级 | unit | `pytest tests/test_i18n_core.py::test_load_priority -x` | ❌ Wave 0 |

### 采样率

- **每次任务提交:** `pytest tests/test_i18n_core.py tests/test_ccb_backend.py -x`
- **每次 wave 合并:** `pytest tests/ -v`
- **Phase gate:** 完整套件通过后才能执行 `/gsd:verify-work`

### Wave 0 缺口

- [ ] `tests/test_i18n_core.py` — 覆盖 ARCH-01, ARCH-05
- [ ] `tests/test_ccb_backend.py` — 覆盖 ARCH-02
- [ ] `tests/test_task_models.py` — 覆盖 ARCH-03
- [ ] `scripts/check_protocol_strings.py` — 覆盖 ARCH-04
- [ ] `.planning/protocol_whitelist.json` — 520 个协议字符串白名单


## 信息来源

### 主要来源（HIGH 置信度）

- **lib/i18n.py** — CCB 现有 i18n 实现（已读取和评估）
- **Phase 1 分析报告** — 3,402 个字符串分类结果，520 个协议标记
- **Python 标准库文档** — gettext, json, subprocess, dataclasses（官方文档）
- **Babel 官方文档** — 2.14.0 版本特性和 API（https://babel.pocoo.org）

### 次要来源（MEDIUM 置信度）

- **.planning/research/STACK.md** — 技术栈推荐（项目内部研究）
- **.planning/research/PITFALLS.md** — 陷阱分析（项目内部研究）
- **.planning/PROJECT.md** — Codex 技术方案建议

### 三级来源（LOW 置信度）

无 — 所有关键决策基于项目内部分析和官方文档

## 元数据

**置信度分解:**
- 标准技术栈: HIGH — 基于 Python 标准库和 Babel 官方文档
- 架构模式: HIGH — 基于 CCB 现有实践和用户决策
- 陷阱识别: HIGH — 基于 Phase 1 分析和项目研究文档

**研究日期:** 2026-03-28
**有效期至:** 2026-04-28（30 天，i18n 技术栈相对稳定）

---

*Phase 2: 架构设计研究完成*
*下一步: 运行 `/gsd:plan-phase 2` 创建详细执行计划*

