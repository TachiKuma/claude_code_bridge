from __future__ import annotations

from dataclasses import dataclass
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import time

_AUTH_MARKER = 'ccbd-control-plane-token-v1'
_AUTH_ACK_MARKER = 'ccbd-control-plane-token-ack-v1'
_MAX_AUTH_LINE_BYTES = 4096


class RpcTransportAuthError(OSError):
    def __init__(self, category: str, detail: str | None = None) -> None:
        self.category = str(category or 'handshake-failed')
        super().__init__(detail or self.category)


@dataclass(frozen=True)
class TokenFile:
    token_ref: str
    token: str
    generation: str
    acl_status: str

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.token.encode('utf-8')).hexdigest()[:16]


def create_token_file(
    path: str | Path,
    *,
    command_runner=None,
    os_name: str | None = None,
) -> TokenFile:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    generation = secrets.token_hex(8)
    token = secrets.token_urlsafe(32)
    payload = {
        'schema': _AUTH_MARKER,
        'generation': generation,
        'token': token,
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    try:
        acl_status = converge_token_acl(target, command_runner=command_runner, os_name=os_name)
    except Exception:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        raise
    return TokenFile(
        token_ref=str(target),
        token=token,
        generation=generation,
        acl_status=acl_status,
    )


def load_token_file(path: str | Path) -> TokenFile:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise RpcTransportAuthError('token-missing', 'ccbd control-plane token is missing') from exc
    if not isinstance(payload, dict) or payload.get('schema') != _AUTH_MARKER:
        raise RpcTransportAuthError('token-invalid', 'ccbd control-plane token file is invalid')
    token = str(payload.get('token') or '').strip()
    generation = str(payload.get('generation') or '').strip()
    if not token or not generation:
        raise RpcTransportAuthError('token-invalid', 'ccbd control-plane token file is incomplete')
    return TokenFile(
        token_ref=str(target),
        token=token,
        generation=generation,
        acl_status=str(payload.get('acl_status') or 'unknown'),
    )


def converge_token_acl(
    path: str | Path,
    *,
    command_runner=None,
    os_name: str | None = None,
) -> str:
    target = Path(path)
    platform = os.name if os_name is None else os_name
    if platform != 'nt':
        try:
            target.chmod(0o600)
        except OSError as exc:
            raise RpcTransportAuthError('token-unprotectable', str(exc)) from exc
        return 'posix-0600'
    user = _current_windows_user()
    if not user:
        raise RpcTransportAuthError('token-unprotectable', 'current Windows user is unavailable')
    runner = command_runner or subprocess.run
    commands = (
        ['icacls', str(target), '/inheritance:r'],
        ['icacls', str(target), '/grant:r', f'{user}:R'],
        ['icacls', str(target), '/remove:g', 'Everyone', 'Users', 'Authenticated Users'],
    )
    for command in commands:
        _run_checked_command(runner, command)
    proof = _read_windows_acl_proof(target, command_runner=runner)
    current_sid = _current_windows_sid(runner)
    _assert_windows_acl_proof(
        proof,
        current_user=user,
        current_sid=current_sid,
    )
    return 'windows-icacls-user-read'


def client_authenticate(sock, token: str) -> None:
    _send_auth_line(sock, token)
    _recv_auth_ack(sock)


def server_authenticate(sock, expected_token: str, *, timeout_s: float | None = None) -> bytes:
    line, remainder = _recv_line(sock, timeout_s=timeout_s)
    payload = _decode_auth_payload(line)
    token = str(payload.get('token') or '')
    if payload.get('schema') != _AUTH_MARKER or not hmac.compare_digest(token, expected_token):
        raise RpcTransportAuthError('not-same-user')
    _send_auth_ack(sock)
    return remainder


def redacted_token_diagnostics(token_file: TokenFile) -> dict[str, str]:
    return {
        'token_ref': token_file.token_ref,
        'acl_status': token_file.acl_status,
        'fingerprint': token_file.fingerprint,
    }


def _send_auth_line(sock, token: str) -> None:
    payload = {
        'schema': _AUTH_MARKER,
        'token': token,
    }
    sock.sendall(json.dumps(payload, ensure_ascii=False).encode('utf-8') + b'\n')


def _send_auth_ack(sock) -> None:
    sock.sendall(json.dumps({'schema': _AUTH_ACK_MARKER, 'ok': True}, ensure_ascii=False).encode('utf-8') + b'\n')


def _recv_auth_ack(sock) -> None:
    try:
        line, remainder = _recv_line(sock)
    except (OSError, RpcTransportAuthError) as exc:
        raise RpcTransportAuthError('not-same-user', 'ccbd auth handshake was rejected') from exc
    payload = _decode_auth_payload(line)
    if payload.get('schema') != _AUTH_ACK_MARKER or payload.get('ok') is not True:
        raise RpcTransportAuthError('handshake-failed', 'ccbd auth ack is invalid')
    if remainder:
        raise RpcTransportAuthError('handshake-failed', 'ccbd auth ack contains unexpected data')


def _recv_line(sock, *, timeout_s: float | None = None) -> tuple[bytes, bytes]:
    raw = b''
    deadline = None
    if timeout_s is not None:
        deadline = time.monotonic() + max(0.0, float(timeout_s))
    while b'\n' not in raw:
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RpcTransportAuthError('handshake-failed', 'auth handshake timed out')
            sock.settimeout(remaining)
        chunk = sock.recv(1024)
        if not chunk:
            raise RpcTransportAuthError('handshake-failed', 'empty auth handshake')
        raw += chunk
        if len(raw) > _MAX_AUTH_LINE_BYTES:
            raise RpcTransportAuthError('handshake-failed', 'auth handshake is too large')
    line, remainder = raw.split(b'\n', 1)
    return line, remainder


def _decode_auth_payload(raw: bytes) -> dict:
    try:
        payload = json.loads(raw.decode('utf-8'))
    except Exception as exc:
        raise RpcTransportAuthError('handshake-failed', 'auth handshake is not JSON') from exc
    if not isinstance(payload, dict):
        raise RpcTransportAuthError('handshake-failed', 'auth handshake must be an object')
    return payload


def _current_windows_user() -> str:
    username = str(os.environ.get('USERNAME') or '').strip()
    if not username:
        try:
            username = str(getpass.getuser() or '').strip()
        except OSError:
            username = ''
    if not username:
        try:
            result = subprocess.run(['whoami'], capture_output=True, text=True, timeout=2.0)
        except Exception:
            result = None
        if result is not None and int(getattr(result, 'returncode', 1) or 0) == 0:
            value = str(getattr(result, 'stdout', '') or '').strip()
            if value:
                return value
    domain = str(os.environ.get('USERDOMAIN') or '').strip()
    if domain and username and '\\' not in username:
        return f'{domain}\\{username}'
    return username


def _current_windows_sid(command_runner) -> str:
    result = command_runner(
        [
            'powershell',
            '-NoProfile',
            '-Command',
            '([System.Security.Principal.WindowsIdentity]::GetCurrent()).User.Value',
        ],
        capture_output=True,
        text=True,
    )
    if int(getattr(result, 'returncode', 1) or 0) != 0:
        stderr = str(getattr(result, 'stderr', '') or '').strip()
        stdout = str(getattr(result, 'stdout', '') or '').strip()
        detail = stderr or stdout or 'unable to read current Windows SID'
        raise RpcTransportAuthError('token-unprotectable', detail)
    raw = str(getattr(result, 'stdout', '') or '').strip()
    sid = raw.splitlines()[-1].strip() if raw else ''
    if not sid:
        raise RpcTransportAuthError('token-unprotectable', 'current Windows SID is unavailable')
    return sid


def _read_windows_acl_proof(path: Path, *, command_runner) -> dict:
    script = (
        '$acl = Get-Acl -LiteralPath '
        + _powershell_literal(str(path))
        + '; '
        + '$payload = [pscustomobject]@{'
        + 'owner = $acl.Owner; '
        + 'sddl = $acl.Sddl; '
        + 'access = @($acl.Access | ForEach-Object { [pscustomobject]@{ '
        + 'identity = $_.IdentityReference.Value; '
        + 'rights = $_.FileSystemRights.ToString(); '
        + 'access_type = $_.AccessControlType.ToString(); '
        + 'inherited = [bool]$_.IsInherited '
        + '} })'
        + '}; '
        + '$payload | ConvertTo-Json -Compress -Depth 4'
    )
    result = command_runner(
        ['powershell', '-NoProfile', '-Command', script],
        capture_output=True,
        text=True,
    )
    if int(getattr(result, 'returncode', 1) or 0) != 0:
        stderr = str(getattr(result, 'stderr', '') or '').strip()
        stdout = str(getattr(result, 'stdout', '') or '').strip()
        detail = stderr or stdout or 'unable to verify Windows ACL proof'
        raise RpcTransportAuthError('token-unprotectable', detail)
    raw = str(getattr(result, 'stdout', '') or '').strip()
    try:
        proof = json.loads(raw)
    except Exception as exc:
        raise RpcTransportAuthError('token-unprotectable', 'Windows ACL proof is not JSON') from exc
    if not isinstance(proof, dict):
        raise RpcTransportAuthError('token-unprotectable', 'Windows ACL proof is invalid')
    return proof


def _assert_windows_acl_proof(proof: dict, *, current_user: str, current_sid: str) -> None:
    owner = str(proof.get('owner') or '').strip()
    sddl = str(proof.get('sddl') or '').strip()
    owner_sid = _sddl_owner_sid(sddl)
    if not owner_sid or owner_sid != current_sid:
        raise RpcTransportAuthError('token-unprotectable', 'Windows token owner did not converge to the current user')
    if owner and owner.casefold() not in {current_user.casefold(), current_sid.casefold()}:
        raise RpcTransportAuthError('token-unprotectable', 'Windows token owner did not converge to the current user')
    access = proof.get('access') or []
    if isinstance(access, dict):
        access = [access]
    if not isinstance(access, list) or not access:
        raise RpcTransportAuthError('token-unprotectable', 'Windows token ACL is empty')
    allowed_identities = {current_user.casefold(), current_sid.casefold()}
    seen_identity = False
    for entry in access:
        if not isinstance(entry, dict):
            raise RpcTransportAuthError('token-unprotectable', 'Windows token ACL proof is invalid')
        identity = str(entry.get('identity') or '').strip()
        rights = str(entry.get('rights') or '').strip()
        access_type = str(entry.get('access_type') or '').strip()
        inherited = bool(entry.get('inherited'))
        if not identity:
            raise RpcTransportAuthError('token-unprotectable', 'Windows token ACL proof is incomplete')
        if inherited or access_type.casefold() != 'allow' or not _windows_acl_rights_prove_read(rights):
            raise RpcTransportAuthError('token-unprotectable', 'Windows token ACL did not converge to a read-only allow entry')
        if identity.casefold() not in allowed_identities:
            raise RpcTransportAuthError('token-unprotectable', 'Windows token ACL contains an unexpected principal')
        seen_identity = True
    if not seen_identity:
        raise RpcTransportAuthError('token-unprotectable', 'Windows token ACL proof is incomplete')


def _sddl_owner_sid(sddl: str) -> str:
    match = re.search(r'O:(.*?)(?=G:|D:|S:|$)', sddl)
    if not match:
        return ''
    return str(match.group(1) or '').strip()


def _windows_acl_rights_prove_read(rights: str) -> bool:
    normalized = rights.casefold()
    return 'read' in normalized or normalized in {'r', 'rx', 'read, synchronize', 'read and execute'}


def _run_checked_command(command_runner, command) -> None:
    result = command_runner(command, capture_output=True, text=True)
    if int(getattr(result, 'returncode', 1) or 0) != 0:
        stderr = str(getattr(result, 'stderr', '') or '').strip()
        stdout = str(getattr(result, 'stdout', '') or '').strip()
        detail = stderr or stdout or 'icacls failed'
        raise RpcTransportAuthError('token-unprotectable', detail)


def _powershell_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"
