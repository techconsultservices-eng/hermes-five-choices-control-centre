@echo off
setlocal
set "APP_ROOT=%LOCALAPPDATA%\HermesFiveChoices"
set "RUNTIME_ROOT=%LOCALAPPDATA%\HermesFiveChoicesRuntime"
set "DATA_ROOT=%LOCALAPPDATA%\HermesFiveChoicesData\hermes"
set "PRESERVE_ROOT=%LOCALAPPDATA%\HermesFiveChoicesData"
if defined H5_INSTALL_TARGET set "APP_ROOT=%H5_INSTALL_TARGET%"
if defined H5_RUNTIME_ROOT set "RUNTIME_ROOT=%H5_RUNTIME_ROOT%"
if defined H5_HERMES_HOME set "DATA_ROOT=%H5_HERMES_HOME%"
if defined H5_PRESERVE_ROOT set "PRESERVE_ROOT=%H5_PRESERVE_ROOT%"
set "PYTHON=%RUNTIME_ROOT%\hermes-agent\venv\Scripts\python.exe"
set "BOOTSTRAP_PYTHON=%RUNTIME_ROOT%\python\python.exe"
set "TEMP_UNINSTALL=%TEMP%\HermesFiveChoicesUninstall"

if not exist "%BOOTSTRAP_PYTHON%" (
  echo The product runtime is already absent. Your data remains at %PRESERVE_ROOT%.
  if not "%H5_NO_PAUSE%"=="1" pause
  exit /b 0
)
echo Chats, profiles, authentication and generated data will be preserved under:
echo   %PRESERVE_ROOT%
echo The application and frozen runtime will be removed.
if not "%H5_UNINSTALL_CONFIRM%"=="1" (
  choice /C YN /N /M "Continue with uninstall? [Y/N] "
  if errorlevel 2 exit /b 0
)
if exist "%APP_ROOT%\installer\start_services.py" (
  "%PYTHON%" "%APP_ROOT%\installer\start_services.py" --app-root "%APP_ROOT%" --runtime-root "%RUNTIME_ROOT%" --hermes-home "%DATA_ROOT%" --stop
  if errorlevel 1 (
    echo Product services could not be stopped safely. Uninstall was not started.
    if not "%H5_NO_PAUSE%"=="1" pause
    exit /b 1
  )
)
rmdir /s /q "%TEMP_UNINSTALL%" >nul 2>&1
mkdir "%TEMP_UNINSTALL%"
xcopy "%RUNTIME_ROOT%\python" "%TEMP_UNINSTALL%\python\" /E /I /Q /Y >nul
copy /Y "%APP_ROOT%\installer\bootstrapper.py" "%TEMP_UNINSTALL%\bootstrapper.py" >nul
"%TEMP_UNINSTALL%\python\python.exe" "%TEMP_UNINSTALL%\bootstrapper.py" uninstall --target "%APP_ROOT%" --runtime-root "%RUNTIME_ROOT%" --hermes-home "%DATA_ROOT%" --preserve-root "%PRESERVE_ROOT%"
if errorlevel 1 (
  echo Uninstall did not complete.
  if not "%H5_NO_PAUSE%"=="1" pause
  exit /b 1
)
rmdir /s /q "%TEMP_UNINSTALL%\python" >nul 2>&1
del /q "%TEMP_UNINSTALL%\bootstrapper.py" >nul 2>&1
del /q "%USERPROFILE%\Desktop\Hermes Five Choices.lnk" >nul 2>&1
del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Hermes Five Choices.lnk" >nul 2>&1
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Hermes Five Choices" >nul 2>&1
echo Hermes Five Choices was removed. Your data was preserved.
if not "%H5_NO_PAUSE%"=="1" pause
exit /b 0
