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
from sqlalchemy import event
from sqlalchemy.pool import Pool

from .config import config


# 初始化扩展
db = SQLAlchemy()
scheduler = BackgroundScheduler()

# 连接池监控统计
pool_stats = {
    'connections_created': 0,
    'connections_checked_out': 0,
    'connections_checked_in': 0,
    'connections_closed': 0,
    'current_overflow': 0
}


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
    
    # 初始化自动备份任务（在调度器启动前添加任务）
    from app.routes.backup import init_auto_backup
    init_auto_backup(app)
    
    # 启动调度器
    if app.config['SCHEDULER_API_ENABLED']:
        scheduler.start()
        app.logger.info("APScheduler 调度器已启动")
    
    return app


def init_extensions(app):
    """初始化 Flask 扩展"""
    # 数据库
    db.init_app(app)
    
    # 配置连接池事件监听器
    setup_pool_event_listeners(app)
    
    # 配置慢查询监控
    setup_slow_query_monitoring(app)
    
    # 初始化 Redis 缓存
    setup_redis_cache(app)
    
    # 初始化备份管理器和监控器
    setup_backup_system(app)
    
    # 初始化监控与可观测性系统
    setup_monitoring_system(app)
    
    # 初始化异步审计队列
    from app.utils.async_audit import init_async_audit
    init_async_audit(app)
    
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
        
        # 创建默认管理员用户
        from app.models.user import create_default_admin
        create_default_admin()


def setup_pool_event_listeners(app):
    """
    配置数据库连接池事件监听器
    监控连接的创建、检出、归还和关闭事件
    """
    logger = logging.getLogger('pool_monitor')
    
    @event.listens_for(Pool, 'connect')
    def on_connect(dbapi_connection, connection_record):
        """连接创建时触发"""
        pool_stats['connections_created'] += 1
        logger.debug(
            f"数据库连接已创建 - 连接ID: {id(dbapi_connection)}, "
            f"总创建数: {pool_stats['connections_created']}"
        )
    
    @event.listens_for(Pool, 'checkout')
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """连接从池中检出时触发"""
        pool_stats['connections_checked_out'] += 1
        logger.debug(
            f"数据库连接已检出 - 连接ID: {id(dbapi_connection)}, "
            f"总检出数: {pool_stats['connections_checked_out']}"
        )
    
    @event.listens_for(Pool, 'checkin')
    def on_checkin(dbapi_connection, connection_record):
        """连接归还到池中时触发"""
        pool_stats['connections_checked_in'] += 1
        logger.debug(
            f"数据库连接已归还 - 连接ID: {id(dbapi_connection)}, "
            f"总归还数: {pool_stats['connections_checked_in']}"
        )
    
    @event.listens_for(Pool, 'close')
    def on_close(dbapi_connection, connection_record):
        """连接关闭时触发"""
        pool_stats['connections_closed'] += 1
        logger.debug(
            f"数据库连接已关闭 - 连接ID: {id(dbapi_connection)}, "
            f"总关闭数: {pool_stats['connections_closed']}"
        )
    
    # 记录连接池配置
    logger.info(
        f"数据库连接池配置 - "
        f"pool_size: {app.config.get('SQLALCHEMY_POOL_SIZE', 10)}, "
        f"max_overflow: {app.config.get('SQLALCHEMY_MAX_OVERFLOW', 10)}, "
        f"pool_recycle: {app.config.get('SQLALCHEMY_POOL_RECYCLE', 3600)}秒, "
        f"pool_timeout: {app.config.get('SQLALCHEMY_POOL_TIMEOUT', 30)}秒, "
        f"pool_pre_ping: {app.config.get('SQLALCHEMY_POOL_PRE_PING', True)}"
    )


def setup_slow_query_monitoring(app):
    """
    配置慢查询监控
    监控执行时间超过阈值的 SQL 查询
    """
    from app.utils.slow_query_monitor import setup_slow_query_monitor
    
    # 初始化慢查询监控器
    monitor = setup_slow_query_monitor(app, db)
    
    # 记录慢查询监控配置
    app.logger.info(
        f"慢查询监控配置 - "
        f"enabled: {app.config.get('SLOW_QUERY_MONITOR_ENABLED', True)}, "
        f"threshold: {app.config.get('SLOW_QUERY_THRESHOLD', 1.0)}秒, "
        f"log_file: {app.config.get('SLOW_QUERY_LOG_FILE', 'logs/slow_queries.log')}"
    )
    
    return monitor


