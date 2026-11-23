@echo off
cd /d "%~dp0\.."
echo ========================================================
echo Starting CURRENT Production Pipeline Dashboard Server...
echo URL: http://127.0.0.1:8001
echo ========================================================
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe current\server.py --port 8001
) else (
    python current\server.py --port 8001
)
pause
