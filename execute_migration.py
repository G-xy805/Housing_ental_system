"""
快速执行迁移脚本

使用方法：
    python execute_migration.py migrate       # 执行迁移
    python execute_migration.py rollback      # 执行回滚
"""

import sys
sys.path.insert(0, '.')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        print("=" * 60)
        print("执行回滚操作...")
        print("=" * 60)
        from app.migrations.migrate_landlord_data import run_rollback
        run_rollback()
    else:
        print("=" * 60)
        print("执行数据迁移...")
        print("=" * 60)
        print("\n【重要提示】")
        print("1. 确保已备份数据库")
        print("2. 确保已运行数据库架构更新 (update_schema.py)")
        print("3. 迁移过程中请勿中断程序")
        print("=" * 60)
        
        confirm = input("\n是否继续执行迁移？(输入 yes 继续): ")
        if confirm.lower() == 'yes':
            from app.migrations.migrate_landlord_data import run_migration
            run_migration()
        else:
            print("已取消迁移操作")
