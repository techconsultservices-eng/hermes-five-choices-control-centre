@echo off
setlocal
call "%~dp0start_background.bat"
if errorlevel 1 (
  mshta "javascript:alert('Hermes Five Choices could not start. Open Run Diagnostics from the Start Menu.');close()"
  exit /b 1
)
start "" http://127.0.0.1:9335/
endlocal
