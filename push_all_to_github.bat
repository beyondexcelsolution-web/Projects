@echo off
title Beyond Excel - Push All Projects to GitHub
cd /d "%~dp0"

echo ======================================================================
echo    Beyond Excel Solution - Master Projects GitHub Push
echo ======================================================================
echo.

set /p MSG="Enter commit message (Press Enter for default): "
if "%MSG%"=="" (
    set MSG="Update client projects codebase"
)

python github_sync_all.py push "%MSG%"

echo.
echo ======================================================================
echo Execution complete.
echo ======================================================================
pause
