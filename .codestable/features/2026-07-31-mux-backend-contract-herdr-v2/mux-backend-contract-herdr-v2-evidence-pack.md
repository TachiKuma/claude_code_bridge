---
doc_type: feature-evidence-pack
feature: 2026-07-31-mux-backend-contract-herdr-v2
status: generated
---

# 2026-07-31-mux-backend-contract-herdr-v2 evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-design.md`
- Checklist: `.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-checklist.yaml`

## 2. DoD Results

```json
{
  "gate_id": "dod-runner",
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-31-mux-backend-contract-herdr-v2\\mux-backend-contract-herdr-v2-checklist.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml\"",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\roadmap\\windows-native-herdr-ccb\\windows-native-herdr-ccb-items.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-002",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py",
      "exit_code": 0,
      "stdout": "..............                                                           [100%]\n14 passed in 0.22s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -m pytest -q test/test_v2_project_namespace_backend.py",
      "exit_code": 0,
      "stdout": "................                                                         [100%]\n16 passed in 0.28s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -c \"import pathlib,re,subprocess; run=lambda a: subprocess.run(a,capture_output=True,text=True,check=True).stdout; collect=lambda a: run(a).splitlines(); untracked=[p.replace(chr(92),'/') for p in collect(['git','ls-files','--others','--exclude-standard']) if p.strip()]; paths={p.replace(chr(92),'/') for a in (['git','diff','--name-only'],['git','diff','--cached','--name-only','--diff-filter=ACMR']) for p in collect(a) if p.strip()}; paths.update(untracked); forbidden_prefix=('lib/provider_backends/','lib/provider_runtime/','lib/ccbd/services/project_namespace_state_runtime/','lib/cli/services/doctor_runtime/'); forbidden_files={'package.json','package-lock.json','install.ps1','install.sh','install.cmd','README.md','docs/ccbd-diagnostics-contract.md','bin/ccb-npm-install.js','lib/cli/management_runtime/install.py','lib/cli/management_runtime/commands_runtime/install.py','lib/cli/services/doctor.py','lib/cli/render_runtime/ops_views_doctor.py','lib/terminal_runtime/rmux_packaging_support.py','lib/terminal_runtime/rmux_packaging_support_projection.json'}; allowed_terminal={'lib/terminal_runtime/mux_backend_contract.py','lib/terminal_runtime/fake_mux_backend.py','lib/terminal_runtime/backend_resolver.py','lib/terminal_runtime/backend_selection.py'}; bad=sorted(p for p in paths if p.startswith(forbidden_prefix) or p in forbidden_files or (p.startswith('lib/terminal_runtime/herdr') and p not in allowed_terminal)); assert not bad, bad; untracked_text=''.join('\\n'+pathlib.Path(p).read_text(encoding='utf-8',errors='ignore') for p in untracked if (p.startswith(('lib/','bin/')) or p in {'package.json','install.ps1','install.sh','install.cmd','README.md','docs/ccbd-diagnostics-contract.md'}) and pathlib.Path(p).is_file()); guard_paths=['lib','package.json','install.ps1','install.sh','install.cmd','README.md','docs/ccbd-diagnostics-contract.md','bin/ccb-npm-install.js','lib/cli/management_runtime/install.py','lib/cli/management_runtime/commands_runtime/install.py']; text=run(['git','diff','--']+guard_paths)+run(['git','diff','--cached','--']+guard_paths)+untracked_text; forbidden=re.compile(r'(class\\s+Herdr.*(Client|Adapter|Schema)|def\\s+.*herdr.*socket|socket[_-]?api|schema[_-]?parser|HerdrSocket|production Herdr adapter|support_tier.*(beta|supported)|windows.*herdr.*supported)', re.I); assert not forbidden.search(text)\"",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "python -c \"import json, pathlib; src=pathlib.Path('.codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json'); fixture=pathlib.Path('.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/evidence/herdr-capability-blocked-fixture.json'); reasons={'herdr-capability-missing','platform-gate-blocked','unsupported-capability','schema-mismatch','herdr-unavailable'}; allowed={'supported','partial','unsupported','workaround'}; load=lambda p: json.loads(p.read_text(encoding='utf-8')); values=lambda m: list((m or {}).values()); has_unknown=lambda m: any(v=='unknown' for v in values(m)); invalid_status=lambda m: any(v not in allowed for v in values(m)); blocked_ok=lambda d: d.get('blocked') is True and d.get('backend_family')=='herdr-native' and d.get('backend_impl')=='herdr' and d.get('requested_backend') in {'herdr','auto'} and d.get('fallback_used') is not True and d.get('effective_backend') in (None,'herdr') and d.get('failure_reason') in reasons; d=load(src) if src.exists() else None; p=(d or {}).get('capability_projection') or {}; rec=(d or {}).get('adapter_recommendation'); verdict=(d or {}).get('verdict'); failure=(d or {}).get('failure_class'); command=p.get('command_status'); semantic=p.get('semantic_status'); must_block=(not src.exists()) or rec not in {'continue','continue-with-gaps'} or rec in {'stop','needs-upstream-issue'} or verdict in {'blocked','failed'} or failure not in (None,'','none') or bool(p.get('blocking_gaps')) or has_unknown(command) or has_unknown(semantic) or invalid_status(command) or invalid_status(semantic); assert not must_block or blocked_ok(load(fixture))\"",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "fix-or-block"
    }
  ],
  "providers": {},
  "feature": "2026-07-31-mux-backend-contract-herdr-v2",
  "inputs": {
    "checklist": ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-checklist.yaml"
  },
  "input_digests": {
    "checklist": "94bec113441a734dc04ee52f9e6f9dff7fb7bef54014ac081f96259ff705ac2d"
  }
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 22967
Checklist bytes: 10796

## 5. Residual Risks

- provider signals `archguard` and `meta_cc` were skipped by configuration, so this pack only reflects local gates and focused tests.

## 6. Provider Signals

```json
{
  "archguard": {
    "status": "skipped",
    "reason": "archguard collection disabled",
    "warnings": []
  },
  "meta_cc": {
    "status": "skipped",
    "reason": "meta-cc collection disabled",
    "warnings": []
  }
}
```

## 7. Gate Results

```json
{
  "gate_id": "scope-gate",
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "changed_files": [
        ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-checklist.yaml",
        "test/test_herdr_spike_no_production_route.py",
        "test/test_mux_backend_contract.py",
        "test/test_terminal_runtime_backend_selection.py",
        ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2/evidence/evidence-pack-results.json",
        ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2/evidence/herdr-capability-blocked-fixture.json",
        ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2/evidence/scope-gate.json",
        ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-evidence-pack.md",
        "lib/terminal_runtime/backend_resolver.py",
        "lib/terminal_runtime/fake_mux_backend.py",
        "lib/terminal_runtime/mux_backend_contract.py"
      ],
      "ignored_machine_artifacts": [],
      "allowed_prefixes": [
        ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2",
        "lib/terminal_runtime",
        "test/test_mux_backend_contract.py",
        "test/test_terminal_runtime_backend_selection.py",
        "test/test_herdr_spike_no_production_route.py"
      ]
    }
  ],
  "providers": {},
  "feature": "2026-07-31-mux-backend-contract-herdr-v2",
  "inputs": {
    "feature_dir": ".codestable/features/2026-07-31-mux-backend-contract-herdr-v2"
  },
  "input_digests": {}
}
```
