# 01：Launch Plan 预计算管线

**What to build:** 在进入运行时动作之前，先对所有目标 agent 做只读解析与启动计划构建。Launch Plan 定义为某个 agent 启动运行时所需的可验证输入集合，包括 provider 入口、workdir、环境约束、session 锚点和 binding 预期。预计算管线产生每个 agent 的 `LaunchPlan` 对象，供后续 ready gate、缓存 key 和并发控制消费。

**Blocked by:** None（可以立即开始）。

**Status:** done (`82a6977d`)

- [x] 定义 `LaunchPlan` 数据模型，包含：provider 入口、workdir、环境约束、session 锚点、Runtime Binding 预期。
- [x] 设计预计算管线入口，接受目标 agent 列表，输出 `dict[agent_name, LaunchPlan]`。
- [x] 预计算管线只读：不创建 provider home、不写 binding、不启动任何进程；只解析 Project Config 和 inherited provider assets。
- [x] 预计算管线支持目标 agent 子集：允许只计算指定 subset，不需要每次都全量计算。
- [x] `LaunchPlan` 提供稳定的输入指纹（fingerprint/hash），供后续缓存失效和 affected agent 定位使用。
- [x] 指纹覆盖内容：provider 入口、model 选择、startup_args、env 集合、workdir、session 锚点；忽略运行时状态（timestamp、seq 等）。
- [x] 预计算管线在 `ccb start` 流程中位于「运行时动作」之前，确保所有 agent 的解析和计划构建先于任何写入/启动。
- [x] 预计算管线失败应返回结构化错误（哪个 agent、哪个阶段失败），不影响其他 agent 的计划构建。
- [x] 结果模型 `PrecomputeResult` 保留每个 agent 的 `LaunchPlan`、指纹、状态（ready/failed/skipped）。

**Validation:**

- `pytest -q test/test_v2_ccbd_start.py -k "launch_plan"`
- 新增测试：预计算管线不产生 provider home 写入
- 新增测试：预计算管线只读，不触发任何 Herdr/WezTerm 命令
- 新增测试：预计算管线按 subset 调用只计算指定 agent
- 新增测试：相同配置的 LaunchPlan 产生相同指纹；配置变化产生不同指纹

**Evidence:** 预计算管线在 start 流程中位于运行时动作之前，只读解析产生结构化 LaunchPlan，指纹稳定可复用。