"""
Gunicorn 配置文件
用于生产环境部署的 WSGI HTTP 服务器配置
"""
import os
import multiprocessing
import sys

# 添加项目根目录到 Python 路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))


# ============================================================================
# Worker 进程配置
# ============================================================================

# Worker 进程数
# 推荐公式：(2 * CPU核心数) + 1
# 这允许每个 CPU 核心处理 2 个 worker，外加一个用于处理 I/O 等待
workers = int(os.getenv('GUNICORN_WORKERS', (multiprocessing.cpu_count() * 2) + 1))

# 每个 worker 的线程数
# 使用 gevent 或 eventlet 时可以设置更高的值
# 使用 sync worker 时建议设置为 1
threads = int(os.getenv('GUNICORN_THREADS', 1))

# Worker 类型
# 可选值: sync, gevent, eventlet, tornado, gthread
# gevent 适合 I/O 密集型应用，需要安装 gevent 包
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')

# 每个 worker 处理的最大请求数
# 超过此数值后 worker 会重启，有助于防止内存泄漏
# 设置为 0 表示不限制
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))

# 最大请求数的抖动值
# 在 max_requests 的基础上增加随机抖动，避免所有 worker 同时重启
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 50))

# Worker 超时时间（秒）
# 超过此时间没有响应的 worker 会被强制重启
# 对于长时间运行的任务，需要适当增加此值
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))

# 优雅关闭超时时间（秒）
# 当 worker 收到 SIGTERM 信号后，在此时间内完成当前请求后关闭
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))

# Keep-alive 超时时间（秒）
# HTTP Keep-Alive 连接的保持时间
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 5))


# ============================================================================
# 网络配置
# ============================================================================

# 监听地址和端口
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:5000')

# 监听地址列表（可以同时监听多个地址）
# binds = ['0.0.0.0:5000', '127.0.0.1:5001']

# 监听队列长度
# 等待连接的最大数量，超过此值的连接会被拒绝
backlog = int(os.getenv('GUNICORN_BACKLOG', 2048))


# ============================================================================
# 进程管理配置
# ============================================================================

# 进程名
# 在进程列表中显示的名称
proc_name = os.getenv('GUNICORN_PROC_NAME', 'housing_rental_system')

# PID 文件路径
# 用于存储主进程 PID，方便管理
pidfile = os.getenv('GUNICORN_PIDFILE', None)

# 用户和组
# 以指定用户和组运行 worker 进程（需要 root 权限启动）
user = os.getenv('GUNICORN_USER', None)
group = os.getenv('GUNICORN_GROUP', None)

# 守护进程模式
# 设置为 True 时，Gunicorn 会在后台运行
daemon = os.getenv('GUNICORN_DAEMON', 'False').lower() == 'true'

# 工作目录
# Gunicorn 的运行目录
# chdir = BASE_DIR


# ============================================================================
# 日志配置
# ============================================================================

# 日志级别
# 可选值: debug, info, warning, error, critical
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# 访问日志文件
# '-' 表示输出到 stdout
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')

# 错误日志文件
# '-' 表示输出到 stderr
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')

# 日志文件目录
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 如果指定了日志文件，则使用文件路径
if accesslog and accesslog != '-':
    accesslog = os.path.join(LOG_DIR, accesslog)
if errorlog and errorlog != '-':
    errorlog = os.path.join(LOG_DIR, errorlog)

# 访问日志格式
# %(h)s - 远程地址
# %(l)s - 远程用户名（通常为 -）
# %(u)s - 认证用户名
# %(t)s - 请求时间
# %(r)s - 请求行
# %(s)s - 状态码
# %(b)s - 响应大小
# %(f)s - Referer
# %(a)s - User-Agent
# %(D)s - 请求处理时间（微秒）
# %(p)s - 进程 ID
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 日志日期格式
# logger_class = 'gunicorn.glogging.Logger'


# ============================================================================
# 安全配置
# ============================================================================

