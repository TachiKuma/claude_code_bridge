# Phase 2 架构设计修复总结

**修复日期:** 2026-03-28
**修复原因:** Codex 审核未通过（5.6/10），发现 4 个关键问题

---

## 修复的关键问题

### 1. CCBCLIBackend 任务模型重设计

**问题:** 客户端生成的 task_id 无法与 CCB 实际任务元数据绑定

**修复:**
- 移除客户端生成的 task_id
- 直接使用 provider 作为任务标识
- 简化 TaskHandle: `{provider, timestamp}`
- 简化 TaskResult: `{provider, status, output, error}`

**文件:**
- `designs/ccb_cli_backend_design_v2.md`
- `designs/task_models_design.md` (已更新)

### 2. subprocess 后台化机制修正

**问题:** 误用 shell `&` 符号，不符合 subprocess 工作方式

**修复:**
- 使用 CCB 内置的 `--background` 标志
- 使用 `subprocess.Popen()` 真正后台执行
- Windows 平台添加 `CREATE_NO_WINDOW` 标志

**代码示例:**
```python
subprocess.Popen(
    ["ask", provider, "--background", prompt],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True  # Unix/Linux/macOS
)
```

### 3. 命令映射修正

**问题:** 从 provider[0] 推导命令名称的逻辑脆弱且对 claude 失效

**修复:**
- poll(): 使用通用 `pend {provider}` 命令
- ping(): 使用通用 `ccb-ping {provider}` 命令
- 移除所有 provider[0] 推导逻辑

**映射表:**
| 方法 | 原设计 | 修复后 |
|------|--------|--------|
| poll() | `{provider[0]}pend` | `pend {provider}` |
| ping() | `{provider[0]}ping` | `ccb-ping {provider}` |

### 4. ccb-mounted 输出解析修正

**问题:** 假设返回纯文本，实际默认返回 JSON

**修复:**
- 正确解析 JSON 输出: `{"cwd": "...", "mounted": [...]}`
- 提取 `mounted` 字段

**代码示例:**
```python
result = subprocess.run(["ccb-mounted"], capture_output=True, text=True)
data = json.loads(result.stdout)
return data.get("mounted", [])
```

---

## 补充的改进点

### 5. i18n 日志系统设计

**问题:** Droid 指出缺少具体的错误日志机制实现细节

**补充:**
- 使用 Python logging 模块
- 定义 ERROR/WARNING/INFO/DEBUG 级别
- 配置日志输出到 stderr
- 支持 `CCB_LOG_LEVEL` 环境变量

**文件:** `designs/i18n_core_design.md` (已补充第 13 节)

### 6. Windows 兼容性设计

**问题:** Droid 指出 subprocess 在 Windows 下的兼容性未充分验证

**补充:**
- 使用 `STARTUPINFO` 和 `CREATE_NO_WINDOW` 标志
- 避免弹出控制台窗口
- 跨平台测试清单

**文件:** `designs/ccb_cli_backend_design_v2.md` (已补充第 14 节)

### 7. 协议字符串保护增强

**问题:** Codex 和 Droid 指出现有机制存在漏报风险

**补充:**
- 双层保护：值检查 + 静态代码扫描
- 扫描代码中误用 `t()` 包装协议字符串
- 优化白名单，使用完整协议字符串而非片段
- CI 集成方案

**文件:** `designs/protocol_protection_design.md` (已补充)

---

## 修复后的文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| ccb_cli_backend_design_v2.md | 新建 | 完全重写，修复所有关键问题 |
| task_models_design.md | 已更新 | 移除 task_id，简化模型 |
| i18n_core_design.md | 已补充 | 添加日志系统设计 |
| protocol_protection_design.md | 已补充 | 添加双层保护机制 |

---

## 下一步

重新提交给 codex 和 droid 审核，期望通过阈值（≥7.0）。
