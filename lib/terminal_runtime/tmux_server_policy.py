from __future__ import annotations

TMUX_ENVIRONMENT_KEYS = (
    "TERM",
    "TERM_PROGRAM",
    "TERM_PROGRAM_VERSION",
    "DISPLAY",
    "WAYLAND_DISPLAY",
    "XDG_RUNTIME_DIR",
    "WSL_DISTRO_NAME",
    "WSL_INTEROP",
    "SSH_AUTH_SOCK",
    "SSH_CONNECTION",
    "KITTY_WINDOW_ID",
    "WEZTERM_EXECUTABLE",
    "WEZTERM_PANE",
    "WEZTERM_UNIX_SOCKET",
    "CCB_WORKBENCH_PROFILE",
    "CCB_WORKBENCH_FORCE_RICH",
    "CCB_WORKBENCH_ROOT",
    "CCB_WORKBENCH_TERMINAL_PROGRAM",
    "CCB_WORKBENCH_TERMINAL_PROGRAM_VERSION",
    "CCB_WORKBENCH_YAZI_SAFE_CONFIG",
    "CCB_WORKBENCH_YAZI_RICH_CONFIG",
    "AGENT_ROLES_STORE",
)

CLIPBOARD_PIPE_COMMAND = (
    "sh -lc '"
    "tmp=$(mktemp \"${TMPDIR:-/tmp}/ccb-clipboard.XXXXXX\") || exit 0; "
    "cat >\"$tmp\"; "
    "if command -v wl-copy >/dev/null 2>&1 && [ -n \"${WAYLAND_DISPLAY:-}\" ]; then (wl-copy <\"$tmp\"; rm -f \"$tmp\") >/dev/null 2>&1 & "
    "elif command -v xclip >/dev/null 2>&1 && [ -n \"${DISPLAY:-}\" ]; then (xclip -selection clipboard <\"$tmp\"; rm -f \"$tmp\") >/dev/null 2>&1 & "
    "elif command -v xsel >/dev/null 2>&1 && [ -n \"${DISPLAY:-}\" ]; then (xsel --clipboard --input <\"$tmp\"; rm -f \"$tmp\") >/dev/null 2>&1 & "
    "elif command -v pbcopy >/dev/null 2>&1; then pbcopy <\"$tmp\"; rm -f \"$tmp\"; "
    "elif command -v powershell.exe >/dev/null 2>&1; then powershell.exe -NoProfile -Command \"[Console]::InputEncoding=[System.Text.UTF8Encoding]::new(); Set-Clipboard -Value ([Console]::In.ReadToEnd())\" <\"$tmp\"; rm -f \"$tmp\"; "
    "elif command -v pwsh >/dev/null 2>&1; then pwsh -NoLogo -NoProfile -Command \"[Console]::InputEncoding=[System.Text.UTF8Encoding]::new(); Set-Clipboard -Value ([Console]::In.ReadToEnd())\" <\"$tmp\"; rm -f \"$tmp\"; "
    "else rm -f \"$tmp\"; fi'"
)


__all__ = ["CLIPBOARD_PIPE_COMMAND", "TMUX_ENVIRONMENT_KEYS"]
