# -*- mode: python ; coding: utf-8 -*-
"""
房屋租赁系统 - PyInstaller 打包配置文件

使用方法:
    pyinstaller HousingRentalSystem.spec

输出:
    release/HousingRentalSystem/HousingRentalSystem.exe
"""

import os
import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(SPECPATH)

# ==================== 基本配置 ====================

# 应用名称
app_name = 'HousingRentalSystem'

# 入口文件
entry_point = project_root / 'run_production.py'

# 输出目录（最终交付目录）
dist_dir = project_root / 'release'

# 构建目录
build_dir = project_root / 'build'

# ==================== 数据文件配置 ====================

datas = []

# 1. 前端构建产物（dist 目录 -> static）
frontend_dist = project_root / 'dist'
if frontend_dist.exists():
    # 添加 dist 目录下的所有文件到 static
    for item in frontend_dist.iterdir():
        if item.is_file():
            datas.append((str(item), 'static'))
        elif item.is_dir() and item.name != 'HousingRentalSystem':
            # 前端的 static 目录直接映射到 static（避免 static/static）
            if item.name == 'static':
                datas.append((str(item), 'static'))
            else:
                datas.append((str(item), f'static/{item.name}'))
    print(f"[OK] 前端构建产物: {frontend_dist} -> static")
else:
    print(f"[WARN] 前端构建产物不存在: {frontend_dist}")
    print("  请先运行 'npm run build' 构建前端")

# 2. 密钥文件
keys_dir = project_root / 'keys'
if keys_dir.exists():
    datas.append((str(keys_dir), 'keys'))
    print(f"[OK] 密钥文件目录: {keys_dir} -> keys")
else:
    print(f"[WARN] 密钥文件目录不存在: {keys_dir}")

# 3. 资源文件
resource_dir = project_root / 'resource'
if resource_dir.exists():
    datas.append((str(resource_dir), 'resource'))
    print(f"[OK] 资源文件目录: {resource_dir} -> resource")
else:
    print(f"[WARN] 资源文件目录不存在: {resource_dir}")

# 4. 环境变量示例文件（可选）
env_example = project_root / '.env.example'
if env_example.exists():
    datas.append((str(env_example), '.'))
    print(f"[OK] 环境变量示例: {env_example}")

# ==================== 隐藏导入配置 ====================

