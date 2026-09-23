@echo off
setlocal
set "APP_DIR=%~dp0"
set "DATA_DIR=%USERPROFILE%\Desktop\Instagram Exporter Data"
py -3 "%APP_DIR%result.py" --data-dir "%DATA_DIR%"
echo.
pause
