@echo off
title Crescent Seat Management - Push to GitHub
cd /d "%~dp0"

echo ======================================================================
echo    Crescent Islamic High School - GitHub Push Tool
echo ======================================================================
echo.

set /p MSG="Enter commit message (Press Enter for default): "
if "%MSG%"=="" (
    set MSG="Update project files"
)

python github_sync.py push "%MSG%"

echo.
echo ======================================================================
echo Execution complete.
echo ======================================================================
pause
