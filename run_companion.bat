@echo off
setlocal
set "RUNTIME_ROOT=%LOCALAPPDATA%\HermesFiveChoicesRuntime"
set "H5_HERMES_ROOT=%LOCALAPPDATA%\HermesFiveChoicesData\hermes"
set "HERMES_API=http://127.0.0.1:8642"
set "HERMES_COMMAND=%RUNTIME_ROOT%\hermes-agent\venv\Scripts\hermes.exe"
set "PYTHON=%RUNTIME_ROOT%\hermes-agent\venv\Scripts\python.exe"
set "PYTHONIOENCODING=utf-8"
if not exist "%PYTHON%" exit /b 1
cd /d "%~dp0"
"%PYTHON%" -u dashboard_server.py
endlocal
