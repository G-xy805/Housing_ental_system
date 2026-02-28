@echo off
chcp 65001 >nul
title Housing Rental System - Backend Service

echo ========================================
echo    Housing Rental System - Backend
echo ========================================
echo.

:: Check virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [Error] Python virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

:: Activate virtual environment and start backend
call .venv\Scripts\activate.bat
python run.py

pause