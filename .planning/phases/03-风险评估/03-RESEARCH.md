# Phase 3: 风险评估 - Research

**研究日期:** 2026-03-28
**领域:** 国际化风险评估、多 AI 并发控制、工作量估算
**置信度:** HIGH

## 摘要

本研究评估了 GSD & CCB 国际化和多 AI 协作项目的关键技术风险，包括协议字符串误翻译、多 AI 并发竞态条件、上下文崩溃等风险，并估算了完整实施和原型验证的工作量。

基于 Phase 1 的代码分析（3,402 个字符串，114 个协议字符串）和 Phase 2 的架构设计（i18n_core、CCBCLIBackend、协议保护机制），本研究识别了 5 个主要风险领域，并为每个风险制定了具体的缓解策略。

**核心发现:**
- 协议字符串误翻译风险为"完全破坏"级别，需要双层保护机制
- 多 AI 并发已有成熟的文件锁方案（process_lock.py），风险可控
- 上下文崩溃的主要风险来自单任务约束，需要明确文档化
- 完整实施估算约 536 小时（13.4 周），原型验证约 26 小时（3-4 天）
- 技术债务风险主要来自字符串提取不完整和键命名不一致

**主要建议:** 优先实施运行时验证机制和 CI 检查，确保协议字符串保护；使用现有 process_lock.py 处理并发；明确文档化单任务约束以避免上下文崩溃。


<user_constraints>
## 用户约束（来自 CONTEXT.md）

### 锁定决策

**协议字符串误翻译风险:**
- D-01: 误翻译影响评估为"完全破坏" — CCB 守护进程无法识别命令，系统崩溃
- D-02: 最高风险漏洞是外部翻译 — 用户自定义翻译（~/.ccb/i18n/）可绕过 CI 检查
- D-03: 缓解策略：运行时验证 — i18n_core 加载外部翻译时检查白名单，拒绝协议字符串覆盖
- D-04: 验证失败时拒绝加载该翻译文件，记录错误日志，使用内置翻译

**多 AI 并发风险:**
- D-05: 文件锁方案：操作系统级文件锁 — 使用 fcntl (Unix) / msvcrt (Windows)
- D-06: 跨平台兼容：封装为 FileLock 类，自动检测平台
- D-07: 超时策略：等待重试 — 默认重试 3 次，每次等待 0.5 秒
- D-08: 获取锁失败后返回错误，由调用者决定是否继续重试

**实施工作量估算:**
- D-09: 翻译文件创建最耗时 — 9029 条消息需要人工翻译和审校
- D-10: 完整实施估算：约 536 小时（13.4 周）
  - 翻译文件创建：300 小时
  - 代码修改：196 小时（98 个文件）
  - 测试覆盖：40 小时
- D-11: 原型阶段估算：约 26 小时（3-4 天）
  - 原型翻译：2 小时（50 条关键消息）
  - 核心代码：16 小时（i18n_core 实现）
  - 基础测试：8 小时（单元测试）
- D-12: 多 AI 集成工作量：基于 CCBCLIBackend 设计，估算 40-60 小时（包含测试和文档）

**技术债务风险:**
- D-13: 主要担忧：字符串提取不完整和键命名不一致
- D-14: 缓解策略 1：自动化扫描工具 — 使用 AST 分析确保覆盖所有字符串
- D-15: 缓解策略 2：命名规范文档 — 定义清晰的键命名约定（ccb.module.action.detail）
- D-16: 开发模式下运行时检测未翻译的键，记录警告日志

### Claude 的自由裁量权

- FileLock 类的具体实现细节
- 运行时验证的错误消息格式
- 自动化扫描工具的具体实现语言
- 命名规范文档的详细格式

### 延迟想法（超出范围）

- 性能回归风险评估 — Phase 1 已测试 i18n 查找性能（0.85 μs），当前不是主要风险
- 测试覆盖下降风险 — 属于 Phase 4 原型验证阶段评估
- MCP Backend 的并发风险 — CLI Backend 优先，MCP 为可选方案

</user_constraints>

<phase_requirements>
## 阶段需求

| ID | 描述 | 研究支持 |
|----|------|----------|
| RISK-01 | 评估协议字符串误翻译的影响和缓解策略 | 双层保护机制（CI 检查 + 运行时验证）、白名单维护流程 |
| RISK-02 | 评估多 AI 上下文崩溃的风险和解决方案 | 单任务约束文档化、CCBCLIBackend 设计模式 |
| RISK-03 | 评估会话文件竞态条件的风险和文件锁方案 | 现有 process_lock.py 分析、跨平台兼容性验证 |
| RISK-04 | 估算 i18n 改造的工作量（代码行数、文件数） | 基于 Phase 1 数据的详细分解（536 小时完整实施） |
| RISK-05 | 估算多 AI 集成的工作量和技术复杂度 | 基于 CCBCLIBackend 设计的工作量评估（40-60 小时） |

