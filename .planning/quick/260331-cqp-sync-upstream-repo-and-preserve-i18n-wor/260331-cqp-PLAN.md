---
phase: quick-sync-upstream
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - bin/ask
  - bin/ccb-completion-hook
  - ccb
  - lib/askd/adapters/base.py
  - lib/askd/adapters/claude.py
  - lib/askd/adapters/codebuddy.py
  - lib/askd/adapters/codex.py
  - lib/askd/adapters/copilot.py
  - lib/askd/adapters/droid.py
  - lib/askd/adapters/gemini.py
  - lib/askd/adapters/opencode.py
  - lib/askd/adapters/qwen.py
  - lib/askd/daemon.py
  - lib/completion_hook.py
  - test/test_stability_regressions.py
autonomous: false
requirements: []
must_haves:
  truths:
    - "All 10 upstream commits are merged into our main branch"
    - "No i18n translations or t() calls are lost or reverted"
    - "bin/ask contains both upstream _caller_pane_info() and our i18n t() calls"
    - "ccb contains both upstream launch_args/launch_env support and our i18n t() calls"
    - "VERSION is updated to 5.2.9"
    - "All pane title markers include project_id[:8] suffix from upstream"
    - "Upstream-only files (adapters, completion_hook, test) merge cleanly"
  artifacts:
    - path: "bin/ask"
      provides: "CLI with i18n + upstream caller pane routing"
      contains: ["_caller_pane_info", "from i18n import t"]
    - path: "ccb"
      provides: "Main launcher with i18n + upstream features"
      contains: ['VERSION = "5.2.9"', "launch_args", "launch_env", "project_id[:8]"]
    - path: "lib/completion_hook.py"
      provides: "Upstream hardened completion hook"
    - path: "test/test_stability_regressions.py"
      provides: "Upstream test additions"
  key_links:
    - from: "bin/ask"
      to: "lib/i18n.py"
      via: "from i18n import t import"
      pattern: "from i18n import t"
    - from: "ccb"
      to: "lib/i18n.py"
      via: "from i18n import t import"
      pattern: "from i18n import t"
---

<objective>
Merge 10 upstream commits from bfly123/claude_code_bridge:main into our fork,
preserving all i18n internationalization work (309 t() calls, 278 translation keys).

Purpose: Get upstream bug fixes (caller pane routing, SIGHUP cleanup, pane title
uniqueness, completion hook hardening, launch_args/launch_env) while keeping
our 95-commit i18n branch intact.

Output: A merged main branch with upstream fixes + i18n, zero conflict markers,
all tests passing.
</objective>

<execution_context>
@E:/GitHub开源项目/TachiKuma/claude_code_bridge/.claude/get-shit-done/workflows/execute-plan.md
@E:/GitHub开源项目/TachiKuma/claude_code_bridge/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
# Upstream commits to merge (10 commits, from cached upstream/main):

