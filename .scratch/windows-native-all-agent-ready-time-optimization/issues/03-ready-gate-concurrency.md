# 03：Ready Gate 严格化与受限并发启动

**What to build:** 在预计算管线（T01）生成 `LaunchPlan` 后，对多个 agent 做受限并发启动。`Agent Ready` 保持严格门槛：Runtime Binding 已写入且可校验、provider 入口进入可接收任务状态、且至少一次 health/ping 成功。并发维持小上限，避免老机器 IO/CPU 争用放大。

**Blocked by:** T01（需要 LaunchPlan 和预计算结果做启动/健康检查输入）。

**Status:** done（commit 见提交记录）

- [x] Ready Gate 定义：agent 达到 Agent Ready 须同时满足三个条件：
  - binding 已写入且可通过 Herdr `snapshot` 或等价 API 校验
  - provider 入口已进入可接收任务状态（health check 成功）
  - 至少一次 health/ping 成功（不能只靠 pane 存在或 provider 横幅出现）
- [x] Ready Gate 不把「运行时完成」（Herdr `done`）、「进程存在」、「前台可见」或「provider banner 已出现」视为达到 Agent Ready。
- [x] Ready Gate 消费运行时事实（Herdr snapshot、health check 结果、binding 校验结果），但不把运行时事实升级为业务完成判定。
- [x] 并发上限设计：
  - 默认并发池大小：可配置上限（如 `max_concurrent_starts: 3`），通过 Project Config 或环境变量控制。
  - 老机器保护：IO 密集型操作（provider home 写入、binding 写入）串行或极小并发；网络密集型操作（health check）允许稍高并发。
  - 并发控制不阻塞预计算管线（预计算始终全并发）。
- [x] 启动结果模型保留每个 agent 的最终状态：
  - `agent_ready`：通过 ready gate
  - `agent_waiting`：仍在启动/收敛中
  - `agent_failed`：启动失败 + failure_reason（区分解析/计划/写入/启动/ready gate 阶段）
  - `agent_skipped`：因缓存命中跳过
- [x] Partial ready 状态可观测：用户能看到哪些 agent 已 ready、哪些仍在收敛、哪些失败。
- [x] 启动度量记录：总 ready 时间、每个 agent 的 ready 时间、并发等待时间、各阶段耗时分布。
- [x] 结果汇总：`start` 命令返回 `AllReadyResult`，包含所有 agent 的最终状态、时间度量和失败详情。

**Validation:**

- `pytest -q test/test_v2_ccbd_start.py -k "ready_gate"`
- `pytest -q test/test_runtime_launch_timings.py`
- 新增测试：binding 未写入时 ready gate 不通过（即使 health 成功）
- 新增测试：health ping 未完成时 ready gate 不通过
- 新增测试：并发上限生效（同一时间启动中的 agent ≤ 上限值）
- 新增测试：预计算阶段不受并发上限限制
- 新增测试：partial ready 结果模型区分 agent_ready/agent_waiting/agent_failed
- 新增测试：启动失败按阶段区分 failure_reason

**Evidence:** Ready Gate 严格三条件在全部 agent 上生效；并发上限在 IO/CPU 争用时保护老机器；partial ready 结果模型可区分就绪状态和工作阶段。