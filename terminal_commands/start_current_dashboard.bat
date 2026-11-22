@echo off
cd /d "%~dp0\.."
echo ========================================================
echo Starting CURRENT Production Pipeline Dashboard Server...
echo URL: http://127.0.0.1:8001
echo ========================================================
.\.venv\Scripts\python.exe current\server.py --port 8001
pause

