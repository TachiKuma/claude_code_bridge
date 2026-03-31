"""CCB configuration for Windows/WSL backend environment."""

import json
import locale
import os
import subprocess
import sys
from pathlib import Path

try:
    from terminal import _subprocess_kwargs
except ModuleNotFoundError:
    try:
        from lib.terminal import _subprocess_kwargs
    except ModuleNotFoundError:
        def _subprocess_kwargs() -> dict:
            """Fallback subprocess kwargs when terminal module is unavailable."""
            kwargs = {}
            if sys.platform == "win32":
                # CREATE_NO_WINDOW = 0x08000000 prevents CMD window flash
                CREATE_NO_WINDOW = 0x08000000
                kwargs["creationflags"] = CREATE_NO_WINDOW
            return kwargs

CONFIG_FILE_NAME = ".ccb-config.json"
VALID_LANGUAGE_VALUES = {"auto", "en", "zh", "xx"}


def get_project_config_path(work_dir: Path | None = None) -> Path:
    """Return the project config file path."""
    base = work_dir or Path.cwd()
    return base / CONFIG_FILE_NAME


def load_project_config(work_dir: Path | None = None) -> dict:
    """Load .ccb-config.json as a dict."""
    path = get_project_config_path(work_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def save_project_config(data: dict, work_dir: Path | None = None) -> Path:
    """Persist .ccb-config.json."""
    path = get_project_config_path(work_dir)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def normalize_language_setting(value: str | None) -> str | None:
    """Normalize user-provided language values to supported settings."""
    normalized = (value or "").strip().lower()
    if normalized in {"zh", "cn", "chinese"}:
        return "zh"
    if normalized in {"en", "english"}:
        return "en"
    if normalized == "xx":
        return "xx"
    if normalized == "auto":
        return "auto"
    return None


def get_language_setting(work_dir: Path | None = None) -> str | None:
    """Get configured language from .ccb-config.json."""
    data = load_project_config(work_dir)
    return normalize_language_setting(str(data.get("Language") or ""))


def detect_locale_language(env: dict[str, str] | None = None) -> str:
    """Detect language from locale-related environment variables."""
    language_env = env or os.environ
    try:
        lang = (
            language_env.get("LANG", "")
            or language_env.get("LC_ALL", "")
            or language_env.get("LC_MESSAGES", "")
        )
        if not lang:
            lang, _ = locale.getlocale()
            lang = lang or ""
        normalized = (lang or "").strip().lower()
        if normalized.startswith("zh") or "chinese" in normalized:
            return "zh"
    except Exception:
        pass
    return "en"


def resolve_language_setting(work_dir: Path | None = None, env: dict[str, str] | None = None) -> str:
    """Resolve effective UI language.

    Priority is fixed to:
    1. `CCB_LANG` environment variable
    2. `.ccb-config.json: Language`
    3. Locale detection

    CLI `--lang` is normalized into `CCB_LANG` before this function is called.
    """
    language_env = env or os.environ
    env_lang = normalize_language_setting(language_env.get("CCB_LANG"))
    if env_lang and env_lang != "auto":
        return env_lang

    configured = get_language_setting(work_dir)
    if configured and configured != "auto":
        return configured

    return detect_locale_language(language_env)


def set_language_setting(lang: str, work_dir: Path | None = None) -> Path:
    """Set project language in .ccb-config.json."""
    value = normalize_language_setting(lang)
    if value not in VALID_LANGUAGE_VALUES:
        raise ValueError(f"Unsupported language: {lang}")
    data = load_project_config(work_dir)
    data["Language"] = value
    return save_project_config(data, work_dir)


def get_backend_env() -> str | None:
    """Get BackendEnv from env var or .ccb-config.json"""
    v = (os.environ.get("CCB_BACKEND_ENV") or "").strip().lower()
    if v in {"wsl", "windows"}:
        return v
    data = load_project_config()
    v = str(data.get("BackendEnv") or "").strip().lower()
    if v in {"wsl", "windows"}:
        return v
    return "windows" if sys.platform == "win32" else None


def _wsl_probe_distro_and_home() -> tuple[str, str]:
    """Probe default WSL distro and home directory.

    On native Windows without WSL, returns defaults immediately after
    a fast check (< 2s timeout) instead of waiting 10+ seconds.
    """
    # Fast check: is WSL installed at all?
    try:
        r = subprocess.run(
            ["wsl.exe", "--list", "--quiet"],
            capture_output=True, text=True, encoding="utf-16-le",
            errors="replace", timeout=2,
            **_subprocess_kwargs()
        )
        if r.returncode != 0:
            # WSL not available or not installed
            return "", ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # wsl.exe doesn't exist or timed out -- no WSL
        return "", ""

    # WSL is available, probe distro and home
    try:
        r = subprocess.run(
            ["wsl.exe", "-e", "sh", "-lc", "echo $WSL_DISTRO_NAME; echo $HOME"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            **_subprocess_kwargs()
        )
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            if len(lines) >= 2:
                return lines[0].strip(), lines[1].strip()
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["wsl.exe", "-l", "-q"],
            capture_output=True, text=True, encoding="utf-16-le", errors="replace", timeout=5,
            **_subprocess_kwargs()
        )
        if r.returncode == 0:
            for line in r.stdout.strip().split("\n"):
                distro = line.strip().strip("\x00")
                if distro:
                    break
            else:
                distro = "Ubuntu"
        else:
            distro = "Ubuntu"
    except Exception:
        distro = "Ubuntu"
    try:
        r = subprocess.run(
            ["wsl.exe", "-d", distro, "-e", "sh", "-lc", "echo $HOME"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            **_subprocess_kwargs()
        )
        home = r.stdout.strip() if r.returncode == 0 else "/root"
    except Exception:
        home = "/root"
    return distro, home


def apply_backend_env() -> None:
    """Apply BackendEnv=wsl settings (set session root paths for Windows to access WSL)"""
    if sys.platform != "win32" or get_backend_env() != "wsl":
        return
    if os.environ.get("CODEX_SESSION_ROOT") and os.environ.get("GEMINI_ROOT"):
        return
    distro, home = _wsl_probe_distro_and_home()
    if not distro:
        # WSL not available, skip WSL path setup
        return
    for base in (fr"\\wsl.localhost\{distro}", fr"\\wsl$\{distro}"):
        prefix = base + home.replace("/", "\\")
        codex_path = prefix + r"\.codex\sessions"
        gemini_path = prefix + r"\.gemini\tmp"
        if Path(codex_path).exists() or Path(gemini_path).exists():
            os.environ.setdefault("CODEX_SESSION_ROOT", codex_path)
            os.environ.setdefault("GEMINI_ROOT", gemini_path)
            return
    prefix = fr"\\wsl.localhost\{distro}" + home.replace("/", "\\")
    os.environ.setdefault("CODEX_SESSION_ROOT", prefix + r"\.codex\sessions")
    os.environ.setdefault("GEMINI_ROOT", prefix + r"\.gemini\tmp")
