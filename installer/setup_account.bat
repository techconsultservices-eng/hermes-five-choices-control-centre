@echo off
setlocal
set "APP_ROOT=%LOCALAPPDATA%\HermesFiveChoices"
set "RUNTIME_ROOT=%LOCALAPPDATA%\HermesFiveChoicesRuntime"
set "DATA_ROOT=%LOCALAPPDATA%\HermesFiveChoicesData\hermes"
set "HERMES=%RUNTIME_ROOT%\hermes-agent\venv\Scripts\hermes.exe"
set "PYTHON=%RUNTIME_ROOT%\hermes-agent\venv\Scripts\python.exe"
if not exist "%HERMES%" (
  echo Hermes Five Choices is not installed correctly. Re-run the installer.
  pause
  exit /b 1
)
set "HERMES_HOME=%DATA_ROOT%\profiles\assistant"
echo.
echo Hermes will open its official Nous Portal sign-in flow.
echo Passwords and OAuth tokens are handled by Hermes and your browser, not this dashboard.
echo.
"%HERMES%" setup --portal
if errorlevel 1 (
  echo.
  echo Account setup did not complete. Nothing was propagated.
  pause
  exit /b 1
)
echo.
choice /C YN /N /M "Use this same Portal account and selected model for all five specialists? [Y/N] "
if errorlevel 2 goto done
"%PYTHON%" "%APP_ROOT%\installer\propagate_account.py" --command "%HERMES%" --hermes-home "%DATA_ROOT%"
if errorlevel 1 (
  echo.
  echo Account propagation did not complete. Review the message above.
  pause
  exit /b 1
)
:done
echo.
echo Account setup finished. You can close this window and return to Five Choices.
pause
endlocal
