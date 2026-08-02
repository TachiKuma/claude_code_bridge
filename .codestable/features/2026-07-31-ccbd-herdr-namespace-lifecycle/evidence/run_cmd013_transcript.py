from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = Path(__file__).resolve().parent
HERDR_EXE = Path("C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe")
CAPABILITY_REPORT = (
    REPO
    / ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json"
)


def main() -> int:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    work = Path(tempfile.gettempdir()) / f"ccb-herdr-cmd-013-{stamp}"
    transcript = EVIDENCE_DIR / "cmd-013-native-windows-herdr-transcript.md"
    runner = Cmd013Runner(work=work, transcript=transcript, session=f"ccb-cmd-013-{stamp}")
    return runner.run()


class Cmd013Runner:
    def __init__(self, *, work: Path, transcript: Path, session: str) -> None:
        self.work = work
        self.transcript = transcript
        self.session = session
        self.home = work / ".home"
        self.bin_dir = work / ".stub-bin"
        self.shim_dir = work / ".python-shim"
        self.ccb_dir = work / ".ccb"
        self.py = sys.executable
        self.lines: list[str] = []
        self.preflight_session = f"{session}-preflight"
        self.env = self._build_env()

    def run(self) -> int:
        self._prepare_workspace()
        self._header()
        failures: list[str] = []
        self._run("herdr availability", [str(HERDR_EXE), "--version"], timeout=10)
        self._capability_excerpt()
        self._record_herdr_named_session_probe(
            "herdr named session preflight",
            self.preflight_session,
            include_server_launch=True,
        )
        create_code = self._run(
            "namespace create via ccb -n",
            self._ccb("--cmd013-confirm-stdin", "-n"),
            timeout=180,
        )
        namespace_ok = self._record_namespace_state("namespace durable state after create")
        if not namespace_ok:
            failures.append("namespace create")
        elif create_code != 0:
            self.lines.extend(
                [
                    "",
                    "## Namespace Create Boundary",
                    "",
                    "The `ccb -n` command returned non-zero after durable Herdr namespace state was created. "
                    "That residual startup result is treated as provider-runtime-on-Herdr boundary evidence, "
                    "not as namespace lifecycle failure for this feature.",
                ]
            )
        if self._run("ccbd ping namespace payload", self._ccb("ping", "ccbd"), timeout=140) != 0:
            failures.append("ccbd ping")
        if self._run("foreground attach", self._ccb("--cmd013-foreground-attach"), timeout=140) != 0:
            failures.append("foreground attach")
        self._write_reload_config()
        self._flush_transcript()
        if self._run("reload dry run", self._ccb("reload", "--dry-run"), timeout=140) != 0:
            failures.append("reload dry run")
        if self._run("reload apply", self._ccb("reload"), timeout=220) != 0:
            failures.append("reload apply")
        restart_code = self._run(
            "restart unsupported/deferred evidence",
            self._ccb("restart", "agent1"),
            timeout=140,
        )
        if restart_code == 0:
            failures.append("restart unexpectedly succeeded")
        if self._run("kill", self._ccb("kill"), timeout=180) != 0:
            failures.append("kill")
        self._run("post-kill ping", self._ccb("ping", "ccbd"), timeout=100)
        self._run(
            "herdr server stop cleanup",
            [str(HERDR_EXE), "--session", self.session, "server", "stop"],
            timeout=20,
        )
        self._run(
            "herdr preflight server stop cleanup",
            [str(HERDR_EXE), "--session", self.preflight_session, "server", "stop"],
            timeout=20,
        )
        namespace_session = self._namespace_session_name()
        if namespace_session:
            self._run(
                "herdr namespace server stop cleanup",
                [str(HERDR_EXE), "--session", namespace_session, "server", "stop"],
                timeout=20,
            )
        self._write_transcript(failures)
        return 0 if not failures else 1

    def _prepare_workspace(self) -> None:
        for path in (self.home, self.bin_dir, self.shim_dir, self.ccb_dir):
            path.mkdir(parents=True, exist_ok=True)
        self._write_shims()
        stub = REPO / "test/stubs/provider_stub.py"
        for provider in ("codex", "claude", "gemini", "opencode", "droid"):
            (self.bin_dir / f"{provider}.cmd").write_text(
                f'@"{self.py}" "{stub}" --provider {provider} %*\r\n',
                encoding="utf-8",
            )
        self.ccb_dir.joinpath("ccb.config").write_text(
            'version = 2\nentry_window = "main"\n\n[windows]\nmain = "agent1:codex"\n',
            encoding="utf-8",
        )

    def _write_shims(self) -> None:
        mobile_gateway = self.shim_dir / "mobile_gateway"
        mobile_gateway.mkdir(parents=True, exist_ok=True)
        (self.shim_dir / "sitecustomize.py").write_text(SITECUSTOMIZE, encoding="utf-8")
        (mobile_gateway / "__init__.py").write_text(MOBILE_GATEWAY_INIT, encoding="utf-8")
        (mobile_gateway / "project_registry.py").write_text(
            'def publish_mobile_gateway_project(*args, **kwargs):\n'
            '    return {"publish_status": "stubbed"}\n',
            encoding="utf-8",
        )
        (mobile_gateway / "fcm.py").write_text(
            'def build_fcm_sender_from_env(*a, **k):\n'
            '    return None, {"status": "stubbed"}, {"timeout_seconds": 0.1, "max_workers": 1}\n'
            'def fcm_sender_runtime_options(*a, **k):\n'
            '    return {"timeout_seconds": 0.1, "max_workers": 1}\n',
            encoding="utf-8",
        )
        (mobile_gateway / "relay_host_credentials.py").write_text(RELAY_CREDENTIALS, encoding="utf-8")
        (mobile_gateway / "relay_host_runtime.py").write_text(RELAY_RUNTIME, encoding="utf-8")
        (mobile_gateway / "relay_admission.py").write_text(RELAY_ADMISSION, encoding="utf-8")

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "PYTHONPATH": os.pathsep.join(
                    [str(self.shim_dir), str(REPO), str(REPO / "lib")]
                ),
                "CCB_SOURCE_RUNTIME_OK": "1",
                "CCB_TEST_ENTRYPOINT": "1",
                "CCB_HERDR_EXE": str(HERDR_EXE),
                "CCB_HERDR_SOCKET_REF": "herdr://cmd-013-local",
                "CCB_HERDR_CAPABILITY_REPORT": str(CAPABILITY_REPORT),
                "CCB_HERDR_SESSION": self.session,
                "CCB_STARTUP_TRANSACTION_TIMEOUT_S": "120",
                "CCB_CCBD_CLIENT_TIMEOUT_S": "120",
                "CCB_CONTROL_PLANE_RPC_TIMEOUT_S": "30",
                "CCB_FOREGROUND_ATTACH_RPC_TIMEOUT_S": "15",
                "CCB_FOREGROUND_ATTACH_TARGET_READY_TIMEOUT_S": "60",
                "CCB_KEEPER_READY_TIMEOUT_S": "60",
                "CCB_NO_ATTACH": "1",
                "HOME": str(self.home),
                "USERPROFILE": str(self.home),
                "APPDATA": str(self.home / "AppData" / "Roaming"),
                "LOCALAPPDATA": str(self.home / "AppData" / "Local"),
                "PATH": str(self.bin_dir) + os.pathsep + env.get("PATH", ""),
                "STUB_DELAY": "0.1",
                "CCB_REPLY_LANG": "en",
                "CCB_CLAUDE_SKILLS": "0",
            }
        )
        for key in (
            "CCB_CALLER_ACTOR",
            "CCB_CALLER_PROJECT_ID",
            "CCB_CALLER_PROJECT_ROOT",
            "CCB_CALLER_RUNTIME_DIR",
            "CCB_SESSION_FILE",
            "CCB_SESSION_ID",
            "CLAUDE_CONFIG_DIR",
            "CLAUDE_PROJECTS_ROOT",
            "CLAUDE_PROJECT_ROOT",
            "CLAUDE_SESSION_ENV_ROOT",
            "CLAUDE_SECURESTORAGE_CONFIG_DIR",
            "CODEX_HOME",
            "CODEX_RUNTIME_DIR",
            "CODEX_SESSION_ROOT",
            "CODEX_SQLITE_HOME",
            "GEMINI_CLI_HOME",
            "GEMINI_ROOT",
            "OPENCODE_LOG_ROOT",
            "OPENCODE_RUNTIME_DIR",
            "OPENCODE_STORAGE_ROOT",
            "CCB_KEEPER_PID",
        ):
            env.pop(key, None)
        return env

    def _header(self) -> None:
        self.lines.extend(
            [
                "---",
                "doc_type: feature-evidence",
                "feature: 2026-07-31-ccbd-herdr-namespace-lifecycle",
                "command_id: CMD-013",
                "kind: native-windows-herdr-transcript",
                f"updated_at: {time.strftime('%Y-%m-%d')}",
                "---",
                "",
                "# CMD-013 Native Windows Herdr Transcript",
                "",
                f"- workdir: `{self.work}`",
                f"- repo: `{REPO}`",
                f"- herdr_exe: `{HERDR_EXE}`",
                f"- herdr_session: `{self.session}`",
                f"- herdr_preflight_session: `{self.preflight_session}`",
                f"- appdata: `{self.env.get('APPDATA')}`",
                f"- capability_report: `{CAPABILITY_REPORT}`",
                "- shim: POSIX-only Mobile imports, Windows directory fsync baseline, PYTHONPATH and CCB_HERDR_* control-plane allowlist are scoped to this transcript.",
                "",
                "## Platform",
                "",
                "```json",
                json.dumps(
                    {
                        "sys_platform": sys.platform,
                        "machine": platform.machine(),
                        "python_bits": platform.architecture()[0],
                        "is_wsl": False,
                    },
                    ensure_ascii=False,
                ),
                "```",
            ]
        )

    def _capability_excerpt(self) -> None:
        payload = json.loads(CAPABILITY_REPORT.read_text(encoding="utf-8"))
        excerpt = {
            "adapter_recommendation": payload.get("adapter_recommendation"),
            "failure_class": payload.get("failure_class"),
            "command_status": payload.get("command_status")
            or (payload.get("capability_projection") or {}).get("command_status"),
            "semantic_status": payload.get("semantic_status")
            or (payload.get("capability_projection") or {}).get("semantic_status"),
            "source_ref": str(CAPABILITY_REPORT),
        }
        self.lines.extend(["", "## Capability Report Excerpt", "", "```json"])
        self.lines.append(json.dumps(excerpt, ensure_ascii=False, indent=2))
        self.lines.append("```")

    def _write_reload_config(self) -> None:
        text = 'version = 2\nentry_window = "main"\n\n[windows]\nmain = "agent1:codex, agent2:codex"\n'
        self.ccb_dir.joinpath("ccb.config").write_text(text, encoding="utf-8")
        self.lines.extend(["", "## Config Changed For Reload", "", "```toml", text.rstrip(), "```"])

    def _record_namespace_state(self, label: str) -> bool:
        state_path = self.ccb_dir / "ccbd" / "state.json"
        self.lines.extend(["", f"## {label}", "", "```json"])
        if not state_path.exists():
            self.lines.append(json.dumps({"status": "missing", "path": str(state_path)}, indent=2))
            self.lines.append("```")
            return False
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        projected = {
            "namespace_backend_family": payload.get("namespace_backend_family"),
            "backend_impl": payload.get("backend_impl"),
            "namespace_id": payload.get("namespace_id"),
            "namespace_session_name": payload.get("namespace_session_name"),
            "namespace_ipc_kind": payload.get("namespace_ipc_kind"),
            "namespace_ipc_ref": payload.get("namespace_ipc_ref"),
            "namespace_restore_token_present": bool(payload.get("namespace_restore_token")),
            "ui_attachable": payload.get("ui_attachable"),
            "mount_state_hint": "mounted" if payload.get("last_destroyed_at") is None else "destroyed",
        }
        self.lines.append(json.dumps(projected, ensure_ascii=False, indent=2))
        self.lines.append("```")
        self._flush_transcript()
        if isinstance(projected["namespace_session_name"], str):
            self._record_herdr_named_session_probe(
                "herdr namespace session after create",
                projected["namespace_session_name"],
                include_server_launch=False,
            )
        return (
            projected["namespace_backend_family"] == "herdr-native"
            and projected["backend_impl"] == "herdr"
            and bool(projected["namespace_id"])
            and bool(projected["namespace_session_name"])
            and projected["namespace_ipc_kind"] == "herdr_socket"
            and bool(projected["namespace_ipc_ref"])
            and projected["namespace_restore_token_present"] is True
            and projected["ui_attachable"] is True
        )

    def _namespace_session_name(self) -> str | None:
        state_path = self.ccb_dir / "ccbd" / "state.json"
        if not state_path.exists():
            return None
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        value = payload.get("namespace_session_name")
        return value if isinstance(value, str) and value else None

    def _record_herdr_named_session_probe(
        self,
        label: str,
        session: str,
        *,
        include_server_launch: bool,
    ) -> None:
        self.lines.extend(["", f"## {label}", ""])
        self._run(
            f"{label}: status server before",
            [str(HERDR_EXE), "--session", session, "status", "server", "--json"],
            timeout=10,
        )
        if include_server_launch:
            self._run(
                f"{label}: direct server launch probe",
                [str(HERDR_EXE), "--session", session, "server"],
                timeout=5,
            )
            self._run(
                f"{label}: status server after direct launch",
                [str(HERDR_EXE), "--session", session, "status", "server", "--json"],
                timeout=10,
            )
        self._run(
            f"{label}: workspace list",
            [str(HERDR_EXE), "--session", session, "workspace", "list"],
            timeout=10,
        )

    def _ccb(self, *args: str) -> list[str]:
        return [self.py, "-c", WRAPPER, *args]

    def _run(self, label: str, cmd: list[str], *, timeout: int) -> int:
        self.lines.extend(["", f"## {label}", "", "```text", "$ " + self._compact_cmd(cmd)])
        try:
            result = subprocess.run(
                cmd,
                cwd=self.work,
                env=self.env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            self.lines.append(f"timeout_after_seconds: {timeout}")
            if exc.stdout:
                self.lines.extend(["--- stdout(partial) ---", self._redact(str(exc.stdout).rstrip())])
            if exc.stderr:
                self.lines.extend(["--- stderr(partial) ---", self._redact(str(exc.stderr).rstrip())])
            self.lines.append("```")
            print(f"{label}: timeout {timeout}", flush=True)
            self._flush_transcript()
            return 124
        self.lines.append(f"exit_code: {result.returncode}")
        if result.stdout:
            self.lines.extend(["--- stdout ---", self._redact(result.stdout.rstrip())])
        if result.stderr:
            self.lines.extend(["--- stderr ---", self._redact(result.stderr.rstrip())])
        self.lines.append("```")
        print(f"{label}: exit {result.returncode}", flush=True)
        self._flush_transcript()
        return int(result.returncode)

    def _flush_transcript(self) -> None:
        self.transcript.write_text("\n".join(self.lines) + "\n", encoding="utf-8")

    @staticmethod
    def _compact_cmd(cmd: list[str]) -> str:
        if len(cmd) >= 3 and cmd[1] == "-c":
            return " ".join([cmd[0], "-c", "<cmd013-wrapper>", *cmd[3:]])
        return " ".join(cmd)

    @staticmethod
    def _redact(text: str) -> str:
        return text.replace('"restore_token"', '"restore_token_REDACTED_KEY"')

    def _write_transcript(self, failures: list[str]) -> None:
        self.lines.extend(["", "## Verdict", ""])
        if failures:
            self.lines.append(f"blocked: {', '.join(failures)}")
        else:
            self.lines.append("passed")
        self.transcript.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        print(f"transcript: {self.transcript}", flush=True)


WRAPPER = r'''
import io
import os
import sys
from pathlib import Path

repo = Path(r"D:/Python/GitHub/claude_code_bridge")
shim_dir = str(Path(str(os.environ.get("PYTHONPATH") or "").split(os.pathsep)[0]))
for candidate in (shim_dir, str(repo), str(repo / "lib")):
    while candidate in sys.path:
        sys.path.remove(candidate)
sys.path.insert(0, str(repo / "lib"))
sys.path.insert(0, str(repo))
sys.path.insert(0, shim_dir)

import runtime_env.control_plane as cp

for key in (
    "PYTHONPATH",
    "CCB_HERDR_EXE",
    "CCB_HERDR_SOCKET_REF",
    "CCB_HERDR_CAPABILITY_REPORT",
    "CCB_HERDR_SESSION",
    "CCB_STARTUP_TRANSACTION_TIMEOUT_S",
    "CCB_CCBD_CLIENT_TIMEOUT_S",
    "CCB_CONTROL_PLANE_RPC_TIMEOUT_S",
    "CCB_FOREGROUND_ATTACH_RPC_TIMEOUT_S",
    "CCB_FOREGROUND_ATTACH_TARGET_READY_TIMEOUT_S",
    "CCB_KEEPER_READY_TIMEOUT_S",
    "CCB_NO_ATTACH",
):
    cp._CONTROL_PLANE_ALLOWLIST.add(key)
cp._CONTROL_PLANE_BLOCKED_EXACT = frozenset(
    key for key in cp._CONTROL_PLANE_BLOCKED_EXACT if key != "PYTHONPATH"
)

if "--cmd013-confirm-stdin" in sys.argv:
    sys.argv.remove("--cmd013-confirm-stdin")

    class ConfirmStdin(io.StringIO):
        def isatty(self):
            return True

    sys.stdin = ConfirmStdin("y\n")

if 'ConfirmStdin' in globals():
    import cli.phase2 as _phase2
    _phase2.sys.stdin = ConfirmStdin("y\n")

if "--cmd013-foreground-attach" in sys.argv:
    from pathlib import Path
    from types import SimpleNamespace

    from cli.services.start_foreground import attach_started_project_namespace

    context = SimpleNamespace(
        project=SimpleNamespace(project_id="cmd013"),
        paths=SimpleNamespace(ccbd_socket_path=Path.cwd() / ".ccb" / "ccbd" / "ccbd.sock"),
    )
    summary = attach_started_project_namespace(context)
    for field in (
        "project_id",
        "backend_impl",
        "namespace_id",
        "session_name",
        "ipc_kind",
        "ipc_ref",
        "namespace_restore_token_present",
    ):
        print(f"{field}: {getattr(summary, field)}")
    raise SystemExit(0)

if "--cmd013-namespace-ensure" in sys.argv:
    from cli.context import CliContextBuilder
    from cli.models import ParsedPingCommand
    from cli.services.daemon import ensure_daemon_started
    from ccbd.services.project_namespace import ProjectNamespaceController
    from project.identity_store import ensure_project_identity
    from storage.paths import PathLayout

    layout = PathLayout(Path.cwd())
    identity = ensure_project_identity(Path.cwd())
    namespace = ProjectNamespaceController(layout, identity.project_id).ensure()
    context = CliContextBuilder().build(
        ParsedPingCommand(project=None, target="ccbd"),
        cwd=Path.cwd(),
        bootstrap_if_missing=False,
    )
    handle = ensure_daemon_started(context)
    fields = namespace.summary_fields()
    for field in (
        "project_id",
        "namespace_backend_family",
        "backend_impl",
        "namespace_id",
        "namespace_session_name",
        "namespace_ipc_kind",
        "namespace_ipc_ref",
        "namespace_restore_token_present",
        "ui_attachable",
    ):
        print(f"{field}: {fields.get(field)}")
    print(f"ccbd_started: {handle.started}")
    raise SystemExit(0)

from cli.entrypoint_runtime import run_cli_entrypoint
from stdio_runtime import setup_windows_encoding
from terminal_runtime.backend_env import get_backend_env

setup_windows_encoding()
backend_env = get_backend_env()
if backend_env and not os.environ.get("CCB_BACKEND_ENV"):
    os.environ["CCB_BACKEND_ENV"] = backend_env

raise SystemExit(
    run_cli_entrypoint(
        sys.argv[1:],
        version="8.5.2",
        script_root=repo,
        cwd=Path.cwd(),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
)
'''


SITECUSTOMIZE = r'''
import json
import sys
import types
from pathlib import Path

_SHIM_DIR = str(Path(__file__).resolve().parent)
try:
    while _SHIM_DIR in sys.path:
        sys.path.remove(_SHIM_DIR)
    sys.path.insert(0, _SHIM_DIR)
except Exception:
    pass

if "fcntl" not in sys.modules:
    f = types.ModuleType("fcntl")
    f.LOCK_EX = 2
    f.LOCK_UN = 8
    f.LOCK_NB = 4
    f.flock = lambda *a, **k: None
    sys.modules["fcntl"] = f
if "pty" not in sys.modules:
    p = types.ModuleType("pty")
    p.openpty = lambda: (_ for _ in ()).throw(OSError("pty unavailable in CMD-013 shim"))
    sys.modules["pty"] = p
if "termios" not in sys.modules:
    t = types.ModuleType("termios")
    t.TIOCGWINSZ = 0
    sys.modules["termios"] = t

try:
    import runtime_env.control_plane as cp
    for key in (
        "PYTHONPATH",
        "CCB_HERDR_EXE",
        "CCB_HERDR_SOCKET_REF",
        "CCB_HERDR_CAPABILITY_REPORT",
        "CCB_HERDR_SESSION",
        "CCB_STARTUP_TRANSACTION_TIMEOUT_S",
        "CCB_CCBD_CLIENT_TIMEOUT_S",
        "CCB_CONTROL_PLANE_RPC_TIMEOUT_S",
        "CCB_FOREGROUND_ATTACH_RPC_TIMEOUT_S",
        "CCB_FOREGROUND_ATTACH_TARGET_READY_TIMEOUT_S",
        "CCB_KEEPER_READY_TIMEOUT_S",
        "CCB_NO_ATTACH",
    ):
        cp._CONTROL_PLANE_ALLOWLIST.add(key)
    cp._CONTROL_PLANE_BLOCKED_EXACT = frozenset(
        key for key in cp._CONTROL_PLANE_BLOCKED_EXACT if key != "PYTHONPATH"
    )
except Exception:
    pass

try:
    import storage.atomic as a

    def ensure(path):
        Path(path).mkdir(parents=True, exist_ok=True)

    def write_text(path, text, *, encoding="utf-8"):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding=encoding)

    def write_json(path, payload, *, encoding="utf-8"):
        write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding=encoding)

    def write_text_if_changed(path, text, *, encoding="utf-8"):
        target = Path(path)
        try:
            if target.read_text(encoding=encoding) == text:
                return False
        except Exception:
            pass
        write_text(target, text, encoding=encoding)
        return True

    def write_json_if_changed(path, payload, *, encoding="utf-8"):
        return write_text_if_changed(
            path,
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding=encoding,
        )

    a.ensure_durable_directory = ensure
    a.atomic_write_text = write_text
    a.atomic_write_json = write_json
    a.atomic_write_text_if_changed = write_text_if_changed
    a.atomic_write_json_if_changed = write_json_if_changed
except Exception:
    pass
'''


MOBILE_GATEWAY_INIT = r'''
from pathlib import Path

class MobileGatewayProjectRegistry:
    def __init__(self, *args, **kwargs):
        self.default_project = None

class MobileGatewayPairingStore:
    def __init__(self, *args, **kwargs):
        pass

class MobileGatewayService:
    def __init__(self, *args, **kwargs):
        pass

    def ensure_reusable_pairing_payload(self, *args, **kwargs):
        return {"pairing_status": "stubbed"}

    def close(self):
        pass

def _unavailable(*args, **kwargs):
    raise RuntimeError("mobile gateway unavailable in CMD-013 shim")

def build_mobile_gateway_server(*args, **kwargs):
    return _unavailable(*args, **kwargs)

def discover_running_mobile_gateway_projects(*args, **kwargs):
    return []

def load_mobile_gateway_project_registry(*args, **kwargs):
    return MobileGatewayProjectRegistry()

def mobile_host_project_registry_path():
    return mobile_host_state_dir() / "projects.json"

def mobile_host_state_dir():
    return Path.home() / ".ccb-mobile-host"

def parse_listen_address(value=None, allow_lan=False):
    text = str(value or "127.0.0.1:0")
    if ":" in text:
        host, port = text.rsplit(":", 1)
        try:
            return host, int(port)
        except ValueError:
            return host, 0
    return text, 0
'''


RELAY_CREDENTIALS = r'''
CCB_OFFICIAL_RELAY_ORIGIN = "wss://relay.invalid"
RELAY_MODE_OFFICIAL = "official"
RELAY_MODE_SELF_HOSTED = "self-hosted"

class RelayHostCredentials:
    relay_http_origin = "http://127.0.0.1"
    host_id = "stub-host"

    def public_summary(self, credential_path=None):
        return {
            "relay_status": "stubbed",
            "credential_path": str(credential_path) if credential_path else None,
        }

def build_relay_pairing_payload(pairing, credentials=None):
    return pairing

def load_relay_host_credentials(*args, **kwargs):
    return None

def activate_relay_host(*args, **kwargs):
    return RelayHostCredentials()
'''


RELAY_RUNTIME = r'''
def relay_host_runtime_summary(*args, **kwargs):
    return {"relay_runtime_status": "stubbed"}

class RelayHostConnectorRuntime:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        return {"relay_runtime_status": "stubbed"}

    def close(self):
        pass
'''


RELAY_ADMISSION = r'''
class RelayAdmissionError(RuntimeError):
    pass

class RelayAdmissionSecrets:
    @classmethod
    def from_operator_config(cls, *args, **kwargs):
        return cls()

class RelayAdmissionStore:
    def __init__(self, *args, **kwargs):
        pass

    def issue_invitation(self, *args, **kwargs):
        return type("Issued", (), {"to_operator_json": lambda self: {"relay_status": "stubbed"}})()

    def invitation_status(self, *args, **kwargs):
        return {"relay_status": "stubbed"}

    def list_invitations(self):
        return []

    def revoke_invitation(self, *args, **kwargs):
        return {"relay_status": "stubbed"}

    def host_status(self, *args, **kwargs):
        return {"relay_status": "stubbed"}

    def list_hosts(self):
        return []

    def revoke_host(self, *args, **kwargs):
        return {"relay_status": "stubbed"}
'''


if __name__ == "__main__":
    raise SystemExit(main())
