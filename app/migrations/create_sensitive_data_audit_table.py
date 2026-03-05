"""
敏感数据访问审计日志表迁移脚本
创建 sensitive_data_audit_logs 表
"""
from datetime import datetime
from app import create_app, db
from app.models.sensitive_data_audit import SensitiveDataAuditLog


def upgrade():
    """
    升级数据库
    创建 sensitive_data_audit_logs 表
    """
    app = create_app()
    
    with app.app_context():
        print("开始创建敏感数据访问审计日志表...")
        
        # 创建表
        db.create_all()
        
        print("敏感数据访问审计日志表创建成功！")
        print(f"表名: {SensitiveDataAuditLog.__tablename__}")
        print(f"创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def downgrade():
    """
    降级数据库
    删除 sensitive_data_audit_logs 表
    """
    app = create_app()
    
    with app.app_context():
        print("开始删除敏感数据访问审计日志表...")
        
        # 删除表
        db.session.execute(f"DROP TABLE IF EXISTS {SensitiveDataAuditLog.__tablename__}")
        db.session.commit()
        
        print("敏感数据访问审计日志表删除成功！")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()