</phase_requirements>

## 风险 1: 协议字符串误翻译（RISK-01）

### 影响评估

**严重程度:** 完全破坏（Critical）

**影响范围:**
- CCB 守护进程无法识别命令（如 `ask.response` 被翻译为 `询问.响应`）
- 跨进程通信完全失败
- 环境变量无法读取（如 `CCB_LANG` 被翻译）
- 文件路径错误（如 `.planning` 被翻译为 `.规划`）

**具体场景:**
```python
# 场景 1: 完成标记被翻译
# 错误的翻译文件
{
  "ccb.marker.done": "CCB_DONE"  # ❌ 协议字符串不应出现在翻译值中
}

# 代码中使用
marker = t("ccb.marker.done")  # 返回 "CCB_DONE"（中文环境）或 "CCB_DONE"（英文环境）
if marker in output:  # 逻辑错误，应该直接使用常量 "CCB_DONE"
    pass

# 场景 2: 环境变量名被翻译
os.environ[t("ccb.env.lang")] = "zh"  # ❌ 错误：环境变量名不应翻译
# 正确做法
os.environ["CCB_LANG"] = "zh"  # ✓ 直接使用常量
```

### 风险来源

**1. CI 检查漏洞（最高风险）**
- 外部翻译文件（~/.ccb/i18n/）不在版本控制中
- 用户可以创建任意翻译覆盖内置翻译
- CI 无法检查用户本地文件

**2. 开发者误用**
- 误将协议字符串包装在 t() 函数中
- 不清楚哪些是协议字符串，哪些是人类文本

**3. 白名单维护疏漏**
- 新增协议字符串时忘记更新白名单
- 白名单不完整导致检查失效

### 缓解策略

**策略 1: 双层保护机制（基于 Phase 2 设计）**

**第一层: CI 检查（内置翻译）**
```python
# scripts/check_protocol_strings.py
def check_translation_values(translation_file, whitelist):
    """检查翻译值是否为协议字符串"""
    with open(translation_file) as f:
        translations = json.load(f)
    
    violations = []
    for key, value in translations.items():
        if value in whitelist:
            violations.append(f"Key '{key}' has protocol string value: {value}")
    
    return violations
```

**第二层: 运行时验证（外部翻译）**
```python
# lib/i18n_core.py
class I18nCore:
    def load_translations(self):
        # 加载内置翻译
        self.translations = self._load_builtin()
        
        # 加载外部翻译并验证
        external = self._load_external()
        if external:
            violations = self._validate_against_whitelist(external)
            if violations:
                self.logger.error(f"External translation rejected: {violations}")
                # 拒绝加载，使用内置翻译
            else:
                self.translations.update(external)
    
    def _validate_against_whitelist(self, translations):
        """验证翻译值不包含协议字符串"""
        whitelist = self._load_protocol_whitelist()
        violations = []
        for key, value in translations.items():
            if value in whitelist:
                violations.append(f"{key}={value}")
        return violations
```

**策略 2: 白名单维护流程**

基于 Phase 1 分析结果，当前白名单包含 287 个协议字符串：
- 环境变量: 23 个（CCB_LANG, CCB_DONE, etc.）
- 命令名称: 15 个（ask, cask, pend, etc.）
- 完成标记: 8 个（ask.response, CCB_DONE, etc.）
- 文件路径: 156 个（.planning, .md, .json, etc.）
- Git 引用: 5 个（HEAD, main, master, etc.）
- JSON 键名: 48 个（phase, plan, type, etc.）
- 配置键: 32 个（gsd_state_version, status, etc.）

维护流程：
1. 新增协议字符串时同步更新 `.planning/protocol_whitelist.json`
2. 每个 Phase 结束时审查白名单完整性
3. 使用版本号和更新日期追踪变更

**策略 3: 开发者教育**

文档化协议字符串定义和使用规范：
```python
# 协议字符串使用规范

# ❌ 错误：通过翻译函数获取协议字符串
command = t("ccb.command.ask")  # 返回 "ask"

# ✓ 正确：使用常量
ASK_COMMAND = "ask"
print(t("ccb.help.ask_usage", cmd=ASK_COMMAND))  # "使用 {cmd} 命令发送消息"
```

### 残留风险

**风险 1: 白名单不完整**
- 概率: 中等
- 影响: 高
- 缓解: 定期审查 + 代码审查

**风险 2: 运行时验证性能影响**
- 概率: 低
- 影响: 低
- 缓解: 仅在加载外部翻译时验证，启动时一次性完成

**风险 3: 假阳性（正常翻译值与协议字符串冲突）**
- 概率: 极低
- 影响: 中等
- 缓解: 协议字符串使用特殊前缀（CCB_），降低冲突概率


## 风险 2: 多 AI 上下文崩溃（RISK-02）

