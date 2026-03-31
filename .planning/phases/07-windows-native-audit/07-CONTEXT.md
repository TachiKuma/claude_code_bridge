# Phase 7: Windows 原生环境专项检查 - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

专项检查项目在原生 Windows 环境中安装后用户使用时的性能、兼容性和安全性，输出问题清单、量化数据和提升方案，并按优先级实施全部修复。

三大维度必须全面覆盖：
1. **性能**：daemon 启动延迟、命令响应时间、内存占用、socket 通信效率、文件 I/O
2. **兼容性**：编码处理（UTF-8/GBK/其他）、路径转换、PowerShell 版本兼容、终端模拟器差异
3. **安全性**：文件权限、敏感信息泄露、进程隔离、token 处理、代码注入风险、socket 通信安全、daemon 提权检查

</domain>

<decisions>
## Implementation Decisions

### 检查维度与优先级
- **D-01:** 全面覆盖性能、兼容性、安全性三大维度，不做裁剪
- **D-02:** 性能和兼容性列为重点关注方向（用户同时选择了"全部三大维度"和"性能优先、兼容性优先、安全性优先"）

### 检查方法
- **D-03:** 使用 pytest 测试套件实现全面自动化测试，集成到现有测试体系
- **D-04:** 在当前原生 Windows 10 Pro 环境中直接运行所有测试和检查
- **D-05:** 检查深度为"全面自动化测试"——建立可回归的自动化测试套件覆盖核心场景

### 性能基准线（严格指标）
- **D-06:** daemon 冷启动 < 3 秒
- **D-07:** 命令响应 < 500ms（从用户输入到响应输出）
- **D-08:** 内存占用 < 50MB（daemon 常驻进程）

### 兼容性编码覆盖
- **D-09:** 全面编码覆盖——不仅 UTF-8，还必须验证 GBK、Windows-1252、Shift-JIS 等其他 Windows 常见编码的回退行为
- **D-10:** 重点关注中文路径、中文内容、PowerShell 5.1 兼容性

### 安全检查深度
- **D-11:** 深入渗透级别——包含代码注入风险评估、socket 通信安全审计、daemon 提权路径检查
- **D-12:** 检查范围：文件权限、敏感信息泄露、进程隔离、token 处理、eval/exec 滥用、subprocess 参数注入、socket 认证机制

### 交付形式
- **D-13:** 先输出完整问题清单 + 提升方案文档
- **D-14:** 然后按优先级逐项实施修复，覆盖所有发现的问题（Critical/High/Medium/Low 全部修复）

### 测试框架
- **D-15:** 使用 pytest 编写测试用例，覆盖 Windows 特定场景
- **D-16:** 测试应覆盖以下核心场景：编码处理、路径转换、daemon 生命周期、socket 通信、文件锁、进程管理、install.ps1 安装流程

### Claude's Discretion
- 测试文件的组织结构和命名约定
- 性能测试的具体实现方式（timeit、pytest-benchmark 或自定义计时器）
- 问题严重程度的分级标准（基于影响范围和发生概率）
- 修复的优先级排序策略
- pytest fixture 和 conftest 的组织方式

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Windows 兼容性核心
- `lib/compat.py` — Windows UTF-8 编码设置和 stdin 解码
- `lib/terminal.py` — Windows 子进程标志（CREATE_NO_WINDOW）、WSL 路径处理、WezTerm 集成
- `lib/process_lock.py` — Windows 进程检测（kernel32.OpenProcess）
- `lib/file_lock.py` — Windows 文件锁（msvcrt.locking）
- `lib/ccb_config.py` — Windows 环境检测、WSL 路径探测

### 安装与配置
- `install.ps1` — PowerShell 安装脚本（UTF-8 BOM 兼容、Python 检测、shebang 修复）
- `install.cmd` — Windows 批处理安装入口

### 入口与通信
- `ccb` — 主入口，路径规范化（Windows/WSL/MSYS）
- `bin/ask` — 后台任务 PowerShell 脚本生成、进程标志
- `lib/askd_server.py` — RPC 服务器（socket 通信）
- `lib/askd_client.py` — RPC 客户端
- `lib/askd/daemon.py` — daemon 进程管理

### 现有测试参考
- `tests/test_i18n_core.py` — 现有 i18n 测试模式参考
- `tests/test_stability_regressions.py` — 上游新增的稳定性回归测试

### 安全相关
- `lib/session_utils.py` — 会话文件操作（文件权限）
- `lib/pane_registry.py` — pane 注册表持久化
- `lib/cli_output.py` — CLI 输出格式化

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lib/compat.py` — 已有 `setup_windows_encoding()` 和 `decode_stdin_bytes()` 编码工具
- `lib/file_lock.py` — 已有跨平台文件锁实现（Windows msvcrt + Unix fcntl）
- `lib/process_lock.py` — 已有 Windows 进程检测（ctypes kernel32）
- `tests/` — 现有测试目录结构

### Established Patterns
- pytest 测试模式：`tests/test_*.py` 命名约定
- Windows 检测模式：`os.name == "nt"` / `sys.platform == "win32"` / `platform.system() == "Windows"`
- 子进程 Windows 处理：`CREATE_NO_WINDOW` / `DETACHED_PROCESS` / `CREATE_NEW_PROCESS_GROUP`
- 错误处理：多层级编码回退（UTF-8 → locale → mbcs）

### Integration Points
- `ccb` 主入口是所有功能的起点，Windows 路径处理在此集中
- `bin/ask` 的 PowerShell 脚本生成是 Windows 后台任务的核心
- daemon 生命周期通过 `lib/askd/daemon.py` 管理，socket 通信是性能关键路径
- `install.ps1` 是用户首次接触的 Windows 体验

### 已知 Windows 问题线索
1. `lib/compat.py` 中 `mbcs` 编码可能丢失数据
2. `lib/terminal.py` 的 WSL 路径处理逻辑复杂
3. `bin/ask` 生成的 PowerShell 脚本依赖 PS 5.1+
4. `lib/ccb_config.py` 的 WSL 探测在纯 Windows 环境可能失效
5. `os.chmod(0o600)` 在 Windows NTFS 上效果有限

</code_context>

<specifics>
## Specific Ideas

- 性能测试应包含 daemon 冷启动、热启动、重复命令调用、长时间运行后的内存增长
- 兼容性测试应模拟中文目录路径（如 `C:\用户\桌面\测试项目\`）、含空格路径、UNC 路径
- 安全测试应检查 daemon socket 是否有认证机制、token 是否在日志/临时文件中泄露
- 安装测试应验证 install.ps1 在不同 PowerShell 版本（5.1、7.x）中的行为

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---
*Phase: 07-windows-native-audit*
*Context gathered: 2026-03-31*
