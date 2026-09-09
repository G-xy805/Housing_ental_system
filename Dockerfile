# ============================================
# 房屋租赁系统 - Docker 多阶段构建文件
# ============================================
# 构建阶段:
#   Stage 1: 前端构建 (Node.js)
#   Stage 2: 后端依赖安装 (Python)
#   Stage 3: 最终运行镜像
# ============================================

# ============================================
# Stage 1: 前端构建
# ============================================
FROM node:20-alpine AS frontend-builder

# 设置工作目录
WORKDIR /app/frontend

# 设置 npm 镜像源（加速依赖下载）
RUN npm config set registry https://registry.npmmirror.com

# 复制前端依赖文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm ci --legacy-peer-deps

# 复制前端源代码
COPY src/ ./src/
COPY index.html ./
COPY vite.config.js ./
COPY vitest.config.js ./

# 复制样式文件
COPY src/styles/ ./src/styles/

# 构建前端（生产模式）
RUN npm run build

# ============================================
# Stage 2: 后端依赖安装
# ============================================
FROM python:3.11-slim AS backend-builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 3: 最终运行镜像
# ============================================
FROM python:3.11-slim AS runtime

# 设置标签
LABEL maintainer="Housing Rental System"
LABEL version="1.0.0"
LABEL description="房屋租赁系统 - 生产环境 Docker 镜像"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_APP=app \
    PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=backend-builder /opt/venv /opt/venv

# 复制后端应用代码
COPY app/ ./app/
COPY wsgi.py .
COPY .env.production.example .env.example

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/frontend/dist ./dist

# 创建必要的目录
RUN mkdir -p uploads backups logs keys instance

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 启动命令 - 使用 gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--worker-class", "gthread", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "wsgi:app"]
