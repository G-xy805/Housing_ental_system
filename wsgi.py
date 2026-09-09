"""
房屋租赁系统 - Docker 入口文件
用于 Gunicorn 启动
"""
import os
import sys
from pathlib import Path

# 设置工作目录
app_root = Path(__file__).parent
os.chdir(app_root)

# 设置环境变量（必须在导入 app 之前）
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_APP', 'app')
os.environ.setdefault('DB_TYPE', 'mysql')

# 如果没有设置 MYSQL_HOST，使用默认值
if not os.getenv('MYSQL_HOST'):
    os.environ.setdefault('MYSQL_HOST', 'mysql')
if not os.getenv('MYSQL_PORT'):
    os.environ.setdefault('MYSQL_PORT', '3306')

# 创建必要的目录
for dir_name in ['logs', 'uploads', 'backups', 'keys', 'instance']:
    (app_root / dir_name).mkdir(exist_ok=True)

# 导入并创建应用
from app import create_app

# 创建应用实例
app = create_app(config_name='production')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
