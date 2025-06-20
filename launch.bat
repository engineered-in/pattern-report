@echo off
setlocal enabledelayedexpansion
echo Checking for updates and running the script...
git pull origin main
git switch main
uv sync
.venv\scripts\python.exe main.py
if %ERRORLEVEL% neq 0 (
    pause
    exit /b %ERRORLEVEL%
)
for /f "tokens=*" %%i in ('dir "Reports\Report_*.xlsx" /b /o-d /t:c') do (
    set "LAST_REPORT=%%i"
    goto :found
)
:found
    REM Check if a report was found
    if defined LAST_REPORT (
        start "" "Reports\!LAST_REPORT!"
    ) else (
        echo No report files found.
    )
pause