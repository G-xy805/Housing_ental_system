@echo off
REM Gunicorn 启动脚本 (Windows 使用 waitress)
REM 注意: Gunicorn 不支持 Windows，请使用 waitress 或部署到 Linux 服务器

echo ========================================
echo 房屋租赁系统 - 生产环境启动
echo ========================================
echo.

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [OK] 虚拟环境已激活
) else (
    echo [警告] 未找到虚拟环境，使用系统 Python
)

echo.
echo [提示] Gunicorn 不支持 Windows 系统
echo [提示] Windows 用户请使用以下方式之一:
echo   1. 使用 waitress: pip install waitress
echo   2. 使用 run_production.py
echo   3. 部署到 Linux 服务器使用 Gunicorn
echo.
echo 正在启动 waitress 服务器...
echo.

REM 使用 waitress 启动 (Windows 替代方案)
python -c "from waitress import serve; from run import app; serve(app, host='0.0.0.0', port=5000, threads=4)"

pause