1. `6f2bcaf` fix: use bracketed paste + send-key Enter for WezTerm completion hook response
2. `af5cc56` feat: add per-provider launch_args and launch_env support in ccb.config
3. `357e407` fix: thread caller pane ID through ask chain for cross-instance isolation
4. `be5f83e` fix: harden completion hook auto-submit and add debug tracing
5. `65c62a8` fix: add project_id suffix to pane title markers for multi-directory uniqueness
6. `b7598b3` fix: handle SIGHUP to clean up processes on terminal close (issue #155)
7-10: Merge PR commits (#150, #151, #154, #156) - no additional code changes

# Files changed by upstream (15 files):
- bin/ask, bin/ccb-completion-hook, ccb
- lib/askd/adapters/{base,claude,codebuddy,codex,copilot,droid,gemini,opencode,qwen}.py
- lib/askd/daemon.py, lib/completion_hook.py
- test/test_stability_regressions.py

# Potential conflict files (2 files - modified by BOTH upstream and us):

## bin/ask
- Upstream: Added `_caller_pane_info()` function (new, after line 96), modified
  `_send_via_unified_daemon()` to pass caller_pane_id/caller_terminal in RPC request,
  added pane env vars in Windows/Unix background task launchers.
- Ours (i18n): Added `from i18n import t` import, replaced hardcoded strings in
  `_require_caller()`, `_usage()`, `main()` with t() calls.
- **No overlap**: upstream touches lines ~96-100 (new function) and ~346-360, ~685-760
  (RPC/env). Ours touches lines ~46 (import), ~466-500 (_require_caller, _usage),
  ~510-620 (main error messages). These regions do not overlap.

## ccb
- Upstream: VERSION 5.2.8->5.2.9, AILauncher.__init__ launch_args/launch_env params,
  pane title markers with project_id[:8] suffix, SIGHUP handler, launch_args append
  to provider start commands.
- Ours (i18n): Added `from i18n import t` import + `resolve_language_setting` import,
  replaced hardcoded strings in `cmd_mail()`, `cmd_droid_subcommand()`, added
  `_extract_global_lang_arg()` and `cmd_config()`.
- **No overlap**: upstream touches AILauncher class internals and pane titles.
  Ours touches cmd_mail (line ~4709) and cmd_droid_subcommand (line ~4808) at the
  end of the file. These regions do not overlap.

# Strategy: git merge upstream/main with ours as the base. Since regions don't
overlap, git should auto-resolve. If manual resolution needed, accept BOTH sides.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Merge upstream/main into our fork</name>
  <files>
    bin/ask
    bin/ccb-completion-hook
    ccb
    lib/askd/adapters/base.py
    lib/askd/adapters/claude.py
    lib/askd/adapters/codebuddy.py
    lib/askd/adapters/codex.py
    lib/askd/adapters/copilot.py
    lib/askd/adapters/droid.py
    lib/askd/adapters/gemini.py
    lib/askd/adapters/opencode.py
    lib/askd/adapters/qwen.py
    lib/askd/daemon.py
    lib/completion_hook.py
    test/test_stability_regressions.py
  </files>
  <action>
    Perform a git merge of upstream/main into HEAD:

    ```bash
    git fetch upstream 2>/dev/null || echo "fetch failed, using cached"
    git merge upstream/main --no-edit
    ```

    If git reports conflicts (expected on bin/ask and ccb), resolve them:

    **bin/ask conflict resolution:**
    - Accept BOTH upstream changes (_caller_pane_info function, caller_pane_id in RPC,
      pane env vars in launchers) AND our i18n changes (from i18n import t, t() calls
      in _require_caller/_usage/main).
    - These modify different line ranges, so both should be present. If git creates
      conflict markers, manually combine: keep all upstream additions + all our t() calls.

    **ccb conflict resolution:**
    - Accept BOTH upstream changes (VERSION 5.2.9, launch_args/launch_env params,
      project_id[:8] in pane titles, SIGHUP handler) AND our i18n changes (t() calls
      in cmd_mail/cmd_droid_subcommand, _extract_global_lang_arg, cmd_config).
    - For VERSION line: use upstream's "5.2.9".
    - These modify different regions (upstream in AILauncher class, ours in CLI
      command functions at end of file), so both should coexist.

    After merge, verify no conflict markers remain:
    ```bash
    grep -rn "<<<<<<\|======\|>>>>>>" bin/ask ccb lib/askd/adapters/ lib/completion_hook.py
    ```

    If conflict markers found, fix them. If ANY i18n t() call was lost, restore it.
  </action>
  <verify>
    <automated>cd "E:/GitHub开源项目/TachiKuma/claude_code_bridge" && grep -rn "<<<<<<\|======\|>>>>>>" bin/ask ccb lib/askd/adapters/ lib/completion_hook.py; echo "EXIT:$?"</automated>
  </verify>
  <done>
    - All 10 upstream commits merged (verify: git log --oneline -12 includes upstream commits)
    - Zero conflict markers in any file
    - bin/ask contains both _caller_pane_info() and from i18n import t
    - ccb contains both VERSION = "5.2.9" and from i18n import t
    - All pane title markers include project_id[:8] suffix
    - launch_args and launch_env support present in AILauncher.__init__
  </done>
</task>

<task type="auto">
  <name>Task 2: Validate merge integrity</name>
  <files>
    bin/ask
    ccb
    lib/i18n.py
    lib/i18n/ccb/en.json
    lib/i18n/ccb/zh.json
  </files>
  <action>
    Run comprehensive post-merge validation:

    1. **Count t() calls preserved:**
       ```bash
       grep -c "t(" bin/ask
       # Expect: same count as before merge (our i18n additions intact)
       grep -c "t(" ccb
       ```

    2. **Verify i18n import present:**
       ```bash
       grep "from i18n import t" bin/ask ccb
       # Must appear in both files
       ```

    3. **Verify upstream features present:**
       ```bash
       # caller pane routing
       grep "_caller_pane_info" bin/ask
       grep "caller_pane_id" bin/ask
       # launch_args/launch_env
       grep "launch_args" ccb
       grep "launch_env" ccb
       # VERSION
       grep 'VERSION = "5.2.9"' ccb
       # SIGHUP
       grep "SIGHUP" ccb
       # pane title uniqueness
       grep "project_id\[:8\]" ccb
       ```

    4. **Run existing tests:**
       ```bash
       python -m pytest test/ -x -q --timeout=30 2>/dev/null || python -m pytest test/ -x -q 2>/dev/null || echo "no pytest"
       ```

    5. **Verify all 15 upstream-modified files exist and have content:**
       ```bash
       for f in bin/ask bin/ccb-completion-hook ccb lib/askd/adapters/base.py lib/askd/adapters/claude.py lib/askd/adapters/codebuddy.py lib/askd/adapters/codex.py lib/askd/adapters/copilot.py lib/askd/adapters/droid.py lib/askd/adapters/gemini.py lib/askd/adapters/opencode.py lib/askd/adapters/qwen.py lib/askd/daemon.py lib/completion_hook.py test/test_stability_regressions.py; do test -f "$f" && echo "OK: $f" || echo "MISSING: $f"; done
       ```
  </action>
  <verify>
    <automated>
      cd "E:/GitHub开源项目/TachiKuma/claude_code_bridge" && python -c "
      checks = []
      # i18n imports
      for f in ['bin/ask', 'ccb']:
          with open(f, encoding='utf-8', errors='replace') as fh:
              content = fh.read()
          has_i18n = 'from i18n import t' in content
          checks.append(f'{f}: i18n import = {has_i18n}')
          # no conflict markers
          has_conflict = '<<<<<<<' in content or '>>>>>>>' in content
          checks.append(f'{f}: no conflict markers = {not has_conflict}')
      # upstream features in ccb
      with open('ccb', encoding='utf-8', errors='replace') as fh:
          ccb = fh.read()
      checks.append(f'ccb: VERSION 5.2.9 = {\"VERSION = \\\"5.2.9\\\"\" in ccb}')
      checks.append(f'ccb: launch_args = {\"launch_args\" in ccb}')
      checks.append(f'ccb: SIGHUP = {\"SIGHUP\" in ccb}')
      # upstream features in bin/ask
      with open('bin/ask', encoding='utf-8', errors='replace') as fh:
          ask = fh.read()
      checks.append(f'bin/ask: _caller_pane_info = {\"_caller_pane_info\" in ask}')
      checks.append(f'bin/ask: caller_pane_id = {\"caller_pane_id\" in ask}')
      for c in checks:
          print(c)
      ok = all('True' in c or '= True' in c for c in checks)
      print(f'ALL PASS: {ok}')
      exit(0 if ok else 1)
      "
    </automated>
  </verify>
  <done>
    - All i18n imports present in both bin/ask and ccb
    - Zero conflict markers in any file
    - All 6 upstream features verified present (caller_pane_info, launch_args,
      launch_env, VERSION 5.2.9, SIGHUP, project_id pane titles)
    - Tests pass (or no test framework available but no regressions)
    - All 15 upstream-modified files exist with content
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Merged upstream/main (10 commits) with all i18n work preserved</what-built>
  <how-to-verify>
    1. Run `git log --oneline -15` and confirm upstream commits appear (6f2bcaf, af5cc56, etc.)
    2. Run `git diff upstream/main -- bin/ask ccb` and confirm only OUR i18n additions remain
       as differences (no upstream code missing)
    3. Set CCB_LANG=zh and run `./bin/ask --help` — confirm Chinese output (i18n works)
    4. Set CCB_LANG=en and run `./bin/ask --help` — confirm English output
    5. Run `ccb --help` and confirm no errors, VERSION shows 5.2.9
    6. Grep for conflict markers: `grep -rn "<<<<<<" bin/ ccb lib/` — expect zero results
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues to fix</resume-signal>
</task>

</tasks>

<verification>
1. `git log --oneline HEAD -15` shows upstream commits merged after our i18n commits
2. `grep -rn "<<<<<<" bin/ ccb lib/` returns zero matches (no conflict markers)
3. `grep "from i18n import t" bin/ask ccb` returns 2 matches
4. `grep 'VERSION = "5.2.9"' ccb` returns 1 match
5. `grep "_caller_pane_info" bin/ask` returns matches (upstream feature present)
6. All i18n t() call counts match pre-merge baseline
</verification>

<success_criteria>
- 10 upstream commits successfully merged with zero data loss
- All i18n work (309 t() calls, 278 keys, i18n_core, i18n_runtime) fully preserved
- All upstream features functional (caller pane routing, SIGHUP cleanup, pane title
  uniqueness, completion hook hardening, launch_args/launch_env)
- No conflict markers remain in any file
- Both en and zh locales work correctly post-merge
</success_criteria>

<output>
After completion, create `.planning/quick/260331-cqp-sync-upstream-repo-and-preserve-i18n-wor/260331-cqp-SUMMARY.md`
</output>
