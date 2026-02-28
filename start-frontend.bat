@echo off
chcp 65001 >nul
title Housing Rental System - Frontend Service

echo ========================================
echo    Housing Rental System - Frontend
echo ========================================
echo.

:: Check Node.js
where node >nul 2>nul
if errorlevel 1 (
    echo [Error] Node.js not found!
    echo Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)

:: Check dependencies
if not exist "node_modules" (
    echo [Info] First run, installing dependencies...
    call npm install
    if errorlevel 1 (
        echo [Error] Dependencies installation failed!
        pause
        exit /b 1
    )
)

:: Start frontend
npm run dev

pause