def setup_redis_cache(app):
    """
    配置 Redis 缓存
    初始化 Redis 连接池和缓存管理器
    """
    from app.utils.redis_cache import get_cache_manager
    
    # 检查是否启用缓存
    cache_enabled = app.config.get('CACHE_ENABLED', True)
    
    if not cache_enabled:
        app.logger.info("Redis 缓存已禁用")
        return None
    
    try:
        # 初始化缓存管理器
        cache_manager = get_cache_manager()
        cache_manager.init_app(app)
        
        # 记录缓存配置
        app.logger.info(
            f"Redis 缓存配置 - "
            f"host: {app.config.get('REDIS_HOST')}, "
            f"port: {app.config.get('REDIS_PORT')}, "
            f"db: {app.config.get('REDIS_DB')}, "
            f"default_timeout: {app.config.get('CACHE_DEFAULT_TIMEOUT')}秒, "
            f"key_prefix: {app.config.get('CACHE_KEY_PREFIX')}"
        )
        
        # 注册关闭钩子
        @app.teardown_appcontext
        def close_redis_connection(exception=None):
            """应用关闭时清理 Redis 连接"""
            # 注意：不要在每次请求后关闭连接池，保持连接复用
            pass
        
        return cache_manager
        
    except Exception as e:
        app.logger.warning(f"Redis 缓存初始化失败，系统将在无缓存模式下运行: {str(e)}")
        return None


def setup_backup_system(app):
    """
    配置备份系统
    初始化备份管理器和监控器
    """
    from app.utils.backup_manager import get_backup_manager
    from app.utils.backup_monitor import get_backup_monitor
    
    try:
        # 初始化备份管理器
        backup_manager = get_backup_manager()
        backup_manager.init_app(app)
        
        # 初始化备份监控器
        backup_monitor = get_backup_monitor()
        backup_monitor.init_app(app)
        
        # 记录备份配置
        app.logger.info(
            f"备份系统配置 - "
            f"backup_folder: {app.config.get('BACKUP_FOLDER')}, "
            f"retention_days: {app.config.get('BACKUP_RETENTION_DAYS')}, "
            f"encryption_enabled: {app.config.get('BACKUP_ENCRYPTION_ENABLED')}, "
            f"compression_enabled: {app.config.get('BACKUP_COMPRESSION_ENABLED')}, "
            f"auto_backup_enabled: {app.config.get('BACKUP_AUTO_ENABLED')}, "
            f"auto_backup_time: {app.config.get('BACKUP_AUTO_TIME')}"
        )
        
        return backup_manager, backup_monitor
        
    except Exception as e:
        app.logger.error(f"备份系统初始化失败: {str(e)}")
        return None, None


