@echo off
REM OpsCollector-CLI launcher
REM Runs the application using the bundled virtual environment.
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py %*
