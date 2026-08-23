@echo off
setlocal enableextensions enabledelayedexpansion

rem ============================================================
rem  ccb.cmd - Windows launcher for the CCB source checkout
rem
rem  Wraps the project's `ccb` (bash launcher) for native Windows:
rem    1. resolves a CCB-compatible Python interpreter (same priority
rem       order and requirements as bin\_ccb-python)
rem    2. runs ccb.py in source-checkout mode (CCB_SOURCE_RUNTIME_OK=1)
rem
rem  Usage: ccb.cmd [args...]
rem ============================================================

set "SCRIPT_DIR=%~dp0"
if not "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR%\"
set "TARGET=%SCRIPT_DIR%ccb.py"

if not exist "%TARGET%" (
    echo ccb.cmd: entrypoint missing: %TARGET%
    exit /b 127
)

rem ---- CCB-compatible Python validation ----
rem Mirrors the heredoc check in bin\_ccb-python: Python >= 3.10 plus
rem tomllib/tomli, aiohttp and the cryptography primitives.
set "VALIDATE_CODE=import sys, importlib.util; assert sys.version_info >= (3, 10); assert importlib.util.find_spec('tomllib') or importlib.util.find_spec('tomli'); import aiohttp; from cryptography.hazmat.primitives.asymmetric import ed25519, x25519; from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305"

set "PYEXE="
set "WRITE_CACHE=0"

rem 1) explicit override CCB_PYTHON
if defined CCB_PYTHON (
    call :probe_validated "%CCB_PYTHON%"
    if "!VALID!"=="1" set "PYEXE=%CCB_PYTHON%"
)

rem 2) managed interpreter beside the source checkout (.venv)
if not defined PYEXE (
    if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
        call :probe_validated "%SCRIPT_DIR%.venv\Scripts\python.exe"
        if "!VALID!"=="1" (
            set "PYEXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
            set "WRITE_CACHE=1"
        )
    )
)

rem 3) cached interpreter from ~/.ccb/state/python-bin
if not defined PYEXE (
    if defined USERPROFILE (
        if exist "%USERPROFILE%\.ccb\state\python-bin" (
            set /p CACHE_PY=<"%USERPROFILE%\.ccb\state\python-bin"
            call :probe_validated "!CACHE_PY!"
            if "!VALID!"=="1" set "PYEXE=!CACHE_PY!"
        )
    )
)

rem 4) probe PATH (python3.13 ... py); first valid match wins
if not defined PYEXE (
    for %%C in (python3.13 python3.12 python3.11 python3.10 python3 python py) do (
        if not defined PYEXE (
            for /f "delims=" %%P in ('where %%C 2^>nul') do (
                if not defined PYEXE (
                    call :probe_validated "%%P"
                    if "!VALID!"=="1" (
                        set "PYEXE=%%P"
                        set "WRITE_CACHE=1"
                    )
                )
            )
        )
    )
)

if not defined PYEXE (
    echo ccb.cmd: cannot find a Python interpreter compatible with CCB.
    echo     Required: Python ^>= 3.10 with tomllib/tomli, aiohttp, and cryptography.
    echo     Set CCB_PYTHON to an absolute path to python.exe if an explicit override is needed.
    exit /b 127
)

if "%WRITE_CACHE%"=="1" if defined USERPROFILE (
    if not exist "%USERPROFILE%\.ccb\state\" mkdir "%USERPROFILE%\.ccb\state" >nul 2>&1
    > "%USERPROFILE%\.ccb\state\python-bin" echo %PYEXE%
)

rem ---- Run CCB in source-checkout mode ----
set "CCB_PYTHON=%PYEXE%"
set "CCB_SOURCE_RUNTIME_OK=1"

"%PYEXE%" "%TARGET%" %*
set "CCB_EXIT=%ERRORLEVEL%"
endlocal & exit /b %CCB_EXIT%

rem ============================================================
rem  Subroutine: validate a candidate Python interpreter.
rem  Sets VALID=1 if the candidate is usable by CCB, else VALID=0.
rem ============================================================
:probe_validated
set "VALID=0"
set "CAND=%~1"
if "%CAND%"=="" exit /b 0
"%CAND%" -c "%VALIDATE_CODE%" >nul 2>&1
if not errorlevel 1 set "VALID=1"
exit /b 0
