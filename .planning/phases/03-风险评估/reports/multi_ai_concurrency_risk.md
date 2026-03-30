# 多 AI 上下文崩溃风险评估报告

**评估日期:** 2026-03-30
**需求:** RISK-02
**严重程度:** 高（High）

---

## 1. 执行摘要

**风险描述:** 在 GSD 使用 CCB 多 AI 协作时，如果同一 provider 并发提交多个任务，会导致任务结果覆盖和追踪混淆。

**根本原因:** CCB 架构的单任务约束 — 每个 provider 同时只能有一个活跃任务。这是 CCB 会话管理的固有限制，每个 provider 只维护一个会话文件。

**影响范围:**
- 任务结果丢失或混淆
- 无法追踪哪个回复对应哪个请求
- 并发任务相互覆盖

**缓解策略:**
1. 明确文档化单任务约束
2. 提供正确的使用模式建议
3. 运行时检测并发提交并记录警告

**残留风险:** 开发者忽略文档导致误用（中等概率），复杂工作流串行化困难（低概率）

---

## 2. 风险影响评估

### 2.1 任务结果覆盖场景

**场景描述:**
```python
backend = CCBCLIBackend()

# 提交任务 1
handle1 = backend.submit("codex", "Review code A")

# 立即提交任务 2（覆盖任务 1）
handle2 = backend.submit("codex", "Review code B")

# 轮询任务 1 的结果
result1 = backend.poll(handle1)  # ❌ 实际返回任务 2 的结果
```

**影响:**
- 任务 1 的结果永久丢失
- handle1 返回错误的结果
- 开发者无法区分哪个结果对应哪个任务

### 2.2 追踪混淆场景

**场景描述:**
```python
# 并发提交多个任务到同一 provider
handles = []
for i in range(5):
    handle = backend.submit("codex", f"Task {i}")
    handles.append(handle)

# 尝试收集所有结果
results = []
for handle in handles:
    result = backend.poll(handle)
    results.append(result)  # ❌ 所有 handle 返回相同结果（最后一个任务）
```

**影响:**
- 只有最后一个任务的结果可用
- 前 4 个任务的结果全部丢失
- 结果列表包含 5 个相同的回复

---

## 3. 根本原因分析

### 3.1 CCB 架构约束

基于 CCBCLIBackend 设计分析（ccb_cli_backend_design_v3.md）：

**单任务约束说明:**
- CCB 的 `pend` 命令返回该 provider 的最新回复
- 每个 provider 只维护一个活跃会话
- 这是 CCB 架构的固有限制，非设计缺陷

### 3.2 技术原因

**会话文件管理:**
```python
# lib/askd_server.py 的会话管理
# 每个 provider 只有一个会话文件
session_file = f"~/.ccb/sessions/{provider}.session"

# 新请求覆盖旧会话
def submit_request(provider, prompt):
    write_session_file(provider, prompt)  # 覆盖旧内容
```

**pend 命令行为:**
```bash
# pend 命令返回最新回复
$ ask codex "Task 1" --background
$ ask codex "Task 2" --background
$ pend codex
# 只返回 Task 2 的结果，Task 1 的结果已被覆盖
```

---

## 4. 缓解策略

### 4.1 明确文档化单任务约束

**在 CCBCLIBackend 类文档中说明:**
```python
class CCBCLIBackend:
    """CCB CLI 包装接口，提供结构化的多 AI 协作能力

    约束：每个 provider 同时只能有一个活跃任务。
    如果在前一个任务完成前提交新任务，前一个任务的结果将丢失。

    正确用法：
    - 串行化同一 provider 的任务（等待完成后再提交下一个）
    - 不同 provider 可以并发使用

    错误用法：
    - 同时提交多个任务到同一 provider
    """
```

### 4.2 使用模式建议

