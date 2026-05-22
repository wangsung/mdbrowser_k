@echo off
title Evernote Archive Navigator
chcp 65001 > nul
cls

echo ===================================================
echo          Evernote Archive Navigator Launcher
echo ===================================================
echo  Base Path: C:\_My2026\_EVERBK
echo ===================================================
echo.

echo [*] Checking Python environment...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [-] Error: Python is not installed or not in PATH!
    echo     Please install Python 3.8+ and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [*] Installing required libraries (Flask, PyYAML)...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [-] Warning: Failed to install some dependencies.
    echo     We will still attempt to run the server.
)

echo.
echo [+] Starting local web server on http://127.0.0.1:5000/ ...
echo [+] Your default browser will open automatically in 2 seconds.
echo [!] Keep this window open while using the application!
echo.

# Delay 2 seconds and launch default browser
timeout /t 2 /nobreak > nul
start "" "http://127.0.0.1:5000/"

# Launch the Flask server
python server.py

pause
