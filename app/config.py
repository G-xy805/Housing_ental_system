"""
应用配置模块
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置类"""
    
    # 基础配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 数据库配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URI = os.getenv('DATABASE_URI', f'sqlite:///{os.path.join(BASE_DIR, "housing_rental.db")}')
    SQLALCHEMY_DATABASE_URI = DATABASE_URI  # Flask-SQLAlchemy 需要这个
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'

    # 数据库连接池配置
    # 连接池大小：保持的连接数量
    SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', 10))

    # 最大溢出连接数：超过 pool_size 后允许创建的额外连接数
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', 10))

    # 连接回收时间（秒）：自动回收长时间未使用的连接，防止连接过期
    SQLALCHEMY_POOL_RECYCLE = int(os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600))

    # 获取连接超时时间（秒）：从连接池获取连接的最大等待时间
    SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', 30))

    # 连接健康检查：每次使用连接前检查连接是否有效
    SQLALCHEMY_POOL_PRE_PING = os.getenv('SQLALCHEMY_POOL_PRE_PING', 'True').lower() == 'true'
    
    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # CORS 配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'}
    
    # 备份配置
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    
    # 备份保留天数（自动清理超过此天数的备份）
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
    
    # 备份加密配置
    BACKUP_ENCRYPTION_ENABLED = os.getenv('BACKUP_ENCRYPTION_ENABLED', 'True').lower() == 'true'
    
    # 备份压缩配置
    BACKUP_COMPRESSION_ENABLED = os.getenv('BACKUP_COMPRESSION_ENABLED', 'True').lower() == 'true'
    
    # 自动备份配置
    BACKUP_AUTO_ENABLED = os.getenv('BACKUP_AUTO_ENABLED', 'True').lower() == 'true'
    BACKUP_AUTO_TIME = os.getenv('BACKUP_AUTO_TIME', '02:00')  # 每日凌晨2点
    BACKUP_AUTO_FREQUENCY = os.getenv('BACKUP_AUTO_FREQUENCY', 'daily')  # daily/weekly
    
    # 备份告警配置
    BACKUP_ALERT_ENABLED = os.getenv('BACKUP_ALERT_ENABLED', 'True').lower() == 'true'
    BACKUP_ALERT_EMAIL = os.getenv('BACKUP_ALERT_EMAIL', None)  # 告警邮箱
    
    # 调度器配置
    SCHEDULER_API_ENABLED = os.getenv('SCHEDULER_API_ENABLED', 'True').lower() == 'true'
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    
    # 慢查询日志配置
    # 慢查询阈值（秒）：执行时间超过此值的查询将被记录
    SLOW_QUERY_THRESHOLD = float(os.getenv('SLOW_QUERY_THRESHOLD', 1.0))
    
    # 慢查询日志文件路径
    SLOW_QUERY_LOG_FILE = os.path.join(BASE_DIR, 'logs', 'slow_queries.log')
    
    # 慢查询日志最大文件大小（字节）
    SLOW_QUERY_LOG_MAX_SIZE = int(os.getenv('SLOW_QUERY_LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
    
    # 慢查询日志备份数量
    SLOW_QUERY_LOG_BACKUP_COUNT = int(os.getenv('SLOW_QUERY_LOG_BACKUP_COUNT', 10))
    
    # 慢查询监控
    SLOW_QUERY_MONITOR_ENABLED = os.getenv('SLOW_QUERY_MONITOR_ENABLED', 'True').lower() == 'true'
    
    # Redis 缓存配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Redis 连接池配置
    REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', 50))
    REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', 5))
    REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', 5))
    REDIS_RETRY_ON_TIMEOUT = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'True').lower() == 'true'
    
    # 缓存配置
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))  # 默认缓存时间 5 分钟
    CACHE_KEY_PREFIX = os.getenv('CACHE_KEY_PREFIX', 'housing_rental:')
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    
    # 加密配置
    # 旧的 Fernet 加密密钥（用于向后兼容，解密旧数据）
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'generate-new-key-for-production')
    
    # AES-256-GCM 加密配置
    # 主密钥（Base64 编码的 256 位密钥）
    AES_PRIMARY_KEY = os.getenv('AES_PRIMARY_KEY', None)
    
    # 密钥轮换周期（天）
    AES_KEY_ROTATION_DAYS = int(os.getenv('AES_KEY_ROTATION_DAYS', 90))
    
    # 密钥存储路径
    AES_KEY_STORAGE_PATH = os.path.join(BASE_DIR, 'keys')
    
    # 加密审计日志配置
    ENCRYPTION_AUDIT_ENABLED = os.getenv('ENCRYPTION_AUDIT_ENABLED', 'True').lower() == 'true'
    ENCRYPTION_AUDIT_LOG_FILE = os.path.join(BASE_DIR, 'logs', 'encryption_audit.log')
    
    # HTTPS 安全配置
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    REMEMBER_COOKIE_SECURE = os.getenv('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))
    
    # 密码策略配置
    # 密码最小长度
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    
    # 密码是否要求包含大写字母
    PASSWORD_REQUIRE_UPPERCASE = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'True').lower() == 'true'
    
    # 密码是否要求包含小写字母
    PASSWORD_REQUIRE_LOWERCASE = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'True').lower() == 'true'
    
    # 密码是否要求包含数字
    PASSWORD_REQUIRE_DIGIT = os.getenv('PASSWORD_REQUIRE_DIGIT', 'True').lower() == 'true'
    
    # 密码是否要求包含特殊字符
    PASSWORD_REQUIRE_SPECIAL = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'True').lower() == 'true'
    
    # 密码过期天数（默认90天）
    PASSWORD_EXPIRE_DAYS = int(os.getenv('PASSWORD_EXPIRE_DAYS', 90))
    
    # 密码历史记录数量（防止重复使用最近N个密码，默认5个）
    PASSWORD_HISTORY_COUNT = int(os.getenv('PASSWORD_HISTORY_COUNT', 5))
    
    # 密码过期提醒天数（提前N天提醒用户修改密码，默认7天）
    PASSWORD_EXPIRE_WARNING_DAYS = int(os.getenv('PASSWORD_EXPIRE_WARNING_DAYS', 7))
    
    # 密码最少不同字符数
    PASSWORD_MIN_UNIQUE_CHARS = int(os.getenv('PASSWORD_MIN_UNIQUE_CHARS', 4))
    
    # 密码最大连续重复字符数
    PASSWORD_MAX_REPEATED_CHARS = int(os.getenv('PASSWORD_MAX_REPEATED_CHARS', 3))
    
    # 监控与可观测性配置
    # Prometheus 监控配置
    PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'True').lower() == 'true'
    PROMETHEUS_PATH = os.getenv('PROMETHEUS_PATH', '/metrics')
    
    # 健康检查配置
    HEALTH_DB_RESPONSE_TIME_WARNING = float(os.getenv('HEALTH_DB_RESPONSE_TIME_WARNING', 1.0))
    HEALTH_DB_RESPONSE_TIME_CRITICAL = float(os.getenv('HEALTH_DB_RESPONSE_TIME_CRITICAL', 3.0))
    HEALTH_CPU_USAGE_WARNING = int(os.getenv('HEALTH_CPU_USAGE_WARNING', 70))
    HEALTH_CPU_USAGE_CRITICAL = int(os.getenv('HEALTH_CPU_USAGE_CRITICAL', 90))
    HEALTH_MEMORY_USAGE_WARNING = int(os.getenv('HEALTH_MEMORY_USAGE_WARNING', 80))
    HEALTH_MEMORY_USAGE_CRITICAL = int(os.getenv('HEALTH_MEMORY_USAGE_CRITICAL', 95))
    HEALTH_DISK_USAGE_WARNING = int(os.getenv('HEALTH_DISK_USAGE_WARNING', 80))
    HEALTH_DISK_USAGE_CRITICAL = int(os.getenv('HEALTH_DISK_USAGE_CRITICAL', 95))
    HEALTH_POOL_USAGE_WARNING = int(os.getenv('HEALTH_POOL_USAGE_WARNING', 80))
    HEALTH_POOL_USAGE_CRITICAL = int(os.getenv('HEALTH_POOL_USAGE_CRITICAL', 95))
    
    # 性能监控配置
    PERF_RESPONSE_TIME_WARNING = float(os.getenv('PERF_RESPONSE_TIME_WARNING', 1.0))
    PERF_RESPONSE_TIME_CRITICAL = float(os.getenv('PERF_RESPONSE_TIME_CRITICAL', 3.0))
    PERF_ERROR_RATE_WARNING = float(os.getenv('PERF_ERROR_RATE_WARNING', 5.0))
    PERF_ERROR_RATE_CRITICAL = float(os.getenv('PERF_ERROR_RATE_CRITICAL', 10.0))
    PERF_QPS_WARNING = int(os.getenv('PERF_QPS_WARNING', 100))
    PERF_QPS_CRITICAL = int(os.getenv('PERF_QPS_CRITICAL', 200))
    
    # 告警配置
    ALERT_EMAIL_ENABLED = os.getenv('ALERT_EMAIL_ENABLED', 'False').lower() == 'true'
    ALERT_EMAIL_SMTP_SERVER = os.getenv('ALERT_EMAIL_SMTP_SERVER', '')
    ALERT_EMAIL_SMTP_PORT = int(os.getenv('ALERT_EMAIL_SMTP_PORT', 587))
    ALERT_EMAIL_USERNAME = os.getenv('ALERT_EMAIL_USERNAME', '')
    ALERT_EMAIL_PASSWORD = os.getenv('ALERT_EMAIL_PASSWORD', '')
    ALERT_EMAIL_RECIPIENTS = os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',') if os.getenv('ALERT_EMAIL_RECIPIENTS') else []
    ALERT_WEBHOOK_ENABLED = os.getenv('ALERT_WEBHOOK_ENABLED', 'False').lower() == 'true'
    ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', '')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    ENV = 'production'
    
    # 生产环境需要更严格的配置
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 测试环境禁用密码历史记录
    PASSWORD_HISTORY_COUNT = 0
    
    # 测试环境禁用缓存
    CACHE_ENABLED = False
    
    # 测试环境禁用调度器
    SCHEDULER_API_ENABLED = False
    
    # 测试环境禁用慢查询监控
    SLOW_QUERY_MONITOR_ENABLED = False
    
    # 测试环境禁用 Prometheus
    PROMETHEUS_ENABLED = False
    
    # 测试环境禁用加密审计
    ENCRYPTION_AUDIT_ENABLED = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
