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
