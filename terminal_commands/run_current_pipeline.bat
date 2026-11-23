@echo off
cd /d "%~dp0\.."
echo ========================================================
echo Starting OWN Sense CURRENT Production Pipeline...
echo ========================================================
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe current\run_pipeline.py
) else (
    python current\run_pipeline.py
)
pause
