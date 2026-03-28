# Phase 2 架构设计修复总结 v3

**修复日期:** 2026-03-28
**修复原因:** Codex 第二次审核未通过（6.0/10），发现退出码映射错误

---

## v3 关键修复

### 1. poll() 退出码映射修正

**问题:** v2 设计将 EXIT_NO_REPLY(2) 误判为 error

**修复:**
```python
# v2 错误设计
if result.returncode != 0:
    return TaskResult(status="error")  # EXIT_NO_REPLY 被误判

# v3 正确设计
if result.returncode == 0:      # EXIT_OK
    return TaskResult(status="completed", output=stdout)
elif result.returncode == 2:    # EXIT_NO_REPLY
    return TaskResult(status="pending")
else:                            # EXIT_ERROR
    return TaskResult(status="error", error=stderr)
```

### 2. 单任务约束明确化

**问题:** v2 隐含约束未明确文档化

**修复:**
- 明确说明每个 provider 同时只能有一个活跃任务
- 提供正确和错误的使用示例
- 说明这是 CCB 架构限制，非设计缺陷

### 3. submit() 实现优化

**问题:** v2 使用 Popen + DEVNULL 丢失调试信息

**修复:**
- 使用 subprocess.run() 保留输出
- 便于调试和故障排查

---

## 修复后的文件

- `designs/ccb_cli_backend_design_v3.md` (新建)
- 基于 CCB 实际退出码：EXIT_OK(0)、EXIT_ERROR(1)、EXIT_NO_REPLY(2)

---

## 期望结果

Codex 评分 >= 7.0，通过审核阈值
