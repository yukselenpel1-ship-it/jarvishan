@echo off
title JARVIS Windows Koprusu (PC Kontrol)
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Once KURULUM.bat dosyasini calistirin.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" kopru_servisi.py %*
if errorlevel 1 pause
