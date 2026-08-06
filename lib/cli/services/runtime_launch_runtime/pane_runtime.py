from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import shutil
import tempfile

from .tmux_panes import launch_pane


def _resolve_sh_exe() -> str | None:
    """Windows 下 PowerShell pane 无 `sh` 命令；解析 Git Bash 的 sh.exe 完整路径。"""
    found = shutil.which('sh')
    if found:
        return str(found)
    for candidate in (
        r'C:\Program Files\Git\bin\sh.exe',
        r'C:\Program Files\Git\usr\bin\sh.exe',
        r'C:\Program Files\Git\cmd\sh.exe',
    ):
        if Path(candidate).exists():
            return candidate
    return None


def _herdr_launch_command(start_cmd: str, run_cwd: Path, spec_name: str) -> list[str]:
    """构造 herdr respawn 的启动命令 argv：PowerShell 调 sh.exe 执行 bash 脚本。

    herdr pane 的 shell 是 PowerShell，codex 启动命令是 bash 语法（export/codex）。
    直接注入会触发 PowerShell ReadLine/Parser 错误（无 sh 命令、嵌套引号解析）。
    方案（已实测）：把 start_cmd 写入 bash 脚本文件，respawn 注入
    `& <sh.exe> <script>` —— PowerShell 调 sh.exe 执行 bash 脚本，codex 进 pane。

    respawn_pane 经 HerdrCliRequestAdapter._respawn_pane 用 subprocess.list2cmdline
    把 command 当作 argv 拼成 `pane run` 命令行（cli.py:1363）；因此这里必须返回
    argv 片段（& + sh.exe + 脚本路径），不能返回已拼好的整条 PowerShell 字符串——
    后者会被 list2cmdline 整体加引号，在 PowerShell 里被当作字符串字面量回显而不执行
    （2026-08-06 herdr pane 实测）。
    """
    sh_exe = _resolve_sh_exe()
    if not sh_exe:
        # 无 sh.exe（非 Windows / Git Bash 缺失）：fallback 原注入（可能失败）
        return ['sh', '-lc', start_cmd]
    script_dir = Path(tempfile.gettempdir()) / 'ccb-agent-launch'
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / f'start-{spec_name}-{os.getpid()}.sh'
    script_path.write_text(f'cd {_sh_quote(str(run_cwd))} && {start_cmd}\n', encoding='utf-8')
    return ['&', sh_exe, script_path.as_posix()]


def _sh_quote(value: str) -> str:
    escaped = value.replace("'", "'\\''")
    return f"'{escaped}'"


def launch_runtime_pane(
    backend,
    *,
    spec_name: str,
    assigned_pane_id: str | None,
    assigned_pane_ref: Mapping[str, object] | None,
    start_cmd: str,
    run_cwd: Path,
    create_detached_tmux_pane_fn,
    pane_meets_minimum_size_fn,
    best_effort_kill_tmux_pane_fn,
    allow_detached_fallback: bool,
):
    if _is_herdr_pane_ref(assigned_pane_ref):
        pane_ref = dict(assigned_pane_ref or {})
        backend.respawn_pane(
            pane_ref,
            command=_herdr_launch_command(start_cmd, run_cwd, spec_name),
            cwd=str(run_cwd),
            env={},
        )
        _best_effort_capture_pane(backend, pane_ref)
        return pane_ref
    return launch_pane(
        backend,
        spec_name=spec_name,
        assigned_pane_id=assigned_pane_id,
        start_cmd=start_cmd,
        run_cwd=run_cwd,
        create_detached_tmux_pane_fn=create_detached_tmux_pane_fn,
        pane_meets_minimum_size_fn=pane_meets_minimum_size_fn,
        best_effort_kill_tmux_pane_fn=best_effort_kill_tmux_pane_fn,
        allow_detached_fallback=allow_detached_fallback,
    )


def pane_runtime_id(pane) -> str:
    if isinstance(pane, Mapping):
        return str(pane.get('pane_id') or '').strip()
    return str(pane or '').strip()


def _is_herdr_pane_ref(value) -> bool:
    return isinstance(value, Mapping) and str(value.get('backend_impl') or '').strip() == 'herdr'


def _best_effort_capture_pane(backend, pane_ref: Mapping[str, object]) -> None:
    capture = getattr(backend, 'capture_pane', None)
    if not callable(capture):
        return
    try:
        capture(dict(pane_ref), lines=1)
    except Exception:
        return


__all__ = [
    'launch_runtime_pane',
    'pane_runtime_id',
]
