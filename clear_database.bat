@echo off
setlocal

set "APP_DIR=%~dp0"
set "DATA_DIR=%USERPROFILE%\Desktop\Instagram Exporter Data"

where py >nul 2>&1
if errorlevel 1 (
  echo Python 3 was not found.
  pause
  exit /b 1
)

py -3 "%APP_DIR%clear_database.py" --data-dir "%DATA_DIR%"
echo.
pause
