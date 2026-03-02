@echo off
chcp 65001 >nul
title Housing Rental System - Backend

echo ========================================
echo    Housing Rental System - Backend
echo ========================================
echo.

:: 查找虚拟环境
set VENV_DIR=
for %%p in (.venv venv env .env) do (
    if exist "%%p\Scripts\python.exe" (
        set VENV_DIR=%%p
        goto :found
    )
)

echo [错误] 未找到虚拟环境
echo.
echo 请先创建虚拟环境：
echo   python -m venv .venv
echo   .venv\Scripts\activate.bat
echo   pip install -r requirements.txt
echo.
pause
exit /b 1

:found
echo [信息] 使用虚拟环境：%VENV_DIR%
echo.

:: 检查依赖
echo [信息] 检查依赖...
"%VENV_DIR%\Scripts\python.exe" -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [信息] 安装依赖...
    "%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

:: 启动
echo [信息] 启动服务...
echo.
"%VENV_DIR%\Scripts\python.exe" run.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查上方错误信息
    pause
)
