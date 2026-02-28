"""
API 路由包
包含所有 API 路由蓝图
"""
from app.routes.auth import auth_bp
from app.routes.houses import houses_bp
from app.routes.upload import upload_bp
from app.routes.tenants import tenants_bp
from app.routes.contracts import contracts_bp
from app.routes.payments import payments_bp
from app.routes.statistics import statistics_bp
from app.routes.backup import backup_bp, init_auto_backup
from app.routes.employees import employees_bp
from app.routes.users import users_bp

__all__ = [
    'auth_bp', 
    'houses_bp', 
    'upload_bp',
    'tenants_bp',
    'contracts_bp',
    'payments_bp',
    'statistics_bp',
    'backup_bp',
    'employees_bp',
    'users_bp',
    'init_auto_backup'
]
