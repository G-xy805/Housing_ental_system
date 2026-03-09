"""
房屋租赁系统 - 生产环境启动入口

使用 Waitress 作为生产服务器，支持 Windows 系统和 PyInstaller 打包
"""
import os
import sys
import webbrowser
import logging
from pathlib import Path
from typing import Optional


def setup_pyinstaller_paths() -> Path:
    """
    配置 PyInstaller 打包后的资源路径

    Returns:
        Path: 应用根目录路径
    """
    # 检查是否在 PyInstaller 打包环境中运行
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的路径
        application_path = Path(sys._MEIPASS)
        # 设置工作目录为 exe 所在目录
        exe_dir = Path(sys.executable).parent
        os.chdir(exe_dir)
        print(f"PyInstaller 模式 - 工作目录: {exe_dir}")
        print(f"PyInstaller 模式 - 资源目录: {application_path}")
        return application_path
    else:
        # 开发环境路径
        application_path = Path(__file__).parent
        return application_path


def setup_environment(app_root: Path) -> None:
    """
    设置环境变量

    Args:
        app_root: 应用根目录路径
    """
    # 设置 Flask 环境
    os.environ['FLASK_ENV'] = 'production'

    # 设置应用根目录（用于配置文件路径）
    os.environ['APP_ROOT'] = str(app_root)

    # 确保日志目录存在
    logs_dir = app_root / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # 确保上传目录存在
    uploads_dir = app_root / 'uploads'
    uploads_dir.mkdir(exist_ok=True)

    # 确保备份目录存在
    backups_dir = app_root / 'backups'
    backups_dir.mkdir(exist_ok=True)


def open_browser(url: str, delay: float = 2.0) -> bool:
    """
    延迟打开浏览器

    Args:
        url: 要打开的 URL
        delay: 延迟时间（秒）

    Returns:
        bool: 是否成功打开浏览器
    """
    import time
    import threading

    def _open_browser():
        """在独立线程中打开浏览器"""
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"✓ 浏览器已打开: {url}")
            return True
        except Exception as e:
            print(f"✗ 无法自动打开浏览器: {str(e)}")
            print(f"  请手动访问: {url}")
            return False

    # 在独立线程中打开浏览器，避免阻塞主线程
    browser_thread = threading.Thread(target=_open_browser, daemon=True)
    browser_thread.start()
    return True


def print_startup_info(host: str, port: int) -> None:
    """
    打印启动信息

    Args:
        host: 服务器主机地址
        port: 服务器端口
    """
    url = f"http://{host}:{port}"

    print("\n" + "=" * 60)
    print("  房屋租赁系统 - 生产环境服务器")
    print("=" * 60)
    print(f"  访问地址: {url}")
    print(f"  API 文档: {url}/api/")
    print(f"  健康检查: {url}/api/health")
    print("=" * 60)
    print("  按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")


def run_server(host: str = '0.0.0.0', port: int = 5000) -> None:
    """
    启动生产服务器

    Args:
        host: 服务器监听地址
        port: 服务器监听端口
    """
    try:
        # 配置 PyInstaller 路径
        app_root = setup_pyinstaller_paths()

        # 设置环境变量
        setup_environment(app_root)

        # 导入 Flask 应用（在设置环境变量后导入）
        from app import create_app

        # 创建应用实例
        app = create_app(config_name='production')

        # 打印启动信息
        print_startup_info(host, port)

        # 尝试打开浏览器
        open_browser(f"http://localhost:{port}")

        # 尝试使用 Waitress 启动服务器
        try:
            from waitress import serve

            print("使用 Waitress 生产服务器...")
            print(f"监听地址: {host}:{port}")
            print(f"线程数: 4 (默认)\n")

            # 使用 Waitress 启动
            serve(
                app,
                host=host,
                port=port,
                threads=4,  # 工作线程数
                url_scheme='http',
                channel_timeout=120,  # 通道超时时间（秒）
                connection_limit=100,  # 最大连接数
                cleanup_interval=30,  # 清理间隔（秒）
                expose_tracebacks=False,  # 不暴露错误堆栈
            )

        except ImportError:
            # 如果没有安装 Waitress，回退到 Flask 开发服务器
            print("⚠ 未安装 Waitress，使用 Flask 开发服务器（不推荐用于生产环境）")
            print("建议安装: pip install waitress\n")

            app.run(
                host=host,
                port=port,
                debug=False,
                threaded=True
            )

    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ 启动失败: {str(e)}")
        logging.exception("服务器启动异常")
        sys.exit(1)


def main() -> None:
    """主函数"""
    # 从环境变量读取配置，或使用默认值
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 5000))

    # 启动服务器
    run_server(host=host, port=port)


if __name__ == '__main__':
    main()
