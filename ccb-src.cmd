@echo off
setlocal
set "CCB_SRC_EXIT_PROCESS=1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ccb-src.ps1" %*
exit /b %ERRORLEVEL%
