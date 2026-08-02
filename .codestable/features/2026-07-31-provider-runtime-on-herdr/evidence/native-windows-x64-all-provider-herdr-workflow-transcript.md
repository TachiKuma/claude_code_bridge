---
doc_type: feature-evidence
feature: 2026-07-31-provider-runtime-on-herdr
command_id: CMD-011
kind: native-windows-x64-all-provider-herdr-workflow-transcript
status: blocked
updated_at: 2026-08-03
---

# CMD-011 Native Windows x64 all-provider Herdr workflow transcript

## 结论

本轮完成了 Native Windows x64 host、Herdr 可用性、当前 public provider catalog snapshot 和 provider CLI 可用性探测；未执行真实 provider `ask` / `pend` / completion / cancel workflow。

阻塞原因：真实 provider workflow 会向外部 provider/API 或本机 AI bridge 发送请求，并可能消耗凭证/额度。本轮没有用户对生产 provider API 请求的明确授权，也没有逐 provider credential/session readiness 证明。因此全部公开 provider 行按 explicit blocked evidence 记录，不得宣称 supported。

## Snapshot reference

- snapshot: `.codestable/features/2026-07-31-provider-runtime-on-herdr/evidence/public-providers-snapshot.json`
- source: `lib/provider_core/registry_runtime/builtin_backends.py:5-23` 的 `CORE_PROVIDER_NAMES + OPTIONAL_PROVIDER_NAMES`
- equivalent registry output: `build_default_provider_catalog(include_optional=True, include_test_doubles=False).providers()`
- public provider count: 20
- catalog delta vs design baseline: 当前源码新增 `qoder`、`qoderclicn`，本 transcript 已覆盖为 blocked rows。

## Platform

```json
{
  "sys_platform": "win32",
  "machine": "AMD64",
  "python_bits": "64bit",
  "is_wsl": false
}
```

## Herdr availability

```text
$ C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe --version
exit_code: 0
stdout: herdr 0.7.5-preview.2026-07-29-44b3adb12552
```

## Provider CLI preflight

```text
$ Get-Command <provider>
codex      ExternalScript  C:\Users\Administrator\AppData\Roaming\npm\codex.ps1
claude     ExternalScript  C:\Users\Administrator\AppData\Roaming\npm\claude.ps1
gemini     ExternalScript  C:\Users\Administrator\AppData\Roaming\npm\gemini.ps1
opencode   ExternalScript  C:\Users\Administrator\AppData\Roaming\npm\opencode.ps1
droid      Application     C:\Users\Administrator\bin\droid.exe
agy        missing
kimi       missing
deepseek   missing
mimo       missing
qwen       missing
qoder      missing
qoderclicn missing
cursor     Application     d:\Program Files\cursor\resources\app\bin\cursor.cmd
copilot    missing
crush      missing
grok       missing
kiro       missing
pi         missing
omp        missing
zai        missing
```

## Per-provider workflow matrix

| provider | launch session payload | ask | pend/completion | cancel | evidence |
|---|---|---|---|---|---|
| codex | blocked | blocked | blocked | blocked | CLI exists, but live workflow would call external provider/API; no explicit production API authorization or credential readiness proof in this run. |
| claude | blocked | blocked | blocked | blocked | CLI exists, but live workflow would call external provider/API; no explicit production API authorization or credential readiness proof in this run. |
| gemini | blocked | blocked | blocked | blocked | CLI exists, but live workflow would call external provider/API; no explicit production API authorization or credential readiness proof in this run. |
| opencode | blocked | blocked | blocked | blocked | CLI exists, but live workflow would call external provider/API; no explicit production API authorization or credential readiness proof in this run. |
| droid | blocked | blocked | blocked | blocked | CLI exists, but live workflow would call external/local AI bridge provider; no explicit provider invocation authorization in this run. |
| agy | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| kimi | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| deepseek | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| mimo | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| qwen | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| qoder | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| qoderclicn | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| cursor | blocked | blocked | blocked | blocked | Command exists, but live provider workflow would require interactive/product credential readiness; no explicit production provider authorization in this run. |
| copilot | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| crush | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| grok | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| kiro | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| pi | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| omp | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |
| zai | blocked | blocked | blocked | blocked | Provider CLI missing from PATH; workflow not runnable on this host without installing/configuring provider CLI and credentials. |

## Scope decision

- 本 transcript 覆盖当前 catalog 的全部 20 个公开 provider，没有遗漏 provider row。
- 本 transcript 不等同于 all-provider supported 证据；它只满足逐 provider explicit blocked evidence。
- 后续 acceptance / public validation matrix 只有在每个 provider 的 Native Windows x64 Herdr launch、ask、pend/completion、cancel 均有通过 transcript 后，才可以把对应 provider 投影为 supported。

## Verdict

blocked