def setup_auto_backup_schedule(app):
    """
    配置自动备份定时任务
    """
    try:
        from app.routes.backup import schedule_auto_backup_full
        
        backup_time = app.config.get('BACKUP_AUTO_TIME', '02:00')
        backup_frequency = app.config.get('BACKUP_AUTO_FREQUENCY', 'daily')
        
        # 解析备份时间
        hour, minute = map(int, backup_time.split(':'))
        
        # 添加定时任务，使用 coalesce=True 确保不重复执行
        if backup_frequency == 'daily':
            scheduler.add_job(
                schedule_auto_backup_full,
                'cron',
                hour=hour,
                minute=minute,
                id='auto_backup',
                replace_existing=True,
                coalesce=True
            )
            app.logger.info(f"已配置每日自动备份任务：{backup_time}")
        
        elif backup_frequency == 'weekly':
            scheduler.add_job(
                schedule_auto_backup_full,
                'cron',
                hour=hour,
                minute=minute,
                day_of_week='mon',
                id='auto_backup',
                replace_existing=True,
                coalesce=True
            )
            app.logger.info(f"已配置每周自动备份任务：周一 {backup_time}")
        
    except Exception as e:
        app.logger.error(f"配置自动备份定时任务失败: {str(e)}")


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
    
    # 注册承包合同管理蓝图
    from app.routes.landlord_contracts import landlord_contracts_bp
    app.register_blueprint(landlord_contracts_bp)
    
    # 注册房东管理蓝图
    from app.routes.landlords import landlords_bp
    app.register_blueprint(landlords_bp)
    
    # 注册对外房源查询蓝图
    from app.routes.public_houses import public_houses_bp
    app.register_blueprint(public_houses_bp)
    
    # 注册审计日志蓝图
    from app.routes.audit import audit_bp
    app.register_blueprint(audit_bp)
    
    # 注册健康检查端点
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': '房屋租赁系统运行正常'
        })
    
    # 连接池监控端点
    @app.route('/api/health/pool', methods=['GET'])
    def pool_health():
        """
        数据库连接池健康检查和监控端点
        返回连接池配置和实时统计信息
        """
        try:
            # 获取连接池对象（使用新的 API）
            engine = db.engine
            pool = engine.pool
            
            # 获取连接池状态
            pool_status = {
                'pool_size': pool.size(),
                'checked_in_connections': pool.checkedin(),
                'checked_out_connections': pool.checkedout(),
                'overflow_connections': pool.overflow(),
                'invalid_connections': pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0,
            }
            
            # 配置信息
            pool_config = {
                'pool_size': app.config.get('SQLALCHEMY_POOL_SIZE', 10),
                'max_overflow': app.config.get('SQLALCHEMY_MAX_OVERFLOW', 10),
                'pool_recycle': app.config.get('SQLALCHEMY_POOL_RECYCLE', 3600),
                'pool_timeout': app.config.get('SQLALCHEMY_POOL_TIMEOUT', 30),
                'pool_pre_ping': app.config.get('SQLALCHEMY_POOL_PRE_PING', True),
            }
            
            # 统计信息
            statistics = {
                'connections_created': pool_stats['connections_created'],
                'connections_checked_out': pool_stats['connections_checked_out'],
                'connections_checked_in': pool_stats['connections_checked_in'],
                'connections_closed': pool_stats['connections_closed'],
            }
            
            return jsonify({
                'status': 'healthy',
                'pool_status': pool_status,
                'pool_config': pool_config,
                'statistics': statistics,
                'message': '数据库连接池运行正常'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'连接池监控异常: {str(e)}'
            }), 500
    
    # 慢查询监控端点
    @app.route('/api/health/slow-queries', methods=['GET'])
    def slow_queries_health():
        """
        慢查询监控和统计端点
        返回慢查询统计信息和最近的慢查询记录
        """
        try:
            from app.utils.slow_query_monitor import get_slow_query_monitor
            
            monitor = get_slow_query_monitor()
            stats = monitor.get_stats()
            
            return jsonify({
                'status': 'healthy',
                'statistics': {
                    'total_queries': stats['total_queries'],
                    'slow_queries': stats['slow_queries'],
                    'slow_query_rate': f"{stats['slow_query_rate']}%",
                    'total_slow_query_time': f"{stats['total_slow_query_time']:.4f}秒",
                    'average_slow_query_time': f"{stats['average_slow_query_time']:.4f}秒",
                    'threshold': f"{stats['threshold']}秒",
                    'enabled': stats['enabled'],
                },
                'analysis': {
                    'by_table': stats['slow_queries_by_table'],
                    'by_type': stats['slow_queries_by_type'],
                },
                'recent_slow_queries': stats['recent_slow_queries'],
                'message': '慢查询监控运行正常'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'慢查询监控异常: {str(e)}'
            }), 500
    
    # 慢查询统计重置端点
    @app.route('/api/health/slow-queries/reset', methods=['POST'])
    def reset_slow_queries_stats():
        """
        重置慢查询统计信息
        """
        try:
            from app.utils.slow_query_monitor import get_slow_query_monitor
            
            monitor = get_slow_query_monitor()
            monitor.reset_stats()
            
            return jsonify({
                'status': 'success',
                'message': '慢查询统计信息已重置'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'重置统计信息失败: {str(e)}'
            }), 500
    
    # 慢查询配置更新端点
    @app.route('/api/health/slow-queries/config', methods=['PUT'])
    def update_slow_queries_config():
        """
        更新慢查询监控配置
        支持更新阈值和启用/禁用状态
        """
        try:
            from flask import request
            from app.utils.slow_query_monitor import get_slow_query_monitor
            
            data = request.get_json()
            monitor = get_slow_query_monitor()
            
            # 更新阈值
            if 'threshold' in data:
                threshold = float(data['threshold'])
                if threshold <= 0:
                    return jsonify({
                        'status': 'error',
                        'message': '阈值必须大于 0'
                    }), 400
                monitor.set_threshold(threshold)
            
            # 更新启用状态
            if 'enabled' in data:
                if data['enabled']:
                    monitor.enable()
                else:
                    monitor.disable()
            
            return jsonify({
                'status': 'success',
                'message': '慢查询监控配置已更新',
                'config': {
                    'threshold': monitor.threshold,
                    'enabled': monitor.enabled
                }
            })
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': f'参数格式错误: {str(e)}'
            }), 400
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'更新配置失败: {str(e)}'
            }), 500
    
    # 缓存监控端点
    @app.route('/api/health/cache', methods=['GET'])
    def cache_health():
        """
        Redis 缓存健康检查和监控端点
        返回缓存统计信息和 Redis 服务器状态
        """
        try:
            from app.utils.redis_cache import get_cache_manager
            
            cache_manager = get_cache_manager()
            
            # 检查 Redis 连接状态
            is_connected = cache_manager.is_connected
            
            if not is_connected:
                return jsonify({
                    'status': 'warning',
                    'message': 'Redis 缓存未连接，系统在无缓存模式下运行',
                    'cache_enabled': current_app.config.get('CACHE_ENABLED', True),
                    'redis_connected': False
                })
            
            # 获取缓存统计信息
            stats = cache_manager.get_stats()
            
            return jsonify({
                'status': 'healthy',
                'cache_enabled': current_app.config.get('CACHE_ENABLED', True),
                'redis_connected': True,
                'statistics': {
                    'hits': stats['hits'],
                    'misses': stats['misses'],
                    'errors': stats['errors'],
                    'sets': stats['sets'],
                    'deletes': stats['deletes'],
                    'hit_rate': stats['hit_rate'],
                    'total_requests': stats['total_requests'],
                    'total_time_saved': stats['total_time_saved']
                },
                'redis_info': stats.get('redis_info', {}),
                'config': {
                    'host': current_app.config.get('REDIS_HOST'),
                    'port': current_app.config.get('REDIS_PORT'),
                    'db': current_app.config.get('REDIS_DB'),
                    'default_timeout': f"{current_app.config.get('CACHE_DEFAULT_TIMEOUT')}秒",
                    'key_prefix': current_app.config.get('CACHE_KEY_PREFIX')
                },
                'message': 'Redis 缓存运行正常'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'缓存监控异常: {str(e)}'
            }), 500
    
    # 缓存统计重置端点
    @app.route('/api/health/cache/reset', methods=['POST'])
    def reset_cache_stats():
        """
        重置缓存统计信息
        """
        try:
            from app.utils.redis_cache import get_cache_manager
            
            cache_manager = get_cache_manager()
            cache_manager.reset_stats()
            
            return jsonify({
                'status': 'success',
                'message': '缓存统计信息已重置'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'重置统计信息失败: {str(e)}'
            }), 500
    
    # 缓存清除端点
    @app.route('/api/health/cache/clear', methods=['POST'])
    def clear_cache():
        """
        清除所有缓存
        """
        try:
            from flask import request
            from app.utils.redis_cache import get_cache_manager, invalidate_cache_pattern
            
            data = request.get_json() or {}
            pattern = data.get('pattern', '*')
            
            cache_manager = get_cache_manager()
            
            if not cache_manager.is_connected:
                return jsonify({
                    'status': 'warning',
                    'message': 'Redis 未连接，无需清除'
                })
            
            # 清除匹配的缓存
            deleted_count = invalidate_cache_pattern(pattern)
            
            return jsonify({
                'status': 'success',
                'message': f'已清除 {deleted_count} 个缓存键',
                'deleted_count': deleted_count,
                'pattern': pattern
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'清除缓存失败: {str(e)}'
            }), 500
    
    # API 根路径
    @app.route('/api/', methods=['GET'])
    def api_root():
        return jsonify({
            'name': '房屋租赁系统 API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'pool_health': '/api/health/pool (连接池监控)',
                'slow_queries': '/api/health/slow-queries (慢查询监控)',
                'cache_health': '/api/health/cache (缓存监控)',
                'auth': '/api/auth',
                'users': '/api/users',
                'employees': '/api/employees',
                'landlords': '/api/landlords',
                'houses': '/api/houses (内部接口，包含房东信息)',
                'public_houses': '/api/public/houses (对外接口，不含房东信息)',
                'rooms': '/api/houses/:id/rooms',
                'tenants': '/api/tenants',
                'contracts': '/api/contracts',
                'payments': '/api/payments',
                'upload': '/api/upload',
                'statistics': '/api/statistics',
                'backup': '/api/backup',
                'audit': '/api/audit (审计日志)'
            }
        })


