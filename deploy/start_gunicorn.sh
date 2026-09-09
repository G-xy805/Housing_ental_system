#!/bin/bash
# Gunicorn 启动脚本 (Linux/Unix)
# 用法: ./start_gunicorn.sh [start|stop|restart|status]

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# 配置文件路径
GUNICORN_CONF="$PROJECT_DIR/deploy/gunicorn.conf.py"
PID_FILE="$PROJECT_DIR/logs/gunicorn.pid"

# 虚拟环境路径
VENV_PATH="$PROJECT_DIR/.venv"

# 加载环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查虚拟环境
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
        log_info "虚拟环境已激活"
    else
        log_warn "未找到虚拟环境，使用系统 Python"
    fi
}

# 启动服务
start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log_warn "服务已在运行中 (PID: $PID)"
            return 1
        fi
    fi
    
    log_info "正在启动 Gunicorn..."
    activate_venv
    
    # 创建日志目录
    mkdir -p "$PROJECT_DIR/logs"
    
    # 启动 Gunicorn
    gunicorn -c "$GUNICORN_CONF" \
        --pid "$PID_FILE" \
        "run:app"
    
    sleep 2
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        log_info "服务启动成功 (PID: $PID)"
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 停止服务
stop() {
    if [ ! -f "$PID_FILE" ]; then
        log_warn "PID 文件不存在，服务可能未运行"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! ps -p $PID > /dev/null 2>&1; then
        log_warn "服务进程不存在 (PID: $PID)"
        rm -f "$PID_FILE"
        return 1
    fi
    
    log_info "正在停止服务 (PID: $PID)..."
    
    # 发送 SIGTERM 信号进行优雅关闭
    kill -TERM $PID
    
    # 等待进程退出
    for i in {1..30}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            log_info "服务已停止"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # 强制终止
    log_warn "优雅关闭超时，强制终止..."
    kill -9 $PID
    rm -f "$PID_FILE"
    log_info "服务已强制停止"
}

# 重启服务
restart() {
    log_info "正在重启服务..."
    stop
    sleep 2
    start
}

# 查看状态
status() {
    if [ ! -f "$PID_FILE" ]; then
        log_warn "服务未运行 (PID 文件不存在)"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p $PID > /dev/null 2>&1; then
        log_info "服务正在运行 (PID: $PID)"
        
        # 显示进程信息
        ps -fp $PID
        
        # 显示 worker 进程
        log_info "Worker 进程:"
        pgrep -P $PID | while read worker_pid; do
            ps -fp $worker_pid 2>/dev/null
        done
    else
        log_warn "服务未运行 (PID: $PID 进程不存在)"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 重新加载配置
reload() {
    if [ ! -f "$PID_FILE" ]; then
        log_error "服务未运行"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    log_info "正在重新加载配置 (PID: $PID)..."
    
    # 发送 HUP 信号进行优雅重载
    kill -HUP $PID
    
    log_info "配置重新加载完成"
}

# 主函数
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    reload)
        reload
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|reload}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  reload  - 重新加载配置"
        exit 1
        ;;
esac

exit $?
