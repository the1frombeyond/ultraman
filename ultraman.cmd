@echo off
REM ULTRAMAN CLI Launcher
REM Created by install.py

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if exist "%SCRIPT_DIR%\main.py" (
    python "%SCRIPT_DIR%\main.py" %*
) else (
    echo Error: ULTRAMAN main.py not found
    exit /b 1
)