def setup_monitoring_system(app):
    """
    配置监控与可观测性系统
    
    集成以下监控组件：
    1. Prometheus 指标采集
    2. 健康检查
    3. 性能监控
    4. 告警管理
    """
    try:
        # 初始化 Prometheus 监控指标
        from app.utils.prometheus_metrics import setup_prometheus_metrics
        setup_prometheus_metrics(app)
        
        # 初始化健康检查器
        from app.utils.health_check import setup_health_checker
        setup_health_checker(app, db)
        
        # 初始化性能监控器
        from app.utils.performance_monitor import setup_performance_monitor
        setup_performance_monitor(app)
        
        # 初始化告警管理器
        from app.utils.alerting import setup_alert_manager
        setup_alert_manager(app)
        
        # 注册监控蓝图
        from app.routes.monitoring import monitoring_bp
        app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
        
        # 集成连接池监控到 Prometheus
        _integrate_pool_monitoring(app)
        
        # 集成慢查询监控到 Prometheus
        _integrate_slow_query_monitoring(app)
        
        app.logger.info(
            f"监控与可观测性系统已启用 - "
            f"Prometheus: /metrics, "
            f"健康检查: /api/monitoring/health, "
            f"性能监控: /api/monitoring/performance, "
            f"告警管理: /api/monitoring/alerts"
        )
        
    except Exception as e:
        app.logger.error(f'监控与可观测性系统初始化失败: {str(e)}')