**正确用法 1: 串行化同一 provider**
```python
# 等待第一个任务完成后再提交第二个
handle1 = backend.submit("codex", "Task 1")
while backend.poll(handle1).status == "pending":
    time.sleep(1)
result1 = backend.poll(handle1)

# 等待完成后再提交下一个
handle2 = backend.submit("codex", "Task 2")  # 安全
```

**正确用法 2: 不同 provider 并发**
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
    while True:
        result = backend.poll(handle)
        if result.status != "pending":
            results[provider] = result
            break
        time.sleep(1)
```

**错误用法示例:**
```python
# ❌ 错误：同时提交多个任务到同一 provider
handle1 = backend.submit("codex", "Task 1")
handle2 = backend.submit("codex", "Task 2")  # 会覆盖 Task 1
```

### 4.3 运行时检测（可选增强）

**实现方案:**
```python
class CCBCLIBackend:
    def __init__(self):
        self._active_tasks = {}  # provider -> TaskHandle
        self.logger = logging.getLogger(__name__)

    def submit(self, provider, prompt, context=None):
        # 检测并发提交
        if provider in self._active_tasks:
            self.logger.warning(
                f"Provider {provider} already has an active task. "
                f"Previous task (timestamp: {self._active_tasks[provider].timestamp}) will be lost."
            )

        handle = TaskHandle(provider=provider, timestamp=time.time())
        self._active_tasks[provider] = handle

        # 执行提交
        subprocess.run(["ask", provider, "--background", prompt])
        return handle

    def poll(self, handle):
        result = subprocess.run(["pend", handle.provider], capture_output=True, text=True)

        # 任务完成后清理追踪
        if result.returncode == 0:  # EXIT_OK
            self._active_tasks.pop(handle.provider, None)

        return self._parse_result(result)
```

**警告日志示例:**
```
WARNING: Provider codex already has an active task. Previous task (timestamp: 1774832527.123) will be lost.
```

---

## 5. 残留风险评估

### 5.1 开发者忽略文档

**风险描述:** 开发者未阅读文档，直接使用 CCBCLIBackend 并发提交任务。

**概率:** 中等
**影响:** 高
**缓解措施:**
- 在类文档字符串中突出显示约束
- 提供清晰的示例代码
- 运行时警告提醒开发者

### 5.2 复杂工作流串行化困难

**风险描述:** 某些工作流需要同一 provider 处理多个任务，串行化导致性能下降。

**概率:** 低
**影响:** 中等
**缓解措施:**
- 使用不同 provider 分担负载
- 提供任务队列辅助类（Phase 4+ 增强）
- 文档化性能权衡

---

## 6. 实施建议

### 6.1 优先级

**高优先级:**
- 在 CCBCLIBackend 类文档中明确说明单任务约束
- 提供正确和错误的使用示例

**中优先级:**
- 实现运行时检测和警告日志

**低优先级:**
- 开发任务队列辅助类（Phase 4+）

### 6.2 时间估算

- 文档更新: 2 小时
- 运行时检测实现: 4 小时
- 单元测试: 2 小时
- **总计: 8 小时**

### 6.3 验收标准

- [ ] CCBCLIBackend 类文档包含单任务约束说明
- [ ] 提供至少 2 个正确用法示例
- [ ] 提供至少 1 个错误用法示例
- [ ] 运行时检测能够识别并发提交
- [ ] 警告日志包含有用的调试信息
- [ ] 单元测试覆盖并发提交场景

---

## 7. 结论

多 AI 上下文崩溃的风险主要来自 CCB 架构的单任务约束。通过明确文档化约束、提供使用模式建议和运行时检测，可以有效降低风险。残留风险主要是开发者忽略文档，可通过运行时警告进一步缓解。

**关键要点:**
- 每个 provider 同时只能有一个活跃任务
- 串行化同一 provider 的任务
- 不同 provider 可以并发使用
- 运行时警告帮助开发者发现问题

---

**报告完成日期:** 2026-03-30
**下一步:** 实施文档更新和运行时检测
