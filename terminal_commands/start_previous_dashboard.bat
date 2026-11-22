@echo off
cd /d "%~dp0\.."
echo ========================================================
echo Starting PREVIOUS KT-Doc Pipeline Dashboard Server...
echo URL: http://127.0.0.1:8002
echo ========================================================
.\.venv\Scripts\python.exe previous\server.py --port 8002
pause