# 限制请求行最大大小（字节）
# 防止过大的请求头攻击
limit_request_line = int(os.getenv('GUNICORN_LIMIT_REQUEST_LINE', 4096))

# 限制请求头字段数量
limit_request_fields = int(os.getenv('GUNICORN_LIMIT_REQUEST_FIELDS', 100))

# 限制请求头字段大小（字节）
limit_request_field_size = int(os.getenv('GUNICORN_LIMIT_REQUEST_FIELD_SIZE', 8190))


# ============================================================================
# 性能调优配置
# ============================================================================

# 预加载应用
# 在 fork worker 之前加载应用代码
# 优点：减少内存使用（Copy-on-Write）
# 缺点：无法在运行时重新加载应用代码
preload_app = os.getenv('GUNICORN_PRELOAD_APP', 'True').lower() == 'true'

# 禁用访问日志
# 在高并发场景下可以提升性能
# disable_redirect_access_to_syslog = True


# ============================================================================
# 钩子函数配置
# ============================================================================

def on_starting(server):
    """
    在主进程启动时调用
    """
    print(f"[Gunicorn] 正在启动房屋租赁系统...")
    print(f"[Gunicorn] Worker 进程数: {workers}")
    print(f"[Gunicorn] 监听地址: {bind}")
    print(f"[Gunicorn] 超时时间: {timeout}s")


def when_ready(server):
    """
    当主进程准备就绪时调用
    """
    print(f"[Gunicorn] 服务已就绪，开始接受请求")


def on_exit(server):
    """
    在主进程退出时调用
    """
    print(f"[Gunicorn] 服务正在关闭...")


def pre_fork(server, worker):
    """
    在 fork worker 之前调用
    """
    pass


def post_fork(server, worker):
    """
    在 fork worker 之后调用
    """
    # 可以在这里初始化数据库连接池等资源
    print(f"[Gunicorn] Worker {worker.pid} 已启动")


def pre_exec(server):
    """
    在 exec 之前调用（用于热重载）
    """
    print(f"[Gunicorn] 正在重新加载应用...")


def worker_int(worker):
    """
    当 worker 收到 INT 或 QUIT 信号时调用
    """
    print(f"[Gunicorn] Worker {worker.pid} 收到中断信号")


def worker_abort(worker):
    """
    当 worker 收到 SIGABRT 信号时调用
    """
    print(f"[Gunicorn] Worker {worker.pid} 被强制终止")


def worker_exit(server, worker):
    """
    当 worker 退出时调用
    """
    print(f"[Gunicorn] Worker {worker.pid} 已退出")


def nworkers_changed(server, new_value, old_value):
    """
    当 worker 数量变化时调用
    """
    print(f"[Gunicorn] Worker 数量从 {old_value} 变更为 {new_value}")


# ============================================================================
# WSGI 应用入口
# ============================================================================

# 指定 WSGI 应用入口
# 格式: module:variable
# wsgi_app = 'run:app'


# ============================================================================
# 配置摘要输出
# ============================================================================

def print_config_summary():
    """打印配置摘要"""
    print("\n" + "=" * 60)
    print("Gunicorn 配置摘要")
    print("=" * 60)
    print(f"  Worker 进程数:     {workers}")
    print(f"  Worker 类型:       {worker_class}")
    print(f"  线程数/Worker:     {threads}")
    print(f"  最大请求数:        {max_requests} (抖动: ±{max_requests_jitter})")
    print(f"  超时时间:          {timeout}s")
    print(f"  优雅关闭超时:      {graceful_timeout}s")
    print(f"  Keep-Alive 超时:   {keepalive}s")
    print(f"  监听地址:          {bind}")
    print(f"  监听队列:          {backlog}")
    print(f"  日志级别:          {loglevel}")
    print(f"  预加载应用:        {preload_app}")
    print(f"  进程名:            {proc_name}")
    print("=" * 60 + "\n")


# 启动时打印配置摘要
if __name__ != '__main__':
    print_config_summary()
