# 02：项目级 Launch Plan 缓存与局部失效

**What to build:** 在 T01 的 `LaunchPlan` 指纹基础上，引入项目级缓存，按输入指纹失效。缓存命中时跳过对应的 provider home / settings 写入和启动动作。某个 agent 的缓存失效时只重建该 agent，不做全量重建。

缓存存放在 `.ccb/launch-plan-cache/` 目录下。

**Blocked by:** T01（需要 LaunchPlan 指纹作为缓存 key）。

**Status:** done（commit 见提交记录）

- [x] 定义缓存存储结构：`.ccb/launch-plan-cache/` 目录，每个缓存条目包含 agent_name、输入指纹、LaunchPlan 序列化、receipt hash、写入时间戳。
- [x] 缓存 key 设计：基于 T01 `LaunchPlan.fingerprint()` + project_id + agent_name 的稳定复合键，不包含 timestamp、seq 等运行时状态。
- [x] 缓存查询流程：读取缓存 → 比较指纹 → 指纹匹配时标记 "cache_hit" → skip provider home/settings 写入 → 直接进入 ready gate。
- [x] 缓存写入流程：预计算完成后写入缓存，写入原子性（避免部分写入）。
- [x] 局部失效：agent 配置变化时指纹改变 → 只重建该 agent 的缓存条目 → 其他 agent 缓存保留。
- [x] 缓存命中时不重复写 provider home / settings：只要 hash / receipt 一致，就跳过写入。
- [x] 缓存失效策略：输入指纹改变、项目 config 重新加载、用户显式 `ccb restart` / `ccb reload` 时清除指定 agent 的缓存。
- [x] 缓存不跨项目共享（每个项目独立的 `.ccb/launch-plan-cache/`）。
- [x] 缓存命中时跳过写入动作的记录应纳入启动度量：cache_hit count、写入跳过量、节省时间。
- [x] 缓存命中路径的并发安全：同一 agent 的多个 start 请求不应同时修改缓存。

**Validation:**

- `pytest -q test/test_v2_ccbd_start.py -k "launch_plan_cache"`
- 新增测试：相同配置的两次 start，第二次命中缓存且不产生重复 provider home 写入
- 新增测试：单个 agent 配置变化后缓存局部失效，不影响其他 agent 的缓存
- 新增测试：缓存目录不存在时回退到全量计算
- 新增测试：缓存 hash/receipt 不一致时触发重写
- 新增测试：缓存命中时启动度量记录 cache_hit

**Evidence:** 缓存按指纹正确命中/失效，命中时跳过重复写入，局部失效只影响单个 agent，project config 变化后准确重建受影响条目。