@echo off
setlocal
set "APP_ROOT=%LOCALAPPDATA%\HermesFiveChoices"
set "RUNTIME_ROOT=%LOCALAPPDATA%\HermesFiveChoicesRuntime"
set "DATA_ROOT=%LOCALAPPDATA%\HermesFiveChoicesData\hermes"
set "PYTHON=%RUNTIME_ROOT%\hermes-agent\venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo The Hermes Five Choices runtime is missing. Re-run the installer.
  pause
  exit /b 1
)
"%PYTHON%" "%APP_ROOT%\installer\diagnostics.py" --target "%APP_ROOT%" --runtime-root "%RUNTIME_ROOT%" --hermes-home "%DATA_ROOT%" --check-services
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo Diagnostics passed.) else (echo Diagnostics found an issue.)
pause
exit /b %RC%
