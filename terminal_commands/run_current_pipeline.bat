@echo off
cd /d "%~dp0\.."
echo ========================================================
echo Starting OWN Sense CURRENT Production Pipeline...
echo ========================================================
.\.venv\Scripts\python.exe current\run_pipeline.py
pause

