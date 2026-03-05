"""
数据库迁移脚本：添加密码历史记录表

功能：
1. 创建 password_history 表
2. 为现有用户创建初始密码历史记录
3. 添加必要的索引
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from sqlalchemy import text
from werkzeug.security import generate_password_hash


def migrate():
    """执行数据库迁移"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("开始迁移：添加密码历史记录表")
        print("=" * 60)
        
        try:
            # 1. 检查 password_history 表是否已存在
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='password_history'
            """)).scalar()
            
            if result == 0:
                print("\n步骤 1: 创建 password_history 表...")
                
                # 创建 password_history 表
                db.session.execute(text("""
                    CREATE TABLE password_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        password_set_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        password_expires_at DATETIME,
                        is_expired BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """))
                
                print("✓ password_history 表创建成功")
                
                # 2. 创建索引
                print("\n步骤 2: 创建索引...")
                
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_password_history_user_id 
                    ON password_history(user_id)
                """))
                
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_password_history_password_set_at 
                    ON password_history(password_set_at)
                """))
                
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_password_history_is_expired 
                    ON password_history(is_expired)
                """))
                
                print("✓ 索引创建成功")
                
                # 3. 为现有用户创建初始密码历史记录
                print("\n步骤 3: 为现有用户创建初始密码历史记录...")
                
                # 获取密码过期天数配置
                password_expire_days = app.config.get('PASSWORD_EXPIRE_DAYS', 90)
                expires_at = datetime.now() + timedelta(days=password_expire_days)
                
                # 查询所有用户
                users = db.session.execute(text("""
                    SELECT id, password_hash 
                    FROM users 
                    WHERE password_hash IS NOT NULL AND password_hash != ''
                """)).fetchall()
                
                if users:
                    print(f"找到 {len(users)} 个用户，正在创建密码历史记录...")
                    
                    for user in users:
                        user_id = user[0]
                        password_hash = user[1]
                        
                        # 检查是否已有密码历史记录
                        existing = db.session.execute(text("""
                            SELECT COUNT(*) 
                            FROM password_history 
                            WHERE user_id = :user_id
                        """), {'user_id': user_id}).scalar()
                        
                        if existing == 0:
                            # 创建初始密码历史记录
                            db.session.execute(text("""
                                INSERT INTO password_history 
                                (user_id, password_hash, password_set_at, password_expires_at, is_expired)
                                VALUES 
                                (:user_id, :password_hash, :password_set_at, :password_expires_at, :is_expired)
                            """), {
                                'user_id': user_id,
                                'password_hash': password_hash,
                                'password_set_at': datetime.now(),
                                'password_expires_at': expires_at,
                                'is_expired': False
                            })
                    
                    print(f"✓ 为 {len(users)} 个用户创建了初始密码历史记录")
                else:
                    print("✓ 没有找到需要处理的用户")
                
                # 提交事务
                db.session.commit()
                
                print("\n" + "=" * 60)
                print("✓ 迁移完成：密码历史记录表已成功创建")
                print("=" * 60)
                print("\n说明：")
                print("1. password_history 表已创建")
                print("2. 索引已创建（user_id, password_set_at, is_expired）")
                print(f"3. 现有用户的密码过期时间设置为 {password_expire_days} 天后")
                print("4. 密码策略已启用，用户修改密码时会自动记录历史")
                
            else:
                print("\n✓ password_history 表已存在，跳过迁移")
                
        except Exception as e:
            print(f"\n✗ 迁移失败：{str(e)}")
            db.session.rollback()
            raise


def rollback():
    """回滚迁移"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("开始回滚：删除密码历史记录表")
        print("=" * 60)
        
        try:
            # 检查表是否存在
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='password_history'
            """)).scalar()
            
            if result > 0:
                print("\n删除 password_history 表...")
                
                # 删除索引
                db.session.execute(text("DROP INDEX IF EXISTS idx_password_history_user_id"))
                db.session.execute(text("DROP INDEX IF EXISTS idx_password_history_password_set_at"))
                db.session.execute(text("DROP INDEX IF EXISTS idx_password_history_is_expired"))
                
                # 删除表
                db.session.execute(text("DROP TABLE password_history"))
                
                db.session.commit()
                
                print("\n✓ 回滚完成：password_history 表已删除")
            else:
                print("\n✓ password_history 表不存在，无需回滚")
                
        except Exception as e:
            print(f"\n✗ 回滚失败：{str(e)}")
            db.session.rollback()
            raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='密码历史记录表迁移脚本')
    parser.add_argument('--rollback', action='store_true', help='回滚迁移')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback()
    else:
        migrate()
