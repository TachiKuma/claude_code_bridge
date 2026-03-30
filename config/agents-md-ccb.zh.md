<!-- CCB_ROLES_START -->
## 角色分配

抽象角色映射到具体 AI provider。skills 引用角色，而不是直接引用 provider。

| Role | Provider | Description |
|------|----------|-------------|
| `designer` | `claude` | 主要负责规划与架构，拥有方案设计职责 |
| `inspiration` | `gemini` | 创意发散参考，只提供灵感（不可靠，不能盲从） |
| `reviewer` | `codex` | 评分质量闸门，按 Rubrics 评估方案与代码 |
| `executor` | `claude` | 代码实现执行者，负责实际编写与修改 |

要修改角色分配，请编辑上表中的 Provider 列。
当某个 skill 引用角色（例如 `reviewer`）时，请把它解析成这里配置的 provider。
<!-- CCB_ROLES_END -->

<!-- REVIEW_RUBRICS_START -->
## Review Rubrics 与模板

当你（Codex）收到来自 `designer` 的 review request 时，按以下 rubrics 打分。

### Rubric A: Plan Review（5 个维度，每项 1-10）

| # | Dimension             | Weight | What to evaluate                                                  |
|---|-----------------------|--------|-------------------------------------------------------------------|
| 1 | Clarity               | 20%    | 步骤是否清晰无歧义，其他开发者能否直接执行                        |
| 2 | Completeness          | 25%    | 是否覆盖所有需求、边界情况与交付物                                |
| 3 | Feasibility           | 25%    | 是否能基于当前代码库与依赖真正落地                                |
| 4 | Risk Assessment       | 15%    | 是否识别风险并给出具体缓解措施                                    |
| 5 | Requirement Alignment | 15%    | 每一步是否都能追溯到明确需求，且没有范围蔓延                      |

**Overall Plan Score** = Clarity×0.20 + Completeness×0.25 + Feasibility×0.25 + Risk×0.15 + Alignment×0.15

### Rubric B: Code Review（6 个维度，每项 1-10）

| # | Dimension        | Weight | What to evaluate                                                |
|---|------------------|--------|-----------------------------------------------------------------|
| 1 | Correctness      | 25%    | 代码是否按方案工作，是否存在逻辑错误                            |
| 2 | Security         | 15%    | 是否存在注入、硬编码密钥、输入校验缺失等问题                    |
| 3 | Maintainability  | 20%    | 代码是否整洁、命名是否清晰、是否符合项目约定                    |
| 4 | Performance      | 10%    | 是否存在不必要的 O(n²)、阻塞调用或资源浪费                      |
| 5 | Test Coverage    | 15%    | 新增/修改路径是否有测试覆盖，测试是否通过                       |
| 6 | Plan Adherence   | 15%    | 实现是否与已批准的 plan 保持一致                                 |

**Overall Code Score** = Correctness×0.25 + Security×0.15 + Maintainability×0.20 + Performance×0.10 + TestCoverage×0.15 + PlanAdherence×0.15

### 返回格式

打分时返回以下 JSON 结构。

#### Plan Review Response

```json
{
  "review_type": "plan",
  "dimensions": {
    "clarity": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "completeness": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "feasibility": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "risk_assessment": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "requirement_alignment": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." }
  },
  "overall": N.N,
  "critical_issues": ["blocking issues that MUST be fixed"],
  "summary": "one-paragraph overall assessment"
}
```

#### Code Review Response

```json
{
  "review_type": "code",
  "dimensions": {
    "correctness": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "security": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "maintainability": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "performance": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "test_coverage": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." },
    "plan_adherence": { "score": N, "strengths": ["..."], "weaknesses": ["..."], "fix": "..." }
  },
  "overall": N.N,
  "critical_issues": ["blocking issues that MUST be fixed"],
  "summary": "one-paragraph overall assessment"
}
```
<!-- REVIEW_RUBRICS_END -->
