from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal, Mapping, TypedDict


ArchState = Literal['x64', 'arm64', 'ia32', 'missing', 'unknown']
OsPlatform = Literal['win32', 'linux', 'darwin', 'unknown']
PythonBitness = Literal['64bit', '32bit', 'unknown']
FailureReason = Literal['not-windows', 'not-x64', 'python-not-x64', 'herdr-not-x64', 'helper-not-x64', 'unknown']
DetailReason = Literal[
    'none',
    'node-not-x64',
    'ccb-version-mismatch',
    'ccb-version-source-mismatch',
    'source-branch-blocked',
    'python-bitness-unknown',
    'herdr-missing',
    'helper-missing',
    'helper-unknown',
    'unknown',
]
HelperName = Literal['ccb-rs-helper', 'ccb-agent-sidebar']
EXPECTED_CCB_VERSION: Literal['8.5.2'] = '8.5.2'


class WindowsX64PlatformGate(TypedDict):
    os_platform: OsPlatform
    cpu_arch: ArchState
    node_arch: ArchState
    python_bitness: PythonBitness
    ccb_version_source: Literal['installation', 'package_json', 'version_file', 'unknown']
    ccb_source_ref: str | None
    ccb_branch_ref: str | None
    ccb_source_status: Literal['strict-v8.5.2', 'not-v8.5.2', 'unknown']
    detected_ccb_version: str | None
    package_json_version: str | None
    version_file_version: str | None
    installation_version: str | None
    expected_ccb_version: Literal['8.5.2']
    herdr_arch: ArchState
    helper_arch: dict[HelperName, ArchState]
    platform_ready: bool
    native_helpers_ready: bool
    herdr_executable_ready: bool
    supported: bool
    failure_reason: FailureReason | None
    detail_reason: DetailReason
    diagnostic: str


def build_windows_x64_platform_gate(
    *,
    os_platform: object,
    cpu_arch: object,
    node_arch: object,
    python_bitness: object,
    version_sources: Mapping[str, object] | None = None,
    ccb_source_ref: object = None,
    ccb_branch_ref: object = None,
    herdr_arch: object = 'missing',
    helper_arch: Mapping[str, object] | None = None,
) -> WindowsX64PlatformGate:
    versions = version_sources or {}
    installation_version = _optional_text(versions.get('installation'))
    package_json_version = _optional_text(versions.get('package_json'))
    version_file_version = _optional_text(versions.get('version_file'))
    version_source, detected_version = _select_version(
        installation_version=installation_version,
        package_json_version=package_json_version,
        version_file_version=version_file_version,
    )
    source_ref = _optional_text(ccb_source_ref)
    branch_ref = _optional_text(ccb_branch_ref)
    source_status = _source_status(detected_version, source_ref=source_ref, branch_ref=branch_ref)
    helper = _helper_arch(helper_arch or {})
    version_sources_consistent = _version_sources_consistent(
        [installation_version, package_json_version, version_file_version],
    )
    normalized_os = _os_platform(os_platform)
    normalized_cpu = _arch(cpu_arch)
    normalized_node = _arch(node_arch)
    normalized_python = _python_bitness(python_bitness)
    normalized_herdr = _arch(herdr_arch)
    failure_reason, detail_reason = _classify_failure(
        os_platform=normalized_os,
        cpu_arch=normalized_cpu,
        node_arch=normalized_node,
        python_bitness=normalized_python,
        version_values=[installation_version, package_json_version, version_file_version],
        detected_version=detected_version,
        ccb_source_status=source_status,
        herdr_arch=normalized_herdr,
        helper_arch=helper,
    )
    platform_ready = (
        normalized_os == 'win32'
        and normalized_cpu == 'x64'
        and normalized_node == 'x64'
        and normalized_python == '64bit'
        and source_status == 'strict-v8.5.2'
        and version_sources_consistent
    )
    native_helpers_ready = all(value == 'x64' for value in helper.values())
    herdr_executable_ready = normalized_herdr == 'x64'
    supported = failure_reason is None and platform_ready and native_helpers_ready and herdr_executable_ready
    return {
        'os_platform': normalized_os,
        'cpu_arch': normalized_cpu,
        'node_arch': normalized_node,
        'python_bitness': normalized_python,
        'ccb_version_source': version_source,
        'ccb_source_ref': source_ref,
        'ccb_branch_ref': branch_ref,
        'ccb_source_status': source_status,
        'detected_ccb_version': detected_version,
        'package_json_version': package_json_version,
        'version_file_version': version_file_version,
        'installation_version': installation_version,
        'expected_ccb_version': EXPECTED_CCB_VERSION,
        'herdr_arch': normalized_herdr,
        'helper_arch': helper,
        'platform_ready': platform_ready,
        'native_helpers_ready': native_helpers_ready,
        'herdr_executable_ready': herdr_executable_ready,
        'supported': supported,
        'failure_reason': failure_reason,
        'detail_reason': detail_reason,
        'diagnostic': _diagnostic(failure_reason, detail_reason, detected_version),
    }


def windows_x64_platform_gate_summary(
    project_root: str | Path,
    *,
    installation: Mapping[str, object] | None = None,
) -> WindowsX64PlatformGate:
    root = _repo_root(project_root)
    install = installation or {}
    node_platform, node_arch = _node_platform_arch()
    return build_windows_x64_platform_gate(
        os_platform=node_platform or sys.platform,
        cpu_arch=platform.machine(),
        node_arch=node_arch or 'missing',
        python_bitness=_runtime_python_bitness(),
        version_sources={
            'installation': install.get('version'),
            'package_json': _package_json_version(root / 'package.json'),
            'version_file': _version_file_version(root / 'VERSION'),
        },
        ccb_source_ref=_first_installation_value(install, 'ccb_source_ref', 'source_ref'),
        ccb_branch_ref=_first_installation_value(install, 'ccb_branch_ref', 'branch_ref'),
        herdr_arch=_first_installation_value(install, 'herdr_arch') or ('unknown' if shutil.which('herdr') else 'missing'),
        helper_arch=_installation_helper_arch(install),
    )


def _classify_failure(
    *,
    os_platform: OsPlatform,
    cpu_arch: ArchState,
    node_arch: ArchState,
    python_bitness: PythonBitness,
    version_values: list[str | None],
    detected_version: str | None,
    ccb_source_status: str,
    herdr_arch: ArchState,
    helper_arch: Mapping[str, ArchState],
) -> tuple[FailureReason | None, DetailReason]:
    if os_platform != 'win32':
        return 'not-windows', 'none'
    if cpu_arch != 'x64':
        return 'not-x64', 'none'
    if node_arch != 'x64':
        return 'not-x64', 'node-not-x64'
    if python_bitness == '32bit':
        return 'python-not-x64', 'none'
    if python_bitness == 'unknown':
        return 'unknown', 'python-bitness-unknown'
    present_versions = {value for value in version_values if value}
    if len(present_versions) > 1:
        return 'unknown', 'ccb-version-source-mismatch'
    if detected_version != EXPECTED_CCB_VERSION:
        return 'unknown', 'ccb-version-mismatch'
    if ccb_source_status != 'strict-v8.5.2':
        return 'unknown', 'source-branch-blocked'
    if herdr_arch == 'missing':
        return 'herdr-not-x64', 'herdr-missing'
    if herdr_arch != 'x64':
        return 'herdr-not-x64', 'unknown'
    if any(value == 'missing' for value in helper_arch.values()):
        return 'helper-not-x64', 'helper-missing'
    if any(value == 'unknown' for value in helper_arch.values()):
        return 'helper-not-x64', 'helper-unknown'
    if any(value != 'x64' for value in helper_arch.values()):
        return 'helper-not-x64', 'unknown'
    return None, 'none'


def _version_sources_consistent(version_values: list[str | None]) -> bool:
    return len({value for value in version_values if value}) <= 1


def _diagnostic(failure_reason: FailureReason | None, detail_reason: DetailReason, detected_version: str | None) -> str:
    if failure_reason is None:
        return 'Native Windows x64 platform gate passed for strict CCB v8.5.2.'
    if detail_reason == 'node-not-x64':
        return 'Node is not x64; win32 is the Windows OS name and does not imply 32-bit support.'
    if detail_reason == 'ccb-version-mismatch':
        return f'Expected CCB {EXPECTED_CCB_VERSION}, detected {detected_version or "unknown"}.'
    if detail_reason == 'ccb-version-source-mismatch':
        return 'CCB version sources disagree; resolve installation, package.json and VERSION before continuing.'
    if detail_reason == 'source-branch-blocked':
        return 'Missing strict v8.5.2 source ref or new implementation branch evidence.'
    if detail_reason == 'python-bitness-unknown':
        return 'Python bitness is unknown; use a 64-bit Python runtime.'
    if detail_reason == 'herdr-missing':
        return 'Herdr executable is missing or not discoverable; CCB will not install Herdr automatically.'
    if detail_reason == 'helper-missing':
        return 'Required native helper arch evidence is missing.'
    if detail_reason == 'helper-unknown':
        return 'Required native helper arch evidence is unknown or conflicting.'
    if failure_reason == 'not-windows':
        return 'Native Windows Herdr route requires os_platform=win32.'
    if failure_reason == 'not-x64':
        return 'Native Windows Herdr route requires x64 CPU and Node runtime.'
    if failure_reason == 'python-not-x64':
        return 'Native Windows Herdr route requires 64-bit Python.'
    return 'Native Windows x64 platform gate failed closed.'


def _source_status(
    detected_version: str | None,
    *,
    source_ref: str | None,
    branch_ref: str | None,
) -> Literal['strict-v8.5.2', 'not-v8.5.2', 'unknown']:
    if detected_version != EXPECTED_CCB_VERSION:
        return 'not-v8.5.2'
    if not _is_v852_source_ref(source_ref) or not _is_implementation_branch_ref(branch_ref):
        return 'unknown'
    return 'strict-v8.5.2'