def _integrate_pool_monitoring(app):
    """
    集成连接池监控到 Prometheus
    将连接池事件转发到 Prometheus 指标
    """
    try:
        from app.utils.prometheus_metrics import get_metrics
        metrics = get_metrics()
        
        # 更新连接池指标
        def update_pool_metrics():
            try:
                engine = db.engine
                pool = engine.pool
                
                metrics.update_db_pool_metrics(
                    pool_size=pool.size(),
                    active=pool.checkedout(),
                    idle=pool.checkedin(),
                    overflow=pool.overflow()
                )
            except Exception:
                pass
        
        # 在每次请求后更新连接池指标
        @app.after_request
        def update_pool_metrics_after_request(response):
            update_pool_metrics()
            return response
        
    except Exception as e:
        app.logger.warning(f'连接池监控集成失败: {str(e)}')


def _integrate_slow_query_monitoring(app):
    """
    集成慢查询监控到 Prometheus
    将慢查询事件转发到 Prometheus 指标
    """
    try:
        from app.utils.prometheus_metrics import get_metrics
        from app.utils.slow_query_monitor import get_slow_query_monitor
        
        metrics = get_metrics()
        slow_query_monitor = get_slow_query_monitor()
        
        # 添加慢查询回调
        def on_slow_query(record):
            try:
                metrics.track_slow_query(
                    table=record.get('table', 'unknown'),
                    query_type=record.get('query_type', 'UNKNOWN')
                )
            except Exception:
                pass
        
        # 注意：这里需要在 SlowQueryMonitor 中添加回调机制
        # 目前通过定期同步统计数据实现
        
    except Exception as e:
        app.logger.warning(f'慢查询监控集成失败: {str(e)}')


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
    """
    注册错误处理器
    
    集成新的全局错误处理中间件，提供：
    1. 统一异常处理
    2. 错误日志记录
    3. 请求上下文跟踪
    4. 错误统计分析
    """
    # 注册新的全局错误处理中间件
    from app.utils.error_handler import register_error_handlers as register_global_errors
    register_global_errors(app)
    
    # 注册原有的 API 错误处理器（保持向后兼容）
    from app.utils.responses import register_error_handlers as register_api_errors
    register_api_errors(app)
