@echo off
setlocal
set "CCB8_PS1=%~dp0ccb8.ps1"
if not exist "%CCB8_PS1%" (
  echo CCB source/dev PowerShell wrapper not found: "%CCB8_PS1%" 1>&2
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%CCB8_PS1%" %*
exit /b %ERRORLEVEL%