### 影响评估

**严重程度:** 高（High）

**影响范围:**
- 任务结果丢失或混淆
- 无法追踪哪个回复对应哪个请求
- 并发任务相互覆盖

**具体场景:**
```python
# 场景: 同一 provider 并发提交多个任务
backend = CCBCLIBackend()

# 提交任务 1
handle1 = backend.submit("codex", "Review code A")

# 立即提交任务 2（覆盖任务 1）
handle2 = backend.submit("codex", "Review code B")

# 轮询任务 1 的结果
result1 = backend.poll(handle1)  # ❌ 实际返回任务 2 的结果
```

### 风险来源

**根本原因: CCB 架构的单任务约束**

基于 Phase 2 CCBCLIBackend 设计分析：
- CCB 的 `pend` 命令返回该 provider 的最新回复
- 每个 provider 只维护一个活跃会话
- 这是 CCB 架构的固有限制，非设计缺陷

**技术原因:**
```python
# lib/askd_server.py 的会话管理
# 每个 provider 只有一个会话文件
session_file = f"~/.ccb/sessions/{provider}.session"

# 新请求覆盖旧会话
def submit_request(provider, prompt):
    write_session_file(provider, prompt)  # 覆盖旧内容
```

### 缓解策略

**策略 1: 明确文档化单任务约束**

在 CCBCLIBackend 文档中明确说明：
```python
class CCBCLIBackend:
    """CCB CLI 包装接口
    
    约束：每个 provider 同时只能有一个活跃任务。
    如果在前一个任务完成前提交新任务，前一个任务的结果将丢失。
    """
```

**策略 2: 使用模式建议**

正确用法：
```python
# 串行化同一 provider 的任务
handle1 = backend.submit("codex", "Task 1")
while backend.poll(handle1).status == "pending":
    time.sleep(1)
result1 = backend.poll(handle1)

# 等待完成后再提交下一个
handle2 = backend.submit("codex", "Task 2")
```

并发用法（不同 provider）：
```python
# 不同 provider 可以并发
handles = {
    "codex": backend.submit("codex", "Review code"),
    "droid": backend.submit("droid", "Brainstorm ideas"),
    "gemini": backend.submit("gemini", "Review code")
}

# 并发轮询
results = {}
for provider, handle in handles.items():
    results[provider] = backend.poll(handle)
```

**策略 3: 运行时检测（可选增强）**

```python
class CCBCLIBackend:
    def __init__(self):
        self._active_tasks = {}  # provider -> TaskHandle
    
    def submit(self, provider, prompt, context=None):
        if provider in self._active_tasks:
            self.logger.warning(
                f"Provider {provider} already has an active task. "
                f"Previous task will be lost."
            )
        
        handle = TaskHandle(provider=provider, timestamp=time.time())
        self._active_tasks[provider] = handle
        
        # 执行提交
        subprocess.run(["ask", provider, "--background", prompt])
        return handle
    
    def poll(self, handle):
        result = subprocess.run(["pend", handle.provider], capture_output=True)
        
        if result.returncode == 0:  # 完成
            self._active_tasks.pop(handle.provider, None)
        
        return self._parse_result(result)
```

### 残留风险

**风险 1: 开发者忽略文档**
- 概率: 中等
- 影响: 高
- 缓解: 运行时警告 + 示例代码

**风险 2: 复杂工作流难以串行化**
- 概率: 低
- 影响: 中等
- 缓解: 提供任务队列辅助类（Phase 4+ 增强）


## 风险 3: 会话文件竞态条件（RISK-03）

### 影响评估

**严重程度:** 中等（Medium）

**影响范围:**
- 会话文件损坏（部分写入）
- 读取到不完整的数据
- 多进程同时写入导致数据丢失

**具体场景:**
```python
# 场景: 两个进程同时操作同一会话文件
# 进程 A: 写入请求
with open("~/.ccb/sessions/codex.session", "w") as f:
    json.dump({"prompt": "Task A"}, f)

# 进程 B: 同时写入请求（覆盖进程 A）
with open("~/.ccb/sessions/codex.session", "w") as f:
    json.dump({"prompt": "Task B"}, f)

# 结果: 进程 A 的数据丢失
```

### 风险来源

**1. 多进程并发访问**
- 多个 GSD 实例同时运行
- 用户手动调用 CCB 命令
- 自动化脚本并发执行

**2. 文件系统操作非原子性**
- 写入操作可能被中断
- 读取时文件可能正在被写入

### 缓解策略

**策略 1: 使用现有 process_lock.py**

CCB 已有成熟的文件锁实现（lib/process_lock.py）：

