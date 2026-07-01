@echo off
chcp 65001 >nul
title Factory R&D PMS - Test Runner

set "SCRIPT_DIR=%~dp0"
set "POWERSHELL_SCRIPT=%SCRIPT_DIR%run_tests.ps1"

if not exist "%POWERSHELL_SCRIPT%" (
    echo Error: run_tests.ps1 not found at %POWERSHELL_SCRIPT%
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%POWERSHELL_SCRIPT%" %*

pause