"""
添加房源朝向和装修情况字段

迁移时间：2026-03-06
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import db
from app.models.house import House


def upgrade():
    """添加 orientation 和 decoration 字段到 houses 表"""
    try:
        # 检查字段是否已存在
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('houses')]
        
        with db.engine.connect() as conn:
            if 'orientation' not in columns:
                print("添加 orientation 字段...")
                conn.execute(db.text('ALTER TABLE houses ADD COLUMN orientation VARCHAR(20)'))
                conn.commit()
                print("✓ orientation 字段添加成功")
            else:
                print("✓ orientation 字段已存在，跳过")
            
            if 'decoration' not in columns:
                print("添加 decoration 字段...")
                conn.execute(db.text('ALTER TABLE houses ADD COLUMN decoration VARCHAR(20)'))
                conn.commit()
                print("✓ decoration 字段添加成功")
            else:
                print("✓ decoration 字段已存在，跳过")
        
        print("\n迁移完成！")
        return True
    except Exception as e:
        print(f"迁移失败: {e}")
        return False


def downgrade():
    """删除 orientation 和 decoration 字段"""
    try:
        with db.engine.connect() as conn:
            print("删除 orientation 字段...")
            conn.execute(db.text('ALTER TABLE houses DROP COLUMN orientation'))
            
            print("删除 decoration 字段...")
            conn.execute(db.text('ALTER TABLE houses DROP COLUMN decoration'))
            
            conn.commit()
        
        print("\n回滚完成！")
        return True
    except Exception as e:
        print(f"回滚失败: {e}")
        return False


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade()
