---
doc_type: feature-evidence-pack
feature: 2026-07-31-windows-x64-release-surface
status: generated
---

# 2026-07-31-windows-x64-release-surface evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml`

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
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml\" --yaml-only",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\features\\2026-07-31-windows-x64-release-surface\\windows-x64-release-surface-checklist.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": null
    },
    {
      "command": "python \".codestable/tools/validate-yaml.py\" --file \".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml\"",
      "exit_code": 0,
      "stdout": "Validated 1 file(s): 1 passed, 0 failed.\n\n  ✓ .codestable\\roadmap\\windows-native-herdr-ccb\\windows-native-herdr-ccb-items.yaml\n\nAll files valid.\n",
      "stderr": "",
      "id": "CMD-002",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": null
    },
    {
      "command": "python -m pytest -q test/test_windows_x64_release_surface.py",
      "exit_code": 0,
      "stdout": ".....................                                                    [100%]\n21 passed in 1.73s\n",
      "stderr": "",
      "id": "CMD-003",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    },
    {
      "command": "python -m pytest -q test/test_cli_doctor_windows_x64_release_surface.py test/test_windows_bootstrap_script.py test/test_cli_management_update.py -k \"windows or release_surface or install or update or doctor\"",
      "exit_code": 0,
      "stdout": "................................................................         [100%]\n64 passed in 4.54s\n",
      "stderr": "",
      "id": "CMD-004",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    },
    {
      "command": "python -m pytest -q test/test_cli_doctor_rmux_packaging.py test/test_install_windows_rmux_contract.py test/test_rmux_packaging_docs_contracts.py",
      "exit_code": 0,
      "stdout": ".....                                                                    [100%]\n5 passed in 1.30s\n",
      "stderr": "",
      "id": "CMD-005",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    },
    {
      "command": "node -e \"const cp=require('child_process'); const out=process.platform==='win32'?cp.execFileSync('cmd',['/d','/s','/c','npm.cmd pack --dry-run --json'],{encoding:'utf8'}):cp.execFileSync('npm',['pack','--dry-run','--json'],{encoding:'utf8'}); const files=JSON.parse(out)[0].files.map(f=>f.path); if(!files.includes('lib/terminal_runtime/windows_x64_release_surface_projection.json')) throw new Error('projection JSON missing from npm pack payload')\"",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-006",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    },
    {
      "command": "python -c \"import pathlib,re,subprocess; roots=('lib','test','docs','README','README.md','package.json','bin','install.ps1'); run=lambda a: subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='ignore',check=True).stdout; tracked=run(['git','diff','--',*roots])+run(['git','diff','--cached','--',*roots]); others=[p for p in run(['git','ls-files','--others','--exclude-standard','--',*roots]).splitlines() if p]; extra=''.join(pathlib.Path(p).read_text(encoding='utf-8',errors='ignore') for p in others if pathlib.Path(p).is_file()); lower=(tracked+extra).lower(); q='['+chr(34)+chr(39)+']?'; patterns=('npm\\\\s+publish','git\\\\s+push','git\\\\s+tag','support_tier\\\\s*[:=]\\\\s*'+q+'supported'+q,'windows\\\\s+x64\\\\s+(is\\\\s+)?(fully\\\\s+|stable\\\\s+)?supported','full\\\\s+windows\\\\s+x64\\\\s+support','stable\\\\s+windows\\\\s+x64\\\\s+support','release[_ -]?promotion\\\\s*[:=]\\\\s*(true|enabled)','provider_completion','recovery_owner'); hits=[p for p in patterns if re.search(p,lower)]; assert not hits,hits\"",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-007",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "existing"
    },
    {
      "command": "python -m pytest -q test/test_windows_x64_release_surface_dependency_admission.py",
      "exit_code": 0,
      "stdout": "..                                                                       [100%]\n2 passed in 0.83s\n",
      "stderr": "",
      "id": "CMD-009",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    },
    {
      "command": "python -m pytest -q test/test_windows_x64_release_surface_baseline_version.py",
      "exit_code": 0,
      "stdout": "..                                                                       [100%]\n2 passed in 0.88s\n",
      "stderr": "",
      "id": "CMD-010",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    },
    {
      "command": "python -m pytest -q test/test_windows_x64_release_surface_update_rollback.py",
      "exit_code": 0,
      "stdout": "...                                                                      [100%]\n3 passed in 1.98s\n",
      "stderr": "",
      "id": "CMD-012",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    },
    {
      "command": "python -c \"import pathlib,re; p=pathlib.Path('docs/ccbd-diagnostics-contract.md'); bad=[(i+1,line.rstrip()) for i,line in enumerate(p.read_text(encoding='utf-8').splitlines()) if 'doctor --bundle' in line.lower() and not re.search(r'deprecated|unsupported|no longer supported|not supported', line, re.I)]; assert not bad,bad\"",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-013",
      "core": true,
      "failure_handling": "fix-or-block",
      "test_status": "new"
    }
  ],
  "providers": {}
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 38724
Checklist bytes: 18834

## 5. Residual Risks

- CMD-008 是 Native Windows diagnostic transcript：覆盖 npm route、install.ps1 projection、update diagnostic-only、doctor 和 doctor --output projection；未执行真实 `install.ps1 install`，不能当作真实 source/dev install transcript。
- CMD-011 只有 blocked evidence 和 fake rollback unit；未执行真实 `install.ps1 uninstall`、用户 PATH cleanup 或 skills cleanup。QA / acceptance 必须按 blocked evidence 复核，不能把它当作真实 cleanup transcript。

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
        ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml",
        ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml",
        "README.md",
        "README/ar.md",
        "README/de.md",
        "README/es.md",
        "README/fr.md",
        "README/ja.md",
        "README/ko.md",
        "README/pt.md",
        "README/ru.md",
        "README/zh.md",
        "bin/ccb-npm-install.js",
        "docs/ccbd-diagnostics-contract.md",
        "install.ps1",
        "lib/cli/management_runtime/commands_runtime/update.py",
        "lib/cli/render_runtime/ops_views_doctor.py",
        "lib/cli/services/doctor.py",
        "package.json",
        "test/test_cli_management_update.py",
        ".codestable/features/2026-07-31-windows-x64-release-surface/evidence/cmd-011-windows-cleanup-rollback-blocked-evidence.md",
        ".codestable/features/2026-07-31-windows-x64-release-surface/evidence/cmd-013-s13-scope-guard-package-cleanliness.md",
        ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-evidence-pack.md",
        ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-implementation.md",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-driver-observation.md",
        "lib/terminal_runtime/windows_x64_release_surface.py",
        "lib/terminal_runtime/windows_x64_release_surface_projection.json",
        "test/test_cli_doctor_rmux_packaging.py",
        "test/test_cli_doctor_windows_x64_release_surface.py",
        "test/test_install_windows_rmux_contract.py",
        "test/test_rmux_packaging_docs_contracts.py",
        "test/test_windows_x64_release_surface.py",
        "test/test_windows_x64_release_surface_baseline_version.py",
        "test/test_windows_x64_release_surface_dependency_admission.py",
        "test/test_windows_x64_release_surface_update_rollback.py"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-dod-results.json",
        ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-evidence-pack-results.json",
        ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-gate-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-07-31-windows-x64-release-surface",
        ".codestable/features/2026-07-31-windows-x64-release-surface",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml",
        ".codestable/roadmap/windows-native-herdr-ccb/goal-driver-observation.md",
        "lib",
        "test",
        "docs",
        "README",
        "README.md",
        "package.json",
        "bin",
        "install.ps1"
      ]
    }
  ],
  "providers": {}
}
```