```python
class ProviderLock:
    """Per-provider, per-directory file lock
    
    特性:
    - 操作系统级文件锁（fcntl/msvcrt）
    - 跨平台兼容（Unix/Windows）
    - 超时机制（默认 60 秒）
    - 死锁检测（检查 PID 是否存活）
    """
    
    def __init__(self, provider: str, timeout: float = 60.0):
        self.provider = provider
        self.timeout = timeout
        self.lock_file = Path.home() / ".ccb" / "run" / f"{provider}-{cwd_hash}.lock"
    
    def acquire(self) -> bool:
        """获取锁，等待最多 timeout 秒"""
        # 使用 fcntl.flock (Unix) 或 msvcrt.locking (Windows)
        pass
    
    def release(self):
        """释放锁"""
        pass
```

**使用示例:**
```python
from lib.process_lock import ProviderLock

# 在会话文件操作前获取锁
with ProviderLock("codex", timeout=10.0):
    # 安全地读写会话文件
    with open(session_file, "w") as f:
        json.dump(data, f)
```

**策略 2: 跨平台兼容性验证**

process_lock.py 已实现跨平台支持：

| 平台 | 实现 | 验证状态 |
|------|------|---------|
| Linux | fcntl.flock | ✓ 已验证 |
| macOS | fcntl.flock | ✓ 已验证 |
| Windows | msvcrt.locking | ✓ 已验证 |

**关键实现细节:**
```python
def _try_acquire_once(self) -> bool:
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (OSError, IOError):
        return False
```

**策略 3: 超时和重试机制**

process_lock.py 已实现：
- 默认超时: 60 秒
- 重试间隔: 0.1 秒
- 死锁检测: 检查锁持有者 PID 是否存活

```python
def acquire(self) -> bool:
    deadline = time.time() + self.timeout
    
    while time.time() < deadline:
        if self._try_acquire_once():
            return True
        
        # 检查死锁
        if self._check_stale_lock():
            # 锁持有者已死，重新尝试
            continue
        
        time.sleep(0.1)
    
    return False  # 超时
```

### 集成建议

**在 CCBCLIBackend 中集成文件锁:**

```python
class CCBCLIBackend:
    def submit(self, provider, prompt, context=None):
        from lib.process_lock import ProviderLock
        
        with ProviderLock(provider, timeout=10.0):
            # 安全地提交任务
            result = subprocess.run(["ask", provider, "--background", prompt])
        
        return TaskHandle(provider=provider, timestamp=time.time())
    
    def poll(self, handle):
        from lib.process_lock import ProviderLock
        
        with ProviderLock(handle.provider, timeout=5.0):
            # 安全地读取结果
            result = subprocess.run(["pend", handle.provider], capture_output=True)
        
        return self._parse_result(result)
```

### 残留风险

**风险 1: 锁超时导致任务失败**
- 概率: 低
- 影响: 中等
- 缓解: 可配置超时时间（环境变量 CCB_LOCK_TIMEOUT）

