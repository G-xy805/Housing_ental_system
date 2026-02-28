"""
房屋租赁系统 - Flask 应用初始化
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

from .config import config


# 初始化扩展
db = SQLAlchemy()
scheduler = BackgroundScheduler()


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称 (development, production, testing)
    
    Returns:
        Flask 应用实例
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 确保上传和备份目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)
    
    # 注册静态文件路由（用于访问上传的文件）
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        """提供上传文件的访问"""
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # 初始化扩展
    init_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 配置日志
    setup_logging(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 启动调度器
    if app.config['SCHEDULER_API_ENABLED']:
        scheduler.start()
    
    # 注册关闭调度器钩子
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if exception:
            scheduler.shutdown()
    
    return app


def init_extensions(app):
    """初始化 Flask 扩展"""
    # 数据库
    db.init_app(app)
    
    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 创建数据库表
    with app.app_context():
        db.create_all()


def register_blueprints(app):
    """注册蓝图"""
    # 注册认证蓝图
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # 注册房源管理蓝图
    from app.routes.houses import houses_bp
    app.register_blueprint(houses_bp)
    
    # 注册文件上传蓝图
    from app.routes.upload import upload_bp
    app.register_blueprint(upload_bp)
    
    # 注册租客管理蓝图
    from app.routes.tenants import tenants_bp
    app.register_blueprint(tenants_bp)
    
    # 注册合同管理蓝图
    from app.routes.contracts import contracts_bp
    app.register_blueprint(contracts_bp)
    
    # 注册租金管理蓝图
    from app.routes.payments import payments_bp
    app.register_blueprint(payments_bp)
    
    # 注册统计管理蓝图
    from app.routes.statistics import statistics_bp
    app.register_blueprint(statistics_bp)
    
    # 注册备份管理蓝图
    from app.routes.backup import backup_bp
    app.register_blueprint(backup_bp)
    
    # 注册员工管理蓝图
    from app.routes.employees import employees_bp
    app.register_blueprint(employees_bp)
    
    # 注册用户管理蓝图
    from app.routes.users import users_bp
    app.register_blueprint(users_bp)
    
    # 初始化自动备份任务
    from app.routes.backup import init_auto_backup
    init_auto_backup(app)
    
    # 注册健康检查端点
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': '房屋租赁系统运行正常'
        })
    
    # API 根路径
    @app.route('/api/', methods=['GET'])
    def api_root():
        return jsonify({
            'name': '房屋租赁系统 API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'users': '/api/users',
                'employees': '/api/employees',
                'houses': '/api/houses',
                'rooms': '/api/houses/:id/rooms',
                'tenants': '/api/tenants',
                'contracts': '/api/contracts',
                'payments': '/api/payments',
                'upload': '/api/upload',
                'statistics': '/api/statistics',
                'backup': '/api/backup'
            }
        })


def setup_logging(app):
    """配置日志系统"""
    if app.debug:
        logging.basicConfig(level=logging.DEBUG)
        return
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # 应用日志记录器
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('房屋租赁系统启动')


def register_error_handlers(app):
    """注册错误处理器"""
    # 注册统一错误处理器
    from app.utils.responses import register_error_handlers as register_api_errors
    register_api_errors(app)