hiddenimports = [
    # Flask 核心模块
    'flask',
    'flask.json',
    'flask.globals',
    'flask.helpers',
    'flask.wrappers',
    'flask.app',
    'flask.blueprints',
    'flask.config',
    'flask.ctx',
    'flask.debughelpers',
    'flask.logging',
    'flask.sessions',
    'flask.signals',
    'flask.templating',
    'flask.testing',
    'flask.views',
    
    # Flask 扩展
    'flask_cors',
    'flask_cors.extension',
    'flask_cors.core',
    'flask_sqlalchemy',
    'flask_sqlalchemy.model',
    
    # SQLAlchemy 相关
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.ext',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.ext.mutable',
    'sqlalchemy.ext.associationproxy',
    'sqlalchemy.ext.hybrid',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.dialects.mysql',
    'sqlalchemy.dialects.postgresql',
    'sqlalchemy.engine',
    'sqlalchemy.pool',
    'sqlalchemy.sql',
    'sqlalchemy.event',
    'sqlalchemy.schema',
    'sqlalchemy.types',
    'sqlalchemy.util',
    
    # APScheduler 调度器
    'apscheduler',
    'apscheduler.schedulers',
    'apscheduler.schedulers.background',
    'apscheduler.schedulers.base',
    'apscheduler.executors',
    'apscheduler.executors.pool',
    'apscheduler.jobstores',
    'apscheduler.jobstores.memory',
    'apscheduler.jobstores.sqlalchemy',
    'apscheduler.triggers',
    'apscheduler.triggers.cron',
    'apscheduler.triggers.interval',
    'apscheduler.triggers.date',
    
    # 加密相关
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.primitives.ciphers.algorithms',
    'cryptography.hazmat.primitives.ciphers.modes',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.default',
    'Crypto',
    'Crypto.Cipher',
    'Crypto.Cipher.AES',
    'Crypto.Random',
    
    # JWT 认证
    'jwt',
    'jwt.algorithms',
    'jwt.exceptions',
    
    # Waitress 生产服务器
    'waitress',
    'waitress.server',
    'waitress.channel',
    'waitress.task',
    'waitress.utilities',
    'waitress.trigger',
    'waitress.adjustments',
    
    # 数据序列化
    'marshmallow',
    'marshmallow.fields',
    'marshmallow.schema',
    'marshmallow_sqlalchemy',
    'marshmallow_sqlalchemy.fields',
    
    # Redis 缓存
    'redis',
    'redis.client',
    'redis.connection',
    'redis.exceptions',
    
    # 监控相关
    'prometheus_client',
    'prometheus_client.core',
    'prometheus_flask_exporter',
    'psutil',
    
    # 文件处理
    'openpyxl',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'reportlab',
    'reportlab.lib',
    'reportlab.pdfgen',
    
    # 其他依赖
    'werkzeug',
    'werkzeug.security',
    'werkzeug.serving',
    'werkzeug.middleware',
    'werkzeug.middleware.shared_data',
    'jinja2',
    'jinja2.ext',
    'markupsafe',
    'dotenv',
    'tqdm',
    
    # 应用模块（确保所有模块都被包含）
    'app',
    'app.models',
    'app.models.user',
    'app.models.house',
    'app.models.tenant',
    'app.models.contract',
    'app.models.payment',
    'app.models.landlord',
    'app.models.landlord_contract',
    'app.models.room',
    'app.models.media',
    'app.models.backup_record',
    'app.models.backup_settings',
    'app.models.archive',
    'app.models.deposit_refund',
    'app.models.encryption_audit',
    'app.models.password_history',
    'app.models.sensitive_data_audit',
    'app.routes',
    'app.routes.auth',
    'app.routes.houses',
    'app.routes.tenants',
    'app.routes.contracts',
    'app.routes.payments',
    'app.routes.landlords',
    'app.routes.landlord_contracts',
    'app.routes.upload',
    'app.routes.statistics',
    'app.routes.backup',
    'app.routes.employees',
    'app.routes.users',
    'app.routes.audit',
    'app.routes.deposit_refunds',
    'app.routes.notifications',
    'app.routes.monitoring',
    'app.routes.public_houses',
    'app.routes.startup_tasks',
    'app.schemas',
    'app.schemas.user_schema',
    'app.schemas.house_schema',
    'app.schemas.tenant_schema',
    'app.schemas.contract_schema',
    'app.schemas.payment_schema',
    'app.schemas.landlord_schema',
    'app.schemas.landlord_contract_schema',
    'app.schemas.room_schema',
    'app.schemas.media_schema',
    'app.utils',
    'app.utils.decorators',
    'app.utils.responses',
    'app.utils.jwt',
    'app.utils.encryption',
    'app.utils.aes_encryption',
    'app.utils.backup_manager',
    'app.utils.backup_monitor',
    'app.utils.redis_cache',
    'app.utils.slow_query_monitor',
    'app.utils.performance_monitor',
    'app.utils.prometheus_metrics',
    'app.utils.health_check',
    'app.utils.alerting',
    'app.utils.async_audit',
    'app.utils.audit_decorator',
    'app.utils.audit_helpers',
    'app.utils.credit_score',
    'app.utils.delete_validation',
    'app.utils.error_handler',
    'app.utils.exceptions',
    'app.utils.file_lock',
    'app.utils.helpers',
    'app.utils.json_validator',
    'app.utils.key_rotation',
    'app.utils.model_utils',
    'app.utils.password_validator',
    'app.utils.query_optimizer',
    'app.utils.retry',
    'app.utils.sensitive_data_audit',
    'app.utils.startup_tasks',
    'app.utils.transaction',
    'app.config',
]

# ==================== 排除不需要的模块 ====================

excludes = [
    # 测试相关
    'pytest',
    'pytest_cov',
    'pytest_flask',
    'pytest_env',
    'factory',
    'faker',
    '_pytest',
    
    # 开发工具
    'IPython',
    'ipython',
    'jupyter',
    'notebook',
    'sphinx',
    
    # 不需要的数据库驱动
    'psycopg2',
    'psycopg2_binary',
    'pymysql',
    'mysql',
    'mysqlclient',
    
    # 其他不需要的模块
    'tkinter',
    'unittest',
    'pydoc',
    'doctest',
]

# ==================== Analysis 配置 ====================

a = Analysis(
    [str(entry_point)],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

# ==================== PYZ 配置（Python 字节码压缩包） ====================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# ==================== EXE 配置 ====================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩（如果可用）
    console=True,  # 显示控制台窗口，便于查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径，如 'resource/icon.ico'
    uac_admin=False,  # 不需要管理员权限
)

# ==================== COLLECT 配置（收集所有文件到输出目录） ====================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
    dest_dir=str(dist_dir),
)

# ==================== 打印配置摘要 ====================

print("\n" + "=" * 60)
print("PyInstaller 打包配置摘要")
print("=" * 60)
print(f"应用名称: {app_name}")
print(f"入口文件: {entry_point}")
print(f"输出目录: {dist_dir}")
print(f"构建目录: {build_dir}")
print(f"数据文件: {len(datas)} 项")
print(f"隐藏导入: {len(hiddenimports)} 个模块")
print(f"排除模块: {len(excludes)} 个模块")
print(f"控制台模式: True（显示日志窗口）")
print(f"管理员权限: False")
print("=" * 60)
print("\n使用方法:")
print("  pyinstaller HousingRentalSystem.spec")
print("\n构建完成后，可执行文件位于:")
print(f"  {dist_dir / (app_name + '.exe')}")
print("=" * 60 + "\n")