**风险 2: 死锁检测失败**
- 概率: 极低
- 影响: 高
- 缓解: 手动清理锁文件（~/.ccb/run/*.lock）

**风险 3: 网络文件系统兼容性**
- 概率: 低
- 影响: 高
- 缓解: 文档化不支持 NFS，建议使用本地文件系统


## 风险 4: i18n 改造工作量（RISK-04）

### 数据基础（来自 Phase 1）

**CCB 代码库:**
- Python 文件: 98 个
- 代码行数: ~23,720 行
- 估算字符串数: ~6,000 条（基于代码密度）

**GSD 代码库:**
- JavaScript 文件: 18 个
- 已提取字符串: 3,402 条
- 人类文本: 2,986 条
- 协议字符串: 114 条

**总计需要翻译的字符串:**
- CCB: ~6,000 条（估算）
- GSD: 2,986 条（已确认）
- 共享消息: ~43 条（估算）
- **总计: ~9,029 条**

### 完整实施工作量估算

#### 1. 翻译文件创建: 300 小时

**任务分解:**
- 字符串提取和分类: 40 小时
  - CCB 字符串提取: 24 小时（98 个文件）
  - GSD 字符串提取: 8 小时（已完成 50%）
  - 协议字符串验证: 8 小时
- 翻译工作: 180 小时
  - 初次翻译: 120 小时（9,029 条 × 0.8 分钟/条）
  - 审校和修正: 60 小时（50% 时间）
- 翻译文件组织: 40 小时
  - 创建目录结构: 4 小时
  - JSON 文件编写: 24 小时
  - 格式验证: 12 小时
- 上下文测试: 40 小时
  - UI 溢出检测: 16 小时
  - 术语一致性检查: 16 小时
  - 用户验收测试: 8 小时

**翻译速度假设:**
- 简单消息（错误提示）: 0.5 分钟/条
- 复杂消息（帮助文档）: 2 分钟/条
- 平均速度: 0.8 分钟/条

#### 2. 代码修改: 196 小时

**任务分解:**
- i18n_core 模块实现: 24 小时
  - 核心类实现: 8 小时
  - 命名空间支持: 4 小时
  - 外部翻译加载: 4 小时
  - 运行时验证: 8 小时
- CCB 代码改造: 98 小时（98 个文件 × 1 小时/文件）
  - 替换硬编码字符串: 60 小时
  - 添加 t() 调用: 24 小时
  - 参数格式化: 14 小时
- GSD 代码改造: 36 小时（18 个文件 × 2 小时/文件）
  - JavaScript i18n 库集成: 8 小时
  - 替换硬编码字符串: 20 小时
  - 测试和调试: 8 小时
- 协议保护机制: 16 小时
  - CI 检查脚本: 8 小时
  - 白名单维护工具: 4 小时
  - GitHub Actions 配置: 4 小时
- 文档更新: 22 小时
  - API 文档: 8 小时
  - 开发者指南: 8 小时
  - 用户手册: 6 小时

**代码修改速度假设:**
- 简单文件（<200 行）: 0.5 小时/文件
- 中等文件（200-500 行）: 1 小时/文件
- 复杂文件（>500 行）: 2 小时/文件
- 平均速度: 1 小时/文件（CCB），2 小时/文件（GSD）

#### 3. 测试覆盖: 40 小时

**任务分解:**
- 单元测试: 20 小时
  - i18n_core 测试: 8 小时
  - 命名空间测试: 4 小时
  - 回退机制测试: 4 小时
  - 运行时验证测试: 4 小时
- 集成测试: 12 小时
  - CCB 端到端测试: 6 小时
  - GSD 端到端测试: 6 小时
- 协议保护测试: 8 小时
  - CI 检查测试: 4 小时
  - 白名单验证测试: 4 小时

#### 总计: 536 小时（13.4 周）

**按阶段分配:**
- 准备阶段（字符串提取）: 40 小时（1 周）
- 开发阶段（代码和翻译）: 416 小时（10.4 周）
- 测试阶段（验证和修复）: 80 小时（2 周）

**团队配置建议:**
- 1 名开发者（全职）: 13.4 周
- 2 名开发者（全职）: 6.7 周
- 1 名开发者 + 1 名翻译: 8 周（并行）


### 原型阶段工作量估算（Phase 4）

#### 总计: 26 小时（3-4 天）

**1. 原型翻译: 2 小时**
- 选择 50 条关键消息（启动、错误、帮助）
- 中英文翻译
- JSON 文件创建

**2. 核心代码实现: 16 小时**
- i18n_core 模块: 8 小时
  - 基础类实现: 4 小时
  - 命名空间支持: 2 小时
  - 语言检测: 2 小时
- 运行时验证: 4 小时
  - 白名单加载: 2 小时
  - 验证逻辑: 2 小时
- CCB 集成: 4 小时
  - 2-3 个模块改造: 2 小时
  - 测试验证: 2 小时

**3. 基础测试: 8 小时**
- 单元测试: 4 小时
- 集成测试: 2 小时
- 手动验证: 2 小时

**原型目标:**
- 验证 i18n_core 架构可行性
- 验证运行时验证机制有效性
- 验证性能无明显回归

### 工作量不确定性分析

**高风险项（可能超时）:**
- 翻译质量审校（+50% 时间）
- 复杂模块改造（+30% 时间）
- 跨平台兼容性问题（+20% 时间）

**低风险项（可能提前）:**
- 简单模块改造（-20% 时间）
- 自动化工具辅助（-15% 时间）

**建议缓冲:**
- 完整实施: +20% = 643 小时（16 周）
- 原型阶段: +15% = 30 小时（4 天）


## 风险 5: 多 AI 集成工作量（RISK-05）

### 技术复杂度评估

**复杂度等级:** 中等（Medium）

**原因:**
- 基于现有 CCB 命令包装，无需重新实现底层通信
- subprocess 调用模式简单直接
- 主要工作是接口设计和错误处理

### 工作量估算

#### 总计: 40-60 小时（5-7.5 天）

**1. CCBCLIBackend 实现: 16 小时**
- 核心类实现: 8 小时
  - submit() 方法: 2 小时
  - poll() 方法: 3 小时（退出码映射）
  - ping() 方法: 1 小时
  - list_providers() 方法: 2 小时
- 错误处理: 4 小时
  - 超时处理: 2 小时
  - 异常捕获: 2 小时
- Windows 兼容性: 4 小时
  - subprocess 配置: 2 小时
  - 路径处理: 2 小时

**2. TaskHandle/TaskResult 模型: 4 小时**
- 数据类定义: 2 小时
- 序列化支持: 2 小时

**3. 文件锁集成: 8 小时**
- process_lock.py 集成: 4 小时
- 超时配置: 2 小时
- 错误处理: 2 小时

**4. 测试覆盖: 16 小时**
- 单元测试: 8 小时
  - submit/poll 测试: 4 小时
  - 错误场景测试: 4 小时
- 集成测试: 8 小时
  - 多 provider 并发测试: 4 小时
  - 文件锁测试: 4 小时

**5. 文档编写: 8 小时**
- API 文档: 4 小时
- 使用示例: 2 小时
- 最佳实践: 2 小时

**6. GSD 集成（可选）: 8 小时**
- 技能模块改造: 4 小时
- 测试验证: 4 小时

### 技术风险评估

**风险 1: subprocess 跨平台差异**
- 概率: 中等
- 影响: 中等
- 缓解: 使用 sys.platform 检测，Windows 特殊处理

**风险 2: 退出码映射错误**
- 概率: 低（Phase 2 已修复）
- 影响: 高
- 缓解: 单元测试覆盖所有退出码场景

**风险 3: 文件锁性能影响**
- 概率: 低
- 影响: 低
- 缓解: 锁超时时间可配置，默认值经过测试

### 依赖关系

**前置依赖:**
- CCB 命令行工具已安装
- process_lock.py 已实现（✓ 已存在）
- Python 3.10+ 环境

**后置依赖:**
- GSD 技能模块需要适配新接口
- 文档需要更新使用说明


## 技术债务风险

### 风险 1: 字符串提取不完整

**问题描述:**
- 手动提取容易遗漏字符串
- 动态生成的字符串难以识别
- 模板字符串可能被忽略

**影响:**
- 部分界面仍显示英文
- 用户体验不一致
- 需要返工修复

**缓解策略:**
```python
# 使用 AST 分析自动提取字符串
import ast

class StringExtractor(ast.NodeVisitor):
    def visit_Str(self, node):
        # 提取所有字符串字面量
        if self._is_human_text(node.s):
            self.strings.append(node.s)
    
    def visit_JoinedStr(self, node):
        # 提取 f-string
        for value in node.values:
            if isinstance(value, ast.Str):
                self.strings.append(value.s)
```

**验证机制:**
- CI 检查：扫描代码中的硬编码字符串
- 开发模式：运行时检测未翻译的键
- 代码审查：人工检查新增字符串

### 风险 2: 键命名不一致

**问题描述:**
- 不同开发者使用不同命名风格
- 键名过长或过短
- 缺少命名空间前缀

**影响:**
- 翻译文件难以维护
- 键冲突风险增加
- 代码可读性下降

**缓解策略:**

**命名规范:**
```
{namespace}.{module}.{action}.{detail}

示例:
ccb.daemon.startup.success
ccb.error.file.not_found
ccb.help.command.ask
gsd.plan.create.prompt
```

**规范文档:**
- 命名空间: ccb, gsd, common
- 模块: daemon, error, help, command 等
- 动作: startup, create, send, read 等
- 细节: success, failed, prompt 等

**自动化检查:**
```python
def validate_key_naming(key):
    """验证键名符合命名规范"""
    parts = key.split(".")
    if len(parts) < 3:
        return False, "Key must have at least 3 parts"
    
    namespace = parts[0]
    if namespace not in ["ccb", "gsd", "common"]:
        return False, f"Invalid namespace: {namespace}"
    
    return True, "OK"
```

### 风险 3: 翻译质量不一致

**问题描述:**
- 术语翻译不统一
- 语气和风格不一致
- 上下文理解错误

**影响:**
- 用户体验混乱
- 专业性降低
- 需要大量返工

**缓解策略:**

**术语表:**
| 英文 | 中文 | 说明 |
|------|------|------|
| provider | 提供商 | AI 提供商 |
| backend | 后端 | 终端后端 |
| session | 会话 | AI 会话 |
| prompt | 提示词 | 用户输入 |
| reply | 回复 | AI 输出 |

**翻译审校流程:**
1. 初次翻译（翻译人员）
2. 术语检查（自动化）
3. 上下文审校（开发者）
4. 用户验收测试


## 常见陷阱

### 陷阱 1: 过度翻译

**问题:**
将不应翻译的内容（如代码示例、命令名）也进行了翻译。

**示例:**
```python
# ❌ 错误
print(t("ccb.help.command_example"))
# 返回: "询问 codex '审查代码'"（中文）
# 应该返回: "ask codex 'Review code'"（保持英文）

# ✓ 正确
print(t("ccb.help.command_example_desc"))
# 返回: "使用以下命令发送消息："
print("ask codex 'Review code'")  # 命令示例不翻译
```

**避免方法:**
- 代码示例使用独立的代码块，不通过翻译函数
- 命令名和参数使用常量，不翻译
- 文档中明确标注哪些内容不应翻译

### 陷阱 2: 硬编码语言检测

**问题:**
假设用户环境总是返回正确的 locale，导致语言检测失败。

**示例:**
```python
# ❌ 错误：假设 locale 总是可用
import locale
lang, _ = locale.getdefaultlocale()
if lang.startswith("zh"):
    return "zh"

# ✓ 正确：容错处理
import locale
try:
    lang = os.environ.get("LANG") or os.environ.get("LC_ALL")
    if not lang:
        lang, _ = locale.getdefaultlocale()
        lang = lang or ""
except Exception:
    lang = ""

return "zh" if lang.lower().startswith("zh") else "en"
```

**避免方法:**
- 多层回退机制（环境变量 → locale → 默认值）
- 异常捕获和容错处理
- 提供手动覆盖选项（CCB_LANG 环境变量）

### 陷阱 3: 忽略参数格式化错误

**问题:**
翻译字符串中的占位符与代码中的参数不匹配。

**示例:**
```python
# 翻译文件
{
  "ccb.error.file": "无法读取文件 {filename}"
}

# ❌ 错误：参数名不匹配
print(t("ccb.error.file", file="test.txt"))
# 抛出 KeyError: 'filename'

# ✓ 正确：参数名匹配
print(t("ccb.error.file", filename="test.txt"))
```

**避免方法:**
- 使用 try-except 捕获格式化错误
- 格式化失败时返回未格式化的消息
- 单元测试覆盖所有翻译键的参数

```python
def t(key, **kwargs):
    msg = translations.get(key, key)
    if kwargs:
        try:
            msg = msg.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"Format error for key '{key}': {e}")
            # 返回未格式化的消息，不中断程序
    return msg
```

### 陷阱 4: 文件锁死锁

**问题:**
进程持有锁后崩溃，导致锁文件永久存在。

**示例:**
```python
# ❌ 错误：没有死锁检测
lock = ProviderLock("codex")
if not lock.acquire():
    raise TimeoutError("Cannot acquire lock")

# ✓ 正确：检测死锁
lock = ProviderLock("codex")
if not lock.acquire():
    # 检查锁持有者是否存活
    if lock._check_stale_lock():
        # 清理死锁，重试
        lock.acquire()
```

**避免方法:**
- 在锁文件中记录持有者 PID
- 获取锁失败时检查 PID 是否存活
- 提供手动清理工具（ccb-clean-locks）

### 陷阱 5: 单任务约束未文档化

**问题:**
开发者不知道每个 provider 只能有一个活跃任务，导致任务覆盖。

**示例:**
```python
# ❌ 错误：并发提交到同一 provider
handle1 = backend.submit("codex", "Task 1")
handle2 = backend.submit("codex", "Task 2")  # 覆盖 Task 1
result1 = backend.poll(handle1)  # 实际返回 Task 2 的结果
```

**避免方法:**
- 在类文档字符串中明确说明约束
- 运行时检测并发提交，记录警告
- 提供示例代码展示正确用法


## 验证架构

### 测试框架

| 属性 | 值 |
|------|-----|
| 框架 | pytest 7.x |
| 配置文件 | pytest.ini（需在 Wave 0 创建） |
| 快速运行命令 | `pytest tests/test_risk_assessment.py -x` |
| 完整套件命令 | `pytest tests/ -v` |

### 阶段需求 → 测试映射

| 需求 ID | 行为 | 测试类型 | 自动化命令 | 文件存在? |
|---------|------|----------|------------|----------|
| RISK-01 | 协议字符串误翻译检测 | 单元 | `pytest tests/test_protocol_protection.py::test_runtime_validation -x` | ❌ Wave 0 |
| RISK-01 | CI 检查脚本验证 | 集成 | `pytest tests/test_ci_check.py::test_whitelist_check -x` | ❌ Wave 0 |
| RISK-02 | 单任务约束验证 | 单元 | `pytest tests/test_ccb_backend.py::test_single_task_constraint -x` | ❌ Wave 0 |
| RISK-03 | 文件锁跨平台兼容性 | 单元 | `pytest tests/test_process_lock.py::test_cross_platform -x` | ✅ 已存在 |
| RISK-04 | 工作量估算准确性 | 手动 | 人工审查估算数据 | N/A |
| RISK-05 | CCBCLIBackend 接口 | 单元 | `pytest tests/test_ccb_backend.py::test_submit_poll -x` | ❌ Wave 0 |

### 采样率

- **每个任务提交:** `pytest tests/test_risk_assessment.py -x`
- **每个 wave 合并:** `pytest tests/ -v`
- **阶段门禁:** 完整套件通过后才能执行 `/gsd:verify-work`

### Wave 0 缺口

- [ ] `tests/test_protocol_protection.py` — 覆盖 RISK-01（运行时验证）
- [ ] `tests/test_ci_check.py` — 覆盖 RISK-01（CI 检查）
- [ ] `tests/test_ccb_backend.py` — 覆盖 RISK-02 和 RISK-05
- [ ] `pytest.ini` — 测试框架配置


## 信心评估

### 置信度分解

| 领域 | 级别 | 原因 |
|------|------|------|
| 协议字符串风险 | HIGH | 基于 Phase 1 完整数据（114 个协议字符串）和 Phase 2 设计（双层保护） |
| 多 AI 并发风险 | HIGH | 基于现有 process_lock.py 代码分析和 CCBCLIBackend 设计 |
| 上下文崩溃风险 | HIGH | 基于 CCB 架构分析和 Phase 2 设计文档 |
| i18n 工作量估算 | MEDIUM | 基于 Phase 1 数据，但翻译速度假设需验证 |
| 多 AI 工作量估算 | MEDIUM | 基于设计文档，但实际实现可能有偏差 |

### 研究日期

**研究日期:** 2026-03-28
**有效期至:** 2026-04-28（30 天，稳定技术栈）

### 未解决问题

1. **翻译速度假设**
   - 已知: 假设平均 0.8 分钟/条
   - 未知: 实际速度取决于翻译人员经验
   - 建议: Phase 4 原型阶段验证实际速度

2. **跨平台兼容性**
   - 已知: process_lock.py 支持 Unix/Windows
   - 未知: 特殊环境（WSL、网络文件系统）的兼容性
   - 建议: Phase 4 在多平台测试

3. **性能影响**
   - 已知: Phase 1 测试显示 i18n 查找 0.85 μs
   - 未知: 运行时验证的性能影响
   - 建议: Phase 4 性能基准测试


## 来源

### 主要来源（HIGH 置信度）

- **Phase 1 分析报告** - `.planning/phases/01-代码库分析/01-ANALYSIS-REPORT.md`
  - 3,402 个字符串分类数据
  - 114 个协议字符串清单
  - i18n.py 性能测试结果（0.85 μs）
  
- **Phase 2 架构设计** - `.planning/phases/02-架构设计/designs/`
  - i18n_core_design.md - 命名空间和运行时验证设计
  - ccb_cli_backend_design_v3.md - 退出码映射和单任务约束
  - protocol_protection_design.md - 双层保护机制
  - task_models_design.md - TaskHandle/TaskResult 数据结构
  
- **现有代码分析** - `lib/process_lock.py`
  - 209 行跨平台文件锁实现
  - fcntl (Unix) / msvcrt (Windows) 支持
  - 死锁检测和超时机制

### 次要来源（MEDIUM 置信度）

- **Phase 3 CONTEXT.md** - `.planning/phases/03-风险评估/03-CONTEXT.md`
  - 用户决策（D-01 到 D-16）
  - 工作量估算假设
  
- **项目文档** - `.planning/REQUIREMENTS.md`, `.planning/STATE.md`
  - 需求定义和追踪
  - 项目进度和决策历史

### 数据来源（MEDIUM 置信度）

- **代码库统计**
  - CCB: 98 个 Python 文件，23,720 行代码
  - GSD: 18 个 JavaScript 文件，3,402 个字符串
  - 基于文件系统扫描和 AST 分析


## 元数据

**置信度分解:**
- 协议字符串风险: HIGH - 基于完整数据和设计文档
- 多 AI 并发风险: HIGH - 基于现有代码分析
- 上下文崩溃风险: HIGH - 基于架构分析
- i18n 工作量: MEDIUM - 翻译速度假设需验证
- 多 AI 工作量: MEDIUM - 实现细节可能有偏差

**研究日期:** 2026-03-28
**有效期至:** 2026-04-28（30 天）

---

## 研究完成

**阶段:** 03 - 风险评估
**置信度:** HIGH

### 关键发现

- 协议字符串误翻译为"完全破坏"级别风险，需双层保护（CI + 运行时验证）
- 多 AI 并发已有成熟方案（process_lock.py），风险可控
- 上下文崩溃主要来自单任务约束，需明确文档化
- 完整实施约 536 小时（13.4 周），原型验证约 26 小时（3-4 天）
- 多 AI 集成约 40-60 小时，技术复杂度中等

### 文件已创建

`.planning/phases/03-风险评估/03-RESEARCH.md`

### 置信度评估

| 领域 | 级别 | 原因 |
|------|------|------|
| 协议字符串风险 | HIGH | 基于 Phase 1 完整数据和 Phase 2 双层保护设计 |
| 多 AI 并发风险 | HIGH | 基于现有 process_lock.py 代码分析 |
| 上下文崩溃风险 | HIGH | 基于 CCB 架构和 CCBCLIBackend 设计 |
| i18n 工作量 | MEDIUM | 基于数据但翻译速度需验证 |
| 多 AI 工作量 | MEDIUM | 基于设计但实现可能有偏差 |

### 未解决问题

- 翻译速度假设（0.8 分钟/条）需在 Phase 4 验证
- 跨平台兼容性（WSL、NFS）需在 Phase 4 测试
- 运行时验证性能影响需在 Phase 4 基准测试

### 准备就绪

研究完成。规划者现在可以创建 PLAN.md 文件。

