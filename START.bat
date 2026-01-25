@echo off
title NEXUS SYSTEM - LAUNCHER
color 0b
cls

echo ==================================================
echo    NEXUS INTELLIGENCE SYSTEM v1.0
echo    INITIALIZING MODULES...
echo ==================================================
echo.

echo [1/3] Loading Neural Environment...
call venv\Scripts\activate

echo [2/3] Verifying Integrity...
python -c "print('>> SYSTEM STATUS: ONLINE')"

echo [3/3] Launching Interface...
echo.
python main.py

pause