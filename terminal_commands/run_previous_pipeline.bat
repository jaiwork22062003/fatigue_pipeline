@echo off
cd /d "%~dp0\.."
echo ========================================================
echo Starting OWN Sense PREVIOUS KT-Doc Pipeline...
echo ========================================================
.\.venv\Scripts\python.exe previous\run_pipeline.py
pause

