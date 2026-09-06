@echo off
setlocal
set "APP_ROOT=%LOCALAPPDATA%\HermesFiveChoices"
set "RUNTIME_ROOT=%LOCALAPPDATA%\HermesFiveChoicesRuntime"
set "DATA_ROOT=%LOCALAPPDATA%\HermesFiveChoicesData\hermes"
set "PYTHON=%RUNTIME_ROOT%\hermes-agent\venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  mshta "javascript:alert('Hermes Five Choices runtime is missing. Re-run the installer to repair it.');close()"
  exit /b 1
)
"%PYTHON%" "%APP_ROOT%\installer\start_services.py" --app-root "%APP_ROOT%" --runtime-root "%RUNTIME_ROOT%" --hermes-home "%DATA_ROOT%"
exit /b %ERRORLEVEL%