def _is_v852_source_ref(value: str | None) -> bool:
    text = (value or '').strip().lower()
    return text in {'v8.5.2', 'refs/tags/v8.5.2'}


def _is_implementation_branch_ref(value: str | None) -> bool:
    text = (value or '').strip().lower()
    if not text:
        return False
    branch = text.removeprefix('refs/heads/')
    return branch.startswith(('feature/', 'feat/', 'impl/', 'implementation/'))


def _select_version(
    *,
    installation_version: str | None,
    package_json_version: str | None,
    version_file_version: str | None,
) -> tuple[Literal['installation', 'package_json', 'version_file', 'unknown'], str | None]:
    if installation_version:
        return 'installation', installation_version
    if package_json_version:
        return 'package_json', package_json_version
    if version_file_version:
        return 'version_file', version_file_version
    return 'unknown', None


def _helper_arch(values: Mapping[str, object]) -> dict[HelperName, ArchState]:
    return {
        'ccb-rs-helper': _trusted_arch(values.get('ccb-rs-helper', 'missing')),
        'ccb-agent-sidebar': _trusted_arch(values.get('ccb-agent-sidebar', 'missing')),
    }


def _installation_helper_arch(installation: Mapping[str, object]) -> Mapping[str, object]:
    helper_arch = installation.get('helper_arch')
    if isinstance(helper_arch, Mapping):
        return helper_arch
    return {
        'ccb-rs-helper': _first_installation_value(installation, 'ccb_rs_helper_arch') or 'missing',
        'ccb-agent-sidebar': _first_installation_value(installation, 'ccb_agent_sidebar_arch') or 'missing',
    }


def _first_installation_value(installation: Mapping[str, object], *keys: str) -> object:
    for key in keys:
        value = installation.get(key)
        if _optional_text(value):
            return value
    return None


def _trusted_arch(value: object) -> ArchState:
    if isinstance(value, Mapping):
        states = [_arch(item) for item in value.values()]
        known = [item for item in states if item not in {'missing', 'unknown'}]
        if not known:
            return 'unknown' if 'unknown' in states else 'missing'
        if any(item != 'x64' for item in known):
            return known[0] if len(set(known)) == 1 else 'unknown'
        if any(item in {'missing', 'unknown'} for item in states):
            return 'unknown'
        return 'x64'
    return _arch(value)


def _arch(value: object) -> ArchState:
    text = str(value or '').strip().lower()
    if text in {'x64', 'amd64', 'x86_64'}:
        return 'x64'
    if text in {'arm64', 'aarch64'}:
        return 'arm64'
    if text in {'ia32', 'x86', 'i386', 'i686', '32bit'}:
        return 'ia32'
    if text == 'missing':
        return 'missing'
    return 'unknown'


def _os_platform(value: object) -> OsPlatform:
    text = str(value or '').strip().lower()
    if text.startswith('win'):
        return 'win32'
    if text.startswith('linux'):
        return 'linux'
    if text in {'darwin', 'macos'}:
        return 'darwin'
    return 'unknown'


def _python_bitness(value: object) -> PythonBitness:
    text = str(value or '').strip().lower()
    if text in {'64bit', '64', 'x64'}:
        return '64bit'
    if text in {'32bit', '32', 'ia32', 'x86'}:
        return '32bit'
    return 'unknown'


def _runtime_python_bitness() -> PythonBitness:
    bits = platform.architecture()[0]
    if bits in {'64bit', '32bit'}:
        return bits  # type: ignore[return-value]
    return '64bit' if sys.maxsize > 2**32 else '32bit'


def _node_platform_arch() -> tuple[str | None, str | None]:
    node = shutil.which('node')
    if node is None:
        return None, None
    try:
        completed = subprocess.run(
            [node, '-p', 'process.platform + "/" + process.arch'],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None, None
    if completed.returncode != 0:
        return None, None
    platform_arch = (completed.stdout or '').strip().split('/', 1)
    if len(platform_arch) != 2:
        return None, None
    return platform_arch[0], platform_arch[1]


def _repo_root(project_root: str | Path) -> Path:
    current = Path(project_root).expanduser().resolve()
    for path in (current, *current.parents):
        if (path / '.git').exists() or (path / '.codestable').exists():
            return path
    return current


def _package_json_version(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    return _optional_text(data.get('version')) if isinstance(data, dict) else None


def _version_file_version(path: Path) -> str | None:
    try:
        return _optional_text(path.read_text(encoding='utf-8'))
    except OSError:
        return None


def _optional_text(value: object) -> str | None:
    text = str(value or '').strip()
    return text or None


__all__ = [
    'WindowsX64PlatformGate',
    'build_windows_x64_platform_gate',
    'windows_x64_platform_gate_summary',
]
