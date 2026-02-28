@echo off
chcp 65001 >nul
title Housing Rental System - Launcher

echo ========================================
echo    Housing Rental System - Launcher
echo ========================================
echo.

:: Start backend service (new window)
echo [Starting Backend Service...]
start "Backend Service" cmd /k "cd /d %~dp0 && call start-backend.bat"

:: Wait 3 seconds
timeout /t 3 /nobreak >nul

:: Start frontend service (new window)
echo [Starting Frontend Service...]
start "Frontend Service" cmd /k "cd /d %~dp0 && call start-frontend.bat"

echo.
echo ========================================
echo    Services Started Successfully!
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Tips:
echo - Services running in separate windows
echo - Close this window does not stop services
echo - To stop services, close corresponding windows
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:5173

